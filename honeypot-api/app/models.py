from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SenderType = Literal["scammer", "user"]
ChannelType = Literal["SMS", "WhatsApp", "Email", "Chat"]


class Message(BaseModel):
    sender: SenderType
    text: str = Field(min_length=1, max_length=5000)
    timestamp: int = Field(ge=0)


class Metadata(BaseModel):
    channel: ChannelType
    language: str = Field(default="English", min_length=1, max_length=40)
    locale: str = Field(default="IN", min_length=1, max_length=10)


class HoneypotRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId", min_length=1, max_length=120)
    message: Message
    conversation_history: list[Message] = Field(default_factory=list, alias="conversationHistory")
    metadata: Metadata = Field(default_factory=lambda: Metadata(channel="SMS", language="English", locale="IN"))


class HoneypotSuccessResponse(BaseModel):
    status: Literal["success"]
    reply: str


class ErrorResponse(BaseModel):
    status: Literal["error"]
    message: str


class ExtractedIntelligence(BaseModel):
    bank_accounts: list[str] = Field(default_factory=list, alias="bankAccounts")
    upi_ids: list[str] = Field(default_factory=list, alias="upiIds")
    phishing_links: list[str] = Field(default_factory=list, alias="phishingLinks")
    phone_numbers: list[str] = Field(default_factory=list, alias="phoneNumbers")
    suspicious_keywords: list[str] = Field(default_factory=list, alias="suspiciousKeywords")


class CallbackPayload(BaseModel):
    session_id: str = Field(alias="sessionId")
    scam_detected: bool = Field(alias="scamDetected")
    total_messages_exchanged: int = Field(alias="totalMessagesExchanged")
    extracted_intelligence: ExtractedIntelligence = Field(alias="extractedIntelligence")
    agent_notes: str = Field(alias="agentNotes")
