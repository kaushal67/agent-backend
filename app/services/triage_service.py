"""Service layer for end-to-end disease triage flow."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.agents.triage_agent import TriageAgent
from app.services.agri_data_service import AgriDataService
from app.utils.logging import get_logger


class TriageService:
    """Coordinates database lookup, fallback advisory generation, and persistence."""

    def __init__(self) -> None:
        """Initialize collaborators for triage processing."""
        self.logger = get_logger(__name__)
        self.data_service = AgriDataService()
        self.agent = TriageAgent()

    def predict(
        self,
        db: Session,
        crop_name: str,
        disease_name: str,
        symptoms: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return disease advisory from database first, then LLM fallback if not found."""
        start_time = time.perf_counter()
        normalized_crop = crop_name.strip()
        normalized_disease = disease_name.strip()
        symptom_text = (symptoms or "").strip()

        disease = self.data_service.get_disease(db, normalized_crop, normalized_disease)

        if disease:
            status = "success"
            source = "database"
            payload = self.data_service.build_database_payload(
                disease=disease,
                crop_name=normalized_crop,
                disease_name=normalized_disease,
            )
        else:
            status = "fallback"
            source = "llm"
            payload = self.agent.generate_advisory(
                crop_name=normalized_crop,
                disease_name=normalized_disease,
                symptoms=symptom_text,
            )

        self.data_service.save_query(
            db=db,
            crop_name=normalized_crop,
            disease_name=normalized_disease,
            symptoms=symptom_text,
            response_payload=payload,
            status=status,
            source=source,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        self.logger.info(
            "Triage completed crop=%s disease=%s source=%s in %.2f ms",
            normalized_crop,
            normalized_disease,
            source,
            duration_ms,
        )

        return {
            "status": status,
            "source": source,
            "data": payload,
        }
