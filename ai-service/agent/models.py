from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator, model_validator

# Safe top-level import: nothing in app/ or tools/ imports agent/, so this cannot
# create a circular import (which it would if these models lived in app/models.py).
from tools.tool_registry import TOOL_REGISTRY


class PlanRequest(BaseModel):
    bug_description: str
    project_id: str


class PlanStep(BaseModel):
    step: int = Field(..., description="1-based position in the plan")
    goal: str = Field(..., description="What this step is trying to learn")
    tool: str = Field(..., description="Tool to call; must be a registered tool name")
    tool_input: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for the tool, WITHOUT project_id (injected at execution time)",
    )
    reasoning: str = Field(..., description="Why this tool and target answer the goal")

    @field_validator("tool")
    @classmethod
    def _tool_must_be_registered(cls, v: str) -> str:
        if v not in TOOL_REGISTRY:
            raise ValueError(
                f"unknown tool '{v}'; choose exactly one of {sorted(TOOL_REGISTRY)}"
            )
        return v


class InvestigationPlan(BaseModel):
    summary: str = Field(..., description="1-2 sentence framing of the investigation")
    steps: List[PlanStep] = Field(..., min_length=1, max_length=6)

    @model_validator(mode="after")
    def _renumber(self) -> "InvestigationPlan":
        # Normalize step numbers to 1..N even if the LLM misnumbers them.
        for i, s in enumerate(self.steps, start=1):
            s.step = i
        return self
