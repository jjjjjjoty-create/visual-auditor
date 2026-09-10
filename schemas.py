from typing import List, Optional
from pydantic import BaseModel


class DesignPrinciple(BaseModel):
    score: int = 50
    status: str = "applicable"
    observation: str = ""
    evidence: List[str] = []
    rationale: str = ""
    perceptual_effect: str = ""
    problem: Optional[str] = None
    recommendation: Optional[str] = None
    score_justification: str = ""


class PriorityIssue(BaseModel):
    priority: str = "medium"
    principle: str = ""
    issue: str = ""
    evidence: str = ""
    perceptual_impact: str = ""
    action: str = ""


class AuditResult(BaseModel):

    overall_design_score: int = 50
    communication_score: int = 50

    composition: DesignPrinciple = DesignPrinciple()
    visual_hierarchy: DesignPrinciple = DesignPrinciple()
    balance: DesignPrinciple = DesignPrinciple()
    contrast: DesignPrinciple = DesignPrinciple()
    typography: DesignPrinciple = DesignPrinciple()
    color: DesignPrinciple = DesignPrinciple()
    negative_space: DesignPrinciple = DesignPrinciple()
    alignment: DesignPrinciple = DesignPrinciple()
    proximity_grouping: DesignPrinciple = DesignPrinciple()
    repetition_rhythm: DesignPrinciple = DesignPrinciple()
    unity_coherence: DesignPrinciple = DesignPrinciple()
    readability_accessibility: DesignPrinciple = DesignPrinciple()
    focal_point: DesignPrinciple = DesignPrinciple()
    proportion_scale: DesignPrinciple = DesignPrinciple()
    overall_coherence: DesignPrinciple = DesignPrinciple()

    priority_issues: List[PriorityIssue] = []

    strengths: List[str] = []

    most_important_problems: List[str] = []

    concrete_recommendations: List[str] = []

    improvement_prompt: str = ""

    designer_brief: str = ""
