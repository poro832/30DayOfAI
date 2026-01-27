오늘의 챌린지 목표는 전문적인 **LinkedIn 게시물**을 생성하는 **Streamlit 웹 애플리케이션을 구축**하는 것입니다. Streamlit 앱 내에서 **Snowflake의 Cortex AI 함수를 호출**하여 URL, 원하는 톤, 길이와 같은 사용자가 제공한 입력을 기반으로 게시물 내용을 생성해야 합니다. 완료되면 **생성된 LinkedIn 게시물 텍스트**를 애플리케이션의 사용자 인터페이스에 표시합니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 설정 및 Snowflake Cortex AI 함수

```python
import streamlit as st
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

# Cached LLM Function
@st.cache_data
def call_cortex_llm(prompt_text):
    """Makes a call to Cortex AI with the given prompt."""
    model = "claude-3-5-sonnet"
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt_text).alias("response")
    )
    
    # Get and parse response
    response_raw = df.collect()[0][0]
    response_json = json.loads(response_raw)
    return response_json
```

* **`import streamlit as st`**: 웹 애플리케이션의 사용자 인터페이스와 로직을 만들기 위해 **Streamlit 라이브러리를 가져옵니다**.
* **`from snowflake...ai_complete`**: **`ai_complete` Snowpark 함수를 가져오며**, 이것은 **Snowflake Cortex AI(LLM)**와 상호 작용하는 핵심입니다.
* **`try/except` 블록**: **환경을 자동으로 감지**하고 적절하게 연결합니다(SiS, 로컬, Community Cloud에서 작동).
* **`session`**: 작업을 실행할 준비가 된 **설정된 Snowflake 연결**입니다.
* **`@st.cache_data...call_cortex_llm(prompt_text)`**: **LLM을 호출하는 함수를 정의**하고 **`@st.cache_data`**를 사용하여 결과를 캐시하여, 입력(`prompt_text`)이 동일하게 유지되는 한 앱이 업데이트될 때마다 비용이 많이 드는 AI 호출을 다시 실행하지 않도록 합니다.
* **`ai_complete(model=model, prompt=prompt_text)`**: 사용자의 프롬프트를 지정된 대규모 언어 모델(예: **`claude-3-5-sonnet`**)로 전송하고 생성된 텍스트를 반환하는 **Snowflake Cortex AI 호출**입니다.

#### 2. Streamlit UI 및 사용자 입력 구축

```python
# --- App UI ---
st.title("LinkedIn Post Generator")

# Input widgets
content = st.text_input("Content URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")
tone = st.selectbox("Tone:", ["Professional", "Casual", "Funny"])
word_count = st.slider("Approximate word count:", 50, 300, 100)

# Generate button
if st.button("Generate Post"):
```

* **`st.title(...)`**: 웹 애플리케이션의 **메인 제목을 설정**하여 앱이 무엇을 하는지 명확하게 합니다.
* **`st.text_input("Content URL:", ...)`**: 사용자가 LinkedIn 게시물에 대한 콘텐츠 URL을 붙여넣을 수 있는 **텍스트 필드를 생성**합니다.
* **`st.selectbox("Tone:", ...)`**: 사용자가 생성된 게시물의 원하는 톤을 선택할 수 있는 **드롭다운 메뉴를 제공**합니다.
* **`st.slider("Approximate word count:", ...)`**: 사용자가 최종 게시물의 대략적인 길이를 쉽게 제어할 수 있는 **슬라이더를 제공**합니다.
* **`if st.button("Generate Post"):`**: **버튼을 생성**합니다; `if` 문 내부의 코드 블록은 사용자가 이 버튼을 클릭할 때만 실행됩니다.

#### 3. 프롬프트 구성 및 출력 표시

```python
    # Construct the prompt
    prompt = f"""
    You are an expert social media manager. Generate a LinkedIn post based on the following:

    Tone: {tone}
    Desired Length: Approximately {word_count} words
    Use content from this URL: {content}

    Generate only the LinkedIn post text. Use dash for bullet points.
    """
    
    response = call_cortex_llm(prompt)
    st.subheader("Generated Post:")
    st.markdown(response)
```

* **`prompt = f"""..."""`**: **f-문자열**을 사용하여 **상세한 LLM 프롬프트를 구성**합니다. 이것은 중요한 단계로, 프롬프트에는 **사용자의 입력**(톤, 길이, URL)이 포함되며 출력 품질을 안내하기 위해 AI를 "전문 소셜 미디어 관리자"로 **역할극**합니다.
* **`response = call_cortex_llm(prompt)`**: 1단계의 **캐시된 함수를 호출**하여 완전한 프롬프트를 Snowflake Cortex AI 모델로 전송하고 생성된 게시물 텍스트를 받습니다.
* **`st.subheader("Generated Post:")`**: 사용자를 위해 출력 영역을 명확하게 구분하는 **작은 제목을 추가**합니다.
* **`st.markdown(response)`**: Streamlit의 `st.markdown`을 사용하여 **AI가 생성한 게시물 텍스트를 표시**하며, 이를 통해 AI가 포함한 경우 응답 텍스트를 Markdown 구문(굵은 텍스트 또는 글머리 기호 등)으로 형식화할 수 있습니다.

이 코드가 실행되면 입력과 버튼이 있는 간단한 웹 페이지가 표시됩니다. 버튼을 클릭하면 Snowflake를 통해 AI 호출이 실행되고 결과 LinkedIn 게시물이 버튼 아래에 표시됩니다.

---

### :material/library_books: 리소스
- [Snowflake Cortex LLM 함수](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [st.text_input 문서](https://docs.streamlit.io/develop/api-reference/widgets/st.text_input)
- [st.selectbox 문서](https://docs.streamlit.io/develop/api-reference/widgets/st.selectbox)
- [st.slider 문서](https://docs.streamlit.io/develop/api-reference/widgets/st.slider)
