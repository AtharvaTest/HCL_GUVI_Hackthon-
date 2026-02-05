from __future__ import annotations

import json
import logging

from app.config import settings
from app.models import Message

logger = logging.getLogger(__name__)

RULE_KEYWORDS = {
    "urgent",
    "immediately",
    "verify",
    "otp",
    "kyc",
    "blocked",
    "suspended",
    "suspension",
    "bank",
    "account",
    "payment",
    "upi",
    "link",
    "click",
    "reward",
    "lottery",
}


class ScamDetector:
    def __init__(self) -> None:
        self._llm_client = None
        if settings.openai_api_key:
            try:
                from openai import OpenAI

                self._llm_client = OpenAI(api_key=settings.openai_api_key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to initialize OpenAI client: %s", exc)

    def detect(self, message: Message, history: list[Message]) -> tuple[bool, str]:
        rule_score = self._rule_score(message.text)
        if rule_score >= 2:
            return True, f"rule_score={rule_score}"

        if self._llm_client is not None:
            llm_result = self._llm_detect(message.text, history)
            if llm_result:
                return True, "llm_detected"

        return False, f"rule_score={rule_score}"

    def _rule_score(self, text: str) -> int:
        lowered = text.lower()
        return sum(1 for keyword in RULE_KEYWORDS if keyword in lowered)

    def _llm_detect(self, text: str, history: list[Message]) -> bool:
        snippet = "\n".join([f"{m.sender}: {m.text}" for m in history[-6:]])
        prompt = (
            "Classify whether this is likely scam intent. Answer JSON with field scam=true/false only.\n"
            f"History:\n{snippet}\nIncoming:\n{text}"
        )
        try:
            response = self._llm_client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                temperature=0,
            )
            raw = response.output_text.strip()
            data = json.loads(raw)
            return bool(data.get("scam", False))
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM scam check failed, fallback to rules only: %s", exc)
            return False


detector = ScamDetector()
