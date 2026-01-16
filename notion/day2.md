# Day 2: Hello, Cortex!

# 0. 목표

<aside>
💡 **Streamlit에서 Snowflake Cortex LLM 실행하기**

1. `snowflake.snowpark.functions.ai_complete` 함수를 이해하고 활용합니다.
2. Streamlit UI를 통해 사용자 입력을 받고, LLM의 응답을 화면에 출력합니다.
3. Snowpark DataFrame을 이용해 LLM 추론을 실행하는 흐름을 익힙니다.

</aside>

# 1. 개념 및 이론 (Theory)

### Snowflake Cortex란?
Snowflake Cortex는 Snowflake 데이터 클라우드 내에서 바로 사용할 수 있는 완전 관리형 AI 서비스입니다. 별도의 GPU 서버를 구축하거나 복잡한 모델 배포 과정 없이, SQL이나 Python 함수 호출만으로 최첨단 LLM(Large Language Model)을 사용할 수 있습니다.

### 주요 개념
- **Serverless AI**: 인프라 관리 없이 API 호출처럼 AI 기능을 사용합니다.
- **Snowpark DataFrame**: Snowflake의 데이터를 파이썬에서 쉽게 다루기 위한 구조입니다. Cortex 함수는 이 DataFrame의 컬럼 단위 연산에 최적화되어 있습니다.

# 2. 단계별 구현 (Step-by-Step)

이 과정은 **Day 1**에서 설정한 개발 환경이 준비되어 있다고 가정합니다.

### Step 1: 파일 생성 및 라이브러리 임포트

프로젝트 폴더(예: `30DaysOfAI`) 내에 `day2.py` 파일을 생성하고 아래 코드를 작성합니다.

```python
import streamlit as st
from snowflake.snowpark.functions import ai_complete
import json

# 페이지 기본 설정
st.title("Day 2: Hello, Cortex! 👋")
```

### Step 2: Snowflake 연결

로컬 환경과 Snowflake 환경(SiS) 모두에서 동작하도록 연결 코드를 작성합니다. (Day 1에서 배운 내용입니다.)

```python
# Snowflake 세션 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except ImportError:
    from snowflake.snowpark import Session
    # secrets.toml 파일이 올바르게 설정되어 있어야 합니다.
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
```

### Step 3: UI 구성 및 모델 선택

사용자가 입력할 수 있는 공간과 사용할 모델을 정의합니다.

```python
st.subheader("Ask Cortex anything!")

# 사용할 Cortex 모델 지정 (현재 가장 성능이 좋은 모델 중 하나)
model = "claude-3-5-sonnet"

# 사용자 입력 받기
prompt = st.text_input("Enter your prompt:", placeholder="What implies Streamlit?")
```

### Step 4: Cortex LLM 실행 및 결과 출력

버튼을 눌렀을 때 Cortex를 호출하고 결과를 받아오는 핵심 로직입니다.

```python
if st.button("Generate Response"):
    if prompt:
        with st.spinner("Thinking..."):
            # 1. 더미 데이터프레임 생성 (1행)
            # 2. ai_complete 함수로 LLM 호출
            # 3. 결과를 'response'라는 이름의 컬럼으로 지정
            df = session.range(1).select(
                ai_complete(model, prompt).alias("response")
            )
            
            # 결과 수집 (DataFrame -> Python 객체)
            # collect()는 리스트를 반환하며, [0][0]으로 첫 번째 셀의 값을 가져옵니다.
            response_raw = df.collect()[0][0]
            
            # JSON 형태의 문자열을 파이썬 딕셔너리로 변환
            response_json = json.loads(response_raw)
            
            # 최종 텍스트 결과 출력 (choices 리스트의 첫 번째 항목의 messages 내용)
            # Cortex 응답 구조에 따라 파싱 방법이 달라질 수 있으므로 전체 JSON을 확인해보는 것이 좋습니다.
            st.markdown("### Answer:")
            st.write(response_json) # 전체 응답 구조 확인용
            
            # 텍스트만 깔끔하게 보고 싶다면:
            # st.write(response_json['choices'][0]['messages']) 
    else:
        st.warning("Please enter a prompt first.")
```

# 3. 핵심 포인트 (Key Takeaways)

- **DataFrame 통합**: `ai_complete`는 원래 테이블의 많은 행을 한 번에 처리하기 위해 설계되었습니다. 단일 응답을 위해 `session.range(1)`을 사용하여 1줄짜리 가상 테이블을 만드는 트릭을 사용했습니다.
- **JSON 파싱**: Cortex의 응답은 단순 텍스트가 아니라 메타데이터가 포함된 JSON 형식이므로 `json.loads`를 통해 파싱해야 합니다.
