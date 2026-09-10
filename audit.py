import json

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT
from schemas import AuditResult


MODEL = "gemini-2.5-flash"


def get_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


def build_user_prompt():
    return """
Проведи полный профессиональный визуальный аудит
предоставленного изображения.

Оцени все 15 принципов дизайна:

1. composition
2. visual_hierarchy
3. balance
4. contrast
5. typography
6. color
7. negative_space
8. alignment
9. proximity_grouping
10. repetition_rhythm
11. unity_coherence
12. readability_accessibility
13. focal_point
14. proportion_scale
15. overall_coherence

Для каждого принципа обязательно дай:

- score
- status
- observation
- evidence
- rationale
- perceptual_effect
- problem
- recommendation
- score_justification

Также верни:

- overall_design_score
- communication_score
- priority_issues
- strengths
- most_important_problems
- concrete_recommendations
- improvement_prompt
- designer_brief

КРИТИЧЕСКИ ВАЖНО:

Анализируй только то, что реально видно.

Не придумывай отсутствующие элементы,
текст, шрифты, цвета, намерения автора
или целевую аудиторию.

Каждая существенная критика должна иметь
конкретное визуальное доказательство.

Объясняй:

что видно
→ почему это относится к принципу
→ почему это проблема
→ как это влияет на восприятие
→ что конкретно изменить.

Не используй общие фразы вроде
"композиция слабая" без объяснения причины.

Верни ТОЛЬКО валидный JSON.
Не используй Markdown.
Не добавляй текст до или после JSON.
"""


def analyze_image(image_bytes: bytes):

    client = get_client()

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg"
    )

    response = client.models.generate_content(
        model=MODEL,

        contents=[
            image_part,
            build_user_prompt()
        ],

        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.2,
        )
    )

    if not response.text:
        raise ValueError(
            "Gemini не вернул результат."
        )

    return parse_result(response.text)


def parse_result(raw_text: str):

    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.replace(
            "```json",
            "",
            1
        )

        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Gemini вернул некорректный JSON: {error}"
        )

    # Gemini иногда оборачивает результаты
    # в поле audit_results.
    if "audit_results" in data:

        audit_items = data["audit_results"]

        if not isinstance(audit_items, list):
            raise ValueError(
                "Поле audit_results должно быть списком."
            )

        principle_map = {}

        for item in audit_items:

            if not isinstance(item, dict):
                continue

            principle = item.get(
                "principle",
                ""
            )

            principle_key = (
                principle
                .lower()
                .strip()
                .replace(" ", "_")
                .replace("/", "_")
                .replace("-", "_")
            )

            principle_map[principle_key] = item

        data = convert_gemini_result(
            data,
            principle_map
        )

    try:

        result = AuditResult.model_validate(
            data
        )

    except Exception as error:

        raise ValueError(
            f"Gemini вернул JSON неправильной структуры: {error}"
        )

    return result


def convert_gemini_result(
    data,
    principle_map
):

    principle_names = {

        "composition": [
            "composition"
        ],

        "visual_hierarchy": [
            "visual_hierarchy",
            "hierarchy"
        ],

        "balance": [
            "balance"
        ],

        "contrast": [
            "contrast"
        ],

        "typography": [
            "typography"
        ],

        "color": [
            "color",
            "colour"
        ],

        "negative_space": [
            "negative_space",
            "whitespace"
        ],

        "alignment": [
            "alignment"
        ],

        "proximity_grouping": [
            "proximity_grouping",
            "proximity",
            "grouping"
        ],

        "repetition_rhythm": [
            "repetition_rhythm",
            "repetition",
            "rhythm"
        ],

        "unity_coherence": [
            "unity_coherence",
            "unity",
            "coherence"
        ],

        "readability_accessibility": [
            "readability_accessibility",
            "readability",
            "accessibility"
        ],

        "focal_point": [
            "focal_point",
            "focal"
        ],

        "proportion_scale": [
            "proportion_scale",
            "proportion",
            "scale"
        ],

        "overall_coherence": [
            "overall_coherence",
            "overall"
        ]
    }

    result = {}

    for target_name, possible_names in principle_names.items():

        found = None

        for name in possible_names:

            if name in principle_map:
                found = principle_map[name]
                break

        if found is None:

            found = {
                "score": 50,
                "status": "not_applicable",
                "observation": "Принцип не был распознан.",
                "evidence": [],
                "rationale": "",
                "perceptual_effect": "",
                "problem": None,
                "recommendation": None,
                "score_justification": ""
            }

        result[target_name] = normalize_principle(
            found
        )

    result["overall_design_score"] = int(
        data.get(
            "overall_design_score",
            50
        )
    )

    result["communication_score"] = int(
        data.get(
            "communication_score",
            50
        )
    )

    result["priority_issues"] = normalize_priority_issues(
        data.get(
            "priority_issues",
            []
        )
    )

    result["strengths"] = data.get(
        "strengths",
        []
    )

    result["most_important_problems"] = data.get(
        "most_important_problems",
        []
    )

    result["concrete_recommendations"] = data.get(
        "concrete_recommendations",
        []
    )

    result["improvement_prompt"] = data.get(
        "improvement_prompt",
        ""
    )

    designer_brief = data.get(
        "designer_brief",
        ""
    )

    if isinstance(designer_brief, dict):

        designer_brief = json.dumps(
            designer_brief,
            ensure_ascii=False,
            indent=2
        )

    result["designer_brief"] = designer_brief

    return result


def normalize_principle(item):

    return {
        "score": item.get(
            "score",
            50
        ),

        "status": item.get(
            "status",
            "applicable"
        ),

        "observation": item.get(
            "observation",
            ""
        ),

        "evidence": item.get(
            "evidence",
            []
        ),

        "rationale": item.get(
            "rationale",
            ""
        ),

        "perceptual_effect": item.get(
            "perceptual_effect",
            ""
        ),

        "problem": item.get(
            "problem",
            None
        ),

        "recommendation": item.get(
            "recommendation",
            None
        ),

        "score_justification": item.get(
            "score_justification",
            ""
        )
    }


def normalize_priority_issues(items):

    result = []

    for item in items:

        if not isinstance(item, dict):
            continue

        result.append(
            {
                "priority": item.get(
                    "priority",
                    "medium"
                ),

                "principle": item.get(
                    "principle",
                    ""
                ),

                "issue": item.get(
                    "issue",
                    ""
                ),

                "evidence": item.get(
                    "evidence",
                    ""
                ),

                "perceptual_impact": item.get(
                    "perceptual_impact",
                    ""
                ),

                "action": item.get(
                    "action",
                    ""
                )
            }
        )

    return result
