# Day 4: Caching your App

# 0. 목표

<aside>
💡 **앱의 성능을 높이고 비용을 절약하는 캐싱(Caching) 구현하기**

1. 동일한 질문에 대해 쓸데없이 LLM을 다시 호출하지 않도록 방지합니다.
2. Streamlit의 강력한 데코레이터 `@st.cache_data`를 활용합니다.
3. 실제 실행 시간을 측정하여 캐싱의 효과를 눈으로 확인합니다.

</aside>

# 1. 개념 및 이론 (Theory)

### 캐싱(Caching)이란?
캐싱은 한 번 계산한 결과나 불러온 데이터를 임시 저장소(Cache)에 보관해 두는 기술입니다. 다음에 똑같은 요청이 오면, 무거운 계산을 다시 하지 않고 저장해 둔 결과를 즉시 반환합니다.

### 왜 필요한가요?
1.  **비용 절감**: LLM 호출은 토큰당 비용이 듭니다. 같은 질문에 또 돈을 쓸 필요가 없습니다.
2.  **속도 향상**: LLM 응답은 수 초가 걸리지만, 캐시된 응답은 0.001초 만에 나옵니다.

![Cache Flow](https://mermaid.ink/img/pako:eNxlkMFqwzAMhl9F6NRC_QA9DBaGncYuu4zQxWmsNI5sZ2WU0nefkrVdSttJEvz6P1kn9CoNaoQfK3v2DoXh-6wM8uO6Wq836zWslvBQAQ-P5e317e0V1ou3dAmF-w1-7O_xY72D3eH6CI8H-H4qC6VCD9o59Cgo9J5aQ4vCCd2QU_tYy5_6O2q0h0_0M_rL6D_oBw5kDW1JkYwS52xxSjJOTFw482ySTJz4kIs0M2nmxCUvM5N1lU1zlmW5S7P8B6r7V6E?type=png)

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 파일 생성 및 기본 구조

`day4.py`를 생성하고 필요한 모듈을 임포트합니다.

```python
import streamlit as st
from snowflake.cortex import Complete
import time

st.title("Day 4: Super Fast Caching ⚡")
```

### Step 2: 캐싱 함수 만들기

이전 Day와 달리, LLM 호출 부분을 별도의 함수로 분리하고 **`@st.cache_data`** 데코레이터를 붙입니다. 이게 전부입니다!

```python
# Snowflake 세션 연결 (이전과 동일)
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except ImportError:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# ---------------------------------------------------------
# 핵심: @st.cache_data 데코레이터 사용
# ---------------------------------------------------------
@st.cache_data
def get_llm_response(prompt_text):
    """
    이 함수는 입력값(prompt_text)이 같으면 
    함수 내부 코드를 실행하지 않고 저장된 값을 반환합니다.
    """
    # 잠시 딜레이를 주어 캐싱 효과를 더 극적으로 비교해볼 수도 있습니다.
    # time.sleep(2) 
    
    return Complete("claude-3-5-sonnet", prompt_text, session=session)
```

### Step 3: 실행 시간 측정 및 UI

버튼을 누르면 시간을 재고 결과를 보여줍니다.

```python
prompt = st.text_input("Ask something:", "What represents the number 42?")

if st.button("Submit"):
    if prompt:
        # 시작 시간 기록
        start_completion = time.time()
        
        # 캐싱된 함수 호출
        # 처음에는 느리지만, 같은 질문을 두 번째 할 때는 매우 빠릅니다.
        response = get_llm_response(prompt)
        
        # 종료 시간 기록
        end_completion = time.time()
        time_taken = end_completion - start_completion
        
        st.markdown(f"**⏱️ Time taken:** `{time_taken:.4f}` seconds")
        st.write(response)
        
        # 팁 표시
        if time_taken < 0.1:
            st.success("⚡ Cache Hit! (저장된 결과를 가져왔습니다)")
        else:
            st.info("🐢 Cache Miss (새로 계산했습니다)")
```

# 3. 핵심 포인트 (Key Takeaways)

- **`@st.cache_data`**: 데이터(텍스트, 숫자, DataFrame 등)를 저장할 때 씁니다.
- **`@st.cache_resource`**: 데이터베이스 연결 객체나 ML 모델 같이 계속 유지해야 하는 무거운 리소스를 저장할 때 씁니다.
- **테스트 방법**: 앱을 실행하고 같은 질문을 두 번 연속으로 입력해보세요. 첫 번째는 2~3초가 걸리지만, 두 번째는 순식간에 결과가 뜰 것입니다.
