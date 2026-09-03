import logging

from fastapi import APIRouter

from mini_soar.core.events import ZabbixEvent
from mini_soar.playbooks.router import route_event
from mini_soar.services.event_parser import parse_zabbix_event


router = APIRouter()

logger = logging.getLogger("mini-soar")


@router.post("/webhooks/zabbix")
def receive_zabbix_event(event: ZabbixEvent):
    soar_event = parse_zabbix_event(event)

    logger.info(
        "event_id=%s event_type=%s state=%s host=%s service=%s",
        soar_event.event_id,
        soar_event.event_type.value,
        soar_event.state.value,
        soar_event.host,
        soar_event.service,
    )

    route_event(soar_event)

    return {
        "status": "accepted",
        "event": {
            "event_id": soar_event.event_id,
            "event_type": soar_event.event_type.value,
            "state": soar_event.state.value,
            "host": soar_event.host,
            "service": soar_event.service,
        },
    }
