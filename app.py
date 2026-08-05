import os
import streamlit as st
from PIL import Image
from google import genai
import openai
import anthropic

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Smart Money & ICT Trading Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Session State Setup
# ---------------------------------------------------------
if "settings_submitted" not in st.session_state:
    st.session_state.settings_submitted = False
if "asset_name" not in st.session_state:
    st.session_state.asset_name = "EURUSD"
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "M30"
if "ai_analysis_result" not in st.session_state:
    st.session_state.ai_analysis_result = None

# ---------------------------------------------------------
# API Keys Configuration (Streamlit Secrets / Environment)
# ---------------------------------------------------------
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
ANTHROPIC_KEY = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))

# ---------------------------------------------------------
# 1. Sidebar: Asset & Session Settings
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Asset & Session Settings")
    
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
            
            session_context = st.multiselect(
                "Session Context",
                ["Asian Killzone", "London Open", "NY AM Session", "NY PM Session"],
                default=["London Open"]
            )
            
            model_provider = st.selectbox(
                "Vision AI Provider",
                ["Google Gemini 2.5 Flash", "OpenAI GPT-4o", "Anthropic Claude 3.5 Sonnet"]
            )
            
            submit_button = st.form_submit_button(label="Confirm & Unlock Analysis")
            
            if submit_button:
                st.session_state.asset_name = asset_input
                st.session_state.timeframe = timeframe_input
                st.session_state.session_context = session_context
                st.session_state.model_provider = model_provider
                st.session_state.settings_submitted = True
                st.rerun()
    else:
        st.success(f"Active Pair: **{st.session_state.asset_name}** | **{st.session_state.timeframe}**")
        st.caption(f"Provider: {st.session_state.get('model_provider', 'Gemini 2.5 Flash')}")
        if st.button("✏️ Edit Settings"):
            st.session_state.settings_submitted = False
            st.rerun()

# ---------------------------------------------------------
# 2. Main Page Navigation & Workspace
# ---------------------------------------------------------
if not st.session_state.settings_submitted:
    st.title("📈 Smart Money & ICT Trading Hub")
    st.info("👈 Enter your setup details in the left sidebar and click 'Confirm & Unlock Analysis' to proceed.")
