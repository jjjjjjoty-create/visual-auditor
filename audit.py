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

            principle = str(
                item.get("principle", "")
            )

            principle_key = normalize_principle_name(
                principle
            )

            if principle_key:
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


def normalize_principle_name(name):

    name = str(name).lower().strip()

    name = (
        name
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )

    aliases = {

        "composition": "composition",

        "visual_hierarchy": "visual_hierarchy",
        "hierarchy": "visual_hierarchy",

        "balance": "balance",

        "contrast": "contrast",

        "typography": "typography",

        "color": "color",
        "colour": "color",

        "negative_space": "negative_space",
        "whitespace": "negative_space",
        "white_space": "negative_space",

        "alignment": "alignment",

        "proximity_grouping": "proximity_grouping",
        "proximity": "proximity_grouping",
        "grouping": "proximity_grouping",

        "repetition_rhythm": "repetition_rhythm",
        "repetition": "repetition_rhythm",
        "rhythm": "repetition_rhythm",

        "unity_coherence": "unity_coherence",
        "unity_visual_coherence": "unity_coherence",
        "unity": "unity_coherence",

        "readability_accessibility": "readability_accessibility",
        "readability": "readability_accessibility",
        "accessibility": "readability_accessibility",

        "focal_point": "focal_point",
        "focal": "focal_point",

        "proportion_scale": "proportion_scale",
        "proportion": "proportion_scale",
        "scale": "proportion_scale",

        "overall_coherence": "overall_coherence",
        "overall": "overall_coherence",
    }

    if name in aliases:
        return aliases[name]

    # Дополнительная защита:
    # Gemini может написать более длинное название принципа.

    if "visual_hierarchy" in name or "hierarchy" in name:
        return "visual_hierarchy"

    if "composition" in name:
        return "composition"

    if "balance" in name:
        return "balance"

    if "contrast" in name:
        return "contrast"

    if "typography" in name:
        return "typography"

    if "color" in name or "colour" in name:
        return "color"

    if "negative" in name or "whitespace" in name:
        return "negative_space"

    if "alignment" in name:
        return "alignment"

    if "proximity" in name or "grouping" in name:
        return "proximity_grouping"

    if "repetition" in name or "rhythm" in name:
        return "repetition_rhythm"

    if "unity" in name or "coherence" in name:
        if "overall" in name:
            return "overall_coherence"

        return "unity_coherence"

    if "readability" in name or "accessibility" in name:
        return "readability_accessibility"

    if "focal" in name:
        return "focal_point"

    if "proportion" in name or "scale" in name:
        return "proportion_scale"

    if "overall" in name:
        return "overall_coherence"

    return ""


