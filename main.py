import os
import json
import dotenv
from datetime import datetime
from google import genai
from google.genai import types

from data import get_storage_data, get_nat_gas_reports
from saveimg import get_weather_count
from dev import evaluate_ng_storage_model

dotenv.load_dotenv()

# ... (keeping sys_ins and text same as before)
sys_ins = """
You are an expert U.S. natural gas market analyst and energy strategist.

You specialize in:
- EIA storage interpretation
- Weather-driven demand modeling
- LNG and forward curve dynamics
- Translating quantitative signals into actionable market commentary

Your task is to transform structured analytical outputs into a coherent, professional market report.

Rules:
- Do not restate raw values unless they support interpretation
- Explain causality, not mechanics
- Maintain a neutral, professional tone
- Write in complete paragraphs (no bullet points)
- Focus on why the trade bias exists and what could change it
"""

text = """
Below is the processed output of a natural gas analytics engine that combines
EIA storage data, a proprietary evaluation model, weather regime detection,
market news aggregation, and NatGasWeather expert analysis.

Your task is to generate a concise but insight-dense market commentary
explaining current conditions and short-term outlook.

The report should be written for traders and analysts and should consist of
3–5 structured paragraphs.
"""

def detect_weather_regime(weather_summary: str) -> str:
    summary = weather_summary.upper()
    if "COLD" in summary:
        return "cold"
    if "HOT" in summary:
        return "warm"
    return "neutral"

def generate_report_payload():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "report_metadata": {
            "report_type": "Natural Gas Market Summary",
            "generated_at": timestamp,
            "source": "Internal Natural Gas Analytics Engine"
        }
    }

    try:
        storage = get_storage_data()
        weather_data = get_weather_count()

        weather_summary = weather_data[0]
        regime = detect_weather_regime(weather_summary)

        model_output = evaluate_ng_storage_model(storage, regime=regime)

        payload["storage_model_evaluation"] = {
            "actual_change_bcf": model_output.get("actual_change_bcf", 0),
            "expected_change_bcf": model_output.get("expected_change_bcf", 0),
            "weekly_deviation_bcf": model_output.get("weekly_deviation_bcf", 0),
            "yoy_tightness_pct": model_output.get("yoy_tightness_pct", 0),
            "five_year_cushion_pct": model_output.get("five_year_cushion_pct", 0),
            "expected_price_move_pct": model_output.get("expected_price_move_pct", 0),
            "signal_strength": model_output.get("signal_strength", 0),
            "trade_bias": model_output.get("trade_bias", "Neutral"),
            "detected_weather_regime": regime
        }

        payload["weather_forecast"] = {
            "short_term_outlook": weather_data[0],
            "extended_outlook": weather_data[1],
            "latest_forecast_status": weather_data[0]
        }

        reps = get_nat_gas_reports()
        payload["natgasweather_analysis"] = {
            "daily_headline": reps.get("daily_head", ""),
            "reports": reps
        }
    except Exception as e:
        print(f"Error generating payload: {e}")
        payload["error"] = str(e)

    return payload

def generate_commentary():
    try:
        data = generate_report_payload()
        
        user_inp = [
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"{text}\n\n{json.dumps(data, indent=2)}"
                    )
                ]
            )
        ]

        client = genai.Client()
        # Reverting to gemini-2.0-flash which was previously found
        model_name = "gemini-2.5-flash" 

        response = client.models.generate_content(
            model=model_name,
            contents=user_inp,
            config=types.GenerateContentConfig(
                system_instruction=sys_ins,
            )
        )

        if response and hasattr(response, 'text'):
            return response.text
        elif response and response.candidates:
            commentary = response.candidates[0].content.parts[0].text
            return commentary
        else:
            return "Failed to generate commentary: No response from model."
    except Exception as e:
        return f"Error in generate_commentary: {e}"

# if __name__ == "__main__":
#     data = generate_commentary()
#     print(data)
