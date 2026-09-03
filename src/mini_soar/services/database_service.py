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
