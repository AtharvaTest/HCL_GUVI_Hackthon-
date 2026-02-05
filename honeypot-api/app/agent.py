from __future__ import annotations

from app.models import Message

ENGAGEMENT_QUESTIONS = [
    "I didn't understand. Which bank is this about?",
    "Can you share the exact verification steps?",
    "Where should I complete this process, on app or website?",
    "Can you send the official link once more?",
    "What details do you need from me to avoid suspension?",
    "Is there a helpline number in case this fails?",
    "Do you need account number or only UPI ID?",
    "Can I complete this after confirming with my branch?",
]

SAFE_FALLBACK_REPLY = "Okay, can you explain the issue in more detail?"


class PersonaAgent:
    def generate_reply(self, latest_message: Message, history: list[Message], scam_detected: bool) -> str:
        if not scam_detected:
            return "Could you clarify what you mean?"

        turn_count = len(history) + 1
        if turn_count <= len(ENGAGEMENT_QUESTIONS):
            return ENGAGEMENT_QUESTIONS[turn_count - 1]

        text = latest_message.text.lower()
        if "upi" in text:
            return "I only use UPI sometimes, which UPI ID should I use exactly?"
        if "link" in text or "http" in text:
            return "I cannot open it right now, can you paste the full link here again?"
        if "account" in text:
            return "Which account number format do you need for this verification?"
        if "otp" in text:
            return "I have not received it yet, where should it come from?"
        return SAFE_FALLBACK_REPLY

    def create_agent_notes(self, history: list[Message], extracted_count: int) -> str:
        tactic_tags = []
        corpus = " ".join(m.text.lower() for m in history)
        if "urgent" in corpus or "immediately" in corpus:
            tactic_tags.append("urgency tactics")
        if "link" in corpus or "http" in corpus:
            tactic_tags.append("phishing link redirection")
        if "upi" in corpus or "payment" in corpus:
            tactic_tags.append("payment rerouting attempt")
        if "otp" in corpus:
            tactic_tags.append("OTP harvesting")
        summary = ", ".join(tactic_tags) if tactic_tags else "social engineering indicators"
        return f"Scammer engagement indicates {summary}; extracted {extracted_count} intelligence items."


agent = PersonaAgent()
