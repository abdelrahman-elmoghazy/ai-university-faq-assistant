"""
Logging service HTTP client
"""
import logging
import requests

logger = logging.getLogger(__name__)


def send_log(logging_service_url: str, payload: dict) -> bool:
    """POST a structured log event to the logging service."""
    try:
        resp = requests.post(
            f"{logging_service_url}/internal/logs",
            json=payload,
            timeout=5
        )
        if resp.status_code not in (200, 201):
            logger.warning(f"Logging service returned {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    except Exception as exc:
        logger.error(f"Failed to reach logging service: {exc}")
        return False