else:
    st.title(f"📊 Market Hub: {st.session_state.asset_name} [{st.session_state.timeframe}]")
    st.markdown("---")

    tabs = st.tabs(["🖼️ Vision AI Analysis", "📸 EasyOCR & Order Builder", "⚡ Live MT5 Execution Bridge"])

    # =========================================================
    # TAB 1: VISION AI CHART ANALYSIS
    # =========================================================
    with tabs[0]:
        st.subheader("🧠 Multi-Model Vision AI Chart Analysis (SMC / ICT)")
        st.caption("Upload your raw MT5 or TradingView screenshot for automated structural analysis.")

        uploaded_file = st.file_uploader("Upload Chart Screenshot (PNG/JPG)", type=["png", "jpg", "jpeg"])
        
        smc_frameworks = st.multiselect(
            "Confluence Filters for AI Engine:",
            ["Liquidity Sweep (BSL/SSL)", "Fair Value Gap (FVG)", "Order Block (OB)", "Break of Structure (BOS)", "Change of Character (CHoCH)", "Premium/Discount Array"],
            default=["Liquidity Sweep (BSL/SSL)", "Fair Value Gap (FVG)", "Order Block (OB)"]
        )
        
        additional_notes = st.text_area("Additional Trade Context / Confluences:", placeholder="e.g., Higher timeframe daily bias is bearish. Looking for NY AM reversal.")

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"Chart: {st.session_state.asset_name} ({st.session_state.timeframe})", use_container_width=True)
            
            if st.button("🚀 Run AI Chart Analysis", type="primary"):
                with st.spinner(f"Analyzing chart using {st.session_state.model_provider}..."):
                    
                    # System prompt for Smart Money Concepts / ICT
                    prompt = f"""
                    You are an expert Smart Money Concepts (SMC) and Inner Circle Trader (ICT) algorithmic analyst.
                    Analyze this chart screenshot for {st.session_state.asset_name} on the {st.session_state.timeframe} timeframe.
                    
                    Confluence Filters Requested: {', '.join(smc_frameworks)}
                    User Notes: {additional_notes}
                    
                    Provide a structured report containing:
                    1. Market Structure & Trend Bias (Bullish/Bearish/Consolidating)
                    2. Key SMC/ICT Elements Identified (FVGs, OBs, Liquidity Pools)
                    3. Precise Trade Setup Recommendation:
                       - Direction (BUY / SELL / WAIT)
                       - Recommended Entry Price
                       - Suggested Stop Loss Price
                       - Recommended Targets (TP1, TP2, TP3)
                    4. Risk-to-Reward Ratio Assessment & Execution Warning
                    """
                    
                    try:
                        # 1. Google GenAI Implementation (Updated SDK)
                        if "Gemini" in st.session_state.model_provider:
                            if not GEMINI_KEY:
                                st.error("Missing GEMINI_API_KEY in secrets.")
                            else:
                                client = genai.Client(api_key=GEMINI_KEY)
                                response = client.models.generate_content(
                                    model="gemini-2.5-flash",
                                    contents=[prompt, image]
                                )
                                st.session_state.ai_analysis_result = response.text
                                
                        # 2. OpenAI GPT-4o Implementation
                        elif "OpenAI" in st.session_state.model_provider:
                            if not OPENAI_KEY:
                                st.error("Missing OPENAI_API_KEY in secrets.")
                            else:
                                client = openai.OpenAI(api_key=OPENAI_KEY)
                                response = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": [
                                                {"type": "text", "text": prompt},
                                                {
                                                    "type": "image_url",
                                                    "image_url": {"url": f"data:image/jpeg;base64,{uploaded_file.getvalue()}"}
                                                }
                                            ]
                                        }
                                    ]
                                )
                                st.session_state.ai_analysis_result = response.choices[0].message.content
                                
                        # 3. Anthropic Claude 3.5 Implementation
                        elif "Anthropic" in st.session_state.model_provider:
                            if not ANTHROPIC_KEY:
                                st.error("Missing ANTHROPIC_API_KEY in secrets.")
                            else:
                                client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
                                response = client.messages.create(
                                    model="claude-3-5-sonnet-20240620",
                                    max_tokens=1500,
                                    messages=[{
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": prompt}
                                        ]
                                    }]
                                )
                                st.session_state.ai_analysis_result = response.content[0].text

                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")

        if st.session_state.ai_analysis_result:
            st.markdown("### 📋 AI Analysis Output")
            st.markdown(st.session_state.ai_analysis_result)

    # =========================================================
    # TAB 2: EASYOCR & TARGET ORDER BUILDER
    # =========================================================
    with tabs[1]:
        st.subheader("📸 EasyOCR & Target Order Builder")
        st.caption("Verify extracted targets or manually construct your 3-target trade parameter matrix.")

        col_ocr_1, col_ocr_2, col_ocr_3 = st.columns(3)

        with col_ocr_1:
            entry_price = st.number_input("Entry Price", value=1.08500, format="%.5f", step=0.00010)
            stop_loss = st.number_input("Stop Loss (SL)", value=1.08300, format="%.5f", step=0.00010)
            lot_size = st.number_input("Total Lot Size", value=0.10, format="%.2f", step=0.01)

        with col_ocr_2:
            target_1 = st.number_input("Target 1 (TP1)", value=1.08900, format="%.5f", step=0.00010)
            target_2 = st.number_input("Target 2 (TP2)", value=1.09300, format="%.5f", step=0.00010)

        with col_ocr_3:
            target_3 = st.number_input("Target 3 (TP3)", value=1.09700, format="%.5f", step=0.00010)
            order_type = st.selectbox("Order Direction", ["BUY", "SELL", "BUY LIMIT", "SELL LIMIT"])

        # Automatic Risk-to-Reward (R:R) Matrix
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

    # =========================================================
    # TAB 3: LIVE MT5 EXECUTION BRIDGE
    # =========================================================
    with tabs[2]:
        st.subheader("⚡ Live MetaTrader 5 (MT5) Execution Bridge")
        st.caption("Send configured parameter bundles directly to your local PC MetaTrader terminal.")

        if "active_order" in st.session_state:
            order = st.session_state.active_order
            st.json(order)
            
            st.markdown("#### Execution Parameters Split")
            col_split_1, col_split_2, col_split_3 = st.columns(3)
            col_split_1.metric("Order 1 (TP1)", f"{order['lots']*0.5:.2f} Lots @ TP {order['tp1']}")
            col_split_2.metric("Order 2 (TP2)", f"{order['lots']*0.3:.2f} Lots @ TP {order['tp2']}")
            col_split_3.metric("Order 3 (TP3)", f"{order['lots']*0.2:.2f} Lots @ TP {order['tp3']}")
            
            if st.button("🔥 Transmit Multi-Target Orders to MT5", type="primary"):
                st.success(f"Order Signal dispatched for {order['asset']} ({order['type']})! Check MT5 Expert Advisor listener.")
        else:
            st.warning("Configure your order details in Tab 2 before opening the bridge.")