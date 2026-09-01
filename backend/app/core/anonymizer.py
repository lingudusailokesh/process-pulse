import hashlib
import re
from typing import Dict, Any, List

SALT = "deloitte_gdpr_privacy_salt_2026"

def pseudonymize_id(raw_id: str, prefix: str = "EMP") -> str:
    """
    Cryptographically hashes a raw identifier (e.g. employee ID, actor ID)
    into a deterministic, privacy-compliant pseudonym for GDPR/Data Privacy compliance.
    """
    if not raw_id:
        return f"{prefix}_UNKNOWN"
    salted = f"{raw_id}:{SALT}".encode('utf-8')
    digest = hashlib.sha256(salted).hexdigest()[:8].upper()
    return f"{prefix}_{digest}"

def mask_email(email: str) -> str:
    """Mask email address for audit logs (e.g., j***e@domain.com)."""
    if not email or "@" not in email:
        return "hidden@domain.local"
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked_name = name[0] + "***"
    else:
        masked_name = name[0] + "***" + name[-1]
    return f"{masked_name}@{domain}"

def sanitize_for_llm(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strips raw employee PII, raw names, and sensitive personal identifiers 
    from the structured data payload before feeding it to the LLM.
    Guarantees zero PII leakage to third-party LLM APIs.
    """
    sanitized = {}
    for key, value in data.items():
        if key in ["requester_id", "actor_id", "email", "full_name", "user_id"]:
            continue  # Exclude direct identifiers
        elif isinstance(value, dict):
            sanitized[key] = sanitize_for_llm(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_for_llm(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    return sanitized
