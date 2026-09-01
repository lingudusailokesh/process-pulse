from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.core.anonymizer import pseudonymize_id, mask_email, sanitize_for_llm

def test_password_hashing_and_verification():
    """Verify bcrypt password hashing and constant-time comparison."""
    raw_pass = "DeloitteConsulting2026!"
    hashed = get_password_hash(raw_pass)
    
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_token_generation_and_decoding():
    """Verify JWT claims encoding and decoding."""
    token = create_access_token(subject="USR_CONSULTANT", role="CONSULTANT")
    payload = decode_access_token(token)
    
    assert payload is not None
    assert payload.get("sub") == "USR_CONSULTANT"
    assert payload.get("role") == "CONSULTANT"

def test_pii_pseudonymization():
    """Verify deterministic pseudonym hashing."""
    emp_1 = pseudonymize_id("EMP_12345")
    emp_2 = pseudonymize_id("EMP_12345")
    emp_3 = pseudonymize_id("EMP_99999")
    
    # Deterministic for the same input
    assert emp_1 == emp_2
    # Distinct for different inputs
    assert emp_1 != emp_3
    assert emp_1.startswith("EMP_")

def test_email_masking():
    """Verify email masking for audit logs."""
    masked = mask_email("sarah.connor@deloitte.com")
    assert masked == "s***r@deloitte.com"

def test_llm_data_sanitizer():
    """Verify direct PII identifiers are scrubbed before LLM prompt injection."""
    raw_payload = {
        "requester_id": "EMP_SECRET_101",
        "actor_id": "MGR_JOHN_DOE",
        "email": "john.doe@company.com",
        "median_cycle_time_hours": 105.4,
        "nested": {
            "user_id": "USR_999",
            "stage": "IT Security Approval"
        }
    }
    sanitized = sanitize_for_llm(raw_payload)
    assert "requester_id" not in sanitized
    assert "actor_id" not in sanitized
    assert "email" not in sanitized
    assert sanitized["median_cycle_time_hours"] == 105.4
    assert "user_id" not in sanitized["nested"]
    assert sanitized["nested"]["stage"] == "IT Security Approval"
