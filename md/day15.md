**Day 15**는 다양한 LLM 모델을 비교하는 실용적인 도구를 도입하여 Week 2(챗봇)를 마무리합니다. Week 2 동안 점진적으로 정교한 챗봇을 구축한 후, 이제 핵심 질문에 답해야 합니다: **어떤 모델을 사용해야 할까요?**

오늘의 과제는 **나란히 모델 비교 도구를 구축하는 것**입니다. **동일한 프롬프트를 두 개의 다른 모델을 통해 순차적으로 실행**하고 메트릭을 비교해야 합니다. 완료되면 총 지연 시간 및 출력 토큰 수와 같은 성능 메트릭과 함께 **두 응답을 나란히 표시**합니다.

**지금 이것이 중요한 이유:**
- 완전한 챗봇 구축을 막 마쳤습니다 (Days 8-14)
- Week 3는 내일 RAG 애플리케이션을 시작합니다 - 모델을 선택해야 합니다
- 다른 모델은 다른 트레이드오프를 가지고 있습니다: 속도 대 품질, 비용 대 능력
- 이 도구는 사용 사례에 대한 정보에 입각한 결정을 내리는 데 도움이 됩니다

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 모델 실행 및 메트릭 수집

```python
import streamlit as st
import time
import json
from snowflake.snowpark.functions import ai_complete

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

def run_model(model: str, prompt: str) -> dict:
    """Execute model and collect metrics."""
    start = time.time()

    # Call Cortex Complete function
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt).alias("response")
    )

    # Get response from dataframe
    rows = df.collect()
    response_raw = rows[0][0]
    response_json = json.loads(response_raw)

    # Extract text from response
    text = response_json.get("choices", [{}])[0].get("messages", "") if isinstance(response_json, dict) else str(response_json)

    latency = time.time() - start
    tokens = int(len(text.split()) * 4/3)  # Estimate tokens (1 token ≈ 0.75 words)

    return {
        "latency": latency,
        "tokens": tokens,
        "response_text": text
    }
```

* **`from snowflake.snowpark.functions import ai_complete`**: **`ai_complete` 함수를 임포트**하여 **Snowflake Cortex AI 모델**과 상호 작용합니다.
* **`session = get_active_session()`**: Cortex AI 호출을 실행하는 데 필요한 **활성 Snowpark 세션을 검색**합니다.
* **`start = time.time()`**: API 호출을 시작하는 **정확한 순간을 기록**합니다. 이것이 타이밍 측정의 기준선입니다.
* **`df = session.range(1).select(...)`**: 이것은 **Cortex 함수를 호출하는 Snowpark 패턴**입니다. 한 행이 있는 DataFrame을 생성하고 `ai_complete`를 호출합니다.
* **`rows = df.collect()`**: **쿼리를 실행하고 결과를 수집**하여 리스트로 만듭니다. 이를 단계로 나누면 `.collect()[0][0]`을 체이닝하는 것보다 코드를 더 읽기 쉽게 만듭니다.
* **`response_raw = rows[0][0]`**: JSON 응답 문자열을 포함하는 **첫 번째 행의 첫 번째 셀을 추출**합니다.
* **`json.loads(response_raw)`**: **응답이 JSON 문자열로 반환**되므로 중첩된 구조에 액세스하기 위해 파싱합니다.
* **`text = response_json.get(...) if isinstance(response_json, dict) else str(response_json)`**: dict 및 non-dict 응답을 모두 처리하는 인라인 조건을 사용하여 **응답에서 텍스트를 추출**합니다.
* **`latency = time.time() - start`**: API 호출을 시작한 시점부터 완전한 응답을 받을 때까지의 **총 응답 시간을 측정**합니다.
* **`tokens = int(len(text.split()) * 4/3)`**: 1 토큰 ≈ 0.75 단어(또는 1 단어 ≈ 1.33 토큰)라는 경험 법칙을 사용하여 **토큰 수를 추정**합니다. 더 나은 근사치를 위해 단어 수에 4/3을 곱합니다.

#### 2. 나란히 UI 구축

```python
# Model selection
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
st.title(":material/compare: Select Models")
col_a, col_b = st.columns(2)

col_a.write("**Model A**")
model_a = col_a.selectbox("Model A", llm_models, key="model_a", label_visibility="collapsed")

col_b.write("**Model B**")
model_b = col_b.selectbox("Model B", llm_models, key="model_b", index=1, label_visibility="collapsed")

# Response containers
st.divider()
col_a, col_b = st.columns(2)
results = st.session_state.latest_results

# Loop through both models to avoid code duplication
for col, model_name, model_key in [(col_a, model_a, "model_a"), (col_b, model_b, "model_b")]:
    with col:
        st.subheader(model_name)
        container = st.container(height=400, border=True)

        if results:
            display_response(container, results, model_key)

        st.caption("Performance Metrics")
        if results:
            display_metrics(results, model_key)
        else:  # Show placeholders when no results yet
            latency_col, tokens_col = st.columns(2)
            latency_col.metric("Latency (s)", "—")
            tokens_col.metric("Tokens", "—")
```

