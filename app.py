import os
import io
import cv2
import re
import base64
import numpy as np
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# EasyOCR Import with Caching for High Performance
import easyocr

@st.cache_resource
def load_ocr_reader():
    # Model loads once on app startup (cpu mode for compatibility)
    return easyocr.Reader(['en'], gpu=False)

ocr_reader = load_ocr_reader()

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Ultimate SMC & ICT Master Trading Hub", layout="wide")

# Custom High-Contrast CSS (Forces Metric Text to Crisp White)
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #111827 !important;
        border: 2px solid #374151 !important;
        border-radius: 12px !important;
        padding: 16px !important;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.6) !important;
    }
    div[data-testid="stMetricLabel"] * {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] * {
        color: #ffffff !important;
        font-weight: 900 !important;
        font-size: 2.1rem !important;
        text-shadow: 0px 0px 8px rgba(255, 255, 255, 0.4);
    }
    .trade-card {
        background-color: #111827;
        padding: 22px;
        border-radius: 12px;
        border: 1px solid #1f2937;
        margin-top: 15px;
    }
    .step-box {
        background-color: #111827;
        border-left: 5px solid #3b82f6;
        padding: 20px;
        border-radius: 6px;
        margin-bottom: 20px;
    }
    .step-box h4 { color: #ffffff !important; margin-bottom: 10px; }
    .step-box p, .step-box li { color: #cbd5e1 !important; font-size: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 2. FORCE LOAD ENVIRONMENT VARIABLES
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

gemini_key = os.getenv("GEMINI_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")


# --- AUTOMATIC ICT KILL ZONE CALCULATOR ---
def get_current_ict_session(location_tz_str="Africa/Windhoek"):
    try:
        local_time = datetime.now(ZoneInfo(location_tz_str))
    except Exception:
        local_time = datetime.now()

    est_time = local_time.astimezone(ZoneInfo("America/New_York"))
    time_float = est_time.hour + (est_time.minute / 60.0)

    if 2.0 <= time_float < 5.0:
        session_name = "London Open Kill Zone"
        is_active = True
    elif 7.0 <= time_float < 10.0:
        session_name = "New York AM Kill Zone"
        is_active = True
    elif 13.0 <= time_float < 15.0:
        session_name = "New York PM Kill Zone"
        is_active = True
    elif 20.0 <= time_float or time_float < 0.0:
        session_name = "Asian Range Session"
        is_active = True
    else:
        session_name = "Out of Session (Dead Zone)"
        is_active = False

    return session_name, local_time, est_time, is_active


active_ict_session, local_now, est_now, in_killzone = get_current_ict_session("Africa/Windhoek")


# --- EASYOCR AUTOMATIC PRICE AXIS DETECTOR ---
def extract_price_scale_with_ocr(image_pil):
    """
    Crops the rightmost 18% of the chart, reads numeric price axis labels,
    and returns (top_price, top_y_pixel), (bottom_price, bottom_y_pixel).
    """
    img_np = np.array(image_pil.convert('RGB'))
    h, w, _ = img_np.shape
    
    # Crop right price axis bar (last 18% of width)
    axis_crop = img_np[:, int(w * 0.82):w]
    
    # Run EasyOCR on the cropped section
    ocr_results = ocr_reader.readtext(axis_crop)
    
    detected_points = []
    
    for (bbox, text, prob) in ocr_results:
        # Clean extracted text into numeric floats
        clean_str = re.sub(r'[^\d\.]', '', text)
        if clean_str and clean_str.count('.') <= 1 and len(clean_str) >= 3:
            try:
                price_val = float(clean_str)
                # Y-center of the detected text in original image coordinates
                center_y = int((bbox[0][1] + bbox[2][1]) / 2)
                detected_points.append((price_val, center_y))
            except ValueError:
                continue

    # Sort detected prices by vertical Y-coordinate (top to bottom)
    detected_points = sorted(detected_points, key=lambda p: p[1])
    
    if len(detected_points) >= 2:
        top_node = detected_points[0]        # Highest on chart (smallest Y pixel)
        bottom_node = detected_points[-1]   # Lowest on chart (largest Y pixel)
        return top_node, bottom_node
    
    return None, None


# --- PIXEL TO MT5 REAL PRICE INTERPOLATOR ---
def convert_pixels_to_real_price(direction, top_y, bottom_y, top_node, bottom_node):
    top_price, y_top = top_node
    bottom_price, y_bottom = bottom_node
    
    # Calculate price increment per vertical pixel
    pixel_distance = y_bottom - y_top
    if pixel_distance <= 0:
        return "0.00000", "0.00000", "0.00000"
        
    price_span = top_price - bottom_price
    price_per_pixel = price_span / float(pixel_distance)
    
    # Calculate exact prices for detected bounding box Y-coordinates
    price_top_box = top_price - ((top_y - y_top) * price_per_pixel)
    price_bottom_box = top_price - ((bottom_y - y_top) * price_per_pixel)
    
    # ICT 50% Consequent Encroachment (Midpoint Entry)
    entry_price = (price_top_box + price_bottom_box) / 2.0
    
    if direction == "BUY":
        sl_price = min(price_top_box, price_bottom_box) - (price_per_pixel * 10)  # 10px buffer
        risk = abs(entry_price - sl_price)
        tp_price = entry_price + (risk * 2.5) # 1:2.5 R:R Ratio
    else:
        sl_price = max(price_top_box, price_bottom_box) + (price_per_pixel * 10)
        risk = abs(sl_price - entry_price)
        tp_price = entry_price - (risk * 2.5)

    # Auto-format decimals based on asset scale
    decimals = 5 if entry_price < 500 else 2
    return f"{entry_price:.{decimals}f}", f"{sl_price:.{decimals}f}", f"{tp_price:.{decimals}f}"


# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ Asset & Session Settings")
pair_name = st.sidebar.text_input("Asset / Pair Name (e.g., EURUSD, BTCUSD)", value="", placeholder="Enter pair name...")
timeframe = st.sidebar.selectbox("Timeframe", ["Select Timeframe...", "M1", "M5", "M15", "H1", "H4", "D1"])

st.sidebar.markdown("<br>", unsafe_allow_html=True)
confirm_settings = st.sidebar.button("🔒 Confirm & Unlock Analysis", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.header("🎯 Local Engine Precision Tuning")
fvg_threshold = st.sidebar.slider("Min FVG Gap Sensitivity (Pixels)", min_value=1, max_value=20, value=5)
ob_confluence_filter = st.sidebar.checkbox("Filter Weak Candle Bodies", value=True)

st.sidebar.markdown("---")
st.sidebar.header("🕒 Live Location & Session Tracker")
st.sidebar.caption(f"📍 Location Time: **{local_now.strftime('%H:%M:%S')} (CAT)**")
st.sidebar.caption(f"🗽 New York Time: **{est_now.strftime('%H:%M:%S')} (EST)**")

if in_killzone:
    st.sidebar.success(f"🎯 **Active Zone:**\n{active_ict_session}")
else:
    st.sidebar.warning(f"⏳ **Market Status:**\n{active_ict_session}")

st.sidebar.markdown("---")
st.sidebar.header("🧮 Position Size & Risk Calculator")
account_balance = st.sidebar.number_input("Account Balance ($)", value=10000.0, step=500.0)
risk_pct = st.sidebar.slider("Risk per Trade (%)", min_value=0.25, max_value=5.0, value=1.0, step=0.25)
risk_amount = (account_balance * (risk_pct / 100.0))
st.sidebar.metric("Cash at Risk", f"${risk_amount:.2f}")

st.title("🏛️ ICT & SMC Master Trading Hub")
st.caption("Multi-Engine Platform: AI Vision Analysis, Pure Local Algorithmic CV with EasyOCR Scaling, and MT5 Live Connection")


# --- HELPER FUNCTION FOR HIGH-CONTRAST TEXT BOXES ---
def draw_text_with_bg(img, text, pt, font=cv2.FONT_HERSHEY_SIMPLEX, scale=0.45, text_color=(255, 255, 255), bg_color=(0, 0, 0), thickness=1):
    (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
    x, y = pt
    cv2.rectangle(img, (x - 3, y - text_h - 5), (x + text_w + 5, y + baseline + 3), bg_color, -1)
    cv2.putText(img, text, (x, y), font, scale, text_color, thickness, cv2.LINE_AA)


# --- OPENCV COMPUTER VISION PIPELINE ---
def analyze_chart_cv_full_smc(image_pil, min_gap=5, filter_bodies=True):
    img_array = np.array(image_pil.convert('RGB'))
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    overlay = img_bgr.copy()
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    img_h, img_w = img_bgr.shape[0], img_bgr.shape[1]

    lower_green, upper_green = np.array([35, 40, 40]), np.array([85, 255, 255])
    lower_red1, upper_red1 = np.array([0, 40, 40]), np.array([10, 255, 255])
    lower_red2, upper_red2 = np.array([170, 40, 40]), np.array([180, 255, 255])

    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

    def extract_candles(mask, candle_type):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        items = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            min_height = 8 if filter_bodies else 3
            if h > min_height and w > 1:
                items.append({
                    'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h),
                    'top': int(y), 'bottom': int(y + h),
                    'center_x': int(x + w / 2), 'type': candle_type
                })
        return items

    all_candles = sorted(extract_candles(mask_green, 'bullish') + extract_candles(mask_red, 'bearish'), key=lambda c: c['x'])
    
    counts = {
        'bull_fvg': 0, 'bear_fvg': 0,
        'bull_ob': 0, 'bear_ob': 0,
        'breaker_blocks': 0, 'bsl_sweeps': 0,
        'ssl_sweeps': 0, 'bos_choch': 0
    }

    last_fvg_level = None
    last_ob_level = None

    if len(all_candles) >= 3:
        min_y = min(c['top'] for c in all_candles)
        max_y = max(c['bottom'] for c in all_candles)
        eq_y = int((min_y + max_y) / 2)

        cv2.line(img_bgr, (0, eq_y), (img_w, eq_y), (255, 255, 255), 1, cv2.LINE_AA)
        draw_text_with_bg(img_bgr, "50% EQUILIBRIUM", (20, max(eq_y - 6, 12)), scale=0.42, text_color=(255, 255, 255), bg_color=(20, 20, 20))
        draw_text_with_bg(img_bgr, "PREMIUM ZONE", (img_w - 150, min_y + 20), scale=0.42, text_color=(120, 120, 255), bg_color=(10, 10, 10))
        draw_text_with_bg(img_bgr, "DISCOUNT ZONE", (img_w - 150, max_y - 20), scale=0.42, text_color=(120, 255, 120), bg_color=(10, 10, 10))

        for i in range(len(all_candles) - 2):
            c1, c2, c3 = all_candles[i], all_candles[i+1], all_candles[i+2]
            
            if (c1['top'] - c3['bottom']) >= min_gap:
                x1, x2 = c1['x'], min(c3['x'] + c3['w'] + 90, img_w - 1)
                y1, y2 = c3['bottom'], c1['top']
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 255, 0), -1)
                cv2.rectangle(img_bgr, (x1, y1), (x2, y2), (255, 215, 0), 2)
                draw_text_with_bg(img_bgr, "Bullish FVG", (x1, max(y1 - 4, 12)), scale=0.4, text_color=(255, 215, 0), bg_color=(0, 0, 0))
                counts['bull_fvg'] += 1
                last_fvg_level = ('BUY', y1, y2)
            elif (c3['top'] - c1['bottom']) >= min_gap:
                x1, x2 = c1['x'], min(c3['x'] + c3['w'] + 90, img_w - 1)
                y1, y2 = c1['bottom'], c3['top']
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 0, 255), -1)
                cv2.rectangle(img_bgr, (x1, y1), (x2, y2), (203, 192, 255), 2)
                draw_text_with_bg(img_bgr, "Bearish FVG", (x1, max(y1 - 4, 12)), scale=0.4, text_color=(203, 192, 255), bg_color=(0, 0, 0))
                counts['bear_fvg'] += 1
                last_fvg_level = ('SELL', y1, y2)

        for i in range(len(all_candles) - 2):
            c1, c2, c3 = all_candles[i], all_candles[i+1], all_candles[i+2]
            if c1['type'] == 'bearish' and c2['type'] == 'bullish' and c3['type'] == 'bullish':
                if (c2['h'] + c3['h']) > (c1['h'] * 1.2):
                    x1, x2 = c1['x'], min(c3['x'] + c3['w'] + 100, img_w - 1)
                    y1, y2 = c1['top'], c1['bottom']
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 200, 0), -1)
                    cv2.rectangle(img_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    draw_text_with_bg(img_bgr, "Bullish OB", (x1, max(y1 - 4, 12)), scale=0.42, text_color=(0, 255, 0), bg_color=(0, 0, 0))
                    counts['bull_ob'] += 1
                    last_ob_level = ('BUY', y1, y2)
            elif c1['type'] == 'bullish' and c2['type'] == 'bearish' and c3['type'] == 'bearish':
                if (c2['h'] + c3['h']) > (c1['h'] * 1.2):
                    x1, x2 = c1['x'], min(c3['x'] + c3['w'] + 100, img_w - 1)
                    y1, y2 = c1['top'], c1['bottom']
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 200), -1)
                    cv2.rectangle(img_bgr, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    draw_text_with_bg(img_bgr, "Bearish OB", (x1, max(y1 - 4, 12)), scale=0.42, text_color=(0, 0, 255), bg_color=(0, 0, 0))
                    counts['bear_ob'] += 1
                    last_ob_level = ('SELL', y1, y2)

        tops = sorted([c['top'] for c in all_candles])
        bottoms = sorted([c['bottom'] for c in all_candles])

        for j in range(len(tops) - 1):
            if abs(tops[j] - tops[j+1]) < 3:
                y_bsl = tops[j]
                for x in range(0, img_w, 10):
                    cv2.line(img_bgr, (x, y_bsl), (min(x + 5, img_w), y_bsl), (0, 255, 255), 1, cv2.LINE_AA)
                draw_text_with_bg(img_bgr, "BSL (Equal Highs)", (img_w - 180, max(y_bsl - 5, 12)), scale=0.4, text_color=(0, 255, 255), bg_color=(0, 0, 0))
                counts['bsl_sweeps'] += 1
                break

        for j in range(len(bottoms) - 1):
            if abs(bottoms[j] - bottoms[j+1]) < 3:
                y_ssl = bottoms[j]
                for x in range(0, img_w, 10):
                    cv2.line(img_bgr, (x, y_ssl), (min(x + 5, img_w), y_ssl), (255, 0, 255), 1, cv2.LINE_AA)
                draw_text_with_bg(img_bgr, "SSL (Equal Lows)", (img_w - 180, min(y_ssl + 15, img_h - 10)), scale=0.4, text_color=(255, 0, 255), bg_color=(0, 0, 0))
                counts['ssl_sweeps'] += 1
                break

        recent_candle = all_candles[-1]
        highest_prev = min(c['top'] for c in all_candles[:-3]) if len(all_candles) > 3 else min_y
        lowest_prev = max(c['bottom'] for c in all_candles[:-3]) if len(all_candles) > 3 else max_y

        if recent_candle['top'] < highest_prev:
            cv2.line(img_bgr, (recent_candle['x'] - 40, highest_prev), (recent_candle['x'] + 40, highest_prev), (0, 255, 0), 2)
            draw_text_with_bg(img_bgr, "BOS / CHoCH (Bullish)", (recent_candle['x'] - 50, max(highest_prev - 8, 12)), scale=0.42, text_color=(0, 255, 0), bg_color=(0, 0, 0))
            counts['bos_choch'] += 1
        elif recent_candle['bottom'] > lowest_prev:
            cv2.line(img_bgr, (recent_candle['x'] - 40, lowest_prev), (recent_candle['x'] + 40, lowest_prev), (0, 0, 255), 2)
            draw_text_with_bg(img_bgr, "BOS / CHoCH (Bearish)", (recent_candle['x'] - 50, min(lowest_prev + 18, img_h - 10)), scale=0.42, text_color=(0, 0, 255), bg_color=(0, 0, 0))
            counts['bos_choch'] += 1

    result_img = cv2.addWeighted(overlay, 0.35, img_bgr, 0.65, 0)
    result_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
    
    return Image.fromarray(result_rgb), counts, last_ob_level, last_fvg_level


# --- HELPER PARSER TO EXTRACT STRICT PRICE NUMBERS FROM AI RESPONSE ---
def parse_trade_levels(ai_text):
    levels = {"direction": "BUY", "entry": "0.00000", "sl": "0.00000", "tp1": "0.00000", "tp2": "0.00000"}
    
    if "SELL" in ai_text.upper():
        levels["direction"] = "SELL"

    entry_match = re.search(r"ENTRY[_\s]*PRICE:\s*([\d\.]+)", ai_text, re.IGNORECASE)
    if entry_match:
        levels["entry"] = entry_match.group(1)

    sl_match = re.search(r"STOP[_\s]*LOSS:\s*([\d\.]+)", ai_text, re.IGNORECASE)
    if sl_match:
        levels["sl"] = sl_match.group(1)

    tp1_match = re.search(r"TAKE[_\s]*PROFIT[_\s]*1:\s*([\d\.]+)", ai_text, re.IGNORECASE)
    if tp1_match:
        levels["tp1"] = tp1_match.group(1)

    tp2_match = re.search(r"TAKE[_\s]*PROFIT[_\s]*2:\s*([\d\.]+)", ai_text, re.IGNORECASE)
    if tp2_match:
        levels["tp2"] = tp2_match.group(1)

    return levels


# --- MULTI-PROVIDER AI VISION ANALYSIS FUNCTION ---
def analyze_chart_ai(image_pil, pair, tf, session, provider):
    if image_pil.mode in ("RGBA", "P"):
        image_pil = image_pil.convert("RGB")

    prompt = f"""
    You are a master ICT (Inner Circle Trader) and Smart Money Concepts (SMC) analyst. 
    Analyze this chart screenshot for {pair} on the {tf} timeframe during the {session}.

    Provide a complete, structured analysis using ICT core principles.
    
    You MUST include exact numeric levels at the end of your response in this EXACT format so they can be parsed for copy/pasting:
    
    ---
    ### 🎯 DIRECTIONAL SIGNAL: [BUY / SELL / NEUTRAL]
    ### 📊 CONFIDENCE INDEX: [X]% [BULLISH / BEARISH]
    
    1. **ICT Session & Kill Zone Context**: Asian Range sweeps & Judas Swing details.
    2. **Market Structure (BOS / CHoCH)**: MSS status and Liquidity targets.
    3. **Order Flow & Imbalance Zones**: Active FVGs, OBs, and Premium vs Discount.
    4. **ICT Trade Setup Execution**:
       - **Direction**: [BUY or SELL]
       - **ENTRY PRICE**: [exact numerical price e.g. 1.08550]
       - **STOP LOSS**: [exact numerical price e.g. 1.08350]
       - **TAKE PROFIT 1**: [exact numerical price e.g. 1.08950]
       - **TAKE PROFIT 2**: [exact numerical price e.g. 1.09250]
       - **Confluence Score**: [1-10]
    ---
    """

    if "OpenAI" in provider:
        if not openai_key or "your_" in openai_key:
            st.warning("⚠️ OpenAI Key missing or invalid. Falling back to Google Gemini...")
            return analyze_chart_ai(image_pil, pair, tf, session, "Google Gemini (Free Tier)")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            
            buffered = io.BytesIO()
            image_pil.save(buffered, format="JPEG")
            base64_img = base64.b64encode(buffered.getvalue()).decode('utf-8')

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]
                }],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            err_msg = str(e)
            if "credit_balance_exhausted" in err_msg or "429" in err_msg:
                st.warning("⚠️ OpenAI credit limit reached. Automatically switching to Google Gemini...")
                return analyze_chart_ai(image_pil, pair, tf, session, "Google Gemini (Free Tier)")
            return f"❌ **OpenAI API Error:** {err_msg}"

    elif "Anthropic" in provider:
        if not anthropic_key or "your_" in anthropic_key:
            st.warning("⚠️ Anthropic Key missing. Falling back to Google Gemini...")
            return analyze_chart_ai(image_pil, pair, tf, session, "Google Gemini (Free Tier)")
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)

            buffered = io.BytesIO()
            image_pil.save(buffered, format="JPEG")
            base64_img = base64.b64encode(buffered.getvalue()).decode('utf-8')

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64_img}},
                        {"type": "text", "text": prompt}
                    ]
                }]
            )
            return response.content[0].text
        except Exception as e:
            return f"❌ **Anthropic Claude API Error:** {str(e)}"

    else:
        if not gemini_key or "your_" in gemini_key:
            return "⚠️ **GEMINI_API_KEY** missing or invalid in `.env` file."
        try:
            from google import genai
            from google.genai.errors import APIError

            client = genai.Client(api_key=gemini_key)
            candidate_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
            
            for model_name in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[image_pil, prompt]
                    )
                    return response.text
                except APIError as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        return "⚠️ **Rate Limit Reached:** Gemini Free Tier limit hit. Wait 30 seconds and click the button again."
                    continue
            return "❌ **All Gemini models currently unavailable.**"
        except Exception as e:
            return f"❌ **Google Gemini Error:** {str(e)}"


