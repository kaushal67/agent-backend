"""Agent orchestration layer for disease fallback advisory generation."""

from __future__ import annotations

import time
from typing import Dict, Optional

from crewai import Crew, Process, Task

from app.agents.research_agent import ResearchAgent
from app.agents.response_agent import ResponseAgent
from app.utils.config import get_settings
from app.utils.logging import get_logger


class TriageAgent:
    """Coordinates CrewAI delegation and LangChain-based fallback advisory generation."""

    def __init__(self) -> None:
        """Initialize research and advisory agents for runtime orchestration."""
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.research_agent = ResearchAgent()
        self.response_agent = ResponseAgent()

    def _step_logger(self, step_output: object) -> None:
        """Log each CrewAI execution step for observability."""
        self.logger.info("Crew step: %s", str(step_output))

    def generate_advisory(
        self,
        crop_name: str,
        disease_name: str,
        symptoms: Optional[str] = None,
    ) -> Dict[str, str]:
        """Run CrewAI tasks, then synthesize a structured advisory with LangChain."""
        start_time = time.perf_counter()
        symptom_text = (symptoms or "").strip()

        self.logger.info(
            "Agent invocation started crop=%s disease=%s",
            crop_name,
            disease_name,
        )

        research_task = Task(
            name="research_task",
            description=self.research_agent.build_task_description(crop_name, disease_name, symptom_text),
            expected_output="Root causes, risk factors, and field diagnostics as concise bullet points.",
        )

        advisory_task = Task(
            name="advisory_task",
            description=self.response_agent.build_task_description(),
            expected_output=(
                "Structured advisory with clear description, remedy, and prevention recommendations."
            ),
            context=[research_task],
        )

        crew_output_text = ""
        research_summary = ""

        research_agent = self.research_agent.get_agent()
        advisory_agent = self.response_agent.get_agent()

        if research_agent and advisory_agent:
            research_task.agent = research_agent
            advisory_task.agent = advisory_agent
            try:
                crew = Crew(
                    agents=[research_agent, advisory_agent],
                    tasks=[research_task, advisory_task],
                    process=Process.sequential,
                    verbose=self.settings.crewai_verbose,
                    step_callback=self._step_logger,
                )
                self.logger.info("CrewAI execution started.")
                crew_output = crew.kickoff(
                    inputs={
                        "crop_name": crop_name,
                        "disease_name": disease_name,
                        "symptoms": symptom_text,
                    }
                )
                crew_output_text = str(crew_output)
                research_summary = str(research_task.output) if research_task.output else ""
                self.logger.info("CrewAI execution completed successfully.")
            except Exception:
                self.logger.exception("CrewAI execution failed. Continuing with direct LangChain fallback.")
        else:
            self.logger.warning(
                "CrewAI agents unavailable. Skipping crew delegation and using direct LangChain fallback."
            )

        advisory = self.response_agent.generate_structured_advisory(
            crop_name=crop_name,
            disease_name=disease_name,
            symptoms=symptom_text,
            research_summary=research_summary,
            crew_output=crew_output_text,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        self.logger.info("Agent invocation completed in %.2f ms", duration_ms)
        return advisory
