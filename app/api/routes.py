"""FastAPI routes for triage prediction and health monitoring."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.schemas import HealthResponse, PredictRequest, PredictResponse
from app.database.db import get_db
from app.models import FarmerQuery
from app.services.triage_service import TriageService
from app.utils.logging import get_logger


router = APIRouter()
logger = get_logger(__name__)
triage_service = TriageService()
CROP_HINTS: List[str] = [
    "tomato",
    "rice",
    "wheat",
    "cotton",
    "maize",
    "potato",
    "onion",
    "banana",
    "soybean",
    "groundnut",
    "brinjal",
]
DISEASE_HINTS: List[str] = [
    "blight",
    "rust",
    "mildew",
    "wilt",
    "leaf spot",
    "blast",
    "rot",
    "mosaic",
]


def _extract_crop_and_disease(message: str) -> Dict[str, str]:
    """Infer crop and disease labels from free-text message for legacy endpoint support."""
    text_value = (message or "").strip()
    lower_value = text_value.lower()

    crop_name = "Unknown Crop"
    for crop in CROP_HINTS:
        if re.search(rf"\b{re.escape(crop)}\b", lower_value):
            crop_name = crop.title()
            break

    disease_name = "Unknown Disease"
    for disease in DISEASE_HINTS:
        if disease in lower_value:
            disease_name = disease.title()
            break

    if disease_name == "Unknown Disease" and ("yellow spot" in lower_value or "spots" in lower_value):
        disease_name = "Leaf Spot"

    return {"crop_name": crop_name, "disease_name": disease_name}


def _format_legacy_answer(payload: Dict[str, Any], status: str, source: str) -> str:
    """Convert structured `/predict` payload to human-readable answer for legacy frontend cards."""
    return (
        f"Status: {status}\n"
        f"Source: {source}\n\n"
        f"Crop: {payload.get('crop_name', 'Unknown')}\n"
        f"Disease: {payload.get('disease_name', 'Unknown')}\n\n"
        f"Description:\n{payload.get('description', '')}\n\n"
        f"Remedy:\n{payload.get('remedy', '')}\n\n"
        f"Prevention:\n{payload.get('prevention', '')}"
    )


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest, db: Session = Depends(get_db)) -> PredictResponse:
    """Run crop disease triage using database-first strategy with LLM fallback."""
    logger.info(
        "Incoming request /predict crop=%s disease=%s",
        request.crop_name,
        request.disease_name,
    )

    try:
        result = triage_service.predict(
            db=db,
            crop_name=request.crop_name,
            disease_name=request.disease_name,
            symptoms=request.symptoms,
        )
    except SQLAlchemyError as exc:
        logger.exception("Database error while processing /predict.")
        raise HTTPException(status_code=500, detail="Database operation failed.") from exc
    except Exception as exc:
        logger.exception("Unhandled error while processing /predict.")
        raise HTTPException(status_code=500, detail="Prediction failed.") from exc

    return PredictResponse.model_validate(result)


@router.post("/ask")
def ask(payload: Dict[str, str], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Legacy text triage endpoint retained for frontend backward compatibility."""
    message = (payload.get("msg") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="msg is required.")

    inferred = _extract_crop_and_disease(message)
    result = triage_service.predict(
        db=db,
        crop_name=inferred["crop_name"],
        disease_name=inferred["disease_name"],
        symptoms=message,
    )

    return {
        "classification": {"intent": "crop_problem", "urgency": "unknown"},
        "entities": {
            "crop_name": inferred["crop_name"],
            "disease_name": inferred["disease_name"],
            "location": None,
            "farmer_id": None,
            "date": None,
        },
        "answer": _format_legacy_answer(result["data"], result["status"], result["source"]),
        "db_id": None,
        "status": result["status"],
        "source": result["source"],
        "data": result["data"],
    }


@router.post("/ask/image")
async def ask_image(
    image: UploadFile = File(...),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Legacy image triage endpoint retained for frontend backward compatibility."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files supported.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    message = (note or "").strip() or "Image-based crop triage request."
    inferred = _extract_crop_and_disease(message)
    result = triage_service.predict(
        db=db,
        crop_name=inferred["crop_name"],
        disease_name=inferred["disease_name"],
        symptoms=message,
    )

    return {
        "classification": {"intent": "crop_problem", "urgency": "unknown"},
        "entities": {
            "crop_name": inferred["crop_name"],
            "disease_name": inferred["disease_name"],
            "location": None,
            "farmer_id": None,
            "date": None,
        },
        "answer": _format_legacy_answer(result["data"], result["status"], result["source"]),
        "db_id": None,
        "image": {
            "filename": image.filename,
            "content_type": image.content_type,
            "size_bytes": len(image_bytes),
        },
        "status": result["status"],
        "source": result["source"],
        "data": result["data"],
    }


@router.get("/queries")
def list_queries(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Legacy query history endpoint retained for frontend backward compatibility."""
    rows = db.query(FarmerQuery).order_by(FarmerQuery.id.desc()).limit(limit).all()
    return {
        "items": [
            {
                "id": row.id,
                "query": row.query,
                "intent": row.intent,
                "urgency": row.urgency,
                "response": row.response,
            }
            for row in rows
        ]
    }


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    """Check API and database readiness."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Health check failed.")
        raise HTTPException(status_code=503, detail="Service unavailable.") from exc

    return HealthResponse(status="ok")
