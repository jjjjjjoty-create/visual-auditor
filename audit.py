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

Используй все инструкции системного промпта.

Особенно важно:

Каждая существенная критика должна быть основана
на конкретном визуальном доказательстве.

Используй цепочку:

наблюдение
→ доказательство
→ принцип дизайна
→ объяснение
→ влияние на восприятие
→ проблема
→ конкретное действие.

Не придумывай то, чего нет на изображении.

Если какой-либо принцип невозможно оценить,
используй status = "not_applicable".

Оцени все 15 принципов.

Верни результат строго в соответствии
с предоставленной JSON-схемой.
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

            response_schema=AuditResult,

            temperature=0.2,

            max_output_tokens=12000,
        )
    )

    if not response.text:
        raise ValueError(
            "Gemini не вернул текстовый результат."
        )

    return parse_result(response.text)


def parse_result(raw_text: str):

    raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Gemini вернул некорректный JSON: {error}"
        )

    try:
        result = AuditResult.model_validate(data)

    except Exception as error:
        raise ValueError(
            f"JSON имеет неправильную структуру: {error}"
        )

    return result
