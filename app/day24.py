# Day 24
# 이미지 작업 (멀티모달리티) (Working with Images)

import streamlit as st
import io
import time

st.title(":material/image: AI를 활용한 이미지 분석 (Image Analysis with AI)")
st.write("이미지를 업로드하고 Snowflake의 `AI_COMPLETE` 함수를 사용하여 분석합니다.")

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 상태 초기화
if "image_database" not in st.session_state:
    st.session_state.image_database = "RAG_DB"
    st.session_state.image_schema = "RAG_SCHEMA"

# 세션 상태에서 스테이지 경로 가져오기
database = st.session_state.image_database
schema = st.session_state.image_schema
full_stage_name = f"{database}.{schema}.IMAGE_ANALYSIS"
stage_name = f"@{full_stage_name}"

# 사이드바
with st.sidebar:
    st.header(":material/settings: 설정 (Settings)")
    
    with st.expander("데이터베이스 구성", expanded=False):
        database = st.text_input("Database", value=st.session_state.image_database, key="img_db_input")
        schema = st.text_input("Schema", value=st.session_state.image_schema, key="img_schema_input")
        
        if database != st.session_state.image_database or schema != st.session_state.image_schema:
            st.session_state.image_database = database
            st.session_state.image_schema = schema
            st.rerun()
    
    # 모델 선택
    model = st.selectbox(
        "모델 선택",
        ["claude-3-5-sonnet", "openai-gpt-4.1", "openai-o4-mini", "pixtral-large"],
        help="비전 기능이 있는 모델을 선택하세요"
    )
    
    # 스테이지 상태
    with st.expander("스테이지 상태 (Stage Status)", expanded=False):
        database = st.session_state.image_database
        schema = st.session_state.image_schema
        full_stage_name = f"{database}.{schema}.IMAGE_ANALYSIS"
        stage_name = f"@{full_stage_name}"
        
        try:
            # 스테이지 존재 확인
            stage_info = session.sql(f"SHOW STAGES LIKE 'IMAGE_ANALYSIS' IN {database}.{schema}").collect()
            
            if stage_info:
                # 스테이지가 존재하면 드롭하고 다시 생성하여 올바른 암호화 확인
                st.info(f":material/autorenew: 서버 측 암호화로 스테이지 재생성 중...")
                session.sql(f"DROP STAGE IF EXISTS {full_stage_name}").collect()
            
            # 서버 측 암호화로 스테이지 생성 (이미지와 함께 AI_COMPLETE 사용 시 필수)
            session.sql(f"""
            CREATE STAGE {full_stage_name}
                DIRECTORY = ( ENABLE = true )
                ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
            """).collect()
            st.success(f":material/check_box: 이미지 스테이지 준비됨")
            
        except Exception as e:
            st.error(f":material/cancel: 스테이지를 생성할 수 없습니다")
            
            with st.expander(":material/build: 수동 수정"):
                st.code(f"""
DROP STAGE IF EXISTS {full_stage_name};
CREATE STAGE {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );
                """, language="sql")

