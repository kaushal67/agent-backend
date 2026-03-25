import json
import os
import re
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0,
)

prompt = PromptTemplate(
    input_variables=["text"],
    template="""
You are an entity extraction engine for agriculture queries.
Extract these fields:

crop_name
disease_name
location
farmer_id
date

Message: {text}

Rules:
- Return ONLY one valid JSON object.
- No markdown, no explanation, no SQL.
- Use null for missing values.
- Keep keys exactly: crop_name, disease_name, location, farmer_id, date.
""",
)

EXPECTED_KEYS = ("crop_name", "disease_name", "location", "farmer_id", "date")
KEY_ALIASES = {
    "cropname": "crop_name",
    "crop": "crop_name",
    "disease": "disease_name",
    "disease_type": "disease_name",
    "city": "location",
    "state": "location",
    "place": "location",
}
COMMON_CROPS = (
    "rice",
    "wheat",
    "maize",
    "cotton",
    "sugarcane",
    "tomato",
    "potato",
    "onion",
    "chili",
    "banana",
    "soybean",
    "groundnut",
    "brinjal",
)
COMMON_DISEASES = (
    "blight",
    "rust",
    "mildew",
    "wilt",
    "leaf spot",
    "blast",
    "rot",
    "mosaic",
)


def _decode_json_fragment(raw: str) -> Any:
    cleaned = (raw or "").strip().replace("```json", "").replace("```", "").strip()
    if not cleaned:
        return None

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, ch in enumerate(cleaned):
        if ch not in "{[":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
            return value
        except json.JSONDecodeError:
            continue

    return None


def _normalize_to_dict(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, list):
        merged: Dict[str, Any] = {}
        for item in payload:
            if isinstance(item, dict):
                merged.update(item)
        payload = merged

    if not isinstance(payload, dict):
        payload = {}

    normalized: Dict[str, Any] = {}
    for key, value in payload.items():
        mapped_key = KEY_ALIASES.get(str(key).strip().lower(), key)
        if mapped_key in EXPECTED_KEYS:
            normalized[mapped_key] = value

    for key in EXPECTED_KEYS:
        value = normalized.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lower() in {"", "null", "none", "n/a"}:
                normalized[key] = None
            else:
                normalized[key] = stripped
        elif value is None:
            normalized[key] = None

    for key in EXPECTED_KEYS:
        normalized.setdefault(key, None)

    return normalized


def _heuristic_extract(text: str) -> Dict[str, Any]:
    output: Dict[str, Any] = {key: None for key in EXPECTED_KEYS}
    raw_text = text or ""
    lower_text = raw_text.lower()

    for crop in COMMON_CROPS:
        if re.search(rf"\b{re.escape(crop)}\b", lower_text):
            output["crop_name"] = crop.title()
            break

    for disease in COMMON_DISEASES:
        if disease in lower_text:
            output["disease_name"] = disease.title()
            break

    location_match = re.search(
        r"\b(?:in|at|from|near)\s+([A-Za-z][A-Za-z\s\-]{1,40})",
        raw_text,
        flags=re.IGNORECASE,
    )
    if location_match:
        candidate = location_match.group(1).strip(" ,.?")
        candidate = re.split(
            r"\b(?:this|today|tomorrow|for|with|on|about|affect|impact|during|week)\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" ,.?")
        if candidate:
            output["location"] = " ".join(word.capitalize() for word in candidate.split())

    numeric_date = re.search(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", raw_text)
    if numeric_date:
        output["date"] = numeric_date.group(0)
    else:
        relative_date = re.search(r"\b(today|tomorrow|yesterday|this week|next week)\b", lower_text)
        if relative_date:
            output["date"] = relative_date.group(0)

    return output


def extract(text: str) -> Dict[str, Any]:
    chain = prompt | llm
    response = chain.invoke({"text": text})
    data = _normalize_to_dict(_decode_json_fragment(response.content))

    heuristics = _heuristic_extract(text)
    for key in EXPECTED_KEYS:
        if data.get(key) in (None, "", "null", "None") and heuristics.get(key):
            data[key] = heuristics[key]

    return data
