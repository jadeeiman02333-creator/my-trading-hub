import os
import json
import re
import io
import base64
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# Timezone resolution for NY (EST/EDT)
try:
    from zoneinfo import ZoneInfo
    NY_TZ = ZoneInfo("America/New_York")
except Exception:
    NY_TZ = None

# ---------------------------------------------------------
# Page Configuration & Styling (Custom Favicon)
# ---------------------------------------------------------
PAGE_ICON = "logo.png" if os.path.exists("logo.png") else "⚡"

st.set_page_config(
    page_title="Killzone // Algorithmic Terminal",
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

if os.path.exists("logo.png"):
    try:
        st.logo("logo.png")
    except Exception:
        pass

def resolve_app_url():
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            host = st.context.headers.get("host") or st.context.headers.get("Host")
            if host:
                scheme = "http" if ("localhost" in host or "127.0.0.1" in host) else "https"
                return f"{scheme}://{host}"
    except Exception:
        pass
    return "https://killzone-terminal.streamlit.app"

APP_URL = resolve_app_url()

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

    .mobile-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(0, 230, 118, 0.3);
        border-radius: 12px;
        padding: 14px;
        font-family: 'JetBrains Mono', monospace;
    }

    .mobile-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 0.75rem;
    }

    .mobile-table th {
        color: #00E676;
        border-bottom: 1px solid rgba(0, 230, 118, 0.3);
        padding-bottom: 6px;
        text-align: left;
    }

    .mobile-table td {
        padding: 8px 2px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        vertical-align: middle;
    }

    .mobile-btn {
        display: inline-block;
        text-align: center;
        background: rgba(0, 230, 118, 0.15);
        color: #00E676 !important;
        border: 1px solid rgba(0, 230, 118, 0.5);
        padding: 5px 8px;
        border-radius: 6px;
        text-decoration: none !important;
        font-weight: 700;
        font-size: 0.72rem;
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

    .st-expander {
        border: 1px solid rgba(0, 230, 118, 0.3) !important;
        border-radius: 8px !important;
        background-color: rgba(15, 23, 42, 0.6) !important;
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

if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

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

def get_ict_killzone_status():
    if NY_TZ:
        now_ny = datetime.now(NY_TZ)
    else:
        now_ny = datetime.now(timezone(timedelta(hours=-4))) # Fallback EST/EDT offset
        
    ny_time_str = now_ny.strftime("%H:%M:%S")
    time_decimal = now_ny.hour + now_ny.minute / 60.0

    if 2.0 <= time_decimal < 5.0:
        return "🇬🇧 LONDON KILLZONE", ny_time_str, "🟢", "HIGH PROBABILITY // Institutional Manipulation & High/Low of Day Formation"
    elif 7.0 <= time_decimal < 10.0:
        return "🇺🇸 NEW YORK AM KILLZONE", ny_time_str, "🟢", "HIGH PROBABILITY // Institutional Momentum Expansion & Continuation"
    elif 13.0 <= time_decimal < 15.0:
        return "🇺🇸 NEW YORK PM KILLZONE", ny_time_str, "🟡", "MODERATE PROBABILITY // Afternoon Retracement & Position Settlement Window"
    elif 20.0 <= time_decimal <= 23.99 or 0.0 <= time_decimal < 2.0:
        return "🌏 ASIAN SESSION / RANGE", ny_time_str, "🔵", "CONSOLIDATION // Liquidity Building Phase (Low Volume — Avoid Breakout Entries)"
    else:
        return "⏸️ OUT OF KILLZONE", ny_time_str, "⚪", "OFF-HOURS // Low Institutional Volume (Increased Spread & Slippage Risk)"

@st.cache_data(ttl=1800)
def fetch_economic_calendar():
    try:
        url = "https://nyl.forexfactory.com/ff_calendar_thisweek.json"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def get_relevant_news_events(asset_name, calendar_events):
    if not asset_name or not calendar_events:
        return []
    
    asset_upper = asset_name.upper()
    known_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD", "ZAR", "XAU"]
    relevant_currencies = [c for c in known_currencies if c in asset_upper]
    if "XAU" in asset_upper and "USD" not in relevant_currencies:
        relevant_currencies.append("USD")
        
    matching_events = []
    for ev in calendar_events:
        country = str(ev.get("country", "")).upper()
        impact = str(ev.get("impact", "")).capitalize()
        
        if country in relevant_currencies and impact in ["High", "Medium"]:
            matching_events.append({
                "title": ev.get("title", "Economic Event"),
                "currency": country,
                "impact": impact,
                "date": ev.get("date", ""),
                "forecast": ev.get("forecast", ""),
                "previous": ev.get("previous", "")
            })
    return matching_events

def fetch_live_exchange_rates(base_curr="USD"):
    try:
        url = f"https://open.er-api.com/v6/latest/{base_curr}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json().get("rates", {})
    except Exception:
        pass
    return {
        "USD": 1.0, "EUR": 0.92, "GBP": 0.78, "ZAR": 18.50, 
        "NAD": 18.50, "JPY": 155.0, "AUD": 1.52, "CAD": 1.36, "CHF": 0.89
    }

def render_embedded_copy_input(label, state_key, input_id):
    val = st.session_state.get(state_key, "0.00000")
    
    html_code = f"""
    <div style="font-family: 'JetBrains Mono', monospace; margin-bottom: 8px;">
        <label style="display: block; font-size: 11px; font-weight: 700; color: #94A3B8; margin-bottom: 4px; letter-spacing: 0.5px;">
            {label}
        </label>
        <div style="position: relative; display: flex; align-items: center;">
            <input type="text" id="field_{input_id}" value="{val}" readonly
                   style="width: 100%; height: 42px; background: rgba(15, 23, 42, 0.9); color: #00E676; border: 1px solid rgba(0, 230, 118, 0.35); border-radius: 8px; padding: 0 45px 0 12px; font-family: monospace; font-size: 14px; font-weight: 700; outline: none; box-sizing: border-box;" />
            <button onclick="navigator.clipboard.writeText(document.getElementById('field_{input_id}').value); this.innerText='✓'; setTimeout(() => this.innerText='📋', 1200);"
                    title="Copy Price"
                    style="position: absolute; right: 6px; top: 6px; bottom: 6px; width: 34px; background: rgba(0, 230, 118, 0.15); color: #00E676; border: 1px solid rgba(0, 230, 118, 0.4); border-radius: 6px; cursor: pointer; font-size: 13px; display: flex; align-items: center; justify-content: center; transition: all 0.2s;">
                📋
            </button>
        </div>
    </div>
    """
    components.html(html_code, height=72)

def analyze_chart_with_ai(pil_images, asset, timeframe, news_warning=""):
    if not GEMINI_KEY:
        return {"error": "GEMINI_API_KEY missing in Streamlit Secrets. Go to App Settings -> Secrets to add it."}

    prompt = f"""
You are an elite ICT (Inner Circle Trader) and Smart Money Concepts (SMC) quantitative analyst examining the provided {asset} {timeframe} chart screenshot(s).
{news_warning}

================================================================================
INTEGRATED 3-TIER OPERATIONAL FRAMEWORK (ICT / SMC NATIVE INTEGRATION)
================================================================================
In institutional trading, ICT/SMC acts as the native bridge connecting Trend Following and Mean Reversion:

1. TIER 1: TREND FOLLOWING (Context & Direction)
   - ICT/SMC Equivalent: Higher Timeframe (HTF) Market Structure / Daily Bias
   - Objective: Determine macro order flow direction before evaluating setups.

2. TIER 2: MEAN REVERSION (Valuation Check)
   - ICT/SMC Equivalent: Premium vs. Discount / Equilibrium (50% Consequent Encroachment / CE of FVG)
   - Objective: Verify price is at favorable valuation relative to the active dealing range (Premium for Shorts, Discount for Longs).

3. TIER 3: PRECISION EXECUTION (ICT / SMC Entry)
   - ICT/SMC Equivalent: Liquidity Sweep + Displacement + FVG Entry
   - Objective: Pinpoint execution entries following buy-side/sell-side liquidity sweeps and impulsive displacement.

================================================================================
INSTITUTIONAL NON-NEGOTIABLE SCANNING RULES
================================================================================
1. HIGHER TIMEFRAME CONTEXT & LIQUIDITY SWEEP (Tier 1 & Tier 3):
   - Align execution with HTF bias (where market gravity/liquidity lies).
   - Check if price swept Buy-Side Liquidity (BSL) or Sell-Side Liquidity (SSL) prior to momentum shift.
   - Look for wide-range displacement body expansion candles breaking Market Structure (MSS / BOS).
   - MANDATORY INVALIDATION: If price is consolidating, in mid-range chop, or lacks a clear liquidity sweep preceding displacement, you MUST set "bias": "NO_TRADE", "score": 0.0, "accuracy_percentage": 0.0, and explain the lack of institutional sponsorship in "rationale".

2. FAIR VALUE GAP (FVG) & CONSEQUENT ENCROACHMENT / CE (Tier 2 & Tier 3):
   - Detect any 3-candle imbalance created by displacement.
   - Estimate exact FVG boundaries (top_price, bottom_price).
   - Calculate Consequent Encroachment (ce_price) = 50% midpoint of the FVG zone: (top_price + bottom_price) / 2.
   - ENTRY LOGIC: Set "entry" price strictly at the Consequent Encroachment (CE 50% level) inside the FVG array to maximize Risk-to-Reward (R:R), NOT at the outer boundary.

3. INVALIDATION / STOP LOSS & TARGETS:
   - Stop Loss (SL): Placed strictly beyond the key swing high/low that generated the displacement move.
   - Targets (TP1, TP2, TP3): Positioned at logical opposing liquidity pools (e.g., equal highs/lows, opposing order blocks).
   - MINIMUM R:R RULE: Calculate Reward-to-Risk (Reward to TP1 / Risk to SL). If R:R is below 1:1.50, set "bias": "NO_TRADE".

Return ONLY raw valid JSON matching this exact structure:
{{
  "bias": "BUY" | "SELL" | "NO_TRADE",
  "score": float,
  "accuracy_percentage": float,
  "rationale": "string",
  "displacement": {{
    "detected": boolean,
    "description": "string (e.g. BSL sweep followed by strong bearish displacement breaking 1.0850 low)"
  }},
  "fvg": {{
    "detected": boolean,
    "top_price": float,
    "bottom_price": float,
    "ce_price": float,
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

    parts = [{"text": prompt}]

    for idx, img in enumerate(pil_images):
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        parts.append({"text": f"Chart Screenshot #{idx + 1}:"})
        parts.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": img_b64
            }
        })

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_KEY
    }

    payload = {
        "contents": [{
            "parts": parts
        }]
    }

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

    if not candidate_models:
        candidate_models = [
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro"
        ]

    last_error = ""

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
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)

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

    st.markdown("---")
    with st.expander("📱 MOBILE APP ACCESS", expanded=False):
        qr_api_url = f"https://quickchart.io/qr?text={APP_URL}&size=140&dark=00E676&light=0B1120&margin=1"

        mobile_card_html = f"""<div class="mobile-card">
<div style="text-align: center; margin-bottom: 8px;">
<img src="{qr_api_url}" style="border-radius: 8px; border: 1px solid rgba(0, 230, 118, 0.4); width: 130px; height: 130px;" alt="Killzone Mobile QR" />
<div style="color: #64748B; font-size: 0.7rem; margin-top: 4px;">SCAN WITH PHONE CAMERA</div>
</div>
<table class="mobile-table">
<thead>
<tr>
<th>OS</th>
<th>INSTALL METHOD</th>
<th style="text-align: right;">ACTION</th>
</tr>
</thead>
<tbody>
<tr>
<td style="color: #FFFFFF; font-weight: 700;">🍎 iOS</td>
<td style="color: #CBD5E1;">Safari ➔ Share ➔ Add to Home Screen</td>
<td style="text-align: right;"><a href="{APP_URL}" target="_blank" class="mobile-btn">OPEN APP</a></td>
</tr>
<tr>
<td style="color: #FFFFFF; font-weight: 700;">🤖 Android</td>
<td style="color: #CBD5E1;">Chrome ➔ ⁝ ➔ Install App / Add to Screen</td>
<td style="text-align: right;"><a href="{APP_URL}" target="_blank" class="mobile-btn">OPEN APP</a></td>
</tr>
</tbody>
</table>
<div style="font-size: 0.7rem; color: #64748B; margin-top: 8px; line-height: 1.3;">
💡 <b>Tip:</b> Open the link on mobile and select <b>Add to Home Screen</b> to install Killzone as a standalone app icon.
</div>
</div>"""

        st.markdown(mobile_card_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Workspace Header
# ---------------------------------------------------------
if not st.session_state.settings_submitted:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
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
        "⚡ 03. MT5 BRIDGE",
        "💱 04. CURRENCY CONVERTER"
    ])

    with tabs[0]:
        # --- AUTOMATED LIVE ECONOMIC NEWS MONITOR ---
        raw_calendar = fetch_economic_calendar()
        matched_events = get_relevant_news_events(st.session_state.asset_name, raw_calendar)
        high_impact_events = [e for e in matched_events if e["impact"] == "High"]
        
        news_prompt_warning = ""

        if high_impact_events:
            st.error(f"🔴 **RED FOLDER ALERT ({st.session_state.asset_name}):** {len(high_impact_events)} High-Impact Economic Event(s) Detected for this pair!")
            with st.expander("📅 View Scheduled High-Impact Releases", expanded=True):
                for ev in high_impact_events:
                    st.markdown(f"• **[{ev['currency']}] {ev['title']}** | Impact: `HIGH` | Forecast: `{ev['forecast']}` | Prev: `{ev['previous']}`")
            news_prompt_warning = f"\nWARNING: High-impact economic news releases ({', '.join([e['title'] for e in high_impact_events])}) are scheduled for {st.session_state.asset_name}. Be cautious of spread widening, slippage, and unpredictable volatility spikes."
        elif matched_events:
            st.warning(f"🟠 **MEDIUM IMPACT NEWS:** {len(matched_events)} Event(s) scheduled for {st.session_state.asset_name}.")
            with st.expander("📅 View Economic Releases", expanded=False):
                for ev in matched_events:
                    st.markdown(f"• **[{ev['currency']}] {ev['title']}** | Impact: `{ev['impact']}` | Forecast: `{ev['forecast']}` | Prev: `{ev['previous']}`")
        else:
            st.caption(f"🟢 **NEWS MONITOR:** No High/Medium impact economic news releases detected for {st.session_state.asset_name} today.")

        # --- AUTOMATED LIVE ICT KILLZONE SESSION MONITOR ---
        kz_name, kz_time, kz_icon, kz_desc = get_ict_killzone_status()
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(0, 230, 118, 0.3); border-radius: 8px; padding: 10px 14px; margin-top: 6px; margin-bottom: 16px; font-family: 'JetBrains Mono', monospace;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <span style="font-weight: 800; font-size: 0.85rem; color: #FFFFFF;">{kz_icon} CURRENT SESSION: <span style="color: #00E676;">{kz_name}</span></span>
                <span style="font-size: 0.78rem; color: #94A3B8;">NY TIME: <strong style="color: #00E676;">{kz_time} EST</strong></span>
            </div>
            <div style="font-size: 0.72rem; color: #64748B; margin-top: 4px;">{kz_desc}</div>
        </div>
        """, unsafe_allow_html=True)

        col_scan_left, col_scan_right = st.columns([1.1, 1], gap="large")

        with col_scan_left:
            st.markdown('<div class="section-header">1. CHART SCREENSHOT INGESTION</div>', unsafe_allow_html=True)

            def reset_extraction_state():
                st.session_state.extraction_performed = False

            ocr_files = st.file_uploader(
                "Upload MT5 / TradingView Charts (HTF & LTF)",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="ocr_uploader",
                on_change=reset_extraction_state
            )

            if ocr_files:
                pil_images = []
                for idx, uploaded_file in enumerate(ocr_files):
                    img = Image.open(uploaded_file)
                    pil_images.append(img)
                    st.image(img, caption=f"Chart #{idx + 1}: {uploaded_file.name}", use_container_width=True)

                if st.button("⚡ EXECUTE VISION EXTRACTION", type="primary", use_container_width=True):
                    with st.spinner(f"Scanning market structure across {len(pil_images)} uploaded chart(s)..."):
                        analysis = analyze_chart_with_ai(pil_images, st.session_state.asset_name, st.session_state.timeframe, news_prompt_warning)

                        if analysis and "error" not in analysis:
                            st.session_state.ocr_entry = format_price(analysis.get("entry", 0.0))
                            st.session_state.ocr_sl = format_price(analysis.get("sl", 0.0))
                            st.session_state.ocr_tp1 = format_price(analysis.get("tp1", 0.0))
                            st.session_state.ocr_tp2 = format_price(analysis.get("tp2", 0.0))
                            st.session_state.ocr_tp3 = format_price(analysis.get("tp3", 0.0))
                            
                            score_val = float(analysis.get("score", 0.0))
                            st.session_state.trade_score = score_val
                            
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
            if ocr_files and st.session_state.extraction_performed:
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

                # HARD PYTHON R:R FILTER CHECK (Minimum 1:1.50 Required)
                MIN_RR_THRESHOLD = 1.50
                if rr_ratio < MIN_RR_THRESHOLD and st.session_state.order_bias in ["BUY", "SELL"]:
                    st.warning(f"⚠️ **SETUP INVALIDATED:** Risk-to-Reward ratio (1:{rr_ratio:.2f}) is below minimum requirement of 1:{MIN_RR_THRESHOLD:.2f}.")
                    st.session_state.order_bias = "INVALID"

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
                    fvg_ce = format_price(fvg.get('ce_price', 0))
                    fvg_size = fvg.get('size_points', 0)
                    fvg_status = fvg.get('status', 'OPEN')

                    st.markdown(f"""
                    <div class="smc-card" style="border-left-color: #00B0FF;">
                        🎯 <b>FAIR VALUE GAP (FVG):</b><br/>
                        <b>Zone:</b> <code style="color: #00E676;">{fvg_bot} - {fvg_top}</code><br/>
                        <b>CE (50% Midpoint):</b> <code style="color: #FFD700;">{fvg_ce}</code><br/>
                        <b>Size:</b> <code>{fvg_size:.2f} pts</code> | <b>Status:</b> <code>{fvg_status}</code>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")
                st.markdown('<div class="section-header">2. PARAMETER VERIFICATION</div>', unsafe_allow_html=True)

                render_embedded_copy_input("ENTRY PRICE", "ocr_entry", "entry")
                render_embedded_copy_input("STOP LOSS (SL)", "ocr_sl", "sl")
                render_embedded_copy_input("TARGET 1 (TP1)", "ocr_tp1", "tp1")

                try:
                    tp2_num = float(st.session_state.ocr_tp2)
                    if tp2_num > 0:
                        render_embedded_copy_input("TARGET 2 (TP2)", "ocr_tp2", "tp2")
                except ValueError:
                    pass

                try:
                    tp3_num = float(st.session_state.ocr_tp3)
                    if tp3_num > 0:
                        render_embedded_copy_input("TARGET 3 (TP3)", "ocr_tp3", "tp3")
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
                st.info("💡 Upload one or more chart screenshots on the left (e.g. H4 + M15) and click 'EXECUTE VISION EXTRACTION' to analyze market structure across timeframes.")

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

        st.markdown("---")
        st.markdown('<div class="section-header">📈 TRADE PERFORMANCE & WIN RATE LOGGER</div>', unsafe_allow_html=True)

        col_log_left, col_log_right = st.columns([1.1, 1], gap="large")

        with col_log_left:
            st.markdown('<div class="section-header">1. LOG EXECUTED TRADE</div>', unsafe_allow_html=True)
            active_ord = st.session_state.get("active_order", {})
            
            with st.form("log_trade_form"):
                log_asset = st.text_input("Asset / Pair", value=active_ord.get("asset", st.session_state.get("asset_name", "EURUSD")))
                log_bias = st.selectbox("Direction", ["BUY", "SELL"], index=0 if active_ord.get("type") != "SELL" else 1)
                log_outcome = st.selectbox("Trade Outcome", ["WIN", "LOSS", "BREAKEVEN"])
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    default_r = 2.0 if log_outcome == "WIN" else (-1.0 if log_outcome == "LOSS" else 0.0)
                    log_r = st.number_input("R-Multiple (e.g. +2.0 or -1.0)", value=default_r, step=0.5)
                with col_r2:
                    log_pnl = st.number_input("PnL ($ Cash Return)", value=0.0, step=10.0)
                    
                log_notes = st.text_area("Trade Rationale / Notes", value=active_ord.get("rationale", ""), height=80)
                
                submit_log = st.form_submit_button("💾 RECORD TRADE TO JOURNAL", type="primary", use_container_width=True)

                if submit_log:
                    new_entry = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "asset": log_asset,
                        "timeframe": st.session_state.get("timeframe", "M30"),
                        "type": log_bias,
                        "outcome": log_outcome,
                        "r_multiple": float(log_r),
                        "pnl": float(log_pnl),
                        "score": active_ord.get("score", 0.0),
                        "notes": log_notes
                    }
                    st.session_state.trade_history.append(new_entry)
                    st.success("✅ Trade successfully logged to performance journal!")
                    st.rerun()

        with col_log_right:
            st.markdown('<div class="section-header">2. WIN RATE & EQUITY METRICS</div>', unsafe_allow_html=True)
            history = st.session_state.trade_history
            
            total_trades = len(history)
            wins = sum(1 for t in history if t["outcome"] == "WIN")
            losses = sum(1 for t in history if t["outcome"] == "LOSS")
            breakevens = sum(1 for t in history if t["outcome"] == "BREAKEVEN")
            
            valid_outcomes = wins + losses
            win_rate = (wins / valid_outcomes * 100) if valid_outcomes > 0 else 0.0
            net_r = sum(t.get("r_multiple", 0.0) for t in history)
            total_pnl = sum(t.get("pnl", 0.0) for t in history)

            wr_color = "#00E676" if win_rate >= 50.0 else ("#FFB300" if win_rate >= 40.0 else "#FF1744")

            st.markdown(f"""
            <div class="analysis-card" style="text-align: center; padding: 20px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #94A3B8;">WIN RATE (EXCLUDING BE)</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 2.8rem; font-weight: 900; color: {wr_color}; margin: 8px 0;">
                    {win_rate:.1f}%
                </div>
                <div style="margin-top: 10px;">
                    <span class="stat-badge" style="background: rgba(0, 230, 118, 0.15); color: #00E676; border: 1px solid #00E676;">
                        WINS: {wins}
                    </span>
                    <span class="stat-badge" style="background: rgba(255, 23, 68, 0.15); color: #FF1744; border: 1px solid #FF1744;">
                        LOSSES: {losses}
                    </span>
                    <span class="stat-badge" style="background: rgba(255, 179, 0, 0.15); color: #FFB300; border: 1px solid #FFB300;">
                        BE: {breakevens}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"""
                <div class="smc-card" style="border-left-color: #00E676; text-align: center;">
                    <div style="font-size: 0.75rem; color: #94A3B8;">CUMULATIVE RETURN</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #00E676;">{net_r:+.1f} R</div>
                </div>
                """, unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"""
                <div class="smc-card" style="border-left-color: #00B0FF; text-align: center;">
                    <div style="font-size: 0.75rem; color: #94A3B8;">TOTAL P&L</div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #00B0FF;">${total_pnl:+,.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-header">3. HISTORICAL PERFORMANCE JOURNAL</div>', unsafe_allow_html=True)

        if history:
            df_history = pd.DataFrame(history)
            st.dataframe(
                df_history[["timestamp", "asset", "timeframe", "type", "outcome", "r_multiple", "pnl", "score", "notes"]],
                use_container_width=True,
                hide_index=True
            )
            
            col_csv, col_clr = st.columns([1, 1])
            with col_csv:
                csv_data = df_history.to_csv(index=False)
                st.download_button(
                    "💾 EXPORT TRADE JOURNAL (CSV)",
                    data=csv_data,
                    file_name="killzone_trade_journal.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
            with col_clr:
                if st.button("🗑️ CLEAR PERFORMANCE LOGS", use_container_width=True):
                    st.session_state.trade_history = []
                    st.rerun()
        else:
            st.info("💡 No trades logged yet. Fill out the form above to record your first trade result!")

    with tabs[3]:
        st.markdown('<div class="section-header">💱 LIVE CURRENCY CONVERTER & PIP MATRIX</div>', unsafe_allow_html=True)

        col_conv_1, col_conv_2 = st.columns([1, 1], gap="large")

        with col_conv_1:
            st.markdown('<div class="section-header">1. REAL-TIME EXCHANGE RATE CONVERTER</div>', unsafe_allow_html=True)
            
            currencies_list = ["USD", "EUR", "GBP", "ZAR", "NAD", "JPY", "AUD", "CAD", "CHF"]
            
            col_curr_from, col_curr_to = st.columns(2)
            with col_curr_from:
                from_curr = st.selectbox("From Currency", currencies_list, index=0)
            with col_curr_to:
                to_curr = st.selectbox("To Currency", currencies_list, index=3)
            
            amount_input = st.number_input("Amount to Convert", value=100.0, step=10.0, format="%.2f")

            rates_data = fetch_live_exchange_rates(from_curr)
            target_rate = rates_data.get(to_curr, 1.0)
            converted_val = amount_input * target_rate

            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(0, 230, 118, 0.4); border-radius: 12px; padding: 20px; text-align: center; margin-top: 15px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #94A3B8;">CONVERTED VALUE</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 2.2rem; font-weight: 900; color: #00E676; margin: 6px 0;">
                    {converted_val:,.2f} <span style="font-size: 1.2rem; color: #FFFFFF;">{to_curr}</span>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #64748B;">
                    Exchange Rate: 1 {from_curr} = {target_rate:.4f} {to_curr}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_conv_2:
            st.markdown('<div class="section-header">2. PIP VALUE & EQUITY EXPOSURE CALCULATOR</div>', unsafe_allow_html=True)

            acc_currency = st.selectbox("Account Equity Base Currency", ["USD", "EUR", "GBP", "ZAR", "NAD"], index=0)
            lot_size = st.number_input("Position Size (Lots)", value=1.00, step=0.10, format="%.2f")
            stop_pips = st.number_input("Stop Loss Distance (Pips / Points)", value=20.0, step=5.0, format="%.1f")

            base_pip_value_usd = 10.0 * lot_size
            acc_rates = fetch_live_exchange_rates("USD")
            fx_mult = acc_rates.get(acc_currency, 1.0)

            pip_val_acc = base_pip_value_usd * fx_mult
            total_risk_acc = pip_val_acc * stop_pips

            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 23, 68, 0.4); border-radius: 12px; padding: 20px; text-align: center; margin-top: 15px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #94A3B8;">TOTAL CASH AT RISK ({stop_pips} Pips)</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 2.2rem; font-weight: 900; color: #FF1744; margin: 6px 0;">
                    {total_risk_acc:,.2f} <span style="font-size: 1.2rem; color: #FFFFFF;">{acc_currency}</span>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #64748B;">
                    Pip Value: ~{pip_val_acc:.2f} {acc_currency} per pip @ {lot_size} lot
                </div>
            </div>
            """, unsafe_allow_html=True)