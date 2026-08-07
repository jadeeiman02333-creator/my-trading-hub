import os
import json
import streamlit as st
from PIL import Image

# ---------------------------------------------------------
# Page Configuration & High-Tech Theme
# ---------------------------------------------------------
st.set_page_config(
    page_title="Killzone // Algorithmic Order Flow Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from google import genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    code, .stCode, input { font-family: 'JetBrains Mono', monospace !important; }
    .stApp { background-color: #05070A; color: #E2E8F0; }

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

    .analysis-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(0, 230, 118, 0.25);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }

    .rationale-text {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #CBD5E1;
        line-height: 1.5;
    }

    .stat-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        margin-right: 8px;
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

if "extraction_performed" not in st.session_state:
    st.session_state.extraction_performed = False

if "ocr_entry" not in st.session_state:
    st.session_state.ocr_entry = "0.00000"
if "ocr_sl" not in st.session_state:
    st.session_state.ocr_sl = "0.00000"
if "ocr_tp1" not in st.session_state:
    st.session_state.ocr_tp1 = "0.00000"
if "ocr_tp2" not in st.session_state:
    st.session_state.ocr_tp2 = "0.00000"
if "ocr_tp3" not in st.session_state:
    st.session_state.ocr_tp3 = "0.00000"

if "trade_score" not in st.session_state:
    st.session_state.trade_score = 0.0
if "trade_rationale" not in st.session_state:
    st.session_state.trade_rationale = ""
if "order_bias" not in st.session_state:
    st.session_state.order_bias = "INVALID"

GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

def format_price(val):
    try:
        num = float(val)
        if num == 0.0:
            return "0.00000"
        return f"{num:.2f}" if num > 500 else f"{num:.5f}"
    except (ValueError, TypeError):
        return "0.00000"

def analyze_chart_with_ai(image_file, asset, timeframe):
    prompt = f"""
You are an expert ICT (Inner Circle Trader) and Smart Money Concepts (SMC) quantitative trading analyst examining a {asset} {timeframe} chart.
Perform a complete technical analysis of price action and market structure in this image:

1. MARKET STRUCTURE: Scan for Market Structure Shifts (MSS/CHoCH), Breaks of Structure (BOS), Fair Value Gaps (FVG), Order Blocks (OB), or Liquidity Sweeps.
2. DIRECTIONAL BIAS: Determine if the setup is 'BUY', 'SELL', or 'NO_TRADE' (if structure is ambiguous/low probability).
3. PRICE LEVELS: Extract or identify the optimal price points for Entry, Stop Loss (SL), Take Profit 1 (TP1), Take Profit 2 (TP2), and Take Profit 3 (TP3).
4. CONFLUENCE SCORE: Rate the setup quality from 1.0 to 10.0 based on structural clarity.
5. RATIONALE: Write a concise 2-sentence technical breakdown explaining the confluence.

Return ONLY raw valid JSON matching this exact structure:
{{
  "bias": "BUY" | "SELL" | "NO_TRADE",
  "score": float,
  "rationale": "string",
  "entry": float,
  "sl": float,
  "tp1": float,
  "tp2": float,
  "tp3": float
}}
"""

    if not GEMINI_KEY and not OPENAI_KEY:
        st.error("🚨 API Key Missing! Add GEMINI_API_KEY or OPENAI_API_KEY in Streamlit Secrets.")
        return None

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
        st.error(f"Error during AI Chart Analysis: {str(e)}")

    return None

def render_circular_bias_gauge(bias):
    if bias == "BUY":
        percentage = 88
        label = "BULLISH BIAS"
        color = "#00E676"
        rotation = 45
    elif bias == "SELL":
        percentage = 12
        label = "BEARISH BIAS"
        color = "#FF1744"
        rotation = -135
    else:
        percentage = 50
        label = "INVALID / NO TRADE"
        color = "#FFB300"
        rotation = 0

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
            <text x="60" y="58" font-family="'JetBrains Mono', monospace" font-size="14" font-weight="800" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">
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
# Main Workspace
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

    with tabs[0]:
        col_scan_left, col_scan_right = st.columns([1.1, 1], gap="large")

        with col_scan_left:
            st.markdown('<div class="section-header">1. CHART SCREENSHOT INGESTION</div>', unsafe_allow_html=True)

            def reset_extraction_state():
                st.session_state.extraction_performed = False

            ocr_file = st.file_uploader(
                "Upload MT5 / TradingView Chart",
                type=["png", "jpg", "jpeg"],
                key="ocr_uploader",
                on_change=reset_extraction_state
            )

            if ocr_file is not None:
                st.image(Image.open(ocr_file), use_container_width=True)

                if st.button("⚡ EXECUTE VISION EXTRACTION", type="primary", use_container_width=True):
                    with st.spinner("Analyzing market structure & ICT order flow..."):
                        analysis = analyze_chart_with_ai(ocr_file, st.session_state.asset_name, st.session_state.timeframe)
                        if analysis:
                            st.session_state.ocr_entry = format_price(analysis.get("entry", 0.0))
                            st.session_state.ocr_sl = format_price(analysis.get("sl", 0.0))
                            st.session_state.ocr_tp1 = format_price(analysis.get("tp1", 0.0))
                            st.session_state.ocr_tp2 = format_price(analysis.get("tp2", 0.0))
                            st.session_state.ocr_tp3 = format_price(analysis.get("tp3", 0.0))
                            st.session_state.trade_score = float(analysis.get("score", 0.0))
                            st.session_state.trade_rationale = str(analysis.get("rationale", "No analysis rationale provided."))

                            ai_bias = str(analysis.get("bias", "NO_TRADE")).upper()
                            if ai_bias in ["BUY", "SELL"]:
                                st.session_state.order_bias = ai_bias
                            else:
                                st.session_state.order_bias = "INVALID"
                        else:
                            st.session_state.ocr_entry = "0.00000"
                            st.session_state.ocr_sl = "0.00000"
                            st.session_state.ocr_tp1 = "0.00000"
                            st.session_state.ocr_tp2 = "0.00000"
                            st.session_state.ocr_tp3 = "0.00000"
                            st.session_state.trade_score = 0.0
                            st.session_state.trade_rationale = "Failed to analyze chart structure."
                            st.session_state.order_bias = "INVALID"

                        st.session_state.extraction_performed = True
                        st.rerun()

        with col_scan_right:
            if ocr_file is not None and st.session_state.extraction_performed:
                # --- AI ANALYSIS RATIONALE & METRICS ---
                st.markdown('<div class="section-header">ICT ANALYSIS & CONFLUENCE</div>', unsafe_allow_html=True)

                # Compute Risk Reward Ratio dynamically
                try:
                    e_num = float(st.session_state.ocr_entry)
                    sl_num = float(st.session_state.ocr_sl)
                    tp_num = float(st.session_state.ocr_tp1)

                    risk = abs(e_num - sl_num)
                    reward = abs(tp_num - e_num)
                    rr_ratio = (reward / risk) if risk > 0 else 0.0
                except (ValueError, ZeroDivisionError):
                    rr_ratio = 0.0

                score_color = "#00E676" if st.session_state.trade_score >= 7.0 else ("#FFB300" if st.session_state.trade_score >= 5.0 else "#FF1744")

                st.markdown(f"""
                <div class="analysis-card">
                    <div style="margin-bottom: 10px;">
                        <span class="stat-badge" style="background: rgba(0, 230, 118, 0.15); color: {score_color}; border: 1px solid {score_color};">
                            SCORE: {st.session_state.trade_score:.1f} / 10
                        </span>
                        <span class="stat-badge" style="background: rgba(0, 176, 255, 0.15); color: #00B0FF; border: 1px solid #00B0FF;">
                            R:R = 1:{rr_ratio:.2f}
                        </span>
                    </div>
                    <div class="rationale-text">{st.session_state.trade_rationale}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<div class="section-header">2. PARAMETER VERIFICATION</div>', unsafe_allow_html=True)

                st.session_state.ocr_entry = st.text_input("ENTRY PRICE", value=st.session_state.ocr_entry)
                st.session_state.ocr_sl = st.text_input("STOP LOSS (SL)", value=st.session_state.ocr_sl)
                st.session_state.ocr_tp1 = st.text_input("TARGET 1 (TP1)", value=st.session_state.ocr_tp1)

                try:
                    tp2_num = float(st.session_state.ocr_tp2)
                    if tp2_num > 0:
                        st.session_state.ocr_tp2 = st.text_input("TARGET 2 (TP2)", value=st.session_state.ocr_tp2)
                except ValueError:
                    pass

                try:
                    tp3_num = float(st.session_state.ocr_tp3)
                    if tp3_num > 0:
                        st.session_state.ocr_tp3 = st.text_input("TARGET 3 (TP3)", value=st.session_state.ocr_tp3)
                except ValueError:
                    pass

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
                    "lots": st.session_state.get("ocr_lots", 0.50),
                    "score": st.session_state.trade_score,
                    "rationale": st.session_state.trade_rationale
                }
            else:
                st.info("💡 Upload a chart screenshot on the left and click 'EXECUTE VISION EXTRACTION' to analyze market structure and parameters.")

    with tabs[1]:
        order = st.session_state.get("active_order", {})
        st.markdown('<div class="section-header">LOT SIZE & EXPOSURE</div>', unsafe_allow_html=True)
        updated_lots = st.number_input("Aggregate Lots", value=order.get("lots", 0.50), format="%.2f", step=0.01)

        st.markdown("---")
        st.markdown('<div class="section-header">📥 EXPORT BUNDLE</div>', unsafe_allow_html=True)

        json_export = json.dumps(order, indent=4)
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.download_button("💾 DOWNLOAD JSON", data=json_export, file_name="order.json", mime="application/json", type="primary", use_container_width=True)

    with tabs[2]:
        st.markdown('<div class="section-header">⚡ MT5 SIGNAL DISPATCH</div>', unsafe_allow_html=True)
        order = st.session_state.get("active_order", {})
        st.json(order)
        if st.button("🔥 DISPATCH TO MT5", type="primary", use_container_width=True):
            st.success("🚀 Signal Dispatched!")