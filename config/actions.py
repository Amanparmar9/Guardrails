from nemoguardrails.actions import action
import sys
import os

# Ensure src is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.custom_actions import scan_pii, scan_sql_injection, scan_competitors, scan_phone_number

@action(name="check_pii_input")
async def check_pii_input(context: dict = None):
    """Action to check and sanitize PII in user input."""
    if not context:
        return {"has_pii": False}

    user_input = context.get("last_user_message") or context.get("user_message") or ""
    res = scan_pii(user_input)
    if res["has_pii"]:
        return {
            "has_pii": True,
            "cleaned_text": res["cleaned_text"],
            "pii_types": ", ".join(res["pii_types"])
        }
    return {"has_pii": False}

@action(name="check_phone_input")
async def check_phone_input(context: dict = None):
    """Action to detect and redact phone numbers explicitly."""
    if not context:
        return {"has_phone": False}

    user_input = context.get("last_user_message") or context.get("user_message") or ""
    res = scan_phone_number(user_input)
    if res["has_phone"]:
        return {
            "has_phone": True,
            "detected_phone": res["detected_phone"],
            "cleaned_text": res["cleaned_text"]
        }
    return {"has_phone": False}

@action(name="check_sql_injection_input")
async def check_sql_injection_input(context: dict = None):
    """Action to detect SQL injection attempts in user input."""
    if not context:
        return {"is_sql_injection": False}

    user_input = context.get("last_user_message") or context.get("user_message") or ""
    res = scan_sql_injection(user_input)
    if res["is_sql_injection"]:
        return {
            "is_sql_injection": True,
            "matched_pattern": res["matched_pattern"]
        }
    return {"is_sql_injection": False}

@action(name="check_competitor_output")
async def check_competitor_output(context: dict = None):
    """Action to redact competitor mentions from LLM output."""
    if not context:
        return {"has_competitor": False}

    bot_response = context.get("last_bot_message") or context.get("bot_message") or ""
    res = scan_competitors(bot_response)
    if res["has_competitor"]:
        return {
            "has_competitor": True,
            "cleaned_response": res["cleaned_text"]
        }
    return {"has_competitor": False}
