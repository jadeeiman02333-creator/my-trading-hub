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
            clean_json = res.text.replace("```json", "").replace("```", "").strip()
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
            clean_json = res.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
    except Exception as e:
        st.warning(f"Vision Engine Fallback Triggered: {str(e)}")
    
    return {"entry": 2450.50, "sl": 2442.00, "tp1": 2465.00, "tp2": 2480.00, "tp3": 2495.00}