import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# =========================================================
# PAGE CONFIG & CUSTOM CSS
# =========================================================
st.set_page_config(
    page_title="Killzone Terminal - ICT Order Flow",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
    }

    /* Section Headers */
    .section-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem;
        font-weight: 700;
        color: #00E676;
        letter-spacing: 1px;
        margin-bottom: 15px;
        border-left: 3px solid #00E676;
        padding-left: 10px;
    }

    /* Analysis Cards */
    .analysis-card {
        background: #141923;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 15px;
    }

    .smc-card {
        background: rgba(0, 230, 118, 0.05);
        border: 1px solid rgba(0, 230, 118, 0.2);
        border-radius: 8px;
        padding: 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        margin-top: 10px;
    }

    .stat-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.85rem;
        margin-right: 8px;
    }

    .rationale-text {
        font-size: 0.92rem;
        color: #94A3B8;
        line-height: 1.6;
    }

    /* Input Customization */
    div[data-baseweb="input"] {
        background-color: #1A202C !important;
        border-color: #2D3748 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================
if "trade_score" not in st.session_state:
    st.session_state.trade_score = 8.5
if "trade_accuracy" not in st.session_state:
    st.session_state.trade_accuracy = 87
if "order_bias" not in st.session_state:
    st.session_state.order_bias = "BULLISH"
if "asset_name" not in st.session_state:
    st.session_state.asset_name = "EURUSD"
if "ocr_entry" not in st.session_state:
    st.session_state.ocr_entry = "1.08520"
if "ocr_sl" not in st.session_state:
    st.session_state.ocr_sl = "1.08310"
if "ocr_tp1" not in st.session_state:
    st.session_state.ocr_tp1 = "1.08940"
if "ocr_tp2" not in st.session_state:
    st.session_state.ocr_tp2 = "1.09350"
if "trade_rationale" not in st.session_state:
    st.session_state.trade_rationale = "High probability bullish expansion identified following liquidity sweep of London Lows into a 15m Fair Value Gap (FVG). Displacement aligns with Daily Bias."
if "fvg_data" not in st.session_state:
    st.session_state.fvg_data = {"top_price": 1.08610, "bottom_price": 1.08430, "ce_price": 1.08520}
if "disp_data" not in st.session_state:
    st.session_state.disp_data = {"description": "Institutional buying pressure detected (+2.4x average volume)."}
if "trade_history" not in st.session_state:
    st.session_state.trade_history = []

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def format_price(val):
    try:
        return f"{float(val):.5f}"
    except (ValueError, TypeError):
        return "0.00000"

@st.cache_data(ttl=3600)
def fetch_live_exchange_rates(base="USD"):
    try:
        res = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=5)
        if res.status_code == 200:
            return res.json().get("rates", {})
    except Exception:
        pass
    # Fallback rates
    return {"USD": 1.0, "EUR": 0.92, "GBP": 0.78, "ZAR": 18.20, "NAD": 18.20, "JPY": 155.40, "AUD": 1.52, "CAD": 1.36, "CHF": 0.89}

