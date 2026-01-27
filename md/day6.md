오늘의 챌린지 목표는 **"LinkedIn 게시물 생성기" 웹 앱**의 v2를 구축하는 것입니다. 여기서는 **Streamlit 프런트엔드**를 **Snowflake의 Cortex AI**와 통합하여 사용자 정의 매개변수를 기반으로 텍스트를 생성합니다. 특히 이 도구는 Claude 3.5 Sonnet 모델을 사용하여 소셜 미디어 콘텐츠 초안을 작성합니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 연결 및 AI 함수 래퍼

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

@st.cache_data
def call_cortex_llm(prompt_text):
    """Makes a call to Cortex AI with the given prompt."""
    model = "claude-3-5-sonnet"
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt_text).alias("response")
    )
    response_raw = df.collect()[0][0]
    return json.loads(response_raw)
```

* **`get_active_session()`**: Snowflake 데이터베이스 환경에 대한 현재 연결을 검색하여 앱이 데이터 및 AI 서비스에 액세스할 수 있도록 합니다.
* **`try/except` 블록**: 환경을 자동으로 감지하고 적절하게 연결합니다(SiS, 로컬, Community Cloud에서 작동).
* **`@st.cache_data`**: 함수 결과를 캐시하는 Streamlit 데코레이터입니다. 동일한 프롬프트가 두 번 전송되면 AI를 다시 호출하는 대신 캐시에서 데이터를 다시 로드하여 시간과 컴퓨팅 크레딧을 절약합니다.
* **`session.range(1).select(...)`**: 스칼라 함수를 실행하는 Snowpark 패턴입니다. `ai_complete` 함수를 실행하기 위해 단일 행 DataFrame을 생성합니다.
* **`ai_complete`**: 텍스트를 생성하기 위해 프롬프트를 Snowflake Cortex(Claude 3.5 모델 사용)로 전송하는 핵심 함수입니다.

#### 2. 사용자 인터페이스 구축

```python
st.title(":material/post: LinkedIn Post Generator v2")

content = st.text_input("Content URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")
tone = st.selectbox("Tone:", ["Professional", "Casual", "Funny"])
word_count = st.slider("Approximate word count:", 50, 300, 100)
```

* **`st.title`**: 앱의 메인 헤더를 설정합니다.
* **`st.text_input`**: 사용자가 게시물에 대한 소스 URL을 붙여넣을 수 있는 필드를 생성합니다.
* **`st.selectbox`**: 게시물의 톤에 대한 특정 옵션으로 사용자를 제한하는 드롭다운 메뉴를 제공합니다.
* **`st.slider`**: 사용자가 출력 길이에 대한 특정 숫자 범위를 선택할 수 있습니다.

#### 3. 실행 및 상태 관리



```python
if st.button("Generate Post"):
    with st.status("Starting engine...", expanded=True) as status:
        
        st.write(":material/psychology: Thinking: Analyzing constraints and tone...")
        prompt = f"""...""" # (Prompt construction omitted for brevity)
        
        st.write(":material/flash_on: Generating: contacting Snowflake Cortex...")
        response = call_cortex_llm(prompt)
        
        st.write(":material/check_circle: Post generation completed!")
        status.update(label="Post Generated Successfully!", state="complete", expanded=False)

    st.subheader("Generated Post:")
    st.markdown(response)
```

* **`if st.button("Generate Post"):`**: 이 블록 내부의 로직은 사용자가 물리적으로 버튼을 클릭할 때만 실행됩니다.
* **`with st.status(...)`**: AI가 처리하는 동안 사용자에게 시각적 피드백(스피너 등)을 제공하는 컨테이너를 생성하여 앱이 "정지된" 것처럼 보이지 않도록 합니다.
* **`prompt = f"""..."""`**: Python f-문자열을 사용하여 사용자의 특정 변수(톤, 길이, URL)를 AI에 대한 지침에 삽입하는 동적 문자열을 구성합니다.
* **`status.update(...)`**: 데이터가 준비되면 상태 컨테이너의 시각적 상태를 "완료"로 변경하고 축소합니다.
* **`st.markdown(response)`**: AI가 반환한 최종 텍스트를 화면에 렌더링하여 굵게 표시하거나 목록과 같은 형식을 지원합니다.

이 코드가 실행되면 매개변수를 입력하고 "Generate"를 클릭하면 실시간으로 형식화된 LinkedIn 게시물이 생성되는 사이드바 없는 웹 인터페이스가 표시됩니다.

---

### :material/library_books: 리소스
- [st.status 문서](https://docs.streamlit.io/develop/api-reference/status/st.status)
- [LangChain을 사용한 LLM 앱 구축](https://docs.streamlit.io/develop/tutorials/llms/llm-quickstart)
