import os
import json
import re
import io
import base64
import requests
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
        margin-bottom: 6px;
    }

    .smc-card {
        background: rgba(30, 41, 59, 0.5);
        border-left: 3px solid #00E676;
        border-radius: 6px;
        padding: 10px 14px;
        margin-top: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
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
if "trade_accuracy" not in st.session_state:
    st.session_state.trade_accuracy = 0.0
if "trade_rationale" not in st.session_state:
    st.session_state.trade_rationale = ""
if "order_bias" not in st.session_state:
    st.session_state.order_bias = "INVALID"

if "fvg_data" not in st.session_state:
    st.session_state.fvg_data = {}
if "disp_data" not in st.session_state:
    st.session_state.disp_data = {}

raw_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
GEMINI_KEY = str(raw_key).strip().strip('"').strip("'")

def format_price(val):
    try:
        num = float(val)
        if num == 0.0:
            return "0.00000"
        return f"{num:.2f}" if num > 500 else f"{num:.5f}"
    except (ValueError, TypeError):
        return "0.00000"

def analyze_chart_with_ai(pil_image, asset, timeframe):
    if not GEMINI_KEY:
        return {"error": "GEMINI_API_KEY missing in Streamlit Secrets. Go to App Settings -> Secrets to add it."}

    # Convert image to Base64
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    prompt = f"""
You are an expert ICT (Inner Circle Trader) and Smart Money Concepts (SMC) quantitative analyst examining a {asset} {timeframe} chart.
Perform an aggressive structural scan of price action focusing on:

1. DISPLACEMENT CANDLES:
   - Identify if there is a strong, wide-range body expansion candle indicating institutional entry.
   - Confirm if this displacement caused a Market Structure Shift (MSS), Break of Structure (BOS), or Liquidity Sweep.

2. FAIR VALUE GAP (FVG) MEASUREMENT:
   - Detect any 3-candle imbalance created by displacement.
   - Bullish FVG: Gap between High of Candle 1 and Low of Candle 3.
   - Bearish FVG: Gap between Low of Candle 1 and High of Candle 3.
   - Estimate the exact FVG price boundaries (top_price, bottom_price) and calculate its size/height in points or pips.
   - Determine current FVG status: 'OPEN', 'PARTIALLY_FILLED', or 'FULLY_FILLED'.

3. KEY PRICE LEVELS:
   - Extract numeric levels for Entry (optimal trade entry inside FVG or Order Block), Stop Loss (SL), and Targets (TP1, TP2, TP3).

4. DIRECTIONAL BIAS, CONFLUENCE & ACCURACY:
   - Determine directional bias ('BUY', 'SELL', or 'NO_TRADE').
   - Rate setup quality score from 1.0 to 10.0 based on structural clarity.
   - Estimate the setup win probability / accuracy percentage from 0.0 to 100.0 (e.g., 82.5 for an 82.5% high-probability setup).

Return ONLY raw valid JSON matching this exact structure:
{{
  "bias": "BUY" | "SELL" | "NO_TRADE",
  "score": float,
  "accuracy_percentage": float,
  "rationale": "string",
  "displacement": {{
    "detected": boolean,
    "description": "string (e.g. Strong bullish expansion candle breaking 1.0850 high)"
  }},
  "fvg": {{
    "detected": boolean,
    "top_price": float,
    "bottom_price": float,
    "size_points": float,
    "status": "OPEN" | "PARTIALLY_FILLED" | "FULLY_FILLED"
  }},
  "entry": float,
  "sl": float,
  "tp1": float,
  "tp2": float,
  "tp3": float
}}
"""

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_KEY
    }

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": img_b64
                    }
                }
            ]
        }]
    }

    # 1. Dynamically discover supported models
    candidate_models = []
    try:
        models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
        res = requests.get(models_url, headers=headers, timeout=10)
        if res.status_code == 200:
            models_data = res.json()
            for m in models_data.get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    m_id = m.get("name", "").replace("models/", "")
                    if any(k in m_id for k in ["flash", "pro"]):
                        candidate_models.append(m_id)
        elif res.status_code in [400, 401, 403]:
            return {"error": f"API Key rejected by Google (HTTP {res.status_code}). Please verify your key at aistudio.google.com/app/apikey"}
    except Exception:
        pass

    # 2. Fallback model list
    if not candidate_models:
        candidate_models = [
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro"
        ]

    last_error = ""

    # 3. Iterate models and API versions
    for model_name in candidate_models:
        for api_ver in ["v1beta", "v1"]:
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={GEMINI_KEY}"
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    res_data = response.json()
                    raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
                    clean_text = re.sub(r'```(?:json)?', '', raw_text).replace('```', '').strip()
                    return json.loads(clean_text)
                else:
                    last_error = f"[{model_name} @ {api_ver}] HTTP {response.status_code}: {response.text}"
            except Exception as e:
                last_error = f"[{model_name} @ {api_ver}] Exception: {str(e)}"

    return {"error": f"API Call Failed. Last Response: {last_error}"}

