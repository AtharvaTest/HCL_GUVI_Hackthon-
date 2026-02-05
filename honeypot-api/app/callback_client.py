from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.models import CallbackPayload

logger = logging.getLogger(__name__)


async def send_final_callback(payload: CallbackPayload) -> tuple[bool, str | None]:
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(
                settings.callback_url,
                headers={"Content-Type": "application/json"},
                json=payload.model_dump(by_alias=True),
            )
            if 200 <= response.status_code < 300:
                return True, None
            error = f"callback_failed_status_{response.status_code}"
            logger.warning("Callback failed with status %s and body %s", response.status_code, response.text)
            return False, error
    except Exception as exc:  # noqa: BLE001
        logger.warning("Callback request failed: %s", exc)
        return False, str(exc)
