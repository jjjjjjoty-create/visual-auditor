import json
import re

import streamlit as st
from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT
from schemas import AuditResult


MODEL = "gemini-2.5-flash"


# ============================================================
# GEMINI
# ============================================================

def get_client():

    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


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


def build_user_prompt():

    return """
Проведи полный профессиональный визуальный аудит
предоставленного рекламного изображения.

ВАЖНО:

Весь содержательный текст пиши ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.

Анализируй только то, что реально видно на изображении.

Не придумывай отсутствующие элементы.

Проанализируй все 15 принципов:

1. Композиция
2. Визуальная иерархия
3. Баланс
4. Контраст
5. Типографика
6. Цвет
7. Негативное пространство
8. Выравнивание
9. Близость и группировка
10. Повтор и ритм
11. Единство и визуальная согласованность
12. Читаемость и доступность
13. Фокусная точка
14. Пропорции и масштаб
15. Общая визуальная согласованность

Для КАЖДОГО принципа обязательно укажи:

score
status
observation
evidence
rationale
perceptual_effect
problem
recommendation
score_justification

Критически важно:

НЕ оставляй эти поля пустыми.

Если принцип работает хорошо,
всё равно объясни ПОЧЕМУ он работает.

Если принцип работает плохо,
укажи конкретное визуальное доказательство.

Каждая существенная проблема должна быть объяснена
по цепочке:

что видно
→ доказательство
→ принцип дизайна
→ почему это проблема
→ влияние на восприятие
→ что изменить.

Также создай:

overall_design_score
communication_score

priority_issues

strengths — ровно 3

most_important_problems — ровно 3

concrete_recommendations — ровно 3

improvement_prompt

designer_brief


ОСОБОЕ ВНИМАНИЕ:

Если реклама перегружена, слишком пёстрая,
имеет слишком много текста, цветов, декоративных
элементов или конкурирующих акцентов,
укажи это явно.

При создании improvement_prompt:

НЕ сохраняй плохую исходную композицию.

Сохраняй смысл рекламы, основной продукт,
важную информацию и необходимые брендовые элементы.

Но разрешается полностью изменить:

- композицию;
- положение элементов;
- размеры;
- масштаб;
- группировку;
- визуальную иерархию;
- свободное пространство;
- цветовые акценты;
- типографическую систему.

Если исходная композиция является причиной проблем,
её НЕ нужно сохранять.

Редизайн должен упрощать перегруженное изображение,
а не добавлять ещё больше деталей.

ОБЯЗАТЕЛЬНО используй смысл:

"Сохрани содержание, но перестрой дизайн."

Верни только JSON.
"""


# ============================================================
# PARSING
# ============================================================

