# Model Comparison Arena (모델 비교 도구 제작)

# 0. 목표

<aside>
💡

**다양한 LLM 모델의 성능과 응답을 비교하는 Streamlit 앱 구현**

1. Snowflake Cortex AI를 활용한 모델 실행
2. 두 모델을 순차적으로 실행하여 응답 시간(Latency) 및 토큰 수 비교
3. Streamlit을 활용한 직관적인 비교 UI 구성

</aside>

# 1. 개요 및 필요성 (Overview)

- **Week 2(Chatbots)**를 마무리하며, 실제 어플리케이션 구축 시 가장 중요한 질문인 **"어떤 모델을 사용해야 하는가?"**에 답하기 위한 도구입니다.
- RAG(Week 3) 구축 전, 각 모델의 장단점(속도 vs 품질, 비용 vs 성능)을 직접 비교해 볼 수 있습니다.

# 2. Streamlit 앱 구현 (Implementation)

## 2-1. 라이브러리 설정 및 모델 실행 함수

- Snowflake Cortex의 `ai_complete` 함수를 사용하여 LLM을 호출하고, 응답 시간과 토큰 수를 측정합니다.

    ```python
    import streamlit as st
    import time
    import json
    from snowflake.snowpark.functions import ai_complete

    # Connect to Snowflake
    try:
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
    except:
        from snowflake.snowpark import Session
        session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

    def run_model(model: str, prompt: str) -> dict:
        """모델 실행 및 메트릭 수집"""
        start = time.time()

        # Cortex Complete 함수 호출
        df = session.range(1).select(
            ai_complete(model=model, prompt=prompt).alias("response")
        )

        # 결과 파싱
        rows = df.collect()
        response_raw = rows[0][0]
        response_json = json.loads(response_raw)
        
        # 텍스트 추출
        text = response_json.get("choices", [{}])[0].get("messages", "") if isinstance(response_json, dict) else str(response_json)

        latency = time.time() - start
        tokens = int(len(text.split()) * 4/3)  # 토큰 수 추정 (1 word ≈ 1.33 tokens)

        return {
            "latency": latency,
            "tokens": tokens,
            "response_text": text
        }
    ```

    - `ai_complete`: Snowflake에서 제공하는 LLM 호출 함수
    - `time.time()`: API 호출 전후의 시간을 측정하여 Latency 계산
    - `len(text.split()) * 4/3`: 대략적인 토큰 수 계산 공식 활용

## 2-2. 비교 UI 구성 (Side-by-Side UI)

- 두 개의 모델을 선택하고 결과를 나란히 보여주기 위해 `st.columns`를 활용합니다.

    ```python
    # 모델 목록 정의
    llm_models = [
        "llama3-8b", "llama3-70b", "mistral-7b", "mixtral-8x7b",
        "claude-3-5-sonnet", "claude-haiku-4-5", "openai-gpt-5", "openai-gpt-5-mini"
    ]

    st.title(":material/compare: Select Models")
    col_a, col_b = st.columns(2)

    # Model A 선택
    col_a.write("**Model A**")
    model_a = col_a.selectbox("Model A", llm_models, key="model_a", label_visibility="collapsed")

    # Model B 선택 (기본값: 두 번째 모델)
    col_b.write("**Model B**")
    model_b = col_b.selectbox("Model B", llm_models, key="model_b", index=1, label_visibility="collapsed")
    ```

    - `st.columns(2)`: 화면을 좌우 2분할하여 비교에 최적화된 레이아웃 구성
    - `key`: 위젯 고유 식별자 (model_a, model_b)

## 2-3. 실행 및 결과 표시

- 같은 프롬프트로 두 모델을 순차적으로 실행(Sequential Execution)하고 결과를 표시합니다.

    ```python
    # 채팅 입력
    st.divider()
    if prompt := st.chat_input("Enter your message to compare models"):
        # 순차 실행 (Model A -> Model B)
        with st.status(f"Running {model_a}..."):
            result_a = run_model(model_a, prompt)
        with st.status(f"Running {model_b}..."):
            result_b = run_model(model_b, prompt)

        # 결과 저장 (Session State)
        st.session_state.latest_results = {"prompt": prompt, "model_a": result_a, "model_b": result_b}
        st.rerun()
    ```

    - `st.status`: 실행 중임을 사용자에게 시각적으로 알림
    - `st.session_state`: 실행 완료 후 리런(rerun) 되더라도 결과를 유지하기 위해 사용

# 3. 핵심 포인트 및 고려사항

## 환경 호환성 (Cross-Environment Compatibility)
- `try-except` 구문을 통해 로컬 개발 환경과 Snowflake 내부(SiS) 환경 모두에서 코드 수정 없이 동작합니다.

## 성능 측정 (Metrics)
- 단순 텍스트 생성이 아니라, **응답 속도(Latency)**와 **출력량(Tokens)**을 함께 보여줌으로써 비용/성능 효율성을 판단할 수 있는 지표를 제공합니다.

# 실행 결과

## 실행 코드

Streamlit 실행 코드 = python -m streamlit run 파일명.py

예시 : `python -m streamlit run app/day15.py`
