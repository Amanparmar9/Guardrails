import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="NeMo Guardrails POC Launcher")
    parser.add_argument("--mode", choices=["ui", "test"], default="ui", help="Launch Streamlit UI or run CLI tests")
    args = parser.parse_args()

    python_executable = sys.executable

    if args.mode == "ui":
        print("[LAUNCH] Launching NeMo Guardrails Streamlit Playground...")
        cmd = [python_executable, "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=localhost"]
        subprocess.run(cmd)
    elif args.mode == "test":
        print("[TEST] Executing Guardrails CLI Test Matrix...")
        from src.guardrail_manager import run_sync_process
        from src.test_cases import GUARDRAIL_TEST_CASES

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[WARN] GROQ_API_KEY environment variable not set! Enter API key to run LLM tests.")

        for tc in GUARDRAIL_TEST_CASES:
            print(f"\n==========================================")
            print(f"[{tc['id']}] {tc['category']}")
            print(f"Prompt: {tc['prompt']}")
            res = run_sync_process(tc['prompt'], api_key=api_key)
            print(f"Response: {res['response']}")
            print(f"Risk Score: {res['risk_score']}")
            print(f"PII Detected: {res['pii_detected']}")
            print(f"SQL Injection: {res['sql_injection_detected']}")
            print(f"Jailbreak: {res['jailbreak_detected']}")
            print(f"Competitor: {res['competitor_detected']}")

if __name__ == "__main__":
    main()