def convert_gemini_result(
    data,
    principle_map
):

    principle_names = [
        "composition",
        "visual_hierarchy",
        "balance",
        "contrast",
        "typography",
        "color",
        "negative_space",
        "alignment",
        "proximity_grouping",
        "repetition_rhythm",
        "unity_coherence",
        "readability_accessibility",
        "focal_point",
        "proportion_scale",
        "overall_coherence",
    ]

    result = {}

    for principle_name in principle_names:

        found = principle_map.get(
            principle_name
        )

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

        result[principle_name] = normalize_principle(
            found
        )

    result["overall_design_score"] = normalize_score(
        data.get(
            "overall_design_score",
            50
        )
    )

    result["communication_score"] = normalize_score(
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

    result["strengths"] = normalize_string_list(
        data.get(
            "strengths",
            []
        ),
        preferred_keys=[
            "strength",
            "text",
            "description"
        ]
    )

    result["most_important_problems"] = normalize_string_list(
        data.get(
            "most_important_problems",
            []
        ),
        preferred_keys=[
            "problem",
            "issue",
            "text",
            "description"
        ]
    )

    result["concrete_recommendations"] = normalize_string_list(
        data.get(
            "concrete_recommendations",
            []
        ),
        preferred_keys=[
            "recommendation",
            "action",
            "text",
            "description"
        ]
    )

    result["improvement_prompt"] = normalize_string(
        data.get(
            "improvement_prompt",
            ""
        )
    )

    designer_brief = data.get(
        "designer_brief",
        ""
    )

    result["designer_brief"] = normalize_string(
        designer_brief
    )

    return result


def normalize_principle(item):

    evidence = item.get(
        "evidence",
        []
    )

    # Gemini иногда возвращает evidence
    # одной строкой вместо списка.

    if isinstance(evidence, str):

        evidence = [evidence]

    elif not isinstance(evidence, list):

        evidence = [str(evidence)]

    evidence = [
        str(value)
        for value in evidence
        if value is not None
    ]

    return {
        "score": normalize_score(
            item.get(
                "score",
                50
            )
        ),

        "status": normalize_string(
            item.get(
                "status",
                "applicable"
            )
        ),

        "observation": normalize_string(
            item.get(
                "observation",
                ""
            )
        ),

        "evidence": evidence,

        "rationale": normalize_string(
            item.get(
                "rationale",
                ""
            )
        ),

        "perceptual_effect": normalize_string(
            item.get(
                "perceptual_effect",
                ""
            )
        ),

        "problem": normalize_optional_string(
            item.get(
                "problem",
                None
            )
        ),

        "recommendation": normalize_optional_string(
            item.get(
                "recommendation",
                None
            )
        ),

        "score_justification": normalize_string(
            item.get(
                "score_justification",
                ""
            )
        )
    }


def normalize_priority_issues(items):

    if not isinstance(items, list):
        return []

    result = []

    for item in items:

        if isinstance(item, str):

            result.append(
                {
                    "priority": "medium",
                    "principle": "",
                    "issue": item,
                    "evidence": "",
                    "perceptual_impact": "",
                    "action": ""
                }
            )

            continue

        if not isinstance(item, dict):
            continue

        result.append(
            {
                "priority": normalize_string(
                    item.get(
                        "priority",
                        "medium"
                    )
                ),

                "principle": normalize_string(
                    item.get(
                        "principle",
                        ""
                    )
                ),

                "issue": normalize_string(
                    item.get(
                        "issue",
                        item.get(
                            "problem",
                            ""
                        )
                    )
                ),

                "evidence": normalize_string(
                    item.get(
                        "evidence",
                        ""
                    )
                ),

                "perceptual_impact": normalize_string(
                    item.get(
                        "perceptual_impact",
                        item.get(
                            "impact",
                            ""
                        )
                    )
                ),

                "action": normalize_string(
                    item.get(
                        "action",
                        item.get(
                            "recommendation",
                            ""
                        )
                    )
                )
            }
        )

    return result


def normalize_string(value):

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):

        # Пытаемся вытащить основной текст
        for key in [
            "text",
            "description",
            "content",
            "summary",
            "brief"
        ]:

            if key in value:

                return str(
                    value[key]
                )

        # Если подходящего поля нет,
        # сохраняем объект как JSON.

        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2
        )

    if isinstance(value, list):

        return "\n".join(
            str(item)
            for item in value
        )

    return str(value)


def normalize_optional_string(value):

    if value is None:
        return None

    value = normalize_string(
        value
    )

    if not value.strip():
        return None

    return value


def normalize_score(value):

    if isinstance(value, bool):
        return 50

    if isinstance(value, (int, float)):
        return max(
            0,
            min(
                100,
                int(value)
            )
        )

    if isinstance(value, str):

        # Например: "85/100"

        try:
            number = value.split("/")[0]
            number = float(number)

            return max(
                0,
                min(
                    100,
                    int(number)
                )
            )

        except Exception:
            return 50

    return 50


def normalize_string_list(
    value,
    preferred_keys=None
):

    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if not isinstance(value, list):
        return [
            normalize_string(value)
        ]

    result = []

    for item in value:

        if isinstance(item, str):

            result.append(item)

        elif isinstance(item, dict):

            text = ""

            if preferred_keys:

                for key in preferred_keys:

                    if key in item:

                        text = normalize_string(
                            item[key]
                        )

                        if text:
                            break

            if not text:

                text = normalize_string(
                    item
                )

            result.append(text)

        else:

            result.append(
                normalize_string(item)
            )

    return result
