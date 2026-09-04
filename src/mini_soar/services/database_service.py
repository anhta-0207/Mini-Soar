import logging
import os

import pymysql
from dotenv import load_dotenv

logger = logging.getLogger("mini-soar")

load_dotenv()


class DatabaseService:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "127.0.0.1")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.database = os.getenv("DB_NAME", "mini_soar")
        self.user = os.getenv("DB_USER", "mini_soar")
        self.password = os.getenv("DB_PASSWORD", "")
    def get_remediation_distribution(self) -> dict:
        status_sql = """
            SELECT
                status,
                COUNT(*) AS count
            FROM remediation_history
            GROUP BY status
        """

        event_type_sql = """
            SELECT
                event_type,
                COUNT(*) AS count
            FROM remediation_history
            GROUP BY event_type
        """

        connection = self._connect()

        try:
            with connection.cursor(
                pymysql.cursors.DictCursor
            ) as cursor:
                cursor.execute(status_sql)
                status_rows = cursor.fetchall()

                cursor.execute(event_type_sql)
                event_type_rows = cursor.fetchall()

        finally:
            connection.close()

        status_distribution = {
            row["status"]: int(row["count"])
            for row in status_rows
        }

        event_type_distribution = {
            row["event_type"]: int(row["count"])
            for row in event_type_rows
        }

        return {
            "status": status_distribution,
            "event_type": event_type_distribution,
        }

    def _connect(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=5,
        )

    def test_connection(self) -> bool:
        try:
            connection = self._connect()

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

            connection.close()

            return result == (1,)

        except Exception:
            logger.exception("[DATABASE] Connection test failed")
            return False

    def insert_remediation(
        self,
        *,
        event_id: str,
        event_type: str,
        host: str,
        service: str,
        action: str,
        status: str,
        duration_seconds: float,
        message: str,
    ) -> None:
        sql = """
            INSERT INTO remediation_history (
                event_id,
                event_type,
                host,
                service,
                action,
                status,
                duration_seconds,
                message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        connection = self._connect()

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        event_id,
                        event_type,
                        host,
                        service,
                        action,
                        status,
                        duration_seconds,
                        message,
                    ),
                )

        finally:
            connection.close()

        logger.info(
            "[DATABASE] Remediation saved | "
            "event_id=%s action=%s status=%s",
            event_id,
            action,
            status,
        )

    def list_remediations(
        self,
        *,
        limit: int = 20,
        status: str | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        sql = """
            SELECT
                id,
                event_id,
                event_type,
                host,
                service,
                action,
                status,
                duration_seconds,
                message,
                created_at
            FROM remediation_history
        """

        conditions = []
        params = []

        if status:
            conditions.append("status = %s")
            params.append(status)

        if event_type:
            conditions.append("event_type = %s")
            params.append(event_type)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY id DESC LIMIT %s"

        params.append(limit)

        connection = self._connect()

        try:
            with connection.cursor(
                pymysql.cursors.DictCursor
            ) as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                return list(rows)

        finally:
            connection.close()

    def get_remediation_by_event_id(
        self,
        event_id: str,
    ) -> dict | None:
        sql = """
            SELECT
                id,
                event_id,
                event_type,
                host,
                service,
                action,
                status,
                duration_seconds,
                message,
                created_at
            FROM remediation_history
            WHERE event_id = %s
            ORDER BY id DESC
            LIMIT 1
        """

        connection = self._connect()

        try:
            with connection.cursor(
                pymysql.cursors.DictCursor
            ) as cursor:
                cursor.execute(
                    sql,
                    (event_id,),
                )

                return cursor.fetchone()

        finally:
            connection.close()
    def get_remediation_summary(self) -> dict:
        sql = """
            SELECT
                COUNT(*) AS total,

                SUM(CASE
                    WHEN status = 'SUCCESS' THEN 1
                    ELSE 0
                END) AS success,

                SUM(CASE
                    WHEN status = 'FAILED' THEN 1
                    ELSE 0
                END) AS failed,

                SUM(CASE
                    WHEN status = 'ERROR' THEN 1
                    ELSE 0
                END) AS error,

                SUM(CASE
                    WHEN status = 'SKIPPED' THEN 1
                    ELSE 0
                END) AS skipped,

                AVG(
                    CASE
                        WHEN status = 'SUCCESS'
                        THEN duration_seconds
                        ELSE NULL
                    END
                ) AS average_duration_seconds

            FROM remediation_history
        """

        connection = self._connect()

        try:
            with connection.cursor(
                pymysql.cursors.DictCursor
            ) as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()

        finally:
            connection.close()

        total = int(row["total"] or 0)
        success = int(row["success"] or 0)
        failed = int(row["failed"] or 0)
        error = int(row["error"] or 0)
        skipped = int(row["skipped"] or 0)

        average_duration = (
            float(row["average_duration_seconds"])
            if row["average_duration_seconds"] is not None
            else 0.0
        )

        success_rate = (
            round((success / total) * 100, 2)
            if total > 0
            else 0.0
        )

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "error": error,
            "skipped": skipped,
            "success_rate": success_rate,
            "average_duration_seconds": round(
                average_duration,
                3,
            ),
        }
