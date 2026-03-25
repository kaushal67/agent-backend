"""CrewAI advisory agent and LangChain fallback advisory generation."""

from __future__ import annotations

import json
from typing import Dict, Optional

from crewai import Agent
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from app.utils.config import get_settings
from app.utils.logging import get_logger


class ResponseAgent:
    """Builds advisory output from CrewAI context and LangChain LLM."""

    def __init__(self) -> None:
        """Initialize lazy crew advisory agent and optional LangChain LLM."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self._agent: Optional[Agent] = None
        self._init_attempted = False

        self._llm = (
            ChatGroq(
                api_key=self.settings.groq_api_key,
                model=self.settings.langchain_model,
                temperature=0,
            )
            if self.settings.groq_api_key
            else None
        )

        self._prompt = PromptTemplate(
            input_variables=["crop_name", "disease_name", "symptoms", "research_summary", "crew_output"],
            template=(
                "You are an agriculture advisory assistant.\n"
                "Generate concise, safe, practical guidance as strict JSON only.\n"
                "Keys required: crop_name, disease_name, description, remedy, prevention.\n"
                "Do not return markdown.\n\n"
                "Case details:\n"
                "crop_name={crop_name}\n"
                "disease_name={disease_name}\n"
                "symptoms={symptoms}\n\n"
                "research_summary={research_summary}\n\n"
                "crew_output={crew_output}\n"
            ),
        )

    def get_agent(self) -> Optional[Agent]:
        """Create and cache the CrewAI advisory agent when dependencies are available."""
        if self._agent is not None:
            return self._agent
        if self._init_attempted:
            return None

        self._init_attempted = True
        try:
            self._agent = Agent(
                role="Advisory Agent",
                goal="Provide farmer-safe, actionable advisory with remedy and prevention guidance.",
                backstory=(
                    "A senior agri advisory specialist who converts technical findings into simple, "
                    "operational recommendations for farmers."
                ),
                allow_delegation=True,
            )
        except Exception:
            self.logger.exception("Unable to initialize CrewAI Advisory Agent.")
            self._agent = None

        return self._agent

    def build_task_description(self) -> str:
        """Create a CrewAI advisory task prompt."""
        return (
            "Using research findings, produce an advisory with fields: "
            "description, remedy, prevention. Keep instructions field-ready and concise."
        )

    def _default_payload(self, crop_name: str, disease_name: str, symptoms: str) -> Dict[str, str]:
        """Return deterministic advisory when LLM output is unavailable."""
        symptom_text = symptoms or "No symptom details provided."
        return {
            "crop_name": crop_name,
            "disease_name": disease_name,
            "description": f"Possible issue observed in {crop_name}: {symptom_text}",
            "remedy": (
                "Isolate visibly affected plants, avoid overhead irrigation, and apply crop-specific "
                "treatment recommended by a local agronomy officer."
            ),
            "prevention": (
                "Use clean planting material, maintain field sanitation, monitor weekly, and rotate crops "
                "to reduce recurring infection pressure."
            ),
        }

    def _parse_llm_json(self, content: str) -> Optional[Dict[str, str]]:
        """Parse strict JSON content from LLM response."""
        text = (content or "").strip().replace("```json", "").replace("```", "").strip()
        if not text:
            return None

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, dict):
            return None

        required = ["crop_name", "disease_name", "description", "remedy", "prevention"]
        if any(key not in payload for key in required):
            return None

        return {key: str(payload.get(key, "")).strip() for key in required}

    def generate_structured_advisory(
        self,
        crop_name: str,
        disease_name: str,
        symptoms: str,
        research_summary: str,
        crew_output: str,
    ) -> Dict[str, str]:
        """Generate advisory JSON using LangChain LLM with safe deterministic fallback."""
        if not self._llm:
            self.logger.warning("No LLM credentials configured for advisory generation. Using default fallback.")
            return self._default_payload(crop_name, disease_name, symptoms)

        chain = self._prompt | self._llm
        try:
            response = chain.invoke(
                {
                    "crop_name": crop_name,
                    "disease_name": disease_name,
                    "symptoms": symptoms or "Not provided",
                    "research_summary": research_summary or "No research summary available.",
                    "crew_output": crew_output or "No crew output available.",
                }
            )
        except Exception:
            self.logger.exception("LLM invocation failed. Using deterministic fallback payload.")
            return self._default_payload(crop_name, disease_name, symptoms)

        content = getattr(response, "content", "")
        parsed = self._parse_llm_json(content)
        if parsed:
            parsed["crop_name"] = crop_name
            parsed["disease_name"] = disease_name
            return parsed

        self.logger.warning("LLM response parsing failed. Using deterministic fallback payload.")
        return self._default_payload(crop_name, disease_name, symptoms)
