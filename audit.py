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

- score — целое число от 0 до 100;
- status;
- observation;
- evidence — список конкретных наблюдаемых признаков;
- rationale;
- perceptual_effect;
- problem;
- recommendation;
- score_justification.

Также верни:

- overall_design_score;
- communication_score;
- priority_issues;
- strengths;
- most_important_problems;
- concrete_recommendations;
- improvement_prompt;
- designer_brief.

КРИТИЧЕСКИ ВАЖНО:

Анализируй только то, что реально видно.

Не придумывай отсутствующие элементы,
текст, шрифты, цвета, намерения автора
или целевую аудиторию.

Каждая существенная критика должна иметь
конкретное визуальное доказательство.

Объясняй цепочку:

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

    # Если модель вдруг вернула Markdown-обертку
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

    try:

        result = AuditResult.model_validate(
            data
        )

    except Exception as error:

        raise ValueError(
            f"Gemini вернул JSON неправильной структуры: {error}"
        )

    return result
