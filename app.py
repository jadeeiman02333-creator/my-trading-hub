import os
import json
import streamlit as st
from PIL import Image

# ---------------------------------------------------------
# Page Configuration & High-Tech Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Killzone // Algorithmic Terminal",
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

# Custom Modern Cyberpunk CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    code, .stCode, input {
        font-family: 'JetBrains Mono', monospace !important;
    }

    .stApp {
        background-color: #05070A;
        color: #E2E8F0;
    }

    .killzone-title {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 900;
        font-size: 2.2rem;
        letter-spacing: -1px;
        background: linear-gradient(135deg, #FF1744 0%, #00E676 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        margin: 0;
    }

    .killzone-subtitle {
        font-family: 'JetBrains Mono', monospace;
        color: #64748B;
        font-size: 0.85rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .section-header {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.95rem;
        color: #00E676;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .param-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }

    .param-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #94A3B8;
        font-weight: 700;
        text-transform: uppercase;
    }

    .param-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.2rem;
        font-weight: 800;
        color: #FFFFFF;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        background: rgba(0, 230, 118, 0.12);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Setup
# ---------------------------------------------------------
if "settings_submitted" not in st.session_state:
    st.session_state.settings_submitted = False
if "asset_name" not in st.session_state:
    st.session_state.asset_name = ""
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "M30"

# Strict trigger flag for parameters & bias wheel display
if "extraction_performed" not in st.session_state:
    st.session_state.extraction_performed = False

if "ocr_entry" not in st.session_state:
    st.session_state.ocr_entry = 0.0
if "ocr_sl" not in st.session_state:
    st.session_state.ocr_sl = 0.0
if "ocr_tp1" not in st.session_state:
    st.session_state.ocr_tp1 = 0.0
if "ocr_tp2" not in st.session_state:
    st.session_state.ocr_tp2 = 0.0
if "ocr_tp3" not in st.session_state:
    st.session_state.ocr_tp3 = 0.0
if "ocr_lots" not in st.session_state:
    st.session_state.ocr_lots = 0.50

if "order_bias" not in st.session_state:
    st.session_state.order_bias = "BUY"

GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

def extract_chart_levels_with_ai(image_file):
    prompt = (
        "Examine this trading chart image closely. Extract the exact numerical price figures "
        "labeled or drawn for Entry, Stop Loss (SL), Take Profit 1 (TP1), Take Profit 2 (TP2), and Take Profit 3 (TP3). "
        "Return ONLY raw JSON in this exact structure: "
        "{\"entry\": float, \"sl\": float, \"tp1\": float, \"tp2\": float, \"tp3\": float}. "
        "If TP2 or TP3 are not marked on the chart, assign 0.0 for those missing keys."
    )
    
    if not GEMINI_KEY and not OPENAI_KEY:
        st.error("🚨 API Key Missing! Please add GEMINI_API_KEY or OPENAI_API_KEY in Streamlit Cloud Secrets.")
        return {"entry": 0.0, "sl": 0.0, "tp1": 0.0, "tp2": 0.0, "tp3": 0.0}

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
        st.error(f"Error processing image OCR: {str(e)}")
    
    return {"entry": 0.0, "sl": 0.0, "tp1": 0.0, "tp2": 0.0, "tp3": 0.0}

def render_circular_bias_gauge(bias):
    percentage = 88 if bias == "BUY" else 12
    label = "BULLISH BIAS" if bias == "BUY" else "BEARISH BIAS"
    color = "#00E676" if bias == "BUY" else "#FF1744"
    rotation = 45 if bias == "BUY" else -135
    
    radius = 50
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference - (percentage / 100.0) * circumference

    svg_code = f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 20px; margin-top: 10px;">
        <svg width="150" height="150" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="{radius}" stroke="#1E293B" stroke-width="8" fill="none" />
            <circle cx="60" cy="60" r="{radius}" stroke="{color}" stroke-width="8" fill="none"
                    stroke-dasharray="{circumference}" stroke-dashoffset="{dash_offset}"
                    stroke-linecap="round" transform="rotate(-90 60 60)"
                    style="transition: stroke-dashoffset 0.8s ease-in-out, stroke 0.8s ease-in-out;" />
            <g transform="rotate({rotation} 60 60)" style="transition: transform 0.8s ease-in-out;">
                <polygon points="60,20 54,35 66,35" fill="{color}" />
            </g>
            <text x="60" y="58" font-family="'JetBrains Mono', monospace" font-size="16" font-weight="800" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">
                {bias}
            </text>
            <text x="60" y="76" font-family="'Inter', sans-serif" font-size="8" font-weight="700" fill="#94A3B8" text-anchor="middle">
                ORDER FLOW
            </text>
        </svg>
        <div style="margin-top: 8px; font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 13px; color: {color}; text-align: center; letter-spacing: 1px;">
            {label}
        </div>
    </div>
    """
    st.markdown(svg_code, unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="section-header">⚡ CONTROL CENTER</div>', unsafe_allow_html=True)
    
    if not st.session_state.settings_submitted:
        with st.form(key="asset_settings_form"):
            asset_input = st.text_input("Active Asset / Instrument", value="", placeholder="e.g. EURUSD, XAUUSD")
            timeframe_input = st.selectbox("Execution Timeframe", ["M1", "M5", "M15", "M30", "H1", "H4", "D1"], index=3)
            submit_button = st.form_submit_button(label="LAUNCH SESSION", type="primary", use_container_width=True)
            
            if submit_button:
                st.session_state.asset_name = asset_input.strip() if asset_input.strip() else "EURUSD"
                st.session_state.timeframe = timeframe_input
                st.session_state.settings_submitted = True
                st.session_state.extraction_performed = False
                st.rerun()
    else:
        st.markdown(f"**ACTIVE:** `{st.session_state.asset_name}` [{st.session_state.timeframe}]")
        st.write("")
        if st.button("🔄 Change Session", use_container_width=True):
            st.session_state.settings_submitted = False
            st.session_state.extraction_performed = False
            st.rerun()

# ---------------------------------------------------------
# Main Execution Workspace
# ---------------------------------------------------------
if not st.session_state.settings_submitted:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div class="killzone-title">KILLZONE</div>
        <div class="killzone-subtitle" style="margin-top: 10px;">Algorithmic Order Flow & Vision Engine</div>
        <div style="margin-top: 30px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #00E676;">
            👈 CONFIGURE YOUR PAIR IN THE CONTROL CENTER TO BEGIN
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Header Banner
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; margin-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,0.08);">
        <div>
            <div class="killzone-title">KILLZONE</div>
            <div class="killzone-subtitle">{st.session_state.asset_name} // {st.session_state.timeframe} FRAME</div>
        </div>
        <div>
            <span class="status-badge">● ONLINE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "📸 01. VISION SCAN & ORDER BUILDER",
        "📊 02. RISK MATRIX",
        "⚡ 03. MT5 BRIDGE"
    ])

    # =========================================================
    # TAB 1: VISION SCAN & ORDER BUILDER
    # =========================================================
    with tabs[0]:
        col_scan_left, col_scan_right = st.columns([1.1, 1], gap="large")

        with col_scan_left:
            st.markdown('<div class="section-header">1. CHART SCREENSHOT INGESTION</div>', unsafe_allow_html=True)
            ocr_file = st.file_uploader("Upload MT5 / TradingView Chart", type=["png", "jpg", "jpeg"], key="ocr_uploader")

            if ocr_file is not None:
                st.image(Image.open(ocr_file), use_container_width=True)

                if st.button("⚡ EXECUTE VISION EXTRACTION", type="primary", use_container_width=True):
                    with st.spinner("Analyzing image and extracting exact levels..."):
                        extracted_data = extract_chart_levels_with_ai(ocr_file)
                        st.session_state.ocr_entry = float(extracted_data.get("entry", 0.0))
                        st.session_state.ocr_sl = float(extracted_data.get("sl", 0.0))
                        st.session_state.ocr_tp1 = float(extracted_data.get("tp1", 0.0))
                        st.session_state.ocr_tp2 = float(extracted_data.get("tp2", 0.0))
                        st.session_state.ocr_tp3 = float(extracted_data.get("tp3", 0.0))
                        st.session_state.extraction_performed = True
                        st.rerun()

        with col_scan_right:
            # BOTH SECTION 2 AND ORDER DIRECTION BIAS ONLY DISPLAY
            # AFTER PRESSED: 'EXECUTE VISION EXTRACTION'
            if ocr_file is not None and st.session_state.extraction_performed:
                st.markdown('<div class="section-header">2. PARAMETER VERIFICATION</div>', unsafe_allow_html=True)

                def render_copyable_card(label, val_float, color_hex="#FFFFFF"):
                    if val_float <= 0:
                        return
                    fmt_str = f"{val_float:.2f}" if val_float > 500 else f"{val_float:.5f}"
                    
                    c_card, c_btn = st.columns([3, 1])
                    with c_card:
                        st.markdown(f"""
                        <div class="param-box">
                            <div class="param-label">{label}</div>
                            <div class="param-value" style="color: {color_hex};">{fmt_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_btn:
                        st.write("")
                        st.code(fmt_str, language=None)

                # Render extracted price levels
                render_copyable_card("ENTRY PRICE", st.session_state.ocr_entry, "#00B0FF")
                render_copyable_card("STOP LOSS (SL)", st.session_state.ocr_sl, "#FF1744")
                render_copyable_card("TARGET 1 (TP1)", st.session_state.ocr_tp1, "#00E676")

                # Only render TP2 and TP3 if valid prices exist (> 0)
                if st.session_state.ocr_tp2 > 0:
                    render_copyable_card("TARGET 2 (TP2)", st.session_state.ocr_tp2, "#00E676")

                if st.session_state.ocr_tp3 > 0:
                    render_copyable_card("TARGET 3 (TP3)", st.session_state.ocr_tp3, "#00E676")

                st.markdown("---")
                st.markdown('<div class="section-header">ORDER DIRECTION BIAS</div>', unsafe_allow_html=True)

                col_bias1, col_bias2 = st.columns(2)
                with col_bias1:
                    if st.button("🟢 BUY BIAS", use_container_width=True, type="primary" if st.session_state.order_bias == "BUY" else "secondary"):
                        st.session_state.order_bias = "BUY"
                        st.rerun()
                with col_bias2:
                    if st.button("🔴 SELL BIAS", use_container_width=True, type="primary" if st.session_state.order_bias == "SELL" else "secondary"):
                        st.session_state.order_bias = "SELL"
                        st.rerun()

                render_circular_bias_gauge(st.session_state.order_bias)

                st.session_state.active_order = {
                    "asset": st.session_state.asset_name,
                    "timeframe": st.session_state.timeframe,
                    "type": st.session_state.order_bias,
                    "entry": st.session_state.ocr_entry,
                    "sl": st.session_state.ocr_sl,
                    "tp1": st.session_state.ocr_tp1,
                    "tp2": st.session_state.ocr_tp2,
                    "tp3": st.session_state.ocr_tp3,
                    "lots": st.session_state.get("ocr_lots", 0.50)
                }
            else:
                st.info("💡 Upload a chart screenshot on the left and click 'EXECUTE VISION EXTRACTION' to reveal price parameters and directional bias.")

    # =========================================================
    # TAB 2: RISK MATRIX
    # =========================================================
    with tabs[1]:
        order = st.session_state.get("active_order", {
            "asset": st.session_state.asset_name,
            "timeframe": st.session_state.timeframe,
            "type": st.session_state.order_bias,
            "entry": st.session_state.ocr_entry,
            "sl": st.session_state.ocr_sl,
            "tp1": st.session_state.ocr_tp1,
            "tp2": st.session_state.ocr_tp2,
            "tp3": st.session_state.ocr_tp3,
            "lots": st.session_state.ocr_lots
        })

        st.markdown('<div class="section-header">LOT SIZE & EXPOSURE</div>', unsafe_allow_html=True)
        updated_lots = st.number_input("Aggregate Lots", value=order["lots"], format="%.2f", step=0.01, key="risk_matrix_lot_input")
        order["lots"] = updated_lots

        st.markdown("---")
        st.markdown('<div class="section-header">📥 EXPORT BUNDLE</div>', unsafe_allow_html=True)

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

    # =========================================================
    # TAB 3: MT5 BRIDGE
    # =========================================================
    with tabs[2]:
        st.markdown('<div class="section-header">⚡ MT5 SIGNAL DISPATCH</div>', unsafe_allow_html=True)
        order = st.session_state.get("active_order", {})
        st.json(order)
        if st.button("🔥 DISPATCH TO MT5", type="primary", use_container_width=True):
            st.success("🚀 Signal Dispatched!")