def render_circular_bias_gauge(bias, accuracy):
    color = "#00E676" if bias.upper() in ["BUY", "BULLISH"] else "#FF1744"
    st.markdown(f"""
    <div style="text-align: center; background: #141923; padding: 15px; border-radius: 10px; border: 1px solid #1E293B;">
        <div style="font-size: 0.8rem; color: #64748B; font-weight: 600;">INSTITUTIONAL BIAS & ACCURACY</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 800; color: {color}; margin: 5px 0;">
            {bias.upper()} ({accuracy}%)
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_embedded_copy_input(label, key_name, param_type):
    st.session_state[key_name] = st.text_input(label, value=st.session_state[key_name], key=f"input_{key_name}")

# =========================================================
# SIDEBAR NAVIGATION & GLOBAL CONTROLS
# =========================================================
with st.sidebar:
    st.markdown("### ⚡ KILLZONE TERMINAL")
    st.caption("ICT/SMC Order Flow & Vision Suite")
    st.markdown("---")
    
    st.session_state.asset_name = st.selectbox(
        "Active Asset Pair",
        ["EURUSD", "GBPUSD", "XAUUSD", "USDJPY", "BTCUSD", "NDX100"],
        index=0
    )
    
    timeframe = st.selectbox("Primary Timeframe", ["M1", "M5", "M15", "H1", "H4", "D1"], index=2)
    session_type = st.radio("Active Killzone", ["London Open", "New York AM", "New York PM", "Asian Range"], index=1)
    
    st.markdown("---")
    st.markdown("**Session Status:** 🟢 Live Vision Sync")
    st.markdown(f"**Current UTC:** `{datetime.utcnow().strftime('%H:%M:%S')}`")

# =========================================================
# MAIN DASHBOARD TABS
# =========================================================
tabs = st.tabs([
    "🎯 ICT Scan & Confluence",
    "📊 Risk Matrix",
    "⚡ MT5 Bridge",
    "𒒱 Currency Converter"
])

# ---------------------------------------------------------
# TAB 01: ICT SCAN & CONFLUENCE
# ---------------------------------------------------------
with tabs[0]:
    st.markdown('<div class="section-header">1. CHART VISION EXTRACTION & ICT CONFLUENCE SCAN</div>', unsafe_allow_html=True)
    
    col_scan_left, col_scan_right = st.columns([1, 1.2], gap="large")

    with col_scan_left:
        st.markdown("### Screenshot Upload")
        uploaded_file = st.file_uploader("Upload Chart Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Target Chart Screenshot", use_container_width=True)
        else:
            st.info("💡 Upload a chart screenshot to analyze Market Structure, FVGs, and Liquidity Pools.")

        if st.button("🚀 EXECUTE VISION EXTRACTION", use_container_width=True, type="primary"):
            with st.spinner("Analyzing institutional order flow & market structure..."):
                # Mock update for vision extraction simulation
                st.session_state.ocr_entry = "1.08520"
                st.session_state.ocr_sl = "1.08310"
                st.session_state.ocr_tp1 = "1.08940"
                st.session_state.ocr_tp2 = "1.09350"
                st.session_state.trade_score = 9.1
                st.session_state.order_bias = "BUY"
                st.success("Vision extraction complete!")

    with col_scan_right:
        st.markdown("### ICT Analysis & Confluence")
        
        entry_val = float(st.session_state.ocr_entry)
        sl_val = float(st.session_state.ocr_sl)
        tp1_val = float(st.session_state.ocr_tp1)
        
        sl_dist = abs(entry_val - sl_val)
        tp_dist = abs(tp1_val - entry_val)
        rr_ratio = (tp_dist / sl_dist) if sl_dist > 0 else 0.0
        
        score_color = "#00E676" if st.session_state.trade_score >= 7.0 else "#FFC107"

        st.markdown(f"""
        <div class="analysis-card">
            <div style="margin-bottom: 10px;">
                <span class="stat-badge" style="background: rgba(0, 230, 118, 0.15); color: {score_color}; border: 1px solid {score_color};">
                    SCORE: {st.session_state.trade_score:.1f} / 10
                </span>
                <span class="stat-badge" style="background: rgba(0, 230, 118, 0.15); color: #00E676; border: 1px solid #00E676;">
                    R:R = 1:{rr_ratio:.2f}
                </span>
            </div>
            <div class="rationale-text">
                <strong>Institutional Rationale:</strong><br/>
                {st.session_state.trade_rationale}
            </div>
        </div>
        """, unsafe_allow_html=True)

        render_circular_bias_gauge(st.session_state.order_bias, st.session_state.trade_accuracy)

        if st.session_state.fvg_data or st.session_state.disp_data:
            disp_txt = st.session_state.disp_data.get("description", "No displacement logged.") if isinstance(st.session_state.disp_data, dict) else "N/A"
            fvg_top = format_price(st.session_state.fvg_data.get("top_price", 0.0)) if isinstance(st.session_state.fvg_data, dict) else "0.00000"
            fvg_bot = format_price(st.session_state.fvg_data.get("bottom_price", 0.0)) if isinstance(st.session_state.fvg_data, dict) else "0.00000"
            fvg_ce = format_price(st.session_state.fvg_data.get("ce_price", 0.0)) if isinstance(st.session_state.fvg_data, dict) else "0.00000"
            
            st.markdown(f"""
            <div class="smc-card">
                <strong>⚡ DISPLACEMENT:</strong> {disp_txt}<br/><br/>
                <strong>📐 FVG ARRAY (CE 50%):</strong> Top: <code>{fvg_top}</code> | CE: <code>{fvg_ce}</code> | Bottom: <code>{fvg_bot}</code>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top: 20px;">2. EXTRACTED PRICE PARAMETERS</div>', unsafe_allow_html=True)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            render_embedded_copy_input("ENTRY PRICE (CE Midpoint)", "ocr_entry", "entry")
            render_embedded_copy_input("STOP LOSS (SL)", "ocr_sl", "sl")
        with col_p2:
            render_embedded_copy_input("TAKE PROFIT 1 (TP1)", "ocr_tp1", "tp1")
            render_embedded_copy_input("TAKE PROFIT 2 (TP2)", "ocr_tp2", "tp2")

# ---------------------------------------------------------
# TAB 02: RISK MATRIX
# ---------------------------------------------------------
with tabs[1]:
    st.markdown('<div class="section-header">📊 QUANTITATIVE RISK & POSITION SIZING MATRIX</div>', unsafe_allow_html=True)
    
    col_rm1, col_rm2 = st.columns([1, 1.2], gap="large")

    with col_rm1:
        st.markdown("### Account & Risk Setup")
        account_balance = st.number_input("Account Balance", min_value=10.0, value=10000.0, step=500.0, format="%.2f")
        account_currency = st.selectbox("Account Base Currency", ["USD", "EUR", "GBP", "NAD", "ZAR"], index=0)
        risk_percent = st.slider("Risk Per Trade (%)", min_value=0.25, max_value=5.0, value=1.0, step=0.25)

        st.markdown("---")
        st.markdown("### Trade Parameters (Auto-Synced)")
        entry_p = st.number_input("Entry Price", value=float(st.session_state.ocr_entry), format="%.5f")
        sl_p = st.number_input("Stop Loss Price", value=float(st.session_state.ocr_sl), format="%.5f")
        tp_p = st.number_input("Target Price (TP1)", value=float(st.session_state.ocr_tp1), format="%.5f")

    with col_rm2:
        st.markdown("### Calculated Metrics")
        
        risk_amount = account_balance * (risk_percent / 100.0)
        sl_distance = abs(entry_p - sl_p)
        tp_distance = abs(tp_p - entry_p)

        is_gold = "XAU" in st.session_state.asset_name.upper()
        is_jpy = "JPY" in st.session_state.asset_name.upper()
        
        if is_gold:
            pip_value_per_lot = 100.0
            pips_at_risk = sl_distance
        elif is_jpy:
            pip_value_per_lot = 1000.0 / 150.0
            pips_at_risk = sl_distance * 100.0
        else:
            pip_value_per_lot = 10.0
            pips_at_risk = sl_distance * 10000.0

        if sl_distance > 0:
            recommended_lots = risk_amount / (pips_at_risk * (pip_value_per_lot if not is_gold else 100.0))
            rr_calc = (tp_distance / sl_distance) if sl_distance > 0 else 0.0
            reward_amount = risk_amount * rr_calc
        else:
            recommended_lots = 0.00
            rr_calc = 0.0
            reward_amount = 0.0

        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("MONETARY RISK", f"{account_currency} {risk_amount:,.2f}")
            st.metric("ESTIMATED LOT SIZE", f"{max(0.01, recommended_lots):.2f} Lots")
        with m_col2:
            st.metric("POTENTIAL REWARD", f"{account_currency} {reward_amount:,.2f}")
            st.metric("RISK TO REWARD", f"1 : {rr_calc:.2f}")

        st.markdown(f"""
        <div class="analysis-card" style="margin-top: 15px;">
            <div style="font-size: 0.85rem; color: #94A3B8;">
                <strong>🛡️ Risk Rule Evaluation:</strong><br/>
                • Single Trade Risk: <span style="color: {'#00E676' if risk_percent <= 2.0 else '#FF1744'};">{risk_percent:.2f}% ({account_currency} {risk_amount:,.2f})</span><br/>
                • Max Stop Distance: <code>{pips_at_risk:.1f} Pips/Points</code><br/>
                • Account Preservation: Free Margin remains at <code>{account_balance - risk_amount:,.2f}</code> post-execution.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("💾 SAVE TRADE TO SESSION JOURNAL", use_container_width=True):
            trade_record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "asset": st.session_state.asset_name,
                "bias": st.session_state.order_bias,
                "entry": entry_p,
                "sl": sl_p,
                "tp1": tp_p,
                "lots": max(0.01, round(recommended_lots, 2)),
                "risk_usd": risk_amount,
                "rr": round(rr_calc, 2)
            }
            st.session_state.trade_history.append(trade_record)
            st.success("Trade successfully logged to session history!")

# ---------------------------------------------------------
# TAB 03: MT5 BRIDGE
# ---------------------------------------------------------
with tabs[2]:
    st.markdown('<div class="section-header">⚡ METATRADER 5 AUTOMATION & BRIDGE GENERATOR</div>', unsafe_allow_html=True)
    st.caption("Auto-generate execution scripts for MT5 EAs or Python MetaTrader5 API integration.")

    b_col1, b_col2 = st.columns([1, 1], gap="large")

    with b_col1:
        st.markdown("### MQL5 Script Generator")
        
        order_type_str = "ORDER_TYPE_BUY_LIMIT" if st.session_state.order_bias.upper() in ["BUY", "BULLISH"] else "ORDER_TYPE_SELL_LIMIT"
        rec_lots = max(0.01, round(recommended_lots, 2)) if 'recommended_lots' in locals() else 0.10
        
        mql5_code = f"""//+------------------------------------------------------------------+
//|                                         Killzone_Order_Bridge.mq5 |
//|                                   Generated via Killzone Terminal |
//+------------------------------------------------------------------+
#property copyright "Killzone Algorithmic Engine"
#property version   "1.00"
#property script_show_inputs

input double InpLotSize = {rec_lots}; // Lot Size
input double InpEntry   = {st.session_state.ocr_entry}; // Entry Price
input double InpSL      = {st.session_state.ocr_sl}; // Stop Loss
input double InpTP1     = {st.session_state.ocr_tp1}; // Take Profit 1

void OnStart()
{{
   MqlTradeRequest request;
   MqlTradeResult  result;
   ZeroMemory(request);
   ZeroMemory(result);

   request.action       = TRADE_ACTION_PENDING;
   request.symbol       = "{st.session_state.asset_name}";
   request.volume       = InpLotSize;
   request.type         = {order_type_str};
   request.price        = InpEntry;
   request.sl           = InpSL;
   request.tp           = InpTP1;
   request.type_filling = ORDER_FILLING_IOC;
   request.comment      = "Killzone_ICT_Order";

   if(!OrderSend(request, result))
      Print("OrderSend Error: ", GetLastError());
   else
      Print("Killzone Order Successfully Placed ticket #", result.order);
}}
"""
        st.code(mql5_code, language="cpp")
        st.download_button(
            label="📥 DOWNLOAD .MQ5 SCRIPT",
            data=mql5_code,
            file_name=f"Killzone_{st.session_state.asset_name}_{st.session_state.order_bias}.mq5",
            mime="text/x-c",
            use_container_width=True
        )

    with b_col2:
        st.markdown("### Python MT5 Direct Execution Script")
        
        py_mt5_code = f"""import MetaTrader5 as mt5

# Initialize MT5 Connection
if not mt5.initialize():
    print("MT5 Initialization failed")
    mt5.shutdown()

symbol = "{st.session_state.asset_name}"
lot = {rec_lots}
price = {st.session_state.ocr_entry}
sl = {st.session_state.ocr_sl}
tp = {st.session_state.ocr_tp1}
order_type = mt5.ORDER_TYPE_BUY_LIMIT if "{st.session_state.order_bias}" in ["BUY", "BULLISH"] else mt5.ORDER_TYPE_SELL_LIMIT

request = {{
    "action": mt5.TRADE_ACTION_PENDING,
    "symbol": symbol,
    "volume": lot,
    "type": order_type,
    "price": price,
    "sl": sl,
    "tp": tp,
    "deviation": 20,
    "magic": 202608,
    "comment": "Killzone Python Auto-Bridge",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}}

result = mt5.order_send(request)
print(f"Order send result: {{result.retcode}}")
mt5.shutdown()
"""
        st.code(py_mt5_code, language="python")

# ---------------------------------------------------------
# TAB 04: CURRENCY CONVERTER
# ---------------------------------------------------------
with tabs[3]:
    st.markdown('<div class="section-header">𒒱 LIVE INSTITUTIONAL CURRENCY CONVERTER</div>', unsafe_allow_html=True)

    rates = fetch_live_exchange_rates("USD")

    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:
        amount = st.number_input("Amount to Convert", min_value=1.0, value=1000.0, step=100.0)
    with col_c2:
        from_curr = st.selectbox("From Currency", list(rates.keys()), index=list(rates.keys()).index("USD") if "USD" in rates else 0)
    with col_c3:
        to_curr = st.selectbox("To Currency", list(rates.keys()), index=list(rates.keys()).index("ZAR") if "ZAR" in rates else (1 if len(rates) > 1 else 0))

    from_rate = rates.get(from_curr, 1.0)
    to_rate = rates.get(to_curr, 1.0)
    
    converted_amount = (amount / from_rate) * to_rate
    single_rate = to_rate / from_rate

    st.markdown(f"""
    <div class="analysis-card" style="text-align: center; margin-top: 20px;">
        <div style="font-size: 0.9rem; color: #94A3B8;">CONVERTED VALUE</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 2.2rem; font-weight: 800; color: #00E676; margin: 10px 0;">
            {converted_amount:,.2f} <span style="font-size: 1.2rem; color: #FFFFFF;">{to_curr}</span>
        </div>
        <div style="font-size: 0.8rem; color: #64748B;">
            Exchange Rate: 1 {from_curr} = {single_rate:.4f} {to_curr}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Quick Reference Rates (Base USD)")
    
    ref_currencies = ["EUR", "GBP", "ZAR", "NAD", "JPY", "AUD", "CAD", "CHF"]
    ref_data = [{"Currency Pair": f"USD / {c}", "Exchange Rate": f"{rates.get(c, 0.0):.4f}"} for c in ref_currencies if c in rates]
    
    if ref_data:
        st.table(pd.DataFrame(ref_data))