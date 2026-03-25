from typing import Any, Dict, Tuple


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_weather_risk(weather_data: Dict[str, Any], disease_type: str) -> str:
    temp = _to_float(weather_data.get("temperature"))
    humidity = _to_float(weather_data.get("humidity"))
    rainfall = _to_float(weather_data.get("rainfall"))
    normalized_type = (disease_type or "").strip().lower()

    risk = "Low"

    if normalized_type == "fungal":
        if humidity > 80 and 20 <= temp <= 30:
            risk = "High"
        elif humidity > 65:
            risk = "Moderate"
    elif normalized_type == "bacterial":
        if rainfall > 5 and humidity > 70:
            risk = "High"
        elif rainfall > 2:
            risk = "Moderate"
    elif normalized_type == "viral":
        if temp > 28 and humidity > 60:
            risk = "Moderate"

    return risk


def generate_combined_advisory(crop: str, disease_obj: Any, weather_data: Dict[str, Any]) -> Tuple[str, str]:
    disease_type = getattr(disease_obj, "type", "unknown")
    symptoms = getattr(disease_obj, "symptoms", "Not available")
    treatment = getattr(disease_obj, "treatment", "Not available")
    prevention = getattr(disease_obj, "prevention", "Not available")
    crop_name = crop or getattr(disease_obj, "crop_name", "your crop")

    risk_level = calculate_weather_risk(weather_data, disease_type)

    advisory_text = (
        f"Crop: {crop_name}\n"
        f"Disease type: {str(disease_type).title()}\n"
        f"Weather: {weather_data.get('temperature')} C, "
        f"humidity {weather_data.get('humidity')}%, "
        f"rainfall {weather_data.get('rainfall')} mm\n"
        f"Risk level: {risk_level}\n\n"
        "Immediate actions:\n"
        f"- {treatment}\n\n"
        "What to monitor:\n"
        f"- {symptoms}\n\n"
        "Prevention for next 7 days:\n"
        f"- {prevention}"
    )

    return advisory_text, risk_level
