# Day 3
# Write streams

import streamlit as st
from snowflake.cortex import Complete
import time

st.title(":material/airwave: Write Streams")

# Snowflake 연결
try:
    # SiS (Streamlit in Snowflake) 환경에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 개발 환경 및 Streamlit 커뮤니티 클라우드 환경에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

llm_models = ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"]
model = st.selectbox("모델 선택 (Select a model)", llm_models)

example_prompt = "Python에 대해 설명해 주세요."
prompt = st.text_area("프롬프트 입력 (Enter prompt)", example_prompt)

# 스트리밍 방식 선택
streaming_method = st.radio(
    "스트리밍 방식 (Streaming Method):",
    ["Direct (stream=True)", "Custom Generator"]
)

if st.button("Generate Response"):
    if streaming_method == "Direct (stream=True)":
        with st.spinner(f"`{model}` 모델로 응답 생성 중..."):
            # [실습] Complete 함수에 stream=True 옵션을 사용하여 스트리밍 객체를 생성하고 출력하세요.
            
            # 여기에 코드를 작성하세요
            pass
            
            # 힌트:
            # stream_generator = Complete(..., stream=True)
            # st.write_stream(stream_generator)
            
            st.info("코드를 완성하고 실행 버튼을 눌러주세요.")
            
    else:
        # Custom Generator 방식 (참고용)
        def custom_stream_generator():
            output = Complete(session=session, model=model, prompt=prompt)
            for chunk in output: # 실제로는 문자열을 쪼개는 로직이 필요할 수 있음
                yield chunk
                time.sleep(0.01)
        
        with st.spinner(f"`{model}` 모델로 응답 생성 중..."):
            st.write_stream(custom_stream_generator)

st.divider()
st.caption("Day 3: Write streams | 30 Days of AI")