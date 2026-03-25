import base64
import json
import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _parse_json_text(raw_text: str) -> Dict[str, Any]:
    text = (raw_text or "").strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return _safe_dict(json.loads(text))
    except Exception:
        return {}


def analyze_crop_image(image_bytes: bytes, content_type: str, note: str = "") -> Dict[str, Any]:
    if not image_bytes or not GROQ_API_KEY:
        return {}

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    user_note = (note or "").strip()

    prompt = (
        "Analyze this crop image for field triage. "
        "If unsure, state likely possibilities. "
        "Return ONLY JSON with keys: "
        "crop_name, disease_name, urgency, location, observations. "
        "Urgency must be one of low, medium, high. "
        "Use null for unknown values."
    )
    if user_note:
        prompt += f" Farmer note: {user_note}"

    payload = {
        "model": GROQ_VISION_MODEL,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content_type};base64,{encoded_image}"
                        },
                    },
                ],
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            GROQ_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return {}

    message = (
        (((data.get("choices") or [{}])[0]).get("message") or {}).get("content")
        if isinstance(data, dict)
        else None
    )
    parsed = _parse_json_text(message or "")

    normalized = {
        "crop_name": parsed.get("crop_name"),
        "disease_name": parsed.get("disease_name"),
        "location": parsed.get("location"),
        "urgency": parsed.get("urgency"),
        "observations": parsed.get("observations"),
    }
    return {
        key: value
        for key, value in normalized.items()
        if value not in (None, "", "null", "None")
    }
