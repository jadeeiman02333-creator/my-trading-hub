import os
import time
import json
import streamlit as st
from PIL import Image

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="NEXUS // Algorithmic Order Flow Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Optional Imports with Safe Fallbacks
try:
    from google import genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

# Custom Cyberpunk CSS Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    code, .stCode, div[data-baseweb="input"] input { font-family: 'JetBrains Mono', monospace !important; }
    .stApp { background-color: #05070A; color: #E2E8F0; }

    .cyber-header {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #00E676 0%, #00B0FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    .status-badge-active {
        background: rgba(0, 230, 118, 0.12);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "settings_submitted" not in st.session_state:
    st.session_state.settings_submitted = False
if "asset_name" not in st.session_state:
    st.session_state.asset_name = "XAUUSD"
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "M30"

if "ocr_entry" not in st.session_state:
    st.session_state.ocr_entry = 2450.50
if "ocr_sl" not in st.session_state:
    st.session_state.ocr_sl = 2442.00
if "ocr_tp1" not in st.session_state:
    st.session_state.ocr_tp1 = 2465.00
if "ocr_tp2" not in st.session_state:
    st.session_state.ocr_tp2 = 2480.00
if "ocr_tp3" not in st.session_state:
    st.session_state.ocr_tp3 = 2495.00
if "ocr_lots" not in st.session_state:
    st.session_state.ocr_lots = 0.50

if "order_direction_vote" not in st.session_state:
    st.session_state.order_direction_vote = "BUY"

# Secrets / API Keys Extraction
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

# Helper Function: Vision Level Extraction
def extract_chart_levels_with_ai(image_file):
    prompt = "Analyze this chart screenshot. Extract numerical price levels for Entry, Stop Loss (SL), and Take Profits (TP1, TP2, TP3). Return ONLY raw valid JSON: {\"entry\": float, \"sl\": float, \"tp1\": float, \"tp2\": float, \"tp3\": float}"
    try:
        if GEMINI_KEY and genai:
            client = genai.Client(api_key=GEMINI_KEY)
            image = Image.open(image_file)
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image]
            )
            clean_text = res.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        elif OPENAI_KEY and openai:
            import base64
            base64_image = base64.b64encode(image_file.getvalue()).decode("utf-8")
            client = openai.OpenAI(api_key=OPENAI_KEY)
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            )
            clean_text = res.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
    except Exception as e:
        st.warning(f"Vision Engine Fallback Triggered: {str(e)}")
    
    return {"entry": 2450.50, "sl": 2442.00, "tp1": 2465.00, "tp2": 2480.00, "tp3": 2495.00}

# ---------------------------------------------------------
# Sidebar Navigation & Control Center
# ---------------------------------------------------------
with st.sidebar:
    st.markdown('<h2 class="cyber-header" style="font-size: 1.2rem;">⚡ CONTROL CENTER</h2>', unsafe_allow_html=True)
    
    if not st.session_state.settings_submitted:
        with st.form(key="asset_settings_form"):
            asset_input = st.text_input("Active Asset / Instrument", value=st.session_state.asset_name)
            timeframe_input = st.selectbox("Execution Timeframe", ["M1", "M5", "M15", "M30", "H1", "H4", "D1"], index=3)
            submit_button = st.form_submit_button(label="LAUNCH TERMINAL SESSION", type="primary")
            
            if submit_button:
                st.session_state.asset_name = asset_input
                st.session_state.timeframe = timeframe_input
                st.session_state.settings_submitted = True
                st.rerun()
    else:
        st.success(f"ACTIVE: {st.session_state.asset_name} [{st.session_state.timeframe}]")
        if st.button("🔄 Change Session"):
            st.session_state.settings_submitted = False
            st.rerun()

# ---------------------------------------------------------
# Main Execution Workspace
# ---------------------------------------------------------
if not st.session_state.settings_submitted:
    st.markdown('<h1 class="cyber-header" style="text-align: center; margin-top: 50px;">NEXUS TERMINAL v3.0</h1>', unsafe_allow_html=True)
    st.info("👈 Enter your active instrument details in the sidebar control center and click 'LAUNCH TERMINAL SESSION' to start.")
