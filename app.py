import streamlit as st

from audit import analyze_image
from utils import prepare_image, get_image_dimensions


st.set_page_config(
    page_title="VISUAL AUDITOR",
    page_icon="🎨",
    layout="wide"
)


st.markdown(
    """
    <style>

    .main {
        background-color: #f7f4f1;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 3rem;
    }

    h1 {
        font-size: 42px;
        font-weight: 700;
        letter-spacing: -1px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 30px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


st.title("VISUAL AUDITOR")

st.markdown(
    """
    <div class="subtitle">
    AI-powered visual design audit
    </div>
    """,
    unsafe_allow_html=True
)


st.write(
    """
    Загрузите изображение, и AI проведет профессиональный
    визуальный аудит по 15 принципам графического дизайна.

    Анализ основывается только на визуально доступной информации.
    Каждое существенное замечание должно быть обосновано.
    """
)


uploaded_file = st.file_uploader(
    "Загрузите изображение",
    type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)


if uploaded_file:

    st.image(
        uploaded_file,
        caption="Изображение для анализа",
        use_container_width=True
    )

    width, height = get_image_dimensions(
        uploaded_file
    )

    st.caption(
        f"Размер изображения: {width} × {height}px"
    )


    if st.button(
        "🔍 Провести визуальный аудит",
        type="primary"
    ):

        with st.spinner(
            "Gemini анализирует изображение..."
        ):

            try:

                image_bytes = prepare_image(
                    uploaded_file
                )

                result = analyze_image(
                    image_bytes
                )

                st.session_state[
                    "audit_result"
                ] = result

            except Exception as error:

                st.error(
                    f"Ошибка анализа: {error}"
                )


if "audit_result" in st.session_state:

    result = st.session_state[
        "audit_result"
    ]


    st.divider()

    st.header("Итоговая оценка")


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Design Score",
            f"{result.overall_design_score}/100"
        )


    with col2:

        st.metric(
            "Communication Score",
            f"{result.communication_score}/100"
        )


    st.divider()

    st.header("Анализ 15 принципов")


    principles = [
        (
            "Композиция",
            result.composition
        ),
        (
            "Визуальная иерархия",
            result.visual_hierarchy
        ),
        (
            "Баланс",
            result.balance
        ),
        (
            "Контраст",
            result.contrast
        ),
        (
            "Типографика",
            result.typography
        ),
        (
            "Цвет",
            result.color
        ),
        (
            "Негативное пространство",
            result.negative_space
        ),
        (
            "Выравнивание",
            result.alignment
        ),
        (
            "Близость и группировка",
            result.proximity_grouping
        ),
        (
            "Повтор и ритм",
            result.repetition_rhythm
        ),
        (
            "Единство и визуальная согласованность",
            result.unity_coherence
        ),
        (
            "Читаемость и доступность",
            result.readability_accessibility
        ),
        (
            "Фокусная точка",
            result.focal_point
        ),
        (
            "Пропорции и масштаб",
            result.proportion_scale
        ),
        (
            "Общая визуальная согласованность",
            result.overall_coherence
        ),
    ]


    for name, principle in principles:

        with st.expander(
            f"{name} — {principle.score}/100"
        ):

            st.write(
                "**Что видно**"
            )

            st.write(
                principle.observation
            )


            st.write(
                "**Визуальные доказательства**"
            )

            for evidence in principle.evidence:

                st.markdown(
                    f"- {evidence}"
                )


            st.write(
                "**Почему это важно**"
            )

            st.write(
                principle.rationale
            )


            st.write(
                "**Влияние на восприятие**"
            )

            st.write(
                principle.perceptual_effect
            )


            if principle.problem:

                st.write(
                    "**Проблема**"
                )

                st.write(
                    principle.problem
                )


            st.write(
                "**Почему именно такая оценка**"
            )

            st.write(
                principle.score_justification
            )


            if principle.recommendation:

                st.write(
                    "**Что изменить**"
                )

                st.write(
                    principle.recommendation
                )


    st.divider()

    st.header("Приоритетные проблемы")


    for issue in result.priority_issues:

        with st.container(border=True):

            st.subheader(
                f"{issue.priority.upper()} — "
                f"{issue.principle}"
            )

            st.write(
                f"**Проблема:** {issue.issue}"
            )

            st.write(
                f"**Доказательство:** {issue.evidence}"
            )

            st.write(
                f"**Влияние:** {issue.perceptual_impact}"
            )

            st.write(
                f"**Действие:** {issue.action}"
            )


    st.divider()

    st.header("Сильные стороны")


    for strength in result.strengths:

        st.markdown(
            f"✓ {strength}"
        )


    st.header("3 главные проблемы")


    for problem in result.most_important_problems:

        st.markdown(
            f"• {problem}"
        )


    st.header("3 конкретные рекомендации")


    for recommendation in result.concrete_recommendations:

        st.markdown(
            f"→ {recommendation}"
        )


    st.divider()

    st.header("Промпт для улучшения")


    st.code(
        result.improvement_prompt,
        language="text"
    )


    st.header("Designer Brief")


    st.code(
        result.designer_brief,
        language="text"
    )
