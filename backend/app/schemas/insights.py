from typing import Any, Literal

from pydantic import BaseModel, Field


class InsightItem(BaseModel):
    category: Literal["key_win", "risk_issue", "recommended_action"]
    title: str
    statement: str
    why_it_matters: str
    recommended_action: str
    supporting_data: dict[str, Any] = Field(default_factory=dict)
    confidence: Literal["high", "medium", "low"]
    severity: Literal["info", "warning", "critical"]
    evidence_label: str
    rank_score: float = 0.0


class InsightPayload(BaseModel):
    key_wins: list[InsightItem] = Field(default_factory=list)
    risks_issues: list[InsightItem] = Field(default_factory=list)
    recommended_actions: list[InsightItem] = Field(default_factory=list)
    suppressed_due_to_small_dataset: bool = False
    total_generated: int = 0
