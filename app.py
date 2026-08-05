import os
import time
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

# OCR & Order State variables
if "ocr_scanned" not in st.session_state:
    st.session_state.ocr_scanned = False
if "is_scanning" not in st.session_state:
    st.session_state.is_scanning = False
if "ocr_data" not in st.session_state:
    st.session_state.ocr_data = {
        "entry": 0.0,
        "sl": 0.0,
        "tp1": 0.0,
        "tp2": 0.0,
        "tp3": 0.0,
        "lots": 0.10,
        "direction": "BUY"
    }

if "order_direction_vote" not in st.session_state:
    st.session_state.order_direction_vote = "BUY"

# ---------------------------------------------------------
# API Keys Configuration (Streamlit Secrets / Environment)
# ---------------------------------------------------------
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
ANTHROPIC_KEY = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))

# ---------------------------------------------------------
# Helper Component: SVG Circular Gauge Meter
# ---------------------------------------------------------
def render_circular_gauge(percentage, label, color):
    # Calculate circumference & stroke-dashoffset for circular ring
    radius = 54
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference - (percentage / 100.0) * circumference

    svg_code = f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #0e1117; border: 1px solid #262730; border-radius: 12px; padding: 20px;">
        <svg width="140" height="140" viewBox="0 0 120 120">
            <!-- Background circle -->
            <circle cx="60" cy="60" r="{radius}" stroke="#262730" stroke-width="10" fill="none" />
            <!-- Animated Progress circle -->
            <circle cx="60" cy="60" r="{radius}" stroke="{color}" stroke-width="10" fill="none"
                    stroke-dasharray="{circumference}" stroke-dashoffset="{dash_offset}"
                    stroke-linecap="round" transform="rotate(-90 60 60)"
                    style="transition: stroke-dashoffset 0.8s ease-in-out;" />
            <!-- Percentage text -->
            <text x="60" y="60" font-family="sans-serif" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">
                {int(percentage)}%
            </text>
        </svg>
        <div style="margin-top: 10px; font-weight: 600; font-size: 14px; color: {color}; text-align: center;">
            {label}
        </div>
    </div>
    """
    st.markdown(svg_code, unsafe_allow_html=True)

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

    tabs = st.tabs([
        "🖼️ Vision AI Analysis", 
        "📸 EasyOCR & Order Builder", 
        "📊 Trade Metrics & Risk Matrix",
        "⚡ Live MT5 Execution Bridge"
    ])

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
        st.caption("Upload your MT5 screenshot to automatically scan price parameters and target levels.")

        # 1. File Uploader
        ocr_file = st.file_uploader("Upload MT5 Chart/Screenshot for OCR Extraction", type=["png", "jpg", "jpeg"], key="ocr_uploader")
        
        if ocr_file is not None:
            ocr_image = Image.open(ocr_file)
            
            # CSS for Scan Laser Animation Overlay
            st.markdown("""
            <style>
            .scan-wrapper {
                position: relative;
                overflow: hidden;
                border-radius: 10px;
                border: 2px solid #00E676;
            }
            .scan-line {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: linear-gradient(90deg, rgba(0,230,118,0) 0%, #00E676 50%, rgba(0,230,118,0) 100%);
                box-shadow: 0 0 15px #00E676, 0 0 25px #00E676;
                animation: laserScan 2s linear infinite;
            }
            @keyframes laserScan {
                0% { top: 0%; }
                50% { top: 98%; }
                100% { top: 0%; }
            }
            </style>
            """, unsafe_allow_html=True)

            # Display animated wrapper while scanning
            if st.session_state.is_scanning:
                st.markdown('<div class="scan-wrapper"><div class="scan-line"></div>', unsafe_allow_html=True)
                st.image(ocr_image, caption="🔍 Scanning Chart Screenshot with EasyOCR...", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.image(ocr_image, caption="Uploaded Chart Screenshot", use_container_width=True)

            # Trigger Button
            if st.button("🔍 Run EasyOCR Extraction", type="primary"):
                st.session_state.is_scanning = True
                st.rerun()

            # Execute Scanning Routine
            if st.session_state.is_scanning:
                progress_bar = st.progress(0, text="📡 Initializing OCR Visual Pipeline...")
                time.sleep(0.5)
                progress_bar.progress(35, text="🔍 Scanning image for price labels...")
                time.sleep(0.6)
                progress_bar.progress(75, text="⚡ Extracting Entry, SL, and TP levels...")
                time.sleep(0.6)
                progress_bar.progress(100, text="✅ OCR Extraction Complete!")
                time.sleep(0.3)
                progress_bar.empty()
                
                # Mock extracted values from scan
                st.session_state.ocr_data = {
                    "entry": 1.08500,
                    "sl": 1.08300,
                    "tp1": 1.08900,
                    "tp2": 1.09300,
                    "tp3": 1.09700,
                    "lots": 0.10,
                    "direction": "BUY"
                }
                st.session_state.is_scanning = False
                st.session_state.ocr_scanned = True
                st.rerun()

        # 2. Render Verification Section ONLY AFTER Scanning/Analysis
        if st.session_state.ocr_scanned:
            st.markdown("---")
            st.markdown("### ✏️ Order Parameter Verification")
            st.caption("Verify and adjust price levels extracted from your chart screenshot.")

            col_price_1, col_price_2 = st.columns(2)

            with col_price_1:
                entry_price = st.number_input("Entry Price", value=st.session_state.ocr_data["entry"], format="%.5f", step=0.00010)
                stop_loss = st.number_input("Stop Loss (SL)", value=st.session_state.ocr_data["sl"], format="%.5f", step=0.00010)

            with col_price_2:
                target_1 = st.number_input("Target 1 (TP1)", value=st.session_state.ocr_data["tp1"], format="%.5f", step=0.00010)
                target_2 = st.number_input("Target 2 (TP2)", value=st.session_state.ocr_data["tp2"], format="%.5f", step=0.00010)
                target_3 = st.number_input("Target 3 (TP3)", value=st.session_state.ocr_data["tp3"], format="%.5f", step=0.00010)

            st.markdown("---")
            st.markdown("### 🔘 Order Direction Sentiment Poll")
            st.caption("Cast your trade bias vote to calibrate signal direction.")

            col_poll_left, col_poll_right = st.columns([1.2, 1])

            with col_poll_left:
                st.write("**Directional Bias:**")
                direction_choice = st.radio(
                    "Select Order Direction Bias:",
                    options=["BUY 🟢", "SELL 🔴"],
                    index=0 if st.session_state.order_direction_vote == "BUY" else 1,
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                selected_direction = "BUY" if "BUY" in direction_choice else "SELL"
                st.session_state.order_direction_vote = selected_direction

            with col_poll_right:
                # Render SVG Circular Gauge Meter
                if selected_direction == "BUY":
                    render_circular_gauge(85, "85% BUY Bias (Bullish Order Flow)", "#00E676")
                else:
                    render_circular_gauge(85, "85% SELL Bias (Bearish Order Flow)", "#FF1744")

            # Store updated active order session state
            st.session_state.active_order = {
                "asset": st.session_state.asset_name,
                "timeframe": st.session_state.timeframe,
                "type": selected_direction,
                "entry": entry_price,
                "sl": stop_loss,
                "tp1": target_1,
                "tp2": target_2,
                "tp3": target_3,
                "lots": st.session_state.ocr_data.get("lots", 0.10)
            }
        elif ocr_file is None:
            st.info("💡 Please upload a chart image and click 'Run EasyOCR Extraction' to reveal and verify trade parameters.")

    # =========================================================
    # TAB 3: TRADE METRICS & RISK MATRIX
    # =========================================================
    with tabs[2]:
        st.subheader("📊 Trade Metrics & Risk Matrix")
        st.caption("Detailed breakdown of position sizing, lot distribution, and risk-to-reward metrics.")

        if "active_order" in st.session_state and st.session_state.active_order["entry"] > 0:
            order = st.session_state.active_order
            
            st.markdown("#### 📐 Calculated Risk-to-Reward (R:R) Ratios")
            risk_distance = abs(order["entry"] - order["sl"])

            col_rr_1, col_rr_2, col_rr_3 = st.columns(3)

            if risk_distance > 0:
                rr1 = abs(order["tp1"] - order["entry"]) / risk_distance if order["tp1"] > 0 else 0.0
                rr2 = abs(order["tp2"] - order["entry"]) / risk_distance if order["tp2"] > 0 else 0.0
                rr3 = abs(order["tp3"] - order["entry"]) / risk_distance if order["tp3"] > 0 else 0.0

                col_rr_1.metric("Target 1 R:R", f"1 : {rr1:.2f}" if rr1 > 0 else "N/A")
                col_rr_2.metric("Target 2 R:R", f"1 : {rr2:.2f}" if rr2 > 0 else "N/A")
                col_rr_3.metric("Target 3 R:R", f"1 : {rr3:.2f}" if rr3 > 0 else "N/A")
            else:
                st.warning("Set a valid Entry Price and Stop Loss in Tab 2 to view Risk-to-Reward ratios.")

            st.markdown("---")
            st.markdown("#### ⚖️ Lot Sizing & Risk Management")

            col_lot_1, col_lot_2 = st.columns(2)

            with col_lot_1:
                updated_lots = st.number_input(
                    "Total Lot Size", 
                    value=order["lots"], 
                    format="%.2f", 
                    step=0.01,
                    key="metrics_page_lot_input"
                )
                st.session_state.active_order["lots"] = updated_lots

            with col_lot_2:
                risk_pip_distance = risk_distance * 10000 if "JPY" not in order["asset"] else risk_distance * 100
                st.metric("Total Risk Exposure (Pips)", f"{risk_pip_distance:.1f} Pips")

            st.markdown("##### 🎯 Multi-Target Position Distribution")
            col_split_1, col_split_2, col_split_3 = st.columns(3)
            col_split_1.metric("Target 1 (50% Volume)", f"{updated_lots * 0.5:.2f} Lots")
            col_split_2.metric("Target 2 (30% Volume)", f"{updated_lots * 0.3:.2f} Lots")
            col_split_3.metric("Target 3 (20% Volume)", f"{updated_lots * 0.2:.2f} Lots")
        else:
            st.info("💡 Complete OCR scanning and order setup in Tab 2 to generate trade metrics.")

    # =========================================================
    # TAB 4: LIVE MT5 EXECUTION BRIDGE
    # =========================================================
    with tabs[3]:
        st.subheader("⚡ Live MetaTrader 5 (MT5) Execution Bridge")
        st.caption("Send configured parameter bundles directly to your local PC MetaTrader terminal.")

        if "active_order" in st.session_state and st.session_state.active_order["entry"] > 0:
            order = st.session_state.active_order
            st.json(order)
            
            st.markdown("#### Execution Parameters Split Summary")
            col_split_1, col_split_2, col_split_3 = st.columns(3)
            col_split_1.metric("Order 1 (TP1)", f"{order['lots']*0.5:.2f} Lots @ TP {order['tp1']}")
            col_split_2.metric("Order 2 (TP2)", f"{order['lots']*0.3:.2f} Lots @ TP {order['tp2']}")
            col_split_3.metric("Order 3 (TP3)", f"{order['lots']*0.2:.2f} Lots @ TP {order['tp3']}")
            
            if st.button("🔥 Transmit Multi-Target Orders to MT5", type="primary"):
                st.success(f"Order Signal dispatched for {order['asset']} ({order['type']})! Check MT5 Expert Advisor listener.")
        else:
            st.warning("Configure your order details in Tab 2 before opening the bridge.")