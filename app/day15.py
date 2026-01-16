# Day 15
# Model Comparison Arena

import streamlit as st
import time
import json
from snowflake.snowpark.functions import ai_complete

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 세션 상태 초기화
if "latest_results" not in st.session_state:
    st.session_state.latest_results = None

def run_model(model: str, prompt: str) -> dict:
    """모델을 실행하고 메트릭을 수집합니다."""
    start = time.time()

    # [실습] Cortex ai_complete 함수를 호출하여 모델 응답을 생성하세요.
    # 힌트: session.range(1).select(ai_complete(...).alias("response"))
    
    # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
    # df = session.range(1).select(
    #     ai_complete(model=model, prompt=prompt).alias("response")
    # )
    
    # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요. 
    df = None # 이 줄을 수정하세요

    if df is None:
         # 실습 코드가 작성되지 않았을 때의 예외 처리
        return {
            "latency": 0.0,
            "tokens": 0,
            "response_text": "코드를 완성해주세요! (run_model 함수를 확인하세요)"
        }

    # 데이터프레임에서 응답 추출
    rows = df.collect()
    response_raw = rows[0][0]
    response_json = json.loads(response_raw)

    # 응답에서 텍스트 추출
    text = response_json.get("choices", [{}])[0].get("messages", "") if isinstance(response_json, dict) else str(response_json)

    latency = time.time() - start
    tokens = int(len(text.split()) * 4/3)  # 토큰 수 추정 (1 토큰 ≈ 0.75 단어)

    return {
        "latency": latency,
        "tokens": tokens,
        "response_text": text
    }

def display_metrics(results: dict, model_key: str):
    """모델에 대한 메트릭을 표시합니다."""
    latency_col, tokens_col = st.columns(2)  # 2개의 동일한 열 생성

    latency_col.metric("Latency (s)", f"{results[model_key]['latency']:.1f}")  # 초 단위 1자리 소수점
    tokens_col.metric("Tokens", results[model_key]['tokens'])

def display_response(container, results: dict, model_key: str):
    """컨테이너에 채팅 메시지를 표시합니다."""
    with container:
        with st.chat_message("user"):
            st.write(results["prompt"])
        with st.chat_message("assistant"):
            st.write(results[model_key]["response_text"])

# 모델 선택
llm_models = [
    "llama3-8b",
    "llama3-70b",
    "mistral-7b",
    "mixtral-8x7b",
    "claude-3-5-sonnet",
    "claude-haiku-4-5",
    "openai-gpt-5",
    "openai-gpt-5-mini"
]
st.title(":material/compare: 모델 선택 (Select Models)")
col_a, col_b = st.columns(2)  # 드롭다운을 위한 두 개의 열 생성

col_a.write("**모델 A**")
model_a = col_a.selectbox("Model A", llm_models, key="model_a", label_visibility="collapsed")

col_b.write("**모델 B**")
model_b = col_b.selectbox("Model B", llm_models, key="model_b", index=1, label_visibility="collapsed")  # 두 번째 모델을 기본값으로 설정

# 응답 컨테이너
st.divider()
col_a, col_b = st.columns(2)  # 응답을 위한 두 개의 열 생성
results = st.session_state.latest_results

# 코드 중복을 피하기 위해 두 모델 반복
for col, model_name, model_key in [(col_a, model_a, "model_a"), (col_b, model_b, "model_b")]:
    with col:
        st.subheader(model_name)
        container = st.container(height=400, border=True)  # 고정 높이, 스크롤 가능한 컨테이너

        if results:
            display_response(container, results, model_key)

        st.caption("성능 메트릭 (Performance Metrics)")
        if results:
            display_metrics(results, model_key)
        else:  # 결과가 없을 때 플레이스홀더 표시
            latency_col, tokens_col = st.columns(2)
            latency_col.metric("Latency (s)", "—")
            tokens_col.metric("Tokens", "—")

# 채팅 입력 및 실행
st.divider()
if prompt := st.chat_input("모델을 비교할 메시지를 입력하세요"):  # Walrus 연산자: 할당 및 확인
    # 모델 순차 실행 (모델 A, 그 다음 모델 B)
    with st.status(f"{model_a} 실행 중..."):
        result_a = run_model(model_a, prompt)
    with st.status(f"{model_b} 실행 중..."):
        result_b = run_model(model_b, prompt)

    # 결과를 세션 상태에 저장 (이전 결과 교체)
    st.session_state.latest_results = {"prompt": prompt, "model_a": result_a, "model_b": result_b}
    st.rerun()  # 결과를 표시하기 위해 다시 실행

st.divider()
st.caption("Day 15: Model Comparison Arena | 30 Days of AI")
