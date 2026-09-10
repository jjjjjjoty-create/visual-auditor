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

    # Gemini иногда возвращает:
    #
    # {
    #     "audit_results": [...]
    # }
    #
    # вместо нашей внутренней структуры.
    #
    # Если это произошло, пытаемся преобразовать
    # результат Gemini.

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

            principle = item.get("principle", "")

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
