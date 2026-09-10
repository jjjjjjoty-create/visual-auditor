import json
import re

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
Проведи полный визуальный аудит предоставленного изображения.

ВАЖНО:

Весь содержательный текст ответа пиши НА РУССКОМ ЯЗЫКЕ.

Проанализируй изображение как профессиональный арт-директор.

Особенно внимательно проверь, не является ли изображение
перегруженным, слишком пёстрым, информационно плотным
или визуально шумным.

Если исходная композиция плохая, не бойся предложить
полную перестройку композиции.

Нужно сохранить смысл рекламы,
но не обязательно сохранять исходное расположение элементов.

Оцени все 15 принципов:

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

Для каждого принципа дай:

score
status
observation
evidence
rationale
perceptual_effect
problem
recommendation
score_justification

Также дай:

overall_design_score
communication_score
priority_issues
strengths
most_important_problems
concrete_recommendations
improvement_prompt
designer_brief

У каждого существенного замечания должно быть конкретное
визуальное доказательство.

Не придумывай то, чего нет на изображении.

Не используй пустые фразы.

Объясняй:

что видно
→ почему это проблема
→ как это влияет на восприятие
→ что нужно изменить.

IMPROVEMENT PROMPT должен быть профессиональным заданием
на РЕДИЗАЙН.

Если структура исходника перегружена,
разрешается полностью изменить:

- композицию;
- положение элементов;
- размеры;
- масштаб;
- группировку;
- визуальную иерархию;
- свободное пространство;
- цветовые акценты.

Не пытайся сохранить плохую композицию ради сходства
с исходником.

Сохраняй смысл рекламы и необходимые фактические элементы.

Не добавляй новые декоративные элементы без необходимости.

Верни только JSON.
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

    return parse_result(
        response.text
    )


def parse_result(raw_text):

    raw_text = raw_text.strip()

    # Убираем Markdown-обёртку,
    # если Gemini всё-таки её добавил.

    if raw_text.startswith("```"):

        raw_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw_text
        )

        raw_text = re.sub(
            r"\s*```$",
            "",
            raw_text
        )

    try:

        data = json.loads(
            raw_text
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Gemini вернул некорректный JSON: {error}"
        )

    data = extract_report(
        data
    )

    data = normalize_data(
        data
    )

    try:

        return AuditResult.model_validate(
            data
        )

    except Exception as error:

        raise ValueError(
            f"Gemini вернул JSON неправильной структуры: {error}"
        )


def extract_report(data):

    if not isinstance(data, dict):

        return {}

    # Gemini может завернуть результат
    # в audit_report.

    if isinstance(
        data.get("audit_report"),
        dict
    ):

        report = dict(
            data["audit_report"]
        )

        # Добавляем верхнеуровневые поля.

        for key, value in data.items():

            if key != "audit_report":
                report.setdefault(
                    key,
                    value
                )

        return report

    return data


def normalize_data(data):

    result = {}

    # --------------------------------------------------
    # 15 PRINCIPLES
    # --------------------------------------------------

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

    # Сначала ищем принципы прямо по ключам.

    for principle_name in principle_names:

        found = None

        for key, value in data.items():

            if not isinstance(value, dict):
                continue

            normalized_key = normalize_name(
                key
            )

            detected = detect_principle(
                normalized_key
            )

            if detected == principle_name:

                found = value
                break

        if found is None:

            found = {}

        result[
            principle_name
        ] = normalize_principle(
            found
        )

    # --------------------------------------------------
    # SCORES
    # --------------------------------------------------

    result[
        "overall_design_score"
    ] = normalize_score(
        data.get(
            "overall_design_score",
            data.get(
                "design_score",
                50
            )
        )
    )

    result[
        "communication_score"
    ] = normalize_score(
        data.get(
            "communication_score",
            50
        )
    )

    # --------------------------------------------------
    # PRIORITIES
    # --------------------------------------------------

    result[
        "priority_issues"
    ] = normalize_priority_issues(
        data.get(
            "priority_issues",
            []
        )
    )

    # --------------------------------------------------
    # STRENGTHS
    # --------------------------------------------------

    result[
        "strengths"
    ] = normalize_list(
        data.get(
            "strengths",
            []
        ),
        [
            "strength",
            "description",
            "text"
        ]
    )

    # --------------------------------------------------
    # PROBLEMS
    # --------------------------------------------------

    result[
        "most_important_problems"
    ] = normalize_list(
        data.get(
            "most_important_problems",
            []
        ),
        [
            "problem",
            "issue",
            "description",
            "text"
        ]
    )

    # --------------------------------------------------
    # RECOMMENDATIONS
    # --------------------------------------------------

    result[
        "concrete_recommendations"
    ] = normalize_list(
        data.get(
            "concrete_recommendations",
            []
        ),
        [
            "recommendation",
            "action",
            "description",
            "text"
        ]
    )

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    result[
        "improvement_prompt"
    ] = normalize_string(
        data.get(
            "improvement_prompt",
            ""
        )
    )

    # --------------------------------------------------
    # BRIEF
    # --------------------------------------------------

    result[
        "designer_brief"
    ] = normalize_string(
        data.get(
            "designer_brief",
            ""
        )
    )

    return result