# 파일 업로더 컨테이너
with st.container(border=True):
    st.subheader(":material/upload: 이미지 업로드 (Upload an Image)")
    uploaded_file = st.file_uploader(
        "이미지 선택", 
        type=["jpg", "jpeg", "png", "gif", "webp"],
        help="지원 형식: JPG, JPEG, PNG, GIF, WebP (최대 10 MB)"
    )

    if uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(uploaded_file, caption="내 이미지", use_container_width=True)
        
        with col2:
            st.write(f"**파일:** {uploaded_file.name}")
            
            # 파일 크기 형식 지정
            size_bytes = uploaded_file.size
            if size_bytes >= 1_048_576:  # 1 MB = 1,048,576 bytes
                size_display = f"{size_bytes / 1_048_576:.2f} MB"
            elif size_bytes >= 1_024:  # 1 KB = 1,024 bytes
                size_display = f"{size_bytes / 1_024:.2f} KB"
            else:
                size_display = f"{size_bytes} bytes"
            
            st.write(f"**크기:** {size_display}")
        
        # 분석 유형 선택 (버튼 위)
        analysis_type = st.selectbox("분석 유형:", [
            "General description",
            "Extract text (OCR)",
            "Identify objects",
            "Analyze chart/graph",
            "Custom prompt"
        ])
        
        # 선택 시 사용자 지정 프롬프트 입력
        custom_prompt = None
        if analysis_type == "Custom prompt":
            custom_prompt = st.text_area(
                "프롬프트 입력:",
                placeholder="이 이미지에 대해 무엇을 알고 싶으신가요?",
                help="이미지 내용에 대해 무엇이든 물어보세요"
            )
        
        if st.button(":material/search: 이미지 분석 (Analyze Image)", type="primary"):
            # 분석 유형에 따라 프롬프트 생성
            if analysis_type == "General description":
                prompt = "Describe this image in detail. What do you see?"
            elif analysis_type == "Extract text (OCR)":
                prompt = "Extract all text visible in this image. Return only the text content."
            elif analysis_type == "Identify objects":
                prompt = "List all objects and items you can identify in this image. Be specific and comprehensive."
            elif analysis_type == "Analyze chart/graph":
                prompt = "Analyze this chart or graph. Describe the data, trends, and key insights."
            elif analysis_type == "Custom prompt" and custom_prompt:
                prompt = custom_prompt
            else:
                st.warning("사용자 지정 프롬프트를 입력하세요.")
                st.stop()
            
            with st.spinner(":material/upload: 이미지를 Snowflake 스테이지에 업로드 중..."):
                try:
                    # 고유 파일 이름 생성
                    timestamp = int(time.time())
                    file_extension = uploaded_file.name.split('.')[-1]
                    filename = f"image_{timestamp}.{file_extension}"
                    
                    # 스테이지에 업로드
                    image_bytes = uploaded_file.getvalue()
                    image_stream = io.BytesIO(image_bytes)
                    
                    session.file.put_stream(
                        image_stream,
                        f"{stage_name}/{filename}",
                        overwrite=True,
                        auto_compress=False
                    )
                    
                except Exception as e:
                    st.error(f"이미지 업로드 실패: {str(e)}")
                    st.stop()
            
            with st.spinner(f":material/psychology: {model}로 분석 중..."):
                try:
                    # [실습] Snowflake의 AI_COMPLETE 함수를 사용하여 이미지를 분석하세요.
                    # 힌트: SNOWFLAKE.CORTEX.AI_COMPLETE(model, prompt, TO_FILE(stage_name, filename))
                    
                    sql_query = f"""
                    SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
                        '{model}',
                        '{prompt.replace("'", "''")}',
                        TO_FILE('{stage_name}', '{filename}')
                    ) as analysis
                    """
                    
                    # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
                    # result = session.sql(sql_query).collect()
                    # response = result[0]['ANALYSIS']
                    
                    # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요.
                    response = "실습 코드를 완성하여 분석 결과를 보십시오." # 이 부분을 수정하세요
                    pass

                    # [실습 정답용 코드 - 학생에게 제공하지 않음 / 실제 동작을 위해 아래 코드를 사용하지만, 학생 버전에서는 가려야 합니다]
                    # result = session.sql(sql_query).collect()
                    # response = result[0]['ANALYSIS']
                    
                    # 세션 상태에 결과 저장
                    st.session_state.analysis_response = response
                    st.session_state.analysis_model = model
                    st.session_state.analysis_prompt = prompt
                    st.session_state.analysis_stage = stage_name
                    
                    # 참고: 스테이지된 파일은 스테이지에 남아 있습니다 (필요에 따라 수동으로 관리 가능)
                    
                except Exception as e:
                    st.error(f"분석 실패: {str(e)}")
                    st.info(":material/lightbulb: Snowflake 계정에 비전 기능이 있는 모델에 대한 액세스 권한이 있고 스테이지에 서버 측 암호화가 설정되어 있는지 확인하세요.")
                    st.stop()

# 별도 컨테이너에 결과 표시
if "analysis_response" in st.session_state:
    with st.container(border=True):
        st.subheader(":material/auto_awesome: 분석 결과 (Analysis Result)")
        st.markdown(st.session_state.analysis_response)
        
        with st.expander(":material/info: 기술 세부 정보 (Technical Details)"):
            st.write(f"**Model:** {st.session_state.analysis_model}")
            st.write(f"**Prompt:** {st.session_state.analysis_prompt}")
            st.write(f"**Stage:** {st.session_state.analysis_stage}")

# 파일이 업로드되지 않았을 때 정보 섹션
if not uploaded_file:
    st.info(":material/arrow_upward: 분석할 이미지를 업로드하세요!")
    
    st.subheader(":material/lightbulb: Vision AI가 할 수 있는 일")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- 사진 설명\n- 텍스트 읽기 (OCR)\n- 객체 식별")
    with col2:
        st.markdown("- 차트 분석\n- 레이아웃 이해\n- 예술 스타일 설명")

st.divider()
st.caption("Day 24: 이미지 작업 (멀티모달리티) (Working with Images) | 30 Days of AI")
