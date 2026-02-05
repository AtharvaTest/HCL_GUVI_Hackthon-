import re
from collections.abc import Iterable

from app.models import ExtractedIntelligence


UPI_RE = re.compile(r"\b[a-zA-Z0-9._-]{2,}@[a-zA-Z]{2,20}\b")
URL_RE = re.compile(r"\bhttps?://[^\s]+", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}\b")
ACCOUNT_RE = re.compile(r"\b\d{9,18}\b")

SUSPICIOUS_KEYWORDS = {
    "urgent",
    "verify",
    "account blocked",
    "blocked",
    "otp",
    "kyc",
    "upi",
    "suspend",
    "suspension",
    "payment",
    "reward",
    "winner",
    "bank account",
    "update",
}

_ALLOWED_UPI_DOMAINS = {
    "upi",
    "okhdfcbank",
    "okicici",
    "oksbi",
    "okaxis",
    "ibl",
    "paytm",
    "ybl",
    "axl",
}


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"
    if len(digits) == 10:
        return f"+91{digits}"
    return phone.strip()


def _normalize_url(url: str) -> str:
    return url.rstrip('.,;!?)\"\'')


def _valid_bank_account(candidate: str) -> bool:
    if len(set(candidate)) == 1:
        return False
    if candidate.startswith("177"):
        return False
    return True


def _extract_keywords(text: str) -> list[str]:
    lowered = text.lower()
    return sorted([kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered])


def _extract_upi(text: str) -> list[str]:
    results: list[str] = []
    for found in UPI_RE.findall(text):
        name, _, domain = found.partition("@")
        if name and domain.lower() in _ALLOWED_UPI_DOMAINS:
            results.append(found.lower())
    return sorted(set(results))


def extract_intelligence_from_text(text: str) -> ExtractedIntelligence:
    upi_ids = _extract_upi(text)
    links = sorted({_normalize_url(link) for link in URL_RE.findall(text)})
    phones = sorted({_normalize_phone(phone) for phone in PHONE_RE.findall(text)})
    accounts = sorted(
        {
            acc
            for acc in ACCOUNT_RE.findall(text)
            if _valid_bank_account(acc) and acc not in {p.replace("+91", "") for p in phones}
        }
    )
    keywords = _extract_keywords(text)
    return ExtractedIntelligence(
        bankAccounts=accounts,
        upiIds=upi_ids,
        phishingLinks=links,
        phoneNumbers=phones,
        suspiciousKeywords=keywords,
    )


def merge_intelligence(base: ExtractedIntelligence, additions: Iterable[ExtractedIntelligence]) -> ExtractedIntelligence:
    bank = set(base.bank_accounts)
    upi = set(base.upi_ids)
    links = set(base.phishing_links)
    phones = set(base.phone_numbers)
    keywords = set(base.suspicious_keywords)

    for item in additions:
        bank.update(item.bank_accounts)
        upi.update(item.upi_ids)
        links.update(item.phishing_links)
        phones.update(item.phone_numbers)
        keywords.update(item.suspicious_keywords)

    return ExtractedIntelligence(
        bankAccounts=sorted(bank),
        upiIds=sorted(upi),
        phishingLinks=sorted(links),
        phoneNumbers=sorted(phones),
        suspiciousKeywords=sorted(keywords),
    )


def count_intel_items(data: ExtractedIntelligence) -> int:
    return sum(
        [
            len(data.bank_accounts),
            len(data.upi_ids),
            len(data.phishing_links),
            len(data.phone_numbers),
            len(data.suspicious_keywords),
        ]
    )
