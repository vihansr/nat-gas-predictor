from PIL import Image, ImageDraw
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import BytesIO
from PIL import Image
import time


import concurrent.futures
import colorsys


def classify_temperature_from_image(img, dominance_threshold=20):
    # ... (keeping logic same as verified before)
    arr = np.array(img.convert("RGB"))
    avg_r, avg_g, avg_b = arr.mean(axis=(0, 1))
    avg_r, avg_g, avg_b = map(int, (avg_r, avg_g, avg_b))

    if avg_r > avg_b + dominance_threshold:
        rgb_cls = "HOT"
        signal = 1
    elif avg_b > avg_r + dominance_threshold:
        rgb_cls = "COLD"
        signal = -1
    else:
        rgb_cls = "NEUTRAL"
        signal = 0

    h, s, v = colorsys.rgb_to_hsv(avg_r / 255, avg_g / 255, avg_b / 255)
    hue = h * 360

    if 200 <= hue <= 260:
        hsv_cls = "COLD"
    elif hue <= 30 or hue >= 330:
        hsv_cls = "HOT"
    else:
        hsv_cls = "NEUTRAL"

    final_cls = rgb_cls if rgb_cls == hsv_cls else "NEUTRAL"
    final_signal = signal if rgb_cls == hsv_cls else 0

    return {
        "avg_rgb": (avg_r, avg_g, avg_b),
        "classification": final_cls,
        "signal": final_signal
    }

_session = requests.Session()
retries = Retry(total=5, connect=5, read=5, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
adapter = HTTPAdapter(max_retries=retries)
_session.mount("https://", adapter)
_session.mount("http://", adapter)
_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

def get_region(n, sleep_between=0.1): # Reduced sleep for parallel
    url = f"https://www.natgasweather.com/modelData/images/2m/gfs_2m_aTemperatures_{n}.png"
    try:
        r = _session.get(url, timeout=(5, 15))
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        result = classify_temperature_from_image(img)
        return n, result
    except Exception as e:
        print(f"Failed to fetch n={n}: {e}")
        return n, {"signal": 0, "classification": "NEUTRAL"}

def get_latest_gfs_run(now_utc=None):
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    run_hours = [0, 6, 12, 18]
    for hour in reversed(run_hours):
        candidate = now_utc.replace(hour=hour, minute=0, second=0, microsecond=0)
        if now_utc >= candidate + timedelta(hours=2):
            return candidate
    return (now_utc - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)

def weather_rep():
    model_run = get_latest_gfs_run()
    indices = []
    for day in range(1, 17):
        n1 = 2 + (day - 1) * 4
        n2 = n1 + 2
        indices.extend([n1, n2])

    results_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_n = {executor.submit(get_region, n): n for n in indices}
        for future in concurrent.futures.as_completed(future_to_n):
            n, res = future.result()
            results_map[n] = res

    rows = []
    for day in range(1, 17):
        n1 = 2 + (day - 1) * 4
        n2 = n1 + 2
        r1 = results_map.get(n1, {"signal": 0})
        r2 = results_map.get(n2, {"signal": 0})

        temp_signal = (r1["signal"] + r2["signal"]) / 2

        if temp_signal <= -0.75:
            temp_class = "very cold"
        elif -0.75 < temp_signal <= -0.25:
            temp_class = "cold"
        elif -0.25 < temp_signal < 0.25:
            temp_class = "medium"
        elif 0.25 <= temp_signal < 0.75:
            temp_class = "hot"
        else:
            temp_class = "very hot"

        valid_time = model_run + timedelta(hours=24 * day)
        rows.append({
            "valid_time": valid_time,
            "temp_signal": temp_signal,
            "temp_class": temp_class,
            "forecast_day": day,
            "model_run_utc": model_run
        })

    df = pd.DataFrame(rows).set_index("valid_time")
    return df

def get_weather_count():
    try:
        df = weather_rep()
        WEATHER_COL = "temp_class"

        day_1_weather = df.iloc[0][WEATHER_COL] # Day 1 is the first row

        week_df = df.iloc[0:7]
        week_max_weather = (week_df[WEATHER_COL].value_counts().idxmax())
        week_max_count = (week_df[WEATHER_COL].value_counts().max())

        day_8_16_df = df.iloc[7:16]
        range_max_weather = (day_8_16_df[WEATHER_COL].value_counts().idxmax())
        range_max_count = (day_8_16_df[WEATHER_COL].value_counts().max())

        last_day_weather = df.iloc[-1][WEATHER_COL]

        report = f"The weather for the next week is expected to be {week_max_weather.upper()} for {week_max_count} days. After that will experience {range_max_weather.upper()} for {range_max_count} days. "
        lat_rep = f"The latest forecast is {last_day_weather.upper()}."

        return [report, lat_rep, week_max_weather, range_max_weather, week_max_count, range_max_count, last_day_weather, day_1_weather]
    except Exception as e:
        print(f"Error in get_weather_count: {e}")
        return ["Weather data unavailable", "Latest forecast unavailable"]