def render_circular_bias_gauge(bias, accuracy_pct=0.0):
    accuracy_val = max(0.0, min(100.0, float(accuracy_pct)))

    if bias == "BUY":
        percentage = accuracy_val if accuracy_val > 0 else 82.0
        label = "BULLISH BIAS"
        color = "#00E676"
        rotation = 45
    elif bias == "SELL":
        percentage = accuracy_val if accuracy_val > 0 else 82.0
        label = "BEARISH BIAS"
        color = "#FF1744"
        rotation = -135
    else:
        percentage = 0.0
        label = "INVALID / NO TRADE"
        color = "#FFB300"
        rotation = 0

    radius = 50
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference - (percentage / 100.0) * circumference

    svg_code = f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 20px; margin-top: 10px;">
        <svg width="160" height="160" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="{radius}" stroke="#1E293B" stroke-width="8" fill="none" />
            <circle cx="60" cy="60" r="{radius}" stroke="{color}" stroke-width="8" fill="none"
                    stroke-dasharray="{circumference}" stroke-dashoffset="{dash_offset}"
                    stroke-linecap="round" transform="rotate(-90 60 60)"
                    style="transition: stroke-dashoffset 0.8s ease-in-out, stroke 0.8s ease-in-out;" />
            <g transform="rotate({rotation} 60 60)" style="transition: transform 0.8s ease-in-out;">
                <polygon points="60,20 54,35 66,35" fill="{color}" />
            </g>
            <text x="60" y="52" font-family="'JetBrains Mono', monospace" font-size="13" font-weight="800" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">
                {bias}
            </text>
            <text x="60" y="68" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="700" fill="{color}" text-anchor="middle" dominant-baseline="central">
                {percentage:.1f}%
            </text>
            <text x="60" y="82" font-family="'Inter', sans-serif" font-size="7" font-weight="700" fill="#94A3B8" text-anchor="middle">
                PROBABILITY
            </text>
        </svg>
        <div style="margin-top: 8px; font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 13px; color: {color}; text-align: center; letter-spacing: 1px;">
            {label}
        </div>
        <div style="margin-top: 6px; padding: 4px 10px; background: rgba(255, 255, 255, 0.04); border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 11px; color: #94A3B8; text-align: center; border: 1px solid rgba(255,255,255,0.06);">
            EST. ACCURACY: <span style="color: {color}; font-weight: 800;">{percentage:.1f}%</span>
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
                pil_img = Image.open(ocr_file)
                st.image(pil_img, use_container_width=True)

                if st.button("⚡ EXECUTE VISION EXTRACTION", type="primary", use_container_width=True):
                    with st.spinner("Scanning market structure, displacement & FVG bounds..."):
                        analysis = analyze_chart_with_ai(pil_img, st.session_state.asset_name, st.session_state.timeframe)

                        if analysis and "error" not in analysis:
                            st.session_state.ocr_entry = format_price(analysis.get("entry", 0.0))
                            st.session_state.ocr_sl = format_price(analysis.get("sl", 0.0))
                            st.session_state.ocr_tp1 = format_price(analysis.get("tp1", 0.0))
                            st.session_state.ocr_tp2 = format_price(analysis.get("tp2", 0.0))
                            st.session_state.ocr_tp3 = format_price(analysis.get("tp3", 0.0))
                            
                            score_val = float(analysis.get("score", 0.0))
                            st.session_state.trade_score = score_val
                            
                            # Extract accuracy percentage or calculate directly from score
                            default_acc = score_val * 10.0 if score_val > 0 else 0.0
                            st.session_state.trade_accuracy = float(analysis.get("accuracy_percentage", default_acc))

                            st.session_state.trade_rationale = str(analysis.get("rationale", "Analysis completed."))

                            st.session_state.fvg_data = analysis.get("fvg", {})
                            st.session_state.disp_data = analysis.get("displacement", {})

                            ai_bias = str(analysis.get("bias", "NO_TRADE")).upper()
                            if ai_bias in ["BUY", "SELL"]:
                                st.session_state.order_bias = ai_bias
                            else:
                                st.session_state.order_bias = "INVALID"
                        else:
                            error_msg = analysis.get("error", "Unknown error") if analysis else "No response from AI."
                            st.session_state.ocr_entry = "0.00000"
                            st.session_state.ocr_sl = "0.00000"
                            st.session_state.ocr_tp1 = "0.00000"
                            st.session_state.ocr_tp2 = "0.00000"
                            st.session_state.ocr_tp3 = "0.00000"
                            st.session_state.trade_score = 0.0
                            st.session_state.trade_accuracy = 0.0
                            st.session_state.trade_rationale = f"🚨 {error_msg}"
                            st.session_state.order_bias = "INVALID"
                            st.session_state.fvg_data = {}
                            st.session_state.disp_data = {}

                        st.session_state.extraction_performed = True
                        st.rerun()

        with col_scan_right:
            if ocr_file is not None and st.session_state.extraction_performed:
                st.markdown('<div class="section-header">ICT ANALYSIS & CONFLUENCE</div>', unsafe_allow_html=True)

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
                        <span class="stat-badge" style="background: rgba(255, 215, 0, 0.15); color: #FFD700; border: 1px solid #FFD700;">
                            ACCURACY: {st.session_state.trade_accuracy:.1f}%
                        </span>
                    </div>
                    <div class="rationale-text">{st.session_state.trade_rationale}</div>
                </div>
                """, unsafe_allow_html=True)

                # Render Displacement & FVG Structural Cards
                disp = st.session_state.get("disp_data", {})
                fvg = st.session_state.get("fvg_data", {})

                if disp.get("detected"):
                    st.markdown(f"""
                    <div class="smc-card" style="border-left-color: #00E676;">
                        ⚡ <b>DISPLACEMENT DETECTED:</b><br/>
                        <span style="color: #94A3B8;">{disp.get('description', 'Strong institutional expansion candle.')}</span>
                    </div>
                    """, unsafe_allow_html=True)

                if fvg.get("detected"):
                    fvg_bot = format_price(fvg.get('bottom_price', 0))
                    fvg_top = format_price(fvg.get('top_price', 0))
                    fvg_size = fvg.get('size_points', 0)
                    fvg_status = fvg.get('status', 'OPEN')

                    st.markdown(f"""
                    <div class="smc-card" style="border-left-color: #00B0FF;">
                        🎯 <b>FAIR VALUE GAP (FVG):</b><br/>
                        <b>Zone:</b> <code style="color: #00E676;">{fvg_bot} - {fvg_top}</code><br/>
                        <b>Size:</b> <code>{fvg_size:.2f} pts</code> | <b>Status:</b> <code>{fvg_status}</code>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")
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

                # Render the updated circular gauge showing accuracy percentage
                render_circular_bias_gauge(st.session_state.order_bias, st.session_state.trade_accuracy)

                st.session_state.active_order = {
                    "asset": st.session_state.asset_name,
                    "timeframe": st.session_state.timeframe,
                    "type": st.session_state.order_bias,
                    "entry": st.session_state.ocr_entry,
                    "sl": st.session_state.ocr_sl,
                    "tp1": st.session_state.ocr_tp1,
                    "tp2": st.session_state.ocr_tp2,
                    "tp3": st.session_state.ocr_tp3,
                    "displacement": disp,
                    "fvg": fvg,
                    "lots": st.session_state.get("ocr_lots", 0.50),
                    "score": st.session_state.trade_score,
                    "accuracy": st.session_state.trade_accuracy,
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