def normalize_principle(item):

    if not isinstance(item, dict):

        item = {}

    evidence = item.get(
        "evidence",
        []
    )

    if isinstance(
        evidence,
        str
    ):

        evidence = [
            evidence
        ]

    elif not isinstance(
        evidence,
        list
    ):

        evidence = [
            normalize_string(
                evidence
            )
        ]

    evidence = [
        normalize_string(
            item
        )
        for item in evidence
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
                item.get(
                    "impact",
                    ""
                )
            )
        ),

        "problem": normalize_optional_string(
            item.get(
                "problem",
                item.get(
                    "issue",
                    None
                )
            )
        ),

        "recommendation": normalize_optional_string(
            item.get(
                "recommendation",
                item.get(
                    "action",
                    None
                )
            )
        ),

        "score_justification": normalize_string(
            item.get(
                "score_justification",
                item.get(
                    "score_reason",
                    ""
                )
            )
        )
    }


def normalize_priority_issues(items):

    if not isinstance(
        items,
        list
    ):

        return []

    result = []

    for item in items:

        if not isinstance(
            item,
            dict
        ):

            continue

        result.append(
            {
                "priority": normalize_string(
                    item.get(
                        "priority",
                        item.get(
                            "severity",
                            "medium"
                        )
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


def normalize_list(
    value,
    preferred_keys
):

    if value is None:

        return []

    if isinstance(
        value,
        str
    ):

        return [
            value
        ]

    if not isinstance(
        value,
        list
    ):

        return [
            normalize_string(
                value
            )
        ]

    result = []

    for item in value:

        if isinstance(
            item,
            str
        ):

            result.append(
                item
            )

        elif isinstance(
            item,
            dict
        ):

            text = ""

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

            result.append(
                text
            )

        else:

            result.append(
                normalize_string(
                    item
                )
            )

    return result


def normalize_string(value):

    if value is None:

        return ""

    if isinstance(
        value,
        str
    ):

        return value

    if isinstance(
        value,
        dict
    ):

        for key in [
            "text",
            "description",
            "content",
            "summary",
            "brief",
            "value"
        ]:

            if key in value:

                return normalize_string(
                    value[key]
                )

        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2
        )

    if isinstance(
        value,
        list
    ):

        return "\n".join(
            normalize_string(
                item
            )
            for item in value
        )

    return str(value)


def normalize_optional_string(value):

    if value is None:

        return None

    text = normalize_string(
        value
    )

    if not text.strip():

        return None

    return text


def normalize_score(value):

    if isinstance(
        value,
        (int, float)
    ):

        return max(
            0,
            min(
                100,
                int(value)
            )
        )

    if isinstance(
        value,
        str
    ):

        match = re.search(
            r"\d+(?:\.\d+)?",
            value
        )

        if match:

            return max(
                0,
                min(
                    100,
                    int(
                        float(
                            match.group()
                        )
                    )
                )
            )

    return 50


def normalize_name(name):

    return (
        str(name)
        .lower()
        .strip()
        .replace(
            " ",
            "_"
        )
        .replace(
            "-",
            "_"
        )
        .replace(
            "/",
            "_"
        )
    )


def detect_principle(name):

    # Важный момент:
    # overall_coherence проверяем ДО coherence,
    # иначе общий принцип может попасть в unity_coherence.

    if "overall_coherence" in name:
        return "overall_coherence"

    if "overall" in name:
        return "overall_coherence"

    if "composition" in name:
        return "composition"

    if "visual_hierarchy" in name:
        return "visual_hierarchy"

    if name == "hierarchy":
        return "visual_hierarchy"

    if "balance" in name:
        return "balance"

    if "contrast" in name:
        return "contrast"

    if "typography" in name:
        return "typography"

    if "color" in name or "colour" in name:
        return "color"

    if "negative_space" in name:
        return "negative_space"

    if "whitespace" in name:
        return "negative_space"

    if "alignment" in name:
        return "alignment"

    if "proximity" in name:
        return "proximity_grouping"

    if "grouping" in name:
        return "proximity_grouping"

    if "repetition" in name:
        return "repetition_rhythm"

    if "rhythm" in name:
        return "repetition_rhythm"

    if "unity" in name:
        return "unity_coherence"

    if "readability" in name:
        return "readability_accessibility"

    if "accessibility" in name:
        return "readability_accessibility"

    if "focal" in name:
        return "focal_point"

    if "proportion" in name:
        return "proportion_scale"

    if "scale" in name:
        return "proportion_scale"

    # Русские варианты

    if "композиц" in name:
        return "composition"

    if "иерарх" in name:
        return "visual_hierarchy"

    if "баланс" in name:
        return "balance"

    if "контраст" in name:
        return "contrast"

    if "типограф" in name:
        return "typography"

    if "цвет" in name:
        return "color"

    if "негатив" in name:
        return "negative_space"

    if "выравнив" in name:
        return "alignment"

    if "близост" in name or "группиров" in name:
        return "proximity_grouping"

    if "повтор" in name or "ритм" in name:
        return "repetition_rhythm"

    if "единств" in name:

        return "unity_coherence"

    if "согласован" in name:

        if "общ" in name:
            return "overall_coherence"

        return "unity_coherence"

    if "читаем" in name or "доступност" in name:
        return "readability_accessibility"

    if "фокус" in name:
        return "focal_point"

    if "пропорц" in name or "масштаб" in name:
        return "proportion_scale"

    return None
