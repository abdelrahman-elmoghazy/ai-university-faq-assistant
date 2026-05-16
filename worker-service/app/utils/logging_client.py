import os
import logging
import requests

logger = logging.getLogger(__name__)

# Load internal API key for authentication with logging service
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "internal_key")


def send_log(logging_service_url: str, payload: dict) -> bool:
    """POST a structured log event to the logging service."""
    try:
        headers = {
            "X-Internal-Key": INTERNAL_API_KEY,
            "Content-Type": "application/json"
        }
        # Send key in both header and body for maximum compatibility
        full_payload = {**payload, "_internal_key": INTERNAL_API_KEY}
        resp = requests.post(
            f"{logging_service_url}/internal/logs",
            json=full_payload,
            headers=headers,
            timeout=5
        )
        if resp.status_code not in (200, 201):
            logger.warning(f"Logging service returned {resp.status_code} for {payload.get('action', 'unknown')}")
            return False
        
        # logger.debug(f"Log saved successfully: {payload.get('action')}")
        return True
    except Exception as exc:
        logger.error(f"Failed to reach logging service: {exc}")
        return False