def parse_result(raw_text):

    raw_text = clean_json_text(
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

    normalized = normalize_data(
        data
    )

    try:

        return AuditResult.model_validate(
            normalized
        )

    except Exception as error:

        raise ValueError(
            f"Не удалось обработать результат Gemini: {error}"
        )


def clean_json_text(text):

    text = text.strip()

    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

    return text.strip()


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_data(data):

    result = {}

    # --------------------------------------------------------
    # Сначала ищем ВСЕ данные рекурсивно.
    # --------------------------------------------------------

    all_dicts = collect_dictionaries(
        data
    )

    # --------------------------------------------------------
    # 15 ПРИНЦИПОВ
    # --------------------------------------------------------

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

    for principle_name in principle_names:

        found = find_principle(
            data,
            principle_name
        )

        if found is None:

            found = {}

        result[
            principle_name
        ] = normalize_principle(
            found
        )

    # --------------------------------------------------------
    # ОБЩИЕ ОЦЕНКИ
    # --------------------------------------------------------

    result[
        "overall_design_score"
    ] = normalize_score(
        find_value_recursive(
            data,
            [
                "overall_design_score",
                "design_score",
                "overall_score"
            ],
            default=50
        )
    )

    result[
        "communication_score"
    ] = normalize_score(
        find_value_recursive(
            data,
            [
                "communication_score",
                "communication"
            ],
            default=50
        )
    )

    # --------------------------------------------------------
    # ПРИОРИТЕТНЫЕ ПРОБЛЕМЫ
    # --------------------------------------------------------

    priority_data = find_value_recursive(
        data,
        [
            "priority_issues",
            "priorities",
            "critical_issues"
        ],
        default=[]
    )

    result[
        "priority_issues"
    ] = normalize_priority_issues(
        priority_data
    )

    # --------------------------------------------------------
    # СИЛЬНЫЕ СТОРОНЫ
    # --------------------------------------------------------

    strengths = find_value_recursive(
        data,
        [
            "strengths",
            "strengths_of_design"
        ],
        default=[]
    )

    result[
        "strengths"
    ] = normalize_list(
        strengths,
        [
            "strength",
            "description",
            "text"
        ]
    )

    # --------------------------------------------------------
    # ГЛАВНЫЕ ПРОБЛЕМЫ
    # --------------------------------------------------------

    problems = find_value_recursive(
        data,
        [
            "most_important_problems",
            "main_problems",
            "key_problems"
        ],
        default=[]
    )

    result[
        "most_important_problems"
    ] = normalize_list(
        problems,
        [
            "problem",
            "issue",
            "description",
            "text"
        ]
    )

    # --------------------------------------------------------
    # РЕКОМЕНДАЦИИ
    # --------------------------------------------------------

    recommendations = find_value_recursive(
        data,
        [
            "concrete_recommendations",
            "recommendations",
            "actions"
        ],
        default=[]
    )

    result[
        "concrete_recommendations"
    ] = normalize_list(
        recommendations,
        [
            "recommendation",
            "action",
            "description",
            "text"
        ]
    )

    # --------------------------------------------------------
    # IMPROVEMENT PROMPT
    # --------------------------------------------------------

    prompt = find_value_recursive(
        data,
        [
            "improvement_prompt",
            "redesign_prompt",
            "design_prompt"
        ],
        default=""
    )

    result[
        "improvement_prompt"
    ] = normalize_string(
        prompt
    )

    # --------------------------------------------------------
    # DESIGNER BRIEF
    # --------------------------------------------------------

    brief = find_value_recursive(
        data,
        [
            "designer_brief",
            "design_brief",
            "brief"
        ],
        default=""
    )

    result[
        "designer_brief"
    ] = normalize_string(
        brief
    )

    return result


# ============================================================
# РЕКУРСИВНЫЙ ПОИСК
# ============================================================

def collect_dictionaries(data):

    result = []

    if isinstance(
        data,
        dict
    ):

        result.append(
            data
        )

        for value in data.values():

            result.extend(
                collect_dictionaries(
                    value
                )
            )

    elif isinstance(
        data,
        list
    ):

        for item in data:

            result.extend(
                collect_dictionaries(
                    item
                )
            )

    return result


def find_principle(
    data,
    target
):

    dictionaries = collect_dictionaries(
        data
    )

    # --------------------------------------------------------
    # 1. Ищем по ключу
    # --------------------------------------------------------

    for item in dictionaries:

        for key, value in item.items():

            if not isinstance(
                value,
                dict
            ):

                continue

            detected = detect_principle(
                normalize_name(
                    key
                )
            )

            if detected == target:

                return value

    # --------------------------------------------------------
    # 2. Ищем по полю "principle"
    # --------------------------------------------------------

    for item in dictionaries:

        principle_value = item.get(
            "principle"
        )

        if principle_value:

            detected = detect_principle(
                normalize_name(
                    principle_value
                )
            )

            if detected == target:

                return item

    # --------------------------------------------------------
    # 3. Ищем по полю "name"
    # --------------------------------------------------------

    for item in dictionaries:

        name_value = item.get(
            "name"
        )

        if name_value:

            detected = detect_principle(
                normalize_name(
                    name_value
                )
            )

            if detected == target:

                return item

    return None


def find_value_recursive(
    data,
    keys,
    default=None
):

    wanted = {
        normalize_name(key)
        for key in keys
    }

    dictionaries = collect_dictionaries(
        data
    )

    for item in dictionaries:

        for key, value in item.items():

            if normalize_name(
                key
            ) in wanted:

                return value

    return default


# ============================================================
# PRINCIPLE
# ============================================================

def normalize_principle(item):

    if not isinstance(
        item,
        dict
    ):

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

    elif isinstance(
        evidence,
        dict
    ):

        evidence = [
            normalize_string(
                evidence
            )
        ]

    elif not isinstance(
        evidence,
        list
    ):

        evidence = []

    evidence = [

        normalize_string(
            value
        )

        for value in evidence

        if normalize_string(
            value
        ).strip()
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
                item.get(
                    "what_is_visible",
                    ""
                )
            )
        ),

        "evidence": evidence,

        "rationale": normalize_string(
            item.get(
                "rationale",
                item.get(
                    "why_it_matters",
                    ""
                )
            )
        ),

        "perceptual_effect": normalize_string(
            item.get(
                "perceptual_effect",
                item.get(
                    "impact",
                    item.get(
                        "perceptual_impact",
                        ""
                    )
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
                    item.get(
                        "reason",
                        ""
                    )
                )
            )
        )
    }


