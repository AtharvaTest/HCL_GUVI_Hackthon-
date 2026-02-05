from dataclasses import dataclass, field
from threading import Lock

from app.config import settings
from app.extractors import count_intel_items, merge_intelligence
from app.models import ExtractedIntelligence, Message


@dataclass
class SessionState:
    session_id: str
    conversation: list[Message] = field(default_factory=list)
    scam_detected: bool = False
    extracted_intelligence: ExtractedIntelligence = field(default_factory=ExtractedIntelligence)
    callback_completed: bool = False
    callback_attempted: bool = False
    callback_last_error: str | None = None

    @property
    def total_messages_exchanged(self) -> int:
        return len(self.conversation)

    @property
    def intel_item_count(self) -> int:
        return count_intel_items(self.extracted_intelligence)


class InMemorySessionStore:
    def __init__(self) -> None:
        self._store: dict[str, SessionState] = {}
        self._lock = Lock()

    def _get_or_create_unlocked(self, session_id: str) -> SessionState:
        state = self._store.get(session_id)
        if state is None:
            state = SessionState(session_id=session_id)
            self._store[session_id] = state
        return state

    def get_or_create(self, session_id: str) -> SessionState:
        with self._lock:
            return self._get_or_create_unlocked(session_id)

    def replace_messages(self, session_id: str, messages: list[Message]) -> SessionState:
        with self._lock:
            state = self._get_or_create_unlocked(session_id)
            state.conversation = messages[-settings.max_stored_messages :]
            return state

    def update_detection(self, session_id: str, scam_detected: bool) -> SessionState:
        with self._lock:
            state = self._get_or_create_unlocked(session_id)
            state.scam_detected = state.scam_detected or scam_detected
            return state

    def update_intelligence(self, session_id: str, intel: ExtractedIntelligence) -> SessionState:
        with self._lock:
            state = self._get_or_create_unlocked(session_id)
            state.extracted_intelligence = merge_intelligence(state.extracted_intelligence, [intel])
            return state

    def mark_callback_attempt(self, session_id: str, error: str | None) -> SessionState:
        with self._lock:
            state = self._get_or_create_unlocked(session_id)
            state.callback_attempted = True
            state.callback_last_error = error
            state.callback_completed = error is None
            return state


store = InMemorySessionStore()