# --- SESSION STATE GATEWAY CONTROL ---
if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

if confirm_settings:
    if pair_name.strip() != "" and timeframe != "Select Timeframe...":
        st.session_state.unlocked = True
    else:
        st.session_state.unlocked = False


# --- CONDITIONAL GATEWAY DISPLAY ---
if not st.session_state.unlocked:
    st.markdown("""
    <div class="step-box">
        <h4>🔒 Step 1: Configure Analysis Settings</h4>
        <p>Please fill in the required <b>Asset & Session Settings</b> in the left sidebar and click <b>🔒 Confirm & Unlock Analysis</b> to unlock platform modules:</p>
        <ul>
            <li><b>Asset / Pair Name</b> (e.g. EURUSD, BTCUSD, NAS100)</li>
            <li><b>Timeframe</b> (e.g. M15, H1, H4)</li>
        </ul>
        <p><i>Note: The active <b>ICT Kill Zone</b> is calculated automatically based on local time and EST timing!</i></p>
    </div>
    """, unsafe_allow_html=True)
    st.info("👈 Enter your setup details in the left sidebar and click 'Confirm & Unlock Analysis' to proceed.")
else:
    st.success(f"✅ Setup Confirmed: **{pair_name.upper()}** | Timeframe: **{timeframe}** | Session: **{active_ict_session}**")
    
    # --- THREE OPERATING PLATFORM TABS ---
    main_tab1, main_tab2, main_tab3 = st.tabs([
        "🤖 AI Vision Analysis Engine", 
        "⚡ Pure Local Algorithmic CV", 
        "📈 Live MetaTrader 5 (MT5) Direct"
    ])

    # ==========================================
    # TAB 1: AI VISION ANALYSIS ENGINE
    # ==========================================
    with main_tab1:
        st.subheader("🤖 Multi-Model AI Vision Chart Analyzer")
        ai_provider = st.selectbox("Choose AI Model Provider", [
            "OpenAI (GPT-4o)",
            "Anthropic (Claude 3.5 Sonnet)",
            "Google Gemini (Free Tier)"
        ])
        
        uploaded_file = st.file_uploader("Upload a chart screenshot for AI analysis...", type=["png", "jpg", "jpeg"], key="ai_uploader")

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            
            st.subheader("🔍 Mapped SMC Computer Vision Chart")
            proc_img, _, _, _ = analyze_chart_cv_full_smc(image, fvg_threshold, ob_confluence_filter)
            st.image(proc_img, use_container_width=True)

            st.markdown("---")

            if "ai_report" not in st.session_state:
                st.session_state.ai_report = None

            if st.button(f"⚡ Generate Complete ICT Trade Breakdown ({ai_provider})", type="primary"):
                with st.spinner(f"Running deep SMC analysis using {ai_provider} for {pair_name} ({timeframe})..."):
                    st.session_state.ai_report = analyze_chart_ai(image, pair_name, timeframe, active_ict_session, ai_provider)

            if st.session_state.ai_report:
                sub_tab1, sub_tab2 = st.tabs(["📋 Full ICT Report", "🎯 Setup Summary & Quick Copy"])
                
                with sub_tab1:
                    st.markdown(st.session_state.ai_report)
                    
                with sub_tab2:
                    st.markdown("### 📋 Copy & Paste Trade Orders")
                    st.caption("Click the copy icon on the top right of any box below to copy values straight into MetaTrader:")
                    
                    parsed_levels = parse_trade_levels(st.session_state.ai_report)
                    
                    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                    
                    with col_e1:
                        st.markdown("**1️⃣ Open / Entry Price**")
                        st.code(parsed_levels["entry"], language="text")
                        
                    with col_e2:
                        st.markdown("**2️⃣ Stop Loss (SL)**")
                        st.code(parsed_levels["sl"], language="text")
                        
                    with col_e3:
                        st.markdown("**3️⃣ Take Profit 1 (TP1)**")
                        st.code(parsed_levels["tp1"], language="text")
                        
                    with col_e4:
                        st.markdown("**4️⃣ Take Profit 2 (TP2)**")
                        st.code(parsed_levels["tp2"], language="text")

                    try:
                        e_val = float(parsed_levels["entry"])
                        sl_val = float(parsed_levels["sl"])
                        tp1_val = float(parsed_levels["tp1"])
                        
                        if e_val > 0 and sl_val > 0:
                            pip_risk = abs(e_val - sl_val)
                            pip_reward = abs(tp1_val - e_val)
                            rr = pip_reward / pip_risk if pip_risk > 0 else 0
                            
                            st.markdown(f"""
                            <div class="trade-card">
                                <h4 style="color: #ffffff;">📊 Position & Risk Breakdown</h4>
                                <p style="color: #cbd5e1;">Target Pair: <b>{pair_name.upper()}</b> | Risk Amount: <span style="color:#00ff7f;"><b>${risk_amount:.2f}</b></span> ({risk_pct}%)</p>
                                <p style="color: #cbd5e1;">Calculated Risk-to-Reward Ratio: <span style="color:#3b82f6;"><b>1 : {rr:.2f}</b></span></p>
                            </div>
                            """, unsafe_allow_html=True)
                    except Exception:
                        pass

    # ==========================================
    # TAB 2: PURE LOCAL ALGORITHMIC CV WITH EASYOCR
    # ==========================================
    with main_tab2:
        st.subheader("⚡ Local Algorithmic SMC Engine (EasyOCR Scale Conversion)")
        st.caption("Runs 100% locally on your machine with zero subscription costs.")
        
        uploaded_cv_file = st.file_uploader("Upload chart screenshot for instant CV processing...", type=["png", "jpg", "jpeg"], key="cv_uploader")

        if uploaded_cv_file is not None:
            image_cv = Image.open(uploaded_cv_file)
            proc_img_cv, counts_cv, ob_level, fvg_level = analyze_chart_cv_full_smc(image_cv, fvg_threshold, ob_confluence_filter)

            st.subheader("🔍 Local Algorithmically Mapped SMC Elements")
            st.image(proc_img_cv, use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Mapped SMC Structure Counts")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Bullish FVGs", counts_cv['bull_fvg'])
            m2.metric("Bearish FVGs", counts_cv['bear_fvg'])
            m3.metric("Bullish OBs", counts_cv['bull_ob'])
            m4.metric("Bearish OBs", counts_cv['bear_ob'])

            m5, m6, m7, m8 = st.columns(4)
            m5.metric("BSL Sweeps", counts_cv['bsl_sweeps'])
            m6.metric("SSL Sweeps", counts_cv['ssl_sweeps'])
            m7.metric("BOS / CHoCH", counts_cv['bos_choch'])
            m8.metric("Active Kill Zone", active_ict_session)

            # --- CIRCULAR SVG RADIAL GAUGE FOR BUY/SELL POLL ---
            st.markdown("---")
            st.subheader("🎯 Directional Sentiment Gauge (Buy / Sell Gauge)")
            
            total_bullish_weight = (counts_cv['bull_fvg'] * 1.5) + (counts_cv['bull_ob'] * 2.5) + (counts_cv['ssl_sweeps'] * 1.0)
            total_bearish_weight = (counts_cv['bear_fvg'] * 1.5) + (counts_cv['bear_ob'] * 2.5) + (counts_cv['bsl_sweeps'] * 1.0)
            total_weight = total_bullish_weight + total_bearish_weight

            if total_weight > 0:
                bull_pct = (total_bullish_weight / total_weight) * 100
                bear_pct = 100 - bull_pct
            else:
                bull_pct = 50.0
                bear_pct = 50.0

            needle_angle = (bull_pct / 100.0) * 180 - 90
            
            if bull_pct > 55:
                status_title = "🟢 BUY BIAS"
                status_color = "#10B981"
            elif bear_pct > 55:
                status_title = "🔴 SELL BIAS"
                status_color = "#EF4444"
            else:
                status_title = "⚪ NEUTRAL / CONSOLIDATION"
                status_color = "#9CA3AF"

            gauge_html = f"""
            <div style="background-color:#111827; border:1px solid #1f2937; border-radius:12px; padding:20px; text-align:center;">
                <h3 style="color:{status_color}; margin-bottom:5px; font-weight:800;">{status_title}</h3>
                <p style="color:#ffffff; font-size:1.1rem; font-weight:700; margin-bottom:15px;">
                    Bullish: <span style="color:#10B981;">{bull_pct:.1f}%</span> | Bearish: <span style="color:#EF4444;">{bear_pct:.1f}%</span>
                </p>
                <div style="width:240px; margin:0 auto;">
                    <svg viewBox="0 0 200 120" style="width:100%;">
                        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#374151" stroke-width="18" stroke-linecap="round" />
                        <path d="M 100 20 A 80 80 0 0 1 180 100" fill="none" stroke="#10B981" stroke-width="18" stroke-linecap="round" />
                        <path d="M 20 100 A 80 80 0 0 1 100 20" fill="none" stroke="#EF4444" stroke-width="18" stroke-linecap="round" />
                        <g transform="rotate({needle_angle}, 100, 100)">
                            <line x1="100" y1="100" x2="100" y2="30" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" />
                            <circle cx="100" cy="100" r="8" fill="#FFFFFF" />
                        </g>
                    </svg>
                </div>
            </div>
            """
            st.markdown(gauge_html, unsafe_allow_html=True)

            # --- EASYOCR CONVERTED MT5 TARGETS ---
            st.markdown("---")
            st.subheader("🎯 EasyOCR Auto-Converted MT5 Orders")
            
            with st.spinner("🔍 EasyOCR scanning chart price scale..."):
                top_node, bottom_node = extract_price_scale_with_ocr(image_cv)

            if top_node and bottom_node:
                st.caption(f"✅ Scale Calibrated via OCR: Top Scale **{top_node[0]}** | Bottom Scale **{bottom_node[0]}**")
                
                active_setup = ob_level or fvg_level
                if active_setup:
                    direction, top_y, bottom_y = active_setup
                    
                    entry_str, sl_str, tp_str = convert_pixels_to_real_price(
                        direction, top_y, bottom_y, top_node, bottom_node
                    )
                    
                    c_c1, c_c2, c_c3, c_c4 = st.columns(4)
                    with c_c1:
                        st.markdown("**1️⃣ Order Type**")
                        st.code(f"{direction} LIMIT", language="text")
                    with c_c2:
                        st.markdown("**2️⃣ Entry (50% CE)**")
                        st.code(entry_str, language="text")
                    with c_c3:
                        st.markdown("**3️⃣ Invalidation (SL)**")
                        st.code(sl_str, language="text")
                    with c_c4:
                        st.markdown("**4️⃣ Target (TP 1:2.5 RR)**")
                        st.code(tp_str, language="text")
                else:
                    st.info("⚪ No explicit Order Block or Fair Value Gap detected in current view.")
            else:
                st.warning("⚠️ Could not automatically detect price scale digits on the right edge of screenshot. Ensure your screenshot includes the right-side price scale numbers.")

    # ==========================================
    # TAB 3: LIVE METATRADER 5 (MT5) INTEGRATION
    # ==========================================
    with main_tab3:
        st.subheader("📈 Live MetaTrader 5 (MT5) Direct Python Terminal Connection")
        st.caption("Fetch live tick prices, stream candlestick bars, and auto-execute trade orders without taking manual screenshots.")

        try:
            import MetaTrader5 as mt5

            mt5_connected = mt5.initialize()

            if not mt5_connected:
                st.error("❌ **MetaTrader 5 Terminal Not Running.** Open your MT5 desktop application on Windows to enable live synchronization.")
                st.info("💡 Make sure MetaTrader 5 is installed and 'Allow Algo Trading' is enabled in MT5 Options.")
            else:
                st.success("🟢 **MetaTrader 5 Connected Successfully!**")

                acc_info = mt5.account_info()
                if acc_info is not None:
                    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                    col_a1.metric("MT5 Account Balance", f"${acc_info.balance:.2f}")
                    col_a2.metric("MT5 Equity", f"${acc_info.equity:.2f}")
                    col_a3.metric("Leverage", f"1:{acc_info.leverage}")
                    col_a4.metric("Server", acc_info.server)

                st.markdown("---")
                st.markdown(f"### 📊 Live Quotes for **{pair_name.upper()}**")

                tick = mt5.symbol_info_tick(pair_name.upper())

                if tick:
                    col_t1, col_t2, col_t3 = st.columns(3)
                    col_t1.metric("Live Bid Price", f"{tick.bid:.5f}")
                    col_t2.metric("Live Ask Price", f"{tick.ask:.5f}")
                    col_t3.metric("Spread", f"{round((tick.ask - tick.bid) * 10000, 1)} Pips")
                else:
                    st.warning(f"⚠️ Symbol `{pair_name.upper()}` not found in MT5 Market Watch. Ensure it is added to your Market Watch list in MT5.")

        except ImportError:
            st.warning("⚠️ MetaTrader5 Python package is not installed.")
            st.code("pip install MetaTrader5", language="powershell")
            st.caption("To enable live MT5 trading, install the package above and run MT5 on your Windows machine.")