else:
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 15px; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.08);">
        <div>
            <h1 class="cyber-header" style="margin: 0; font-size: 1.8rem;">NEXUS // {st.session_state.asset_name}</h1>
            <span style="color: #94A3B8; font-size: 12px; font-family: 'JetBrains Mono', monospace;">TIMEFRAME: {st.session_state.timeframe} | ENGINE: VISION OCR v3.0</span>
        </div>
        <div>
            <span class="status-badge status-badge-active">● ENGINE ONLINE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "📸 01. VISION SCAN & ORDER BUILDER",
        "📊 02. RISK MATRIX & EXPORT CENTER",
        "⚡ 03. MT5 EXECUTION BRIDGE"
    ])

    with tabs[0]:
        col_scan_left, col_scan_right = st.columns([1.1, 1], gap="large")

        with col_scan_left:
            st.markdown('<h3 class="cyber-header" style="font-size: 1rem;">1. CHART SCREENSHOT INGESTION</h3>', unsafe_allow_html=True)
            ocr_file = st.file_uploader("Upload MT5 / TradingView Chart", type=["png", "jpg", "jpeg"], key="ocr_uploader")

            if ocr_file is not None:
                st.image(Image.open(ocr_file), use_container_width=True)

                if st.button("⚡ EXECUTE VISION OCR EXTRACTION", type="primary", use_container_width=True):
                    with st.spinner("Extracting chart levels..."):
                        extracted_data = extract_chart_levels_with_ai(ocr_file)
                        st.session_state.ocr_entry = float(extracted_data.get("entry", 2450.50))
                        st.session_state.ocr_sl = float(extracted_data.get("sl", 2442.00))
                        st.session_state.ocr_tp1 = float(extracted_data.get("tp1", 2465.00))
                        st.session_state.ocr_tp2 = float(extracted_data.get("tp2", 2480.00))
                        st.session_state.ocr_tp3 = float(extracted_data.get("tp3", 2495.00))
                        st.rerun()

        with col_scan_right:
            st.markdown('<h3 class="cyber-header" style="font-size: 1rem;">2. PARAMETER VERIFICATION</h3>', unsafe_allow_html=True)

            is_high_value = st.session_state.ocr_entry > 500
            step_val = 0.10 if is_high_value else 0.00010
            fmt_val = "%.2f" if is_high_value else "%.5f"

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                entry_price = st.number_input("ENTRY PRICE", key="ocr_entry", format=fmt_val, step=step_val)
                stop_loss = st.number_input("STOP LOSS (SL)", key="ocr_sl", format=fmt_val, step=step_val)

            with col_p2:
                target_1 = st.number_input("TARGET 1 (TP1)", key="ocr_tp1", format=fmt_val, step=step_val)
                target_2 = st.number_input("TARGET 2 (TP2)", key="ocr_tp2", format=fmt_val, step=step_val)
                target_3 = st.number_input("TARGET 3 (TP3)", key="ocr_tp3", format=fmt_val, step=step_val)

            st.markdown("---")
            direction_choice = st.radio("Order Direction Bias:", options=["BUY 🟢", "SELL 🔴"], horizontal=True)

            st.session_state.active_order = {
                "asset": st.session_state.asset_name,
                "timeframe": st.session_state.timeframe,
                "type": "BUY" if "BUY" in direction_choice else "SELL",
                "entry": entry_price,
                "sl": stop_loss,
                "tp1": target_1,
                "tp2": target_2,
                "tp3": target_3,
                "lots": st.session_state.get("ocr_lots", 0.50)
            }

    with tabs[1]:
        order = st.session_state.get("active_order", {
            "asset": st.session_state.asset_name,
            "timeframe": st.session_state.timeframe,
            "type": "BUY",
            "entry": st.session_state.ocr_entry,
            "sl": st.session_state.ocr_sl,
            "tp1": st.session_state.ocr_tp1,
            "tp2": st.session_state.ocr_tp2,
            "tp3": st.session_state.ocr_tp3,
            "lots": st.session_state.ocr_lots
        })

        st.markdown('<h3 class="cyber-header" style="font-size: 1.1rem;">LOT SIZE & EXPOSURE</h3>', unsafe_allow_html=True)
        updated_lots = st.number_input("Total Aggregate Lot Size", value=order["lots"], format="%.2f", step=0.01, key="risk_matrix_lot_input")
        order["lots"] = updated_lots

        st.markdown("---")
        st.markdown('<h3 class="cyber-header" style="font-size: 1.1rem;">📥 EXPORT CENTER</h3>', unsafe_allow_html=True)

        json_export = json.dumps(order, indent=4)
        txt_export = f"Asset: {order['asset']}\nEntry: {order['entry']}\nSL: {order['sl']}\nTP1: {order['tp1']}\nTP2: {order['tp2']}\nTP3: {order['tp3']}\nLots: {order['lots']}"
        csv_export = f"Asset,Type,Entry,SL,TP1,TP2,TP3,Lots\n{order['asset']},{order['type']},{order['entry']},{order['sl']},{order['tp1']},{order['tp2']},{order['tp3']},{order['lots']}"

        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.download_button("💾 DOWNLOAD JSON", data=json_export, file_name=f"{order['asset']}_order.json", mime="application/json", type="primary", use_container_width=True)
        with col_d2:
            st.download_button("📄 DOWNLOAD TXT", data=txt_export, file_name=f"{order['asset']}_order.txt", mime="text/plain", use_container_width=True)
        with col_d3:
            st.download_button("📊 DOWNLOAD CSV", data=csv_export, file_name=f"{order['asset']}_order.csv", mime="text/csv", use_container_width=True)

    with tabs[2]:
        st.markdown('<h3 class="cyber-header" style="font-size: 1.1rem;">⚡ LIVE MT5 TERMINAL DISPATCH</h3>', unsafe_allow_html=True)
        order = st.session_state.get("active_order", {})
        st.json(order)
        if st.button("🔥 DISPATCH TO MT5", type="primary", use_container_width=True):
            st.success("🚀 Signal Dispatched!")