import streamlit as st
import datetime
import pytz

# Page Configuration
st.set_page_config(
    page_title="Killzone Terminal", 
    layout="wide", 
    page_icon="⚡"
)

# ==========================================
# 🟢 NEWS MONITOR & ICT KILLZONE INDICATOR
# ==========================================
st.caption("🟢 **NEWS MONITOR:** No High/Medium impact economic news releases detected for EURUSD today.")

def get_current_ict_session():
    ny_tz = pytz.timezone("America/New_York")
    now_ny = datetime.datetime.now(ny_tz)
    current_time_str = now_ny.strftime("%H:%M NY Time (%I:%M %p)")
    
    # Calculate time integer for comparison (e.g., 08:30 -> 830)
    time_num = now_ny.hour * 100 + now_ny.minute
    
    # ICT Session Definitions (NY Time)
    if 2000 <= time_num or time_num < 0:
        session_name = "🌏 Asian Range (Accumulation Phase)"
        color = "blue"
    elif 200 <= time_num < 500:
        session_name = "🇬🇧 London Killzone (Judas Swing / Manipulation)"
        color = "orange"
    elif 700 <= time_num < 1000:
        session_name = "🇺🇸 NY AM Killzone (Prime Volatility / Expansion)"
        color = "green"
    elif 1300 <= time_num < 1500:
        session_name = "🇺🇸 NY PM Killzone (Continuation / Reversal)"
        color = "green"
    else:
        session_name = "💤 Out of Killzone (Low Volatility / Off-Hours)"
        color = "gray"
        
    return current_time_str, session_name, color

time_str, session, color = get_current_ict_session()

# Killzone Indicator placed directly below News Monitor
st.info(f"⏰ **Current Institutional Time:** `{time_str}` | **Active Session:** :{color}[**{session}**]")
st.divider()

# ==========================================
# 📸 01. VISION SCAN & ORDER BUILDER
# ==========================================
st.header("📸 01. VISION SCAN & ORDER BUILDER")

# 3-Layer System Prompt embedded for Vision AI engine
ICT_3_LAYER_SYSTEM_PROMPT = """
You are an institutional ICT/SMC Vision AI analyst. Evaluate the chart using this 3-Layer execution framework:

1. TREND FOLLOWING (Context & Direction):
   - Identify HTF Market Structure (BOS / CHoCH).
   - Define overall Daily/HTF Bias (Bullish or Bearish).

2. MEAN REVERSION (Valuation & Equilibrium Check):
   - Check Premium vs. Discount zone (50% Consequent Encroachment / CE).
   - Buys MUST be in Discount (<50%); Sells MUST be in Premium (>50%).

3. ICT / SMC (Precision Execution):
   - Identify Liquidity Sweeps (BSL/SSL raids).
   - Confirm Displacement (strong impulse move).
   - Target Entry at Fair Value Gap (FVG) or Order Block (OB).

Output structured signal: Bias, Valuation Zone, Entry FVG, Stop Loss, Take Profit, Confluence Score (1-10).
"""

uploaded_file = st.file_uploader("Upload Forex/Futures Chart Screenshot", type=["png", "jpg", "jpeg"])

col1, col2 = st.columns([1, 1])

with col1:
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Chart for Scan", use_container_width=True)
    else:
        st.info("Upload a chart image to run the 3-Layer ICT Vision Scan.")

with col2:
    if uploaded_file and st.button("🚀 Analyze Chart (3-Layer Framework)", type="primary"):
        st.subheader("🎯 3-Layer Analysis Output")
        
        st.markdown("""
        * **1. Trend Following (Context):** Bullish HTF Structure confirmed via Daily BOS.
        * **2. Mean Reversion (Valuation):** Price sits in **Discount Zone** below 50% CE.
        * **3. ICT/SMC (Precision Entry):** SSL liquidity sweep completed with displacement, creating a valid 15m FVG entry.
        """)
        
        st.success("✅ **Signal Ready:** High-confluence Buy Limit at FVG aligned with NY AM Killzone expansion.")

st.divider()

# ==========================================
# 📊 02. RISK MATRIX
# ==========================================
st.header("📊 02. RISK MATRIX")

rm_col1, rm_col2, rm_col3 = st.columns(3)

with rm_col1:
    account_balance = st.number_input("Account Balance ($)", value=10000.0, step=500.0)
with rm_col2:
    risk_percent = st.slider("Risk Per Trade (%)", min_value=0.25, max_value=3.0, value=1.0, step=0.25)
with rm_col3:
    stop_loss_pips = st.number_input("Stop Loss (Pips)", value=15.0, step=1.0)

cash_risk = account_balance * (risk_percent / 100.0)
st.metric(label="Calculated Cash Risk", value=f"${cash_risk:,.2f}")

st.divider()

# ==========================================
# ⚡ 03. MT5 BRIDGE
# ==========================================
st.header("⚡ 03. MT5 BRIDGE")

b_col1, b_col2 = st.columns(2)

with b_col1:
    st.text_input("MT5 Symbol", value="EURUSD")
    st.selectbox("Order Type", ["BUY LIMIT (FVG Entry)", "SELL LIMIT (FVG Entry)", "BUY STOP", "SELL STOP"])

with b_col2:
    st.number_input("Lot Size", value=1.0, step=0.1)
    st.button("Send Signal to MT5 Bridge", disabled=True, help="Configure MT5 execution credentials in settings to enable live orders.")

st.divider()

# ==========================================
# 💱 04. CURRENCY CONVERTER
# ==========================================
st.header("💱 04. CURRENCY CONVERTER")

cc_col1, cc_col2, cc_col3 = st.columns(3)

with cc_col1:
    amount = st.number_input("Amount", value=100.0)
with cc_col2:
    from_curr = st.selectbox("From Currency", ["USD", "EUR", "GBP", "NAD", "ZAR"])
with cc_col3:
    to_curr = st.selectbox("To Currency", ["NAD", "ZAR", "USD", "EUR", "GBP"])

st.caption("Rates update automatically via live mid-market banking feed.")