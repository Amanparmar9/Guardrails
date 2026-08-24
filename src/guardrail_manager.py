import os
import asyncio
from typing import Dict, Any, List
from nemoguardrails import RailsConfig, LLMRails
from src.custom_actions import scan_pii, scan_sql_injection, scan_competitors, calculate_risk_score

class GuardrailManager:
    def __init__(self, config_dir: str = None, groq_api_key: str = None):
        """
        Initializes NeMo Guardrails with Groq integration.
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
        
        self.config_dir = os.path.abspath(config_dir)
        
        # Set Groq API key in environment if provided
        api_key = groq_api_key or os.getenv("GROQ_API_KEY", "")
        if api_key:
            os.environ["GROQ_API_KEY"] = api_key
            os.environ["OPENAI_API_KEY"] = api_key  # NeMo uses OpenAI client wrapper for openai engine

        self.config = RailsConfig.from_path(self.config_dir)
        self.app = LLMRails(self.config)

    async def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Executes complete Guardrail pipeline on prompt:
        Deterministic Input Check -> LLM Input Rail -> Dialog Flow -> Output Rail.
        """
        audit_log = []
        input_rails_triggered = []
        output_rails_triggered = []

        # 1. Deterministic Pre-processing Checks
        risk_score = calculate_risk_score(prompt)
        audit_log.append(f"[Deterministic] Risk Score Evaluated: {risk_score:.2f}")

        pii_res = scan_pii(prompt)
        if pii_res["has_pii"]:
            input_rails_triggered.append("Deterministic PII Filter")
            audit_log.append(f"[Deterministic Input Rail] PII Detected: {', '.join(pii_res['pii_types'])}")
            audit_log.append(f"[Deterministic Input Rail] Redacted Prompt: '{pii_res['cleaned_text']}'")

        sql_res = scan_sql_injection(prompt)
        if sql_res["is_sql_injection"]:
            input_rails_triggered.append("Deterministic SQL Injection Defense")
            audit_log.append(f"[Deterministic Input Rail] SQL Injection Attempt Matched Pattern: '{sql_res['matched_pattern']}'")
            return {
                "response": "Security Blocked: Database manipulation commands and SQL script injections are strictly blocked by execution guardrails.",
                "risk_score": risk_score,
                "input_rails_triggered": input_rails_triggered,
                "output_rails_triggered": output_rails_triggered,
                "pii_detected": pii_res["has_pii"],
                "sql_injection_detected": True,
                "jailbreak_detected": False,
                "competitor_detected": False,
                "audit_log": audit_log,
                "blocked_by": "Deterministic SQL Injection Rail"
            }

        # Check basic jailbreak keywords deterministically if no API key set
        is_jailbreak_keyword = any(k in prompt.lower() for k in ["ignore previous instructions", "dan mode", "system prompt"])
        if is_jailbreak_keyword:
            input_rails_triggered.append("Deterministic Jailbreak Defense")
            audit_log.append("[Deterministic Input Rail] Jailbreak Keyword Detected")

        # 2. NeMo Guardrails Engine Execution (LLM Input Rails, Colang Dialog, LLM Output Rails)
        try:
            audit_log.append("[NeMo Pipeline] Invoking NeMo LLMRails engine via Groq...")
            messages = [{"role": "user", "content": pii_res["cleaned_text"]}]
            
            response_obj = await self.app.generate_async(messages=messages)
            
            if isinstance(response_obj, dict):
                raw_response = response_obj.get("content", "")
            else:
                raw_response = str(response_obj)

            audit_log.append(f"[NeMo Engine Response Received]: '{raw_response}'")

            # 3. Deterministic Post-processing Checks
            competitor_res = scan_competitors(raw_response)
            final_response = raw_response

            if competitor_res["has_competitor"]:
                output_rails_triggered.append("Deterministic Competitor Redactor")
                final_response = competitor_res["cleaned_text"]
                audit_log.append(f"[Deterministic Output Rail] Redacted Competitor Names: {', '.join(competitor_res['found_competitors'])}")

            is_blocked = "Security Blocked" in raw_response or "cannot assist" in raw_response or is_jailbreak_keyword

            return {
                "response": final_response,
                "risk_score": risk_score,
                "input_rails_triggered": input_rails_triggered,
                "output_rails_triggered": output_rails_triggered,
                "pii_detected": pii_res["has_pii"],
                "sql_injection_detected": False,
                "jailbreak_detected": is_blocked,
                "competitor_detected": competitor_res["has_competitor"],
                "audit_log": audit_log,
                "blocked_by": "NeMo Guardrails Policy" if is_blocked else None
            }

        except Exception as e:
            err_msg = str(e)
            if "Invalid API Key" in err_msg or "401" in err_msg or "APIKey" in err_msg:
                audit_log.append("⚠️ [Groq API Key Required]: Please enter a valid GROQ_API_KEY to execute LLM-based rails.")
                resp = "Groq API Key Required: Please provide your GROQ_API_KEY in the app sidebar or .env file to complete LLM evaluation."
                if pii_res["has_pii"]:
                    resp = f"Notice: PII detected and redacted to: '{pii_res['cleaned_text']}'. (Enter GROQ_API_KEY for LLM generation)."
            else:
                audit_log.append(f"[Engine Exception]: {err_msg}")
                resp = f"System Error executing Guardrails: {err_msg}"

            return {
                "response": resp,
                "risk_score": risk_score,
                "input_rails_triggered": input_rails_triggered,
                "output_rails_triggered": output_rails_triggered,
                "pii_detected": pii_res["has_pii"],
                "sql_injection_detected": False,
                "jailbreak_detected": is_jailbreak_keyword,
                "competitor_detected": False,
                "audit_log": audit_log,
                "blocked_by": "Groq Key Missing" if ("Invalid API Key" in err_msg or "401" in err_msg) else "System Error"
            }

def run_sync_process(prompt: str, api_key: str = None):
    """Synchronous helper for calling the Guardrail pipeline."""
    manager = GuardrailManager(groq_api_key=api_key)
    return asyncio.run(manager.process_prompt(prompt))
