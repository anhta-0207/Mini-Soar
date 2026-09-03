import logging

from fastapi import APIRouter, HTTPException, Query

from mini_soar.core.remediation import (
    RemediationListResponse,
    RemediationRecord,
)
from mini_soar.services.database_service import DatabaseService

logger = logging.getLogger("mini-soar")

router = APIRouter(
    tags=["Remediations"],
)

database = DatabaseService()


@router.get(
    "/remediations",
    response_model=RemediationListResponse,
)
def list_remediations(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    status: str | None = Query(
        default=None,
    ),
    event_type: str | None = Query(
        default=None,
    ),
):
    try:
        rows = database.list_remediations(
            limit=limit,
            status=status,
            event_type=event_type,
        )

        return {
            "count": len(rows),
            "items": rows,
        }

    except Exception:
        logger.exception(
            "[API] Failed to retrieve remediation history"
        )

        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve remediation history",
        )


@router.get(
    "/remediations/{event_id}",
    response_model=RemediationRecord,
)
def get_remediation(
    event_id: str,
):
    try:
        record = database.get_remediation_by_event_id(
            event_id
        )

    except Exception:
        logger.exception(
            "[API] Failed to retrieve remediation | "
            "event_id=%s",
            event_id,
        )

        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve remediation",
        )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Remediation record not found",
        )

    return record
