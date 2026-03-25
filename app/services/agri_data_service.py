"""Database service layer for crop disease retrieval and safe persistence."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import CropDisease, FarmerQuery
from app.utils.logging import get_logger


logger = get_logger(__name__)


class AgriDataService:
    """Handles all disease and query database operations."""

    def get_disease(self, db: Session, crop_name: str, disease_name: str) -> Optional[CropDisease]:
        """Fetch disease details from SQLite using exact-first and fuzzy fallback matching."""
        normalized_crop = (crop_name or "").strip()
        normalized_disease = (disease_name or "").strip()

        if not normalized_crop or not normalized_disease:
            return None

        disease = (
            db.query(CropDisease)
            .filter(
                func.lower(CropDisease.crop_name) == normalized_crop.lower(),
                func.lower(CropDisease.disease_name) == normalized_disease.lower(),
            )
            .first()
        )
        if disease:
            logger.info(
                "DB query result: hit (exact) crop=%s disease=%s",
                normalized_crop,
                normalized_disease,
            )
            return disease

        disease = (
            db.query(CropDisease)
            .filter(
                CropDisease.crop_name.ilike(f"%{normalized_crop}%"),
                CropDisease.disease_name.ilike(f"%{normalized_disease}%"),
            )
            .first()
        )

        logger.info(
            "DB query result: %s crop=%s disease=%s",
            "hit (fuzzy)" if disease else "miss",
            normalized_crop,
            normalized_disease,
        )
        return disease

    def build_database_payload(
        self,
        disease: CropDisease,
        crop_name: str,
        disease_name: str,
    ) -> Dict[str, str]:
        """Convert database model to API response payload."""
        return {
            "crop_name": crop_name,
            "disease_name": disease_name,
            "description": (disease.symptoms or "No description available.").strip(),
            "remedy": (disease.treatment or "No remedy available.").strip(),
            "prevention": (disease.prevention or "No prevention guidance available.").strip(),
        }

    def save_query(
        self,
        db: Session,
        crop_name: str,
        disease_name: str,
        symptoms: Optional[str],
        response_payload: Dict[str, Any],
        status: str,
        source: str,
    ) -> None:
        """Persist request-response audit record with safe commit and rollback behavior."""
        query_text = (
            f"crop_name={crop_name}; disease_name={disease_name}; "
            f"symptoms={symptoms or 'not_provided'}"
        )
        row = FarmerQuery(
            query=query_text,
            intent="crop_problem",
            urgency="unknown",
            response=json.dumps(
                {
                    "status": status,
                    "source": source,
                    "data": response_payload,
                },
                ensure_ascii=True,
            ),
        )

        db.add(row)
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            logger.exception("Failed to commit farmer query. Transaction rolled back.")
            raise
