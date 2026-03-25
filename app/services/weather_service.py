import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_weather(city: str) -> Optional[Dict[str, Any]]:
    city = (city or "").strip()
    if not city or not API_KEY:
        return None

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    rain_data = data.get("rain") or {}
    rainfall = rain_data.get("1h")
    if rainfall is None:
        rainfall = rain_data.get("3h", 0)

    return {
        "temperature": _to_float((data.get("main") or {}).get("temp")),
        "humidity": _to_float((data.get("main") or {}).get("humidity")),
        "rainfall": _to_float(rainfall, 0.0),
        "description": ((data.get("weather") or [{}])[0]).get("description", "Unknown")
    }