* **`llm_models = [...]`**: 비교를 위해 Llama, Mistral, Mixtral, Claude 및 OpenAI GPT 변형을 포함하여 **사용 가능한 모델 목록을 정의**합니다.
* **`st.title(":material/compare: Select Models")`**: 비교 기능을 시각적으로 나타내는 Material 아이콘(비교 아이콘)과 함께 **메인 페이지 제목을 생성**합니다.
* **`col_a, col_b = st.columns(2)`**: `cols[0]` 및 `cols[1]`과 같은 배열 인덱스를 사용하는 대신 의미 있는 이름으로 **두 개의 동일한 너비 열을 생성**합니다. 이렇게 하면 코드가 초보자에게 더 친숙해집니다.
* **`col_a.selectbox(...)`**: Model A 선택을 위해 첫 번째 열에 **드롭다운 메뉴를 생성**합니다.
* **`label_visibility="collapsed"`**: 위에 자체 굵은 제목을 표시하고 있으므로 **선택 상자 레이블을 숨깁니다**.
* **`index=1`**: 기본적으로 다른 모델이 선택되도록 **Model B의 기본 선택을 리스트의 두 번째 모델로 설정**합니다.
* **`st.divider()`**: 모델 선택 영역과 응답 컨테이너 사이에 **시각적 구분선을 생성**합니다.
* **`st.container(height=400, border=True)`**: 테두리가 있는 **고정 높이 컨테이너**(400픽셀)를 생성하여 두 응답 영역이 동일한 크기이고 콘텐츠가 넘치면 스크롤 가능하도록 합니다.
* **`for col, model_name, model_key in [...]`**: Model A 및 Model B에 대한 코드 중복을 제거하는 **튜플 언패킹을 사용한 루프 패턴**입니다. 각 반복은 해당 모델의 열, 모델 이름 및 키를 언패킹합니다.
* **`st.caption("Performance Metrics")`**: 숫자가 무엇을 나타내는지 레이블을 지정하기 위해 메트릭 위에 **작은 캡션을 추가**합니다.
* **플레이스홀더 메트릭**: 아직 결과가 없을 때 빈 상태를 나타내기 위해 지연 시간 및 토큰 모두에 대해 "—"를 표시합니다.

#### 3. 순차 실행 및 표시

```python
# Chat input and execution
st.divider()
if prompt := st.chat_input("Enter your message to compare models"):
    # Run models sequentially (Model A, then Model B)
    with st.status(f"Running {model_a}..."):
        result_a = run_model(model_a, prompt)
    with st.status(f"Running {model_b}..."):
        result_b = run_model(model_b, prompt)

    # Store results in session state (replaces previous results)
    st.session_state.latest_results = {"prompt": prompt, "model_a": result_a, "model_b": result_b}
    st.rerun()  # Trigger rerun to display results

# Display helper functions
def display_response(container, results: dict, model_key: str):
    """Display chat messages in container."""
    with container:
        with st.chat_message("user"):
            st.write(results["prompt"])
        with st.chat_message("assistant"):
            st.write(results[model_key]["response_text"])

def display_metrics(results: dict, model_key: str):
    """Display metrics for a model."""
    latency_col, tokens_col = st.columns(2)

    latency_col.metric("Latency (s)", f"{results[model_key]['latency']:.1f}")
    tokens_col.metric("Tokens", results[model_key]['tokens'])
```

* **`if prompt := st.chat_input(...)`**: 화면 하단에 **채팅 입력 상자를 생성**합니다. 바다코끼리 연산자(`:=`)는 한 줄에서 값을 할당하고 확인합니다.
* **`st.divider()`**: 결과 위의 입력 영역을 명확하게 구분하기 위해 채팅 입력 전에 **시각적 구분선을 생성**합니다.
* **순차 실행 주석**: 인라인 주석 **"Run models sequentially (Model A, then Model B)"**는 학습자를 위해 실행 순서를 명확히 합니다.
* **`with st.status(f"Running {model_a}...\")`**: 내부 코드가 실행되는 동안 "Running model_name..."을 표시하는 **상태 표시기를 생성**하여 대기 중에 사용자에게 시각적 피드백을 제공합니다.
* **순차 실행**: **Model A를 완전히 실행하고 결과를 기다린 다음 Model B를 실행**합니다. 총 시간은 두 모델의 지연 시간의 합입니다. 이것은 병렬 실행보다 느리지만 구현하고 이해하기가 훨씬 간단합니다.
* **`st.session_state.latest_results = {...}`**: 이전 결과를 대체한다는 것을 설명하는 인라인 주석과 함께 **세션 상태에 결과를 저장**하므로 학습자는 최신 프롬프트 및 응답만 유지된다는 것을 이해합니다(전체 채팅 히스토리가 아님).
* **`st.rerun()`**: 컨테이너에 새로 저장된 결과를 표시하기 위해 **재실행을 트리거**합니다. 인라인 주석 "Trigger rerun to display results"는 이것이 왜 필요한지 명확히 합니다.
* **`display_response()` 및 `display_metrics()`**: Model A 및 Model B에 대해 동일한 코드를 반복하지 않는 **헬퍼 함수**입니다.
* **`st.chat_message("user")` 및 `st.chat_message("assistant")`**: 채팅 인터페이스처럼 보이는 **스타일이 지정된 메시지 버블을 생성**합니다.
* **`latency_col, tokens_col = st.columns(2)`**: 두 메트릭을 나란히 표시하기 위해 **의미 있는 이름으로 두 열을 생성**합니다.
* **`latency_col.metric("Latency (s)", ...)`**: 가독성을 위해 소수점 이하 1자리로 **지연 시간 메트릭을 표시**합니다(예: "3.234567s" 대신 "3.2s").
* **`tokens_col.metric("Tokens", ...)`**: 응답 길이 및 비용에 대한 감각을 제공하는 정수로 **추정 토큰 수를 표시**합니다.

이 코드를 실행하면 8개 옵션에서 두 모델을 선택하고, 프롬프트를 입력하고, 응답 속도 및 출력 길이 측면에서 어떻게 비교되는지 즉시 볼 수 있는 깔끔한 비교 인터페이스를 볼 수 있습니다.
