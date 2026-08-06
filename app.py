import os
import time
import json
import re
import streamlit as st
from PIL import Image
from google import genai
import openai

# ---------------------------------------------------------
# Page Configuration & Next-Gen Cyberpunk-Dark Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="NEXUS // Algorithmic Order Flow Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Tech CSS Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    code, .stCode, div[data-baseweb="input"] input {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Background & Main Container */
    .stApp {
        background-color: #05070A;
        color: #E2E8F0;
    }

    /* Glassmorphism Cards */
    .nexus-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: border 0.3s ease;
    }
    .nexus-card:hover {
        border: 1px solid rgba(0, 230, 118, 0.3);
    }

    /* Cyber Accent Headers */
    .cyber-header {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #00E676 0%, #00B0FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
    }

    /* Status Pill */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 1px;
    }
    .status-badge-active {
        background: rgba(0, 230, 118, 0.12);
        color: #00E676;
        border: 1px solid rgba(0, 230, 118, 0.4);
    }
    .status-badge-standby {
        background: rgba(255, 171, 0, 0.12);
        color: #FFAB00;
        border: 1px solid rgba(255, 171, 0, 0.4);
    }

    /* Laser Scanner Animation */
    .scan-wrapper {
        position: relative;
        overflow: hidden;
        border-radius: 12px;
        border: 1px solid rgba(0, 230, 118, 0.5);
        box-shadow: 0 0 20px rgba(0, 230, 118, 0.2);
    }
    .scan-line {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent 0%, #00E676 50%, transparent 100%);
        box-shadow: 0 0 15px #00E676, 0 0 25px #00E676;
        animation: laserScan 1.8s ease-in-out infinite;
        z-index: 10;
    }
    @keyframes laserScan {
        0% { top: 0%; }
        50% { top: 96%; }
        100% { top: 0%; }
    }

    /* Custom Streamlit UI Tweaks */
    .stButton > button {
        border-radius: 10px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.8);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    div[data-baseweb="tab"] {
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13px !important;
        padding: 10px 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Session State Setup
# ---------------------------------------------------------
if "settings_submitted" not in st.session_state:
    st.session_state.settings_submitted = False
if "asset_name" not in st.session_state:
    st.session_state.asset_name = "XAUUSD"
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "M30"

# Vision OCR & Level State
if "ocr_scanned" not in st.session_state:
    st.session_state.ocr_scanned = False
if "is_scanning" not in st.session_state:
    st.session_state.is_scanning = False

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

# Active Order Engine Object
if "active_order" not in st.session_state:
    st.session_state.active_order = {
        "asset": st.session_state.asset_name,
        "timeframe": st.session_state.timeframe,
        "type": "BUY",
        "entry": 2450.50,
        "sl": 2442.00,
        "tp1": 2465.00,
        "tp2": 2480.00,
        "tp3": 2495.00,
        "lots": 0.50
    }

# API Keys Configuration
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

# ---------------------------------------------------------
# UI Component: High-Tech Circular Sentiment Meter
# ---------------------------------------------------------
def render_cyber_gauge(percentage, label, color):
    radius = 54
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference - (percentage / 100.0) * circumference

    svg_code = f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 14px; padding: 18px;">
        <svg width="130" height="130" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="{radius}" stroke="#1E293B" stroke-width="8" fill="none" />
            <circle cx="60" cy="60" r="{radius}" stroke="{color}" stroke-width="8" fill="none"
                    stroke-dasharray="{circumference}" stroke-dashoffset="{dash_offset}"
                    stroke-linecap="round" transform="rotate(-90 60 60)"
                    style="transition: stroke-dashoffset 0.8s ease-in-out; filter: drop-shadow(0 0 8px {color});" />
            <text x="60" y="58" font-family="'JetBrains Mono', monospace" font-size="20" font-weight="800" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central">
                {int(percentage)}%
            </text>
            <text x="60" y="76" font-family="'Inter', sans-serif" font-size="9" font-weight="600" fill="#94A3B8" text-anchor="middle">
                BIAS CONFIRMATION
            </text>
        </svg>
        <div style="margin-top: 8px; font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 12px; color: {color}; text-align: center; letter-spacing: 0.5px;">
            {label}
        </div>
    </div>
    """
    st.markdown(svg_code, unsafe_allow_html=True)

# ---------------------------------------------------------
# Helper Function: Vision OCR Level Extraction
# ---------------------------------------------------------
def extract_chart_levels_with_ai(image_file):
    prompt = """
    Analyze this chart screenshot. Extract numerical price levels for Entry, Stop Loss (SL), and Take Profits (TP1, TP2, TP3).
    Return ONLY a raw valid JSON object with format:
    {"entry": float, "sl": float, "tp1": float, "tp2": float, "tp3": float}
    """
    try:
        if GEMINI_KEY:
            client = genai.Client(api_key=GEMINI_KEY)
            image = Image.open(image_file)
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image]
            )
            clean_json = re.sub(r'```json|```', '', res.text).strip()
            return json.loads(clean_json)
        elif OPENAI_KEY:
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
            clean_json = re.sub(r'```json|