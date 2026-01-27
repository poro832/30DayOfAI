오늘의 챌린지 목표는 Snowflake 내에서 직접 대규모 언어 모델(LLM)을 실행하는 것입니다. 사용자의 프롬프트를 받아 Snowflake Cortex `AI_COMPLETE` 함수로 전송하고 응답을 받는 간단한 Streamlit 인터페이스를 만들어야 합니다. 완료되면 AI가 생성한 응답을 앱에서 사용자에게 다시 표시합니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 필수 라이브러리 설치

앞으로의 레슨에서는 Snowflake의 Cortex AI를 활용할 예정이므로 다음 필수 라이브러리를 설치해 주세요:
```
snowflake-ml-python==1.20.0
snowflake-snowpark-python==1.44.0
```

##### 로컬 환경

위 내용을 `requirements.txt`에 저장하고 `pip install -r requirements.txt`를 실행하세요.

또는 `pip install snowflake-ml-python==1.20.0 snowflake-snowpark-python==1.44.0`을 실행할 수도 있습니다.

##### Streamlit Community Cloud

위 내용을 `requirements.txt`에 저장하고 앱의 GitHub 리포지토리에 포함시키세요.

##### Streamlit in Snowflake

**Packages** 드롭다운을 클릭하고 다음과 같이 라이브러리 이름을 입력하세요:
![](https://github.com/streamlit/30DaysOfAI/blob/main/assets/sis_install_prerequisite_libraries.png?raw=true)

#### 1. 라이브러리 가져오기 및 연결

```python
import streamlit as st
from snowflake.snowpark.functions import ai_complete
import json

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

* **`import streamlit as st`**: 웹 앱의 사용자 인터페이스(UI)를 구축하는 데 사용되는 Streamlit 라이브러리를 가져옵니다.
* **`from snowflake.snowpark.functions ...`**: LLM 추론을 실행할 특정 Cortex AI 함수 `ai_complete`를 가져옵니다.
* **`try/except` 블록**: 환경을 자동으로 감지하고 적절한 연결 방법을 사용합니다:
  * **Streamlit in Snowflake (SiS)**: 자동 인증을 위해 `get_active_session()`을 사용합니다.
  * **로컬 또는 Streamlit Community Cloud**: `.streamlit/secrets.toml`의 자격 증명을 사용하여 `Session.builder`를 사용합니다.
* **`session`**: 쿼리를 실행하고 Cortex AI 함수를 호출할 준비가 된 설정된 Snowflake 연결입니다.

> :material/lightbulb: **왜 `ai_complete()`인가요?** 여기서는 Snowpark DataFrame과 자연스럽게 통합되는 Snowpark `ai_complete()` 함수를 사용합니다. 이 접근 방식은 DataFrame 파이프라인에서 데이터를 처리하거나 SQL과 유사한 워크플로의 일부로 응답이 필요할 때 이상적입니다. 단점은 파싱이 필요한 JSON을 반환하고 스트리밍을 지원하지 않는다는 것입니다. 3일차에서는 직접 호출에 더 간단하고 스트리밍을 지원하는 Python `Complete()` API를 살펴볼 것입니다.

#### 2. 모델 및 UI 설정

```python
# Model and prompt
model = "claude-3-5-sonnet"
prompt = st.text_input("Enter your prompt:")
```

* **`model = "claude-3-5-sonnet"`**: Snowflake Cortex에서 사용할 수 있는 모델 중 어떤 LLM을 사용할지 지정하는 변수를 설정합니다.
* **`prompt = st.text_input(...)`**: "Enter your prompt:" 라벨이 있는 텍스트 입력 상자를 Streamlit UI에 생성합니다. 사용자가 입력하는 내용은 `prompt` 변수에 저장됩니다.

#### 3. 버튼 클릭 시 추론 실행

```python
# Run LLM inference
if st.button("Generate Response"):
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt).alias("response")
    )
```

* **`if st.button(...)`**: UI에 버튼을 생성합니다. 이 `if` 블록 내부의 코드는 사용자가 "Generate Response" 버튼을 클릭할 때만 실행됩니다.
* **`df = session.range(1).select(...)`**: 이 패턴은 이상해 보일 수 있습니다! 함수를 실행하고 출력을 캡처하기 위해 단일 셀 스프레드시트를 만드는 것과 같다고 생각하세요. `session.range(1)`은 1행 "스프레드시트"를 생성하고, `.select()`는 AI 함수를 실행하여 결과를 열에 넣습니다.
* **`ai_complete(...)`**: 핵심 호출입니다. Snowflake에 사용자의 `prompt`를 사용하여 지정된 `model`을 실행하도록 지시합니다.
* **`.alias("response")`**: 더 쉽게 액세스할 수 있도록 출력 열의 이름을 "response"로 변경합니다. 결과는 `df`라는 Snowpark DataFrame에 저장됩니다.

#### 4. 결과 가져오기 및 표시

```python
    # Get and display response
    response_raw = df.collect()[0][0]
    response = json.loads(response_raw)
    st.write(response)
```

* **`response_raw = df.collect()[0][0]`**: `.collect()` 명령은 Snowflake에서 쿼리를 실행하고 DataFrame `df`의 데이터를 앱으로 다시 가져옵니다. `[0][0]`은 첫 번째 행과 첫 번째 열에서 실제 값을 분리합니다.
* **`response = json.loads(response_raw)`**: `ai_complete()`의 원시 응답은 `'{"choices":[{"messages":"Hello! How can I help you?"}]}'`와 같습니다. 이것은 일반 텍스트가 아니라 JSON 문자열입니다! 이 줄은 실제 메시지 내용에 쉽게 액세스할 수 있도록 Python 딕셔너리로 파싱합니다.
* **`st.write(response)`**: 사용자가 볼 수 있도록 최종 파싱된 응답을 Streamlit 앱에 표시합니다.

---

### :material/library_books: 리소스
- [Snowflake Cortex LLM 함수](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [COMPLETE 함수 참조](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
- [사용 가능한 LLM 모델](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability)
