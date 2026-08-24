import re
from typing import Dict, Any, List

# PII Regex Patterns
EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
SSN_REGEX = r'\b\d{3}-\d{2}-\d{4}\b'
CREDIT_CARD_REGEX = r'\b(?:\d[ -]*?){13,16}\b'
PHONE_REGEX = r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\d{5}[-.\s]?\d{5}|\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{10})\b'

# SQL Injection Patterns
SQL_INJECTION_PATTERNS = [
    r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE)\b",
    r"(?i)\bOR\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",
    r"(?i)UNION\s+(ALL\s+)?SELECT",
    r"--;",
    r"/\*.*?\*/",
    r";\s*(DROP|DELETE|UPDATE|ALTER)"
]

# Competitor Brands
COMPETITORS = ["CompetitorX", "EvilAI", "BadCorp", "RivalTech", "StolenModel"]

def scan_pii(text: str) -> Dict[str, Any]:
    """
    Deterministic PII scanner using regex patterns.
    """
    text = text or ""
    found_types = []
    cleaned_text = text

    if re.search(EMAIL_REGEX, text):
        found_types.append("Email Address")
        cleaned_text = re.sub(EMAIL_REGEX, "[REDACTED EMAIL]", cleaned_text)

    if re.search(SSN_REGEX, text):
        found_types.append("Social Security Number")
        cleaned_text = re.sub(SSN_REGEX, "[REDACTED SSN]", cleaned_text)

    if re.search(CREDIT_CARD_REGEX, text):
        found_types.append("Credit Card Number")
        cleaned_text = re.sub(CREDIT_CARD_REGEX, "[REDACTED CREDIT CARD]", cleaned_text)

    if re.search(PHONE_REGEX, text):
        found_types.append("Phone Number")
        cleaned_text = re.sub(PHONE_REGEX, "[REDACTED PHONE]", cleaned_text)

    return {
        "has_pii": len(found_types) > 0,
        "pii_types": found_types,
        "cleaned_text": cleaned_text
    }

def scan_phone_number(text: str) -> Dict[str, Any]:
    """
    Explicit scanner for phone numbers.
    """
    text = text or ""
    match = re.search(PHONE_REGEX, text)
    if match:
        cleaned_text = re.sub(PHONE_REGEX, "[REDACTED PHONE]", text)
        return {
            "has_phone": True,
            "detected_phone": match.group(0),
            "cleaned_text": cleaned_text
        }
    return {
        "has_phone": False,
        "detected_phone": "",
        "cleaned_text": text
    }

def scan_sql_injection(text: str) -> Dict[str, Any]:
    """
    Deterministic SQL / Command Injection scanner.
    """
    text = text or ""
    for pattern in SQL_INJECTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return {
                "is_sql_injection": True,
                "matched_pattern": match.group(0)
            }
    return {
        "is_sql_injection": False,
        "matched_pattern": ""
    }

def scan_competitors(text: str) -> Dict[str, Any]:
    """
    Scans output for competitor brand names.
    """
    text = text or ""
    found = []
    cleaned_text = text
    for comp in COMPETITORS:
        if re.search(r'\b' + re.escape(comp) + r'\b', text, re.IGNORECASE):
            found.append(comp)
            cleaned_text = re.sub(r'\b' + re.escape(comp) + r'\b', "[OUR PARTNER]", cleaned_text, flags=re.IGNORECASE)

    return {
        "has_competitor": len(found) > 0,
        "found_competitors": found,
        "cleaned_text": cleaned_text
    }

def calculate_risk_score(text: str) -> float:
    """
    Calculates a heuristic risk score (0.0 - 1.0) based on input characteristics.
    """
    text = text or ""
    score = 0.0
    pii_res = scan_pii(text)
    if pii_res["has_pii"]:
        score += 0.4

    sql_res = scan_sql_injection(text)
    if sql_res["is_sql_injection"]:
        score += 0.5

    # Check suspicious keywords
    suspicious_words = ["ignore previous instructions", "system prompt", "jailbreak", "override", "dan mode", "sudo"]
    for word in suspicious_words:
        if word in text.lower():
            score += 0.3

    return min(score, 1.0)
