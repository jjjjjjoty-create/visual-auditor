from typing import Optional, List
from pydantic import BaseModel, Field


class DesignPrinciple(BaseModel):
    score: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Оценка принципа от 0 до 100."
    )

    status: str = Field(
        description="applicable или not_applicable"
    )

    observation: str = Field(
        description=(
            "Только непосредственно наблюдаемые визуальные факты. "
            "Без догадок о намерениях автора."
        )
    )

    evidence: List[str] = Field(
        description=(
            "Конкретные визуальные признаки, на которых основана оценка."
        )
    )

    rationale: str = Field(
        description=(
            "Почему наблюдаемый признак важен именно с точки зрения "
            "данного принципа дизайна."
        )
    )

    perceptual_effect: str = Field(
        description=(
            "Как данный признак может влиять на визуальное восприятие: "
            "внимание, иерархию, читаемость, баланс, напряжение и т.д."
        )
    )

    problem: Optional[str] = Field(
        default=None,
        description="Конкретно сформулированная проблема."
    )

    recommendation: Optional[str] = Field(
        default=None,
        description="Конкретное действие по улучшению."
    )

    score_justification: str = Field(
        description=(
            "Почему поставлена именно эта оценка. "
            "Указать положительные и отрицательные факторы."
        )
    )


class PriorityIssue(BaseModel):
    priority: str = Field(
        description="critical, high, medium или low"
    )

    principle: str

    issue: str

    evidence: str

    perceptual_impact: str

    action: str


class AuditResult(BaseModel):

    overall_design_score: int = Field(
        ge=0,
        le=100
    )

    communication_score: int = Field(
        ge=0,
        le=100
    )

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
