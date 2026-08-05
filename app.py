import os
import streamlit as st

# Set page layout configuration
st.set_page_config(
    page_title="Smart Money Trading Hub",
    page_icon="📈",
    layout="wide"
)

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "settings_submitted" not in st.session_state:
    st.session_state.settings_submitted = False

if "asset_name" not in st.session_state:
    st.session_state.asset_name = "EURUSD"

if "timeframe" not in st.session_state:
    st.session_state.timeframe = "M30"

# ---------------------------------------------------------
# 1. Asset & Session Settings (Sidebar)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Asset & Session Settings")
    
    # Form visible BEFORE confirmation
    if not st.session_state.settings_submitted:
        with st.form(key="asset_settings_form"):
            asset_input = st.text_input(
                "Asset / Pair Name", 
                value=st.session_state.asset_name, 
                placeholder="e.g., EURUSD, BTCUSD, XAUUSD"
            )
            
            timeframe_input = st.selectbox(
                "Timeframe", 
                ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"],
                index=["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"].index(st.session_state.timeframe)
            )
            
            submit_button = st.form_submit_button(label="Confirm & Unlock Analysis")
            
            if submit_button:
                st.session_state.asset_name = asset_input
                st.session_state.timeframe = timeframe_input
                st.session_state.settings_submitted = True
                st.rerun()
                
    # Summary box visible AFTER confirmation (Form closes automatically)
    else:
        st.success(f"Active Pair: **{st.session_state.asset_name}**\nTimeframe: **{st.session_state.timeframe}**")
        if st.button("✏️ Edit Settings"):
            st.session_state.settings_submitted = False
            st.rerun()

# ---------------------------------------------------------
# 2. Main Page Layout
# ---------------------------------------------------------
if not st.session_state.settings_submitted:
    st.title("📈 Smart Money Trading Hub")
    st.info("Enter your setup details in the left sidebar and click 'Confirm & Unlock Analysis' to proceed.")
else:
    st.title(f"📊 Market Hub: {st.session_state.asset_name} [{st.session_state.timeframe}]")
    st.markdown("---")

    # ---------------------------------------------------------
    # EasyOCR Auto-Converted MT5 Orders Section
    # ---------------------------------------------------------
    st.subheader("📸 EasyOCR Auto-Converted MT5 Orders")
    st.caption("Upload or verify extracted level targets from your MT5 terminal.")

    col_ocr_1, col_ocr_2, col_ocr_3 = st.columns(3)

    with col_ocr_1:
        entry_price = st.number_input("Entry Price", value=1.08500, format="%.5f", step=0.00010)
        stop_loss = st.number_input("Stop Loss (SL)", value=1.08300, format="%.5f", step=0.00010)
        lot_size = st.number_input("Lot Size", value=0.10, format="%.2f", step=0.01)

    with col_ocr_2:
        target_1 = st.number_input("Target 1 (TP1)", value=1.08900, format="%.5f", step=0.00010)
        target_2 = st.number_input("Target 2 (TP2)", value=1.09300, format="%.5f", step=0.00010)

    with col_ocr_3:
        target_3 = st.number_input("Target 3 (TP3)", value=1.09700, format="%.5f", step=0.00010)
        order_type = st.selectbox("Order Direction", ["BUY", "SELL"])

    # Automatic Risk-to-Reward (R:R) Calculation
    risk_distance = abs(entry_price - stop_loss)
    
    st.markdown("##### 📐 Calculated Risk-to-Reward Ratios")
    col_rr_1, col_rr_2, col_rr_3 = st.columns(3)

    if risk_distance > 0:
        rr1 = abs(target_1 - entry_price) / risk_distance
        rr2 = abs(target_2 - entry_price) / risk_distance
        rr3 = abs(target_3 - entry_price) / risk_distance

        col_rr_1.metric("Target 1 R:R", f"1 : {rr1:.2f}")
        col_rr_2.metric("Target 2 R:R", f"1 : {rr2:.2f}")
        col_rr_3.metric("Target 3 R:R", f"1 : {rr3:.2f}")
    else:
        st.warning("Set a valid Entry Price and Stop Loss to view Risk-to-Reward ratios.")

    # Save details into session state
    st.session_state.active_order = {
        "asset": st.session_state.asset_name,
        "timeframe": st.session_state.timeframe,
        "type": order_type,
        "entry": entry_price,
        "sl": stop_loss,
        "tp1": target_1,
        "tp2": target_2,
        "tp3": target_3,
        "lots": lot_size
    }

    st.markdown("---")
    st.success("Ready for Vision AI Chart Analysis and MT5 Execution.")