오늘의 챌린지 목표는 `snowflake.cortex.Complete` Python API를 사용하여 Snowflake Cortex LLM을 실행하는 것입니다. 사용자가 모델을 선택하고 프롬프트를 입력하면 응답을 스트리밍하는 Streamlit 앱을 만들어야 합니다. 완료되면 AI의 응답이 생성되는 대로 실시간으로 한 단어씩 표시합니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 가져오기 및 세션

```python
import streamlit as st
from snowflake.cortex import Complete
import time

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
```

* **`import streamlit as st`**: 웹 앱의 사용자 인터페이스(UI)를 구축하는 데 필요한 라이브러리를 가져옵니다.
* **`from snowflake.cortex import Complete`**: 핵심 가져오기입니다. SQL 함수 `ai_complete`를 사용하는 대신 Cortex SDK에서 직접 Python `Complete` 클래스를 가져옵니다. 이 클래스는 이러한 종류의 프로그래밍 방식 사용을 위해 설계되었습니다.
* **`import time`**: 부드러운 스트리밍을 위해 약간의 지연을 사용하는 사용자 지정 생성기 메서드를 위해 추가되었습니다.
* **`try/except` 블록**: 환경을 자동으로 감지하고 적절하게 연결합니다(SiS 대 로컬/Community Cloud).
* **`session`**: 설정된 Snowflake 연결입니다.

#### 2. 사용자 인터페이스 구성

```python
llm_models = ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"]
model = st.selectbox("Select a model", llm_models)

example_prompt = "What is Python?"
prompt = st.text_area("Enter prompt", example_prompt)

# Choose streaming method
streaming_method = st.radio(
    "Streaming Method:",
    ["Direct (stream=True)", "Custom Generator"],
    help="Choose how to stream the response"
)
```

* **`llm_models = [...]`**: 사용자가 선택할 수 있는 모델 이름의 Python 목록을 정의합니다.
* **`model = st.selectbox(...)`**: UI에 "Select a model" 라벨이 있는 드롭다운 메뉴를 생성합니다. 사용자의 선택은 `model` 변수에 저장됩니다.
* **`prompt = st.text_area(...)`**: 사용자의 프롬프트를 위한 여러 줄 텍스트 상자를 생성하고 `example_prompt`로 미리 채웁니다. 사용자의 최종 입력은 `prompt` 변수에 저장됩니다.
* **`streaming_method = st.radio(...)`**: 신규 - 사용자가 두 가지 스트리밍 방법 중에서 선택할 수 있도록 라디오 버튼을 추가하여 동작의 차이를 확인할 수 있게 합니다.

#### 3. LLM 응답 스트리밍

이 앱은 응답을 스트리밍하는 **두 가지 방법**을 보여줍니다:

**방법 1: 직접 스트리밍 (stream=True)**

```python
if st.button("Generate Response"):
    with st.spinner(f"Generating response with `{model}`"):
        stream_generator = Complete(
                    session=session,
                    model=model,
                    prompt=prompt,
                    stream=True,  # Built-in streaming
                )
            
        st.write_stream(stream_generator)
```

* **`stream=True`**: 가장 간단한 접근 방식입니다. `Complete`에게 토큰이 도착하는 대로 생성하는 생성기를 반환하도록 지시합니다.
* **작동 조건**: API의 스트리밍이 `st.write_stream()`과 직접 호환될 때 사용합니다.

**방법 2: 사용자 지정 생성기 (호환성 모드)**

```python
def custom_stream_generator():
    """
    Alternative streaming method for cases where
    the generator is not compatible with st.write_stream
    """
    output = Complete(
        session=session,
        model=model,
        prompt=prompt  # No stream parameter
    )
    for chunk in output:
        yield chunk
        time.sleep(0.01)  # Small delay for smooth streaming

with st.spinner(f"Generating response with `{model}`"):
    st.write_stream(custom_stream_generator)
```

* **사용 시기**: `stream=True`가 `st.write_stream()`과 작동하지 않는 경우(예: 대화 기록 또는 특정 API 응답과의 호환성 문제).
* **작동 방식**: 시각적으로 부드러운 스트리밍을 위해 약간의 지연과 함께 청크를 수동으로 생성하는 Python 생성기 함수를 만듭니다.
* **Docstring**: 이 대체 방법이 왜 존재하는지 문서화합니다(직접 방법이 작동하지 않을 때의 호환성을 위해).
* **모범 사례**: 챗봇 및 복잡한 프롬프트에 대해 더 안정적인 방법입니다(나중에 살펴보겠습니다).

> :material/lightbulb: **스트리밍이 중요한 이유:** 스트리밍이 없으면 사용자는 LLM이 전체 응답을 생성하는 동안 몇 초 동안 빈 화면을 응시해야 합니다. 스트리밍을 사용하면 단어가 즉시 나타나므로 총 시간은 같더라도 앱이 더 빠르고 반응성이 좋게 느껴집니다.

---

### :material/library_books: 리소스
- [Cortex Complete Python API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#complete)
- [st.write_stream 문서](https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream)
