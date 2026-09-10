from typing import Optional, List
from pydantic import BaseModel


class DesignPrinciple(BaseModel):
    score: Optional[int] = None
    status: str
    observation: str
    evidence: List[str]
    rationale: str
    perceptual_effect: str
    problem: Optional[str] = None
    recommendation: Optional[str] = None
    score_justification: str


class PriorityIssue(BaseModel):
    priority: str
    principle: str
    issue: str
    evidence: str
    perceptual_impact: str
    action: str


class AuditResult(BaseModel):

    overall_design_score: int
    communication_score: int

    composition: DesignPrinciple
    visual_hierarchy: DesignPrinciple
    balance: DesignPrinciple
    contrast: DesignPrinciple
    typography: DesignPrinciple
    color: DesignPrinciple
    negative_space: DesignPrinciple
    alignment: DesignPrinciple
    proximity_grouping: DesignPrinciple
    repetition_rhythm: DesignPrinciple
    unity_coherence: DesignPrinciple
    readability_accessibility: DesignPrinciple
    focal_point: DesignPrinciple
    proportion_scale: DesignPrinciple
    overall_coherence: DesignPrinciple

    priority_issues: List[PriorityIssue]

    strengths: List[str]

    most_important_problems: List[str]

    concrete_recommendations: List[str]

    improvement_prompt: str

    designer_brief: str