# ============================================================
# PRIORITY ISSUES
# ============================================================

def normalize_priority_issues(
    items
):

    if not isinstance(
        items,
        list
    ):

        if isinstance(
            items,
            dict
        ):

            items = [
                items
            ]

        else:

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
                        item.get(
                            "principle_name",
                            ""
                        )
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


# ============================================================
# LISTS
# ============================================================

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

    if isinstance(
        value,
        dict
    ):

        value = [
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

            if item.strip():

                result.append(
                    item
                )

            continue

        if isinstance(
            item,
            dict
        ):

            text = ""

            for key in preferred_keys:

                if key in item:

                    text = normalize_string(
                        item[key]
                    )

                    if text.strip():

                        break

            if not text:

                text = normalize_string(
                    item
                )

            if text.strip():

                result.append(
                    text
                )

        else:

            text = normalize_string(
                item
            )

            if text.strip():

                result.append(
                    text
                )

    return result


# ============================================================
# STRING
# ============================================================

def normalize_string(
    value
):

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

        # Сначала пытаемся найти нормальное текстовое поле.

        for key in [
            "text",
            "description",
            "content",
            "summary",
            "brief",
            "value",
            "action",
            "recommendation",
            "problem",
            "issue",
            "strength"
        ]:

            if key in value:

                text = normalize_string(
                    value[key]
                )

                if text.strip():

                    return text

        # Если это структурированный объект,
        # превращаем его в читаемый текст.

        parts = []

        for key, item in value.items():

            text = normalize_string(
                item
            )

            if text.strip():

                parts.append(
                    f"{key}: {text}"
                )

        return "\n".join(
            parts
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


def normalize_optional_string(
    value
):

    if value is None:

        return None

    text = normalize_string(
        value
    )

    if not text.strip():

        return None

    return text


# ============================================================
# SCORE
# ============================================================

def normalize_score(
    value
):

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


# ============================================================
# NAMES
# ============================================================

def normalize_name(
    name
):

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


def detect_principle(
    name
):

    # Сначала самые специфичные названия.

    if (
        "overall_coherence"
        in name
    ):

        return "overall_coherence"

    if (
        "overall_visual_coherence"
        in name
    ):

        return "overall_coherence"

    if (
        "overall" in name
        and "coherence" in name
    ):

        return "overall_coherence"

    # --------------------------------------------------------
    # Английские названия
    # --------------------------------------------------------

    if "composition" in name:

        return "composition"

    if (
        "visual_hierarchy"
        in name
    ):

        return "visual_hierarchy"

    if name == "hierarchy":

        return "visual_hierarchy"

    if "balance" in name:

        return "balance"

    if "contrast" in name:

        return "contrast"

    if "typography" in name:

        return "typography"

    if (
        "color" in name
        or "colour" in name
    ):

        return "color"

    if (
        "negative_space"
        in name
    ):

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

    # --------------------------------------------------------
    # Русские названия
    # --------------------------------------------------------

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

    if (
        "близост" in name
        or "группиров" in name
    ):

        return "proximity_grouping"

    if (
        "повтор" in name
        or "ритм" in name
    ):

        return "repetition_rhythm"

    if "единств" in name:

        return "unity_coherence"

    if "согласован" in name:

        if "общ" in name:

            return "overall_coherence"

        return "unity_coherence"

    if (
        "читаем" in name
        or "доступност" in name
    ):

        return "readability_accessibility"

    if "фокус" in name:

        return "focal_point"

    if (
        "пропорц" in name
        or "масштаб" in name
    ):

        return "proportion_scale"

    return None
