오늘의 챌린지 목표는 Snowflake Cortex 대규모 언어 모델(LLM)을 호출하는 Streamlit 웹 애플리케이션을 만드는 것입니다. 사용자가 프롬프트를 입력하면 Snowflake 내부에서 안전하게 실행되는 강력한 AI 모델(Claude 3.5 Sonnet 등)로 전송하고 응답을 받는 인터페이스를 구축해야 합니다. 완료되면 요청에 걸린 시간과 함께 AI의 답변을 웹 앱에 직접 표시합니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 설정: 가져오기 및 세션

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
```

* `import ...`: 이 줄들은 필요한 모든 라이브러리를 가져옵니다: 웹 앱 UI를 위한 `streamlit`, 응답 속도 측정을 위한 `time`, LLM 출력을 파싱하기 위한 `json`, 그리고 Snowflake에 연결하고 AI 함수를 사용하기 위한 `snowpark` 구성 요소입니다.
* **`try/except` 블록**: 환경을 자동으로 감지하고 적절하게 연결하여 모든 배포 시나리오에서 작동합니다.

#### 2. Cortex LLM 호출 정의

```python
@st.cache_data
def call_cortex_llm(prompt_text):
    model = "claude-3-5-sonnet"
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt_text).alias("response")
    )
    
    # Get and parse response
    response_raw = df.collect()[0][0]
    response_json = json.loads(response_raw)
    return response_json
```

* `@st.cache_data`: 이것은 이 함수의 결과를 영리하게 저장하는 Streamlit "데코레이터"입니다. **처음으로** 프롬프트를 제출하면 LLM을 호출하고 3-5초가 걸릴 수 있습니다. **정확히 같은 프롬프트**를 다시 제출하면 Streamlit이 즉시 저장된 답변을 반환합니다(종종 0.1초 미만). 프롬프트에서 한 글자만 변경해도 캐시 누락이 되어 LLM이 다시 실행됩니다.
* `ai_complete(...)`: 핵심 Snowpark 함수입니다. Snowflake Cortex에서 실행되는 지정된 `model`(Claude 3.5 Sonnet)을 안전하게 호출하여 사용자의 `prompt_text`를 전달합니다. 이 함수는 `select` 문으로 래핑되어 있으며, 이는 Snowpark가 함수를 실행하는 방법입니다.
* `df.collect()[0][0]`: 쿼리를 실행합니다. `df.collect()`는 Snowflake에서 결과를 가져오는데, 이는 하나의 행(`[0]`)과 하나의 열(`[0]`)을 포함하는 목록입니다. 결과는 원시 텍스트 문자열입니다.
* `json.loads(response_raw)`: LLM의 원시 텍스트는 JSON이라는 형식입니다. 이 줄은 해당 텍스트를 "파싱" 또는 "로드"하여 구조화된 Python 딕셔너리로 만들어 내용에 쉽게 액세스할 수 있게 합니다.

#### 3. 웹 앱 인터페이스 구축

```python
prompt = st.text_input("Enter your prompt", "Why is the sky blue?")

if st.button("Submit"):
    start_time = time.time()
    response = call_cortex_llm(prompt)
    end_time = time.time()
    
    st.success(f"*Call took {end_time - start_time:.2f} seconds*")
    st.write(response)
```

* `st.text_input(...)`: 이 함수는 라벨("Enter your prompt")과 기본 텍스트("Why is the sky blue?")가 있는 텍스트 입력 상자를 웹 페이지에 그립니다. 사용자의 텍스트는 `prompt` 변수에 저장됩니다.
* `if st.button("Submit"):`: "Submit" 라벨이 있는 버튼을 그립니다. 아래 들여쓰기된 코드는 사용자가 이 버튼을 클릭할 때만 실행됩니다.
* `start_time = ...` / `end_time = ...`: 이 줄들은 LLM 함수를 호출하기 직전과 직후의 시간을 캡처하여 지속 시간을 계산할 수 있습니다.
* `response = call_cortex_llm(prompt)`: 2단계의 함수를 호출하여 사용자의 텍스트를 전달하는 곳입니다. 반환된 딕셔너리는 `response` 변수에 저장됩니다.
* `st.success(...)`: 경과 시간을 표시하는 녹색 상자를 보여줍니다.
* `st.write(response)`: 이 편리한 Streamlit 명령은 전체 `response` 딕셔너리를 페이지에 지능적으로 표시합니다.

이 코드가 실행되면 텍스트 상자와 버튼이 있는 간단한 웹 페이지가 표시됩니다. 프롬프트를 입력하고 "Submit"을 클릭하면 LLM의 응답이 아래에 나타납니다.

---

### :material/library_books: 리소스
- [st.cache_data 문서](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)
- [Streamlit의 캐싱](https://docs.streamlit.io/develop/concepts/architecture/caching)
- [SiS 캐싱 제한 사항](https://docs.snowflake.com/en/developer-guide/streamlit/limitations#st-cache-data-and-st-cache-resource-are-not-fully-supported)
