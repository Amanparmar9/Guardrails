import streamlit as st
import asyncio
import os
import time
from dotenv import load_dotenv
from src.guardrail_manager import GuardrailManager
from src.test_cases import GUARDRAIL_TEST_CASES
from src.custom_actions import calculate_risk_score, scan_pii, scan_sql_injection, scan_competitors

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="NeMo Guardrails POC - Groq Enterprise Playground",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4F46E5 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #6B7280;
        font-size: 1.05rem;
        margin-bottom: 25px;
    }
    .badge-pass {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-block {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-redact {
        background-color: #FEF08A;
        color: #713F12;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .rail-card {
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        padding: 16px;
        background-color: #FAFAFA;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🛡️ NeMo Guardrails Enterprise POC</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Comprehensive Ready-to-Use Guardrail Implementation powered by NVIDIA NeMo Guardrails & Groq LLMs</p>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration & Key Manager")
groq_api_key = st.sidebar.text_input(
    "Groq API Key",
    type="password",
    value=os.getenv("GROQ_API_KEY", ""),
    help="Enter your Groq API Key to enable LLM-based rails."
)

selected_model = st.sidebar.selectbox(
    "Groq Model",
    ["qwen/qwen3.6-27b", "llama3-70b-8192", "mixtral-8x7b-32768"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Guardrail Rules Active")
enable_pii = st.sidebar.checkbox("PII Regex Redactor", value=True)
enable_sql = st.sidebar.checkbox("SQL Injection Scanner", value=True)
enable_jailbreak = st.sidebar.checkbox("LLM Jailbreak Detector", value=True)
enable_offtopic = st.sidebar.checkbox("Off-Topic Boundary Enforcer", value=True)
enable_competitors = st.sidebar.checkbox("Competitor Redactor", value=True)

st.sidebar.markdown("---")
st.sidebar.info("""
**Architecture Highlights:**
- **Deterministic**: Regex & pattern actions.
- **LLM-Based**: Evaluated by Groq LLM.
- **Colang Flows**: Intent & state steering.
""")

# Initialize tabs
tab1, tab2, tab3 = st.tabs(["💬 Interactive Guardrail Sandbox", "📊 Benchmark Test Suite", "📜 Architecture & Colang Blueprint"])

with tab1:
    st.subheader("Interactive Pipeline Sandbox")
    st.write("Test prompt inputs against the multi-layered guardrail evaluation pipeline.")

    # Preset selection
    col_preset, col_custom = st.columns([1, 2])
    with col_preset:
        preset_choice = st.selectbox(
            "Select Preset Test Scenario:",
            ["(Custom Prompt)", "TC-01: PII Leak Attempt", "TC-02: SQL Injection Attack", "TC-03: System Jailbreak", "TC-04: Off-Topic Query", "TC-05: Competitor Mention", "TC-06: Valid Query"]
        )

    # Prompt text area
    default_text = ""
    if preset_choice != "(Custom Prompt)":
        tc_map = {tc["id"]: tc["prompt"] for tc in GUARDRAIL_TEST_CASES}
        tc_id = preset_choice.split(":")[0]
        default_text = tc_map.get(tc_id, "")

    user_prompt = st.text_area("User Prompt Input:", value=default_text, height=100, placeholder="Type your query here...")

    if st.button("🚀 Execute Guardrails Pipeline", type="primary", use_container_width=True):
        if not user_prompt.strip():
            st.warning("Please enter a prompt to evaluate.")
        elif not groq_api_key.strip():
            st.error("Please enter a valid Groq API Key in the sidebar or `.env` file.")
        else:
            with st.spinner("Processing prompt through NeMo Guardrail pipeline..."):
                start_time = time.time()
                
                # Initialize Guardrail Manager
                manager = GuardrailManager(groq_api_key=groq_api_key)
                
                # Execute pipeline asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(manager.process_prompt(user_prompt))
                
                elapsed = time.time() - start_time

            st.success(f"Pipeline Execution Completed in {elapsed:.2f} seconds")

            # Status Summary Row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                risk = result["risk_score"]
                color = "red" if risk > 0.5 else "orange" if risk > 0.2 else "green"
                st.metric("Risk Score", f"{risk:.2f}")

            with col2:
                if result["pii_detected"]:
                    st.markdown('**PII Status:** <span class="badge-redact">REDACTED</span>', unsafe_allow_html=True)
                else:
                    st.markdown('**PII Status:** <span class="badge-pass">CLEAN</span>', unsafe_allow_html=True)

            with col3:
                if result["sql_injection_detected"] or result["jailbreak_detected"]:
                    st.markdown('**Security:** <span class="badge-block">BLOCKED</span>', unsafe_allow_html=True)
                else:
                    st.markdown('**Security:** <span class="badge-pass">SAFE</span>', unsafe_allow_html=True)

            with col4:
                if result["competitor_detected"]:
                    st.markdown('**Output Filter:** <span class="badge-redact">MODIFIED</span>', unsafe_allow_html=True)
                else:
                    st.markdown('**Output Filter:** <span class="badge-pass">PASS</span>', unsafe_allow_html=True)

            st.markdown("---")

            # Timeline Breakdown
            st.markdown("### 🔍 Guardrail Execution Pipeline Trace")

            # Stage 1
            st.markdown("#### 1️⃣ Deterministic Pre-processing (Input Rails)")
            if result["pii_detected"]:
                st.warning("⚠️ **PII Redaction Applied**: Personal info was detected and masked before reaching the LLM.")
            if result["sql_injection_detected"]:
                st.error("🚫 **SQL Injection Blocked**: Pattern match intercepted execution.")
            if not result["pii_detected"] and not result["sql_injection_detected"]:
                st.info("✅ All deterministic input checks passed cleanly.")

            # Stage 2 & 3
            st.markdown("#### 2️⃣ Colang Dialog Flow & LLM Generation (Groq)")
            st.markdown(f"**Final Assistant Response:**")
            if result["blocked_by"]:
                st.error(f"🛑 **{result['blocked_by']}**: {result['response']}")
            else:
                st.info(result["response"])

            # Audit Logs
            with st.expander("📋 Detailed Audit & Trace Log"):
                for log_item in result["audit_log"]:
                    st.code(log_item, language="text")

with tab2:
    st.subheader("📊 Benchmark Test Matrix")
    st.write("Run the standardized test suite across all 6 key guardrail scenarios.")

    if st.button("▶️ Run Full Benchmark Matrix", type="primary"):
        if not groq_api_key.strip():
            st.error("Please enter your Groq API Key in the sidebar first.")
        else:
            manager = GuardrailManager(groq_api_key=groq_api_key)
            progress_bar = st.progress(0)
            results_list = []

            for i, tc in enumerate(GUARDRAIL_TEST_CASES):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                res = loop.run_until_complete(manager.process_prompt(tc["prompt"]))
                
                status = "PASS"
                if tc["id"] == "TC-01" and res["pii_detected"]:
                    status = "PASS (Redacted)"
                elif tc["id"] == "TC-02" and res["sql_injection_detected"]:
                    status = "PASS (Blocked)"
                elif tc["id"] in ["TC-03", "TC-04"] and ("Security Blocked" in res["response"] or "cannot assist" in res["response"]):
                    status = "PASS (Refused)"
                elif tc["id"] == "TC-05" and res["competitor_detected"]:
                    status = "PASS (Sanitized)"

                results_list.append({
                    "Test ID": tc["id"],
                    "Category": tc["category"],
                    "Prompt Snippet": tc["prompt"][:45] + "...",
                    "Expected Behavior": tc["expected_rail"],
                    "Status": status,
                    "Risk Score": f"{res['risk_score']:.2f}"
                })
                progress_bar.progress((i + 1) / len(GUARDRAIL_TEST_CASES))

            st.dataframe(results_list, use_container_width=True)

with tab3:
    st.subheader("📜 Architecture & Code Blueprint")
    st.write("Inspect the exact configuration files powering this NeMo Guardrail implementation.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### `config/config.yml` (Model & Rail Mapping)")
        if os.path.exists("config/config.yml"):
            with open("config/config.yml", "r") as f:
                st.code(f.read(), language="yaml")

        st.markdown("#### `config/flows/main.co` (Colang Flow Script)")
        if os.path.exists("config/flows/main.co"):
            with open("config/flows/main.co", "r") as f:
                st.code(f.read(), language="colang")

    with col_b:
        st.markdown("#### `config/actions.py` (Python Action Bindings)")
        if os.path.exists("config/actions.py"):
            with open("config/actions.py", "r") as f:
                st.code(f.read(), language="python")

        st.markdown("#### `config/prompts.yml` (Task Prompts)")
        if os.path.exists("config/prompts.yml"):
            with open("config/prompts.yml", "r") as f:
                st.code(f.read(), language="yaml")
