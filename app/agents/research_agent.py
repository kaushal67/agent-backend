"""CrewAI research agent configuration."""

from __future__ import annotations

from typing import Optional

from crewai import Agent

from app.utils.logging import get_logger


class ResearchAgent:
    """Builds the research agent used by CrewAI delegation."""

    def __init__(self) -> None:
        """Initialize lazy state for the CrewAI research agent."""
        self.logger = get_logger(__name__)
        self._agent: Optional[Agent] = None
        self._init_attempted = False

    def get_agent(self) -> Optional[Agent]:
        """Create and cache the CrewAI research agent when dependencies are available."""
        if self._agent is not None:
            return self._agent
        if self._init_attempted:
            return None

        self._init_attempted = True
        try:
            self._agent = Agent(
                role="Research Agent",
                goal=(
                    "Collect crop and disease field context, causes, and immediate safety actions "
                    "for agronomy triage."
                ),
                backstory=(
                    "An experienced agricultural researcher specialized in disease pattern analysis "
                    "and practical farmer guidance."
                ),
                allow_delegation=True,
            )
        except Exception:
            self.logger.exception("Unable to initialize CrewAI Research Agent.")
            self._agent = None

        return self._agent

    def build_task_description(self, crop_name: str, disease_name: str, symptoms: str) -> str:
        """Create a structured research task prompt for CrewAI."""
        return (
            "Analyze likely agronomic root causes and field checks for the following case.\n"
            f"Crop: {crop_name}\n"
            f"Disease/Symptom Label: {disease_name}\n"
            f"Farmer Symptom Notes: {symptoms or 'Not provided'}\n"
            "Return concise bullets covering probable causes, risk factors, and immediate diagnostics."
        )
