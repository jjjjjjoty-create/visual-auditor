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

Оцени все 15 принципов дизайна.

Для каждого принципа:

1. Опиши, что непосредственно видно.
2. Приведи конкретные визуальные доказательства.
3. Объясни связь с принципом дизайна.
4. Объясни влияние на визуальное восприятие.
5. Если есть проблема — сформулируй ее конкретно.
6. Предложи конкретное изменение.

Не придумывай элементы, которых нет на изображении.

Если принцип невозможно оценить,
используй status = "not_applicable".

Каждая существенная критика должна быть доказана
наблюдаемыми признаками изображения.

Не ставь оценки случайно.

Верни результат строго в формате JSON-схемы.
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
        )
    )

    if not response.text:
        raise ValueError(
            "Gemini не вернул результат."
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
