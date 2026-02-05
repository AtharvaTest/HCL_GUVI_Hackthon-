from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.agent import agent
from app.callback_client import send_final_callback
from app.config import settings
from app.extractors import extract_intelligence_from_text
from app.memory_store import store
from app.models import CallbackPayload, ErrorResponse, HoneypotRequest, HoneypotSuccessResponse, Message
from app.scam_detector import detector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("honeypot-api")

app = FastAPI(title=settings.app_name)


def api_key_auth(x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(status="error", message=str(exc.detail)).model_dump(),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(status="error", message=str(exc.detail)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(status="error", message=f"Invalid request payload: {exc.errors()}").model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(status="error", message="Internal server error").model_dump(),
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _merged_history(payload: HoneypotRequest) -> list[Message]:
    merged = payload.conversation_history + [payload.message]
    return merged[-settings.max_stored_messages :]


def _should_finalize(total_turns: int, intel_item_count: int, scam_detected: bool, callback_completed: bool) -> bool:
    if callback_completed or not scam_detected:
        return False
    if total_turns >= settings.finalize_turn_threshold:
        return True
    if total_turns >= settings.finalize_min_turn_threshold and intel_item_count >= settings.finalize_min_intel_items:
        return True
    return False


@app.post(
    "/api/honeypot",
    response_model=HoneypotSuccessResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def honeypot(payload: HoneypotRequest, _: None = Depends(api_key_auth)) -> HoneypotSuccessResponse:
    session_id = payload.session_id
    merged_history = _merged_history(payload)
    state = store.replace_messages(session_id, merged_history)

    scam_detected, reason = detector.detect(payload.message, state.conversation)
    state = store.update_detection(session_id, scam_detected)

    intel = extract_intelligence_from_text(payload.message.text)
    state = store.update_intelligence(session_id, intel)

    reply = agent.generate_reply(payload.message, state.conversation, state.scam_detected)

    logger.info(
        "honeypot_event session_id=%s scam_detected=%s reason=%s turns=%s intel_count=%s channel=%s",
        session_id,
        state.scam_detected,
        reason,
        state.total_messages_exchanged,
        state.intel_item_count,
        payload.metadata.channel,
    )

    if _should_finalize(
        total_turns=state.total_messages_exchanged,
        intel_item_count=state.intel_item_count,
        scam_detected=state.scam_detected,
        callback_completed=state.callback_completed,
    ):
        callback_payload = CallbackPayload(
            sessionId=session_id,
            scamDetected=True,
            totalMessagesExchanged=state.total_messages_exchanged,
            extractedIntelligence=state.extracted_intelligence,
            agentNotes=agent.create_agent_notes(state.conversation, state.intel_item_count),
        )
        success, err = await send_final_callback(callback_payload)
        store.mark_callback_attempt(session_id, None if success else err)

    return HoneypotSuccessResponse(status="success", reply=reply)
