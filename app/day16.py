# Day 16
# RAG를 위한 배치 문서 텍스트 추출기 (Batch Document Text Extractor for RAG)

import streamlit as st
from pypdf import PdfReader
import io
import pandas as pd
from datetime import datetime

# Snowflake 연결 설정
# Snowflake에 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

st.title(":material/description: 배치 문서 텍스트 추출기 (Batch Document Text Extractor)")
st.write("여러 문서를 한 번에 업로드하여 텍스트를 추출하고 RAG 애플리케이션을 위해 Snowflake에 저장합니다.")

# 데이터베이스 구성을 위한 세션 상태 초기화
if 'database' not in st.session_state:
    st.session_state.database = "RAG_DB"
if 'schema' not in st.session_state:
    st.session_state.schema = "RAG_SCHEMA"
if 'table_name' not in st.session_state:
    st.session_state.table_name = "EXTRACTED_DOCUMENTS"

# 메인 구성 컨테이너
with st.container(border=True):
    st.subheader(":material/analytics: 데이터베이스 설정 (Database Setup)")

    # 데이터베이스 구성
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.database = st.text_input("Database", value=st.session_state.database, key="db_input")
    with col2:
        st.session_state.schema = st.text_input("Schema", value=st.session_state.schema, key="schema_input")
    with col3:
        st.session_state.table_name = st.text_input("Table Name", value=st.session_state.table_name, key="table_input")
    
    st.info(f":material/location_on: 저장 위치: `{st.session_state.database}.{st.session_state.schema}.{st.session_state.table_name}`")
    st.caption(":material/lightbulb: 문서를 저장할 때 데이터베이스가 자동으로 생성됩니다.")
    
    st.divider()
    
    # 리뷰 데이터 다운로드 섹션
    st.subheader(":material/download: 리뷰 데이터 다운로드 (Download Review Data)")
    st.write("빠르게 시작하려면 Avalanche 겨울 스포츠 장비의 고객 리뷰 샘플 데이터셋(100개)을 다운로드하세요.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(":material/info: **샘플 데이터셋**: 제품 피드백, 감성 점수, 주문 정보가 포함된 100개의 고객 리뷰 파일 (TXT 형식).")
    with col2:
        st.link_button(
            ":material/download: review.zip 다운로드",
            "https://github.com/streamlit/30DaysOfAI/raw/refs/heads/main/assets/review.zip",
            use_container_width=True
        )
    
    with st.expander(":material/help: 샘플 데이터 사용 방법"):
        st.markdown("""
        **단계:**
        1. 위의 **review.zip 다운로드** 버튼을 클릭하세요.
        2. 다운로드한 파일의 압축을 푸세요.
        3. 아래 **문서 업로드 (Upload Documents)** 섹션을 사용하여 100개의 리뷰 파일을 모두 선택하세요.
        4. **텍스트 추출 (Extract Text)**을 클릭하여 처리하고 Snowflake에 저장하세요.
        
        **포함 내용:**
        - 100개의 고객 리뷰 파일 (`review-001.txt` ~ `review-100.txt`)
        - 각 리뷰 포함 내용: 제품명, 날짜, 리뷰 요약, 감성 점수, 주문 ID
        - 배치 처리 테스트 및 RAG 애플리케이션 구축에 최적화됨
        
        **팁:** 최적의 배치 처리를 위해 100개의 파일을 한 번에 업로드할 수 있습니다!
        """)
    
    st.divider()
    
    # 파일 업로더
    st.subheader(":material/upload: 문서 업로드 (Upload Documents)")
    uploaded_files = st.file_uploader(
        "파일 선택",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
        help="지원 형식: TXT, MD, PDF. 여러 파일을 한 번에 업로드하세요!"
)

    # 테이블이 존재하는지 확인하여 replace_mode 기본값 설정
    table_exists = False
    try:
        check_result = session.sql(f"""
            SELECT COUNT(*) as CNT FROM {st.session_state.database}.{st.session_state.schema}.{st.session_state.table_name}
        """).collect()
        table_exists = True  # 쿼리가 성공하면 테이블이 존재함
    except:
        table_exists = False  # 테이블이 존재하지 않음
    
    # 테이블 존재 여부에 따라 체크박스 값 설정
    replace_mode = st.checkbox(
        f":material/sync: `{st.session_state.table_name}` 테이블 교체 모드 (Replace Table Mode)",
        value=table_exists,  # 테이블이 존재하면 True, 아니면 False
        help=f"활성화하면 새 문서를 저장하기 전에 {st.session_state.database}.{st.session_state.schema}.{st.session_state.table_name}의 모든 기존 데이터를 지웁니다."
    )
    
    if replace_mode:
        st.warning(f":material/warning: **교체 모드 활성화됨** - 새 문서를 저장하기 전에 `{st.session_state.table_name}`의 모든 기존 문서가 삭제됩니다.")
    else:
        st.info(f":material/add: **추가 모드** - 새 문서가 `{st.session_state.table_name}`에 추가됩니다.")

# 코드의 나머지 부분에서 사용하기 위해 세션 상태에서 값 가져오기
database = st.session_state.database
schema = st.session_state.schema
table_name = st.session_state.table_name

# 업로드 정보 표시
if uploaded_files:
    with st.container(border=True):
        st.subheader(":material/upload: 업로드된 문서 (Uploaded Documents)")
        st.success(f":material/folder: {len(uploaded_files)}개의 파일이 업로드되었습니다.")
        
        # 선택된 파일 미리보기
        with st.expander(":material/assignment: 선택된 파일 보기", expanded=False):
            file_list_df = pd.DataFrame([
                {
                    "File Name": f.name,
                    "Size": f"{f.size:,} bytes",
                    "Type": "TXT" if f.name.lower().endswith('.txt') 
                           else "Markdown" if f.name.lower().endswith('.md')
                           else "PDF" if f.name.lower().endswith('.pdf')
                           else "Unknown"
                }
                for f in uploaded_files
            ])
            st.dataframe(file_list_df, use_container_width=True)
        
        # 파일 처리 버튼
        process_button = st.button(
            f":material/sync: {len(uploaded_files)}개 파일에서 텍스트 추출",
            type="primary",
            use_container_width=True
        )
    
    if process_button:
        # 진행 상황 추적 초기화
        success_count = 0
        error_count = 0
        extracted_data = []
        
        progress_bar = st.progress(0, text="추출 시작 중...")
        status_container = st.empty()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            progress_pct = (idx + 1) / len(uploaded_files)
            progress_bar.progress(progress_pct, text=f"처리 중 {idx+1}/{len(uploaded_files)}: {uploaded_file.name}")
            
            try:
                # 확장자로 파일 유형 결정
                if uploaded_file.name.lower().endswith('.txt'):
                    file_type = "TXT"
                elif uploaded_file.name.lower().endswith('.md'):
                    file_type = "Markdown"
                elif uploaded_file.name.lower().endswith('.pdf'):
                    file_type = "PDF"
                else:
                    file_type = "Unknown"
                
                # 파일 포인터 리셋
                uploaded_file.seek(0)
                
                # 파일 유형에 따라 텍스트 추출
                extracted_text = ""
                
                if uploaded_file.name.lower().endswith(('.txt', '.md')):
                    # TXT 및 Markdown 파일 처리
                    extracted_text = uploaded_file.read().decode("utf-8")
                
                elif uploaded_file.name.lower().endswith('.pdf'):
                    # PDF 파일 처리
                    pdf_reader = PdfReader(io.BytesIO(uploaded_file.read()))
                    
                    # 모든 페이지에서 텍스트 추출
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text + "\n\n"
                
                # 추출 성공 여부 확인
                if extracted_text and extracted_text.strip():
                    # 메타데이터 계산
                    word_count = len(extracted_text.split())
                    char_count = len(extracted_text)
                    
                    # 추출된 데이터 저장
                    extracted_data.append({
                        'file_name': uploaded_file.name,
                        'file_type': file_type,
                        'file_size': uploaded_file.size,
                        'extracted_text': extracted_text,
                        'word_count': word_count,
                        'char_count': char_count
                    })
                    
                    success_count += 1
                else:
                    error_count += 1
                    status_container.warning(f":material/warning: 텍스트가 추출되지 않음: {uploaded_file.name}")
                    
            except Exception as e:
                error_count += 1
                status_container.error(f":material/cancel: {uploaded_file.name} 처리 중 오류 발생: {str(e)}")
        
        progress_bar.empty()
        status_container.empty()
        
        # 결과 표시
        with st.container(border=True):
            st.subheader(":material/analytics: 데이터베이스 테이블에 기록된 문서 (Documents Written to a Database Table)")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(":material/check_circle: 성공", success_count)
            with col2:
                st.metric(":material/cancel: 실패", error_count)
            with col3:
                st.metric(":material/analytics: 총 단어 수", f"{sum(d['word_count'] for d in extracted_data):,}")
            
            # 리뷰를 위해 세션 상태에 저장
            if extracted_data:
                st.session_state.extracted_data = extracted_data
                st.success(f":material/check_circle: {success_count}개 파일에서 텍스트를 성공적으로 추출했습니다!")
                
                # 추출된 데이터 미리보기
                with st.expander(":material/visibility: 처음 3개 파일 미리보기"):
                    for data in extracted_data[:3]:
                        with st.container(border=True):
                            st.markdown(f"**{data['file_name']}**")
                            st.caption(f"{data['word_count']:,} words")
                            preview_text = data['extracted_text'][:200]
                            if len(data['extracted_text']) > 200:
                                preview_text += "..."
                            st.text(preview_text)
                    
                    if len(extracted_data) > 3:
                        st.caption(f"... 그리고 {len(extracted_data) - 3}개 더")
                
                # Snowflake에 저장
                with st.status("Snowflake에 저장 중...", expanded=True) as status:
                    try:
                        # 데이터베이스 및 스키마 존재 확인
                        st.write(":material/looks_one: 데이터베이스 구조 설정 중...")
                        session.sql(f"CREATE DATABASE IF NOT EXISTS {database}").collect()
                        session.sql(f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}").collect()
                        
                        # 테이블이 없으면 생성
                        st.write(":material/looks_two: 필요시 테이블 생성 중...")
                        create_table_sql = f"""
                        CREATE TABLE IF NOT EXISTS {database}.{schema}.{table_name} (
                            DOC_ID NUMBER AUTOINCREMENT,
                            FILE_NAME VARCHAR,
                            FILE_TYPE VARCHAR,
                            FILE_SIZE NUMBER,
                            EXTRACTED_TEXT VARCHAR,
                            UPLOAD_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                            WORD_COUNT NUMBER,
                            CHAR_COUNT NUMBER
                        )
                        """
                        session.sql(create_table_sql).collect()
                        
                        # 교체 모드: 기존 데이터 삭제
                        if replace_mode:
                            st.write(":material/sync: 교체 모드: 기존 데이터 지우는 중...")
                            try:
                                session.sql(f"TRUNCATE TABLE {database}.{schema}.{table_name}").collect()
                                st.write("   :material/check_circle: 기존 데이터 삭제됨")
                            except Exception as e:
                                st.write(f"   :material/warning: 지울 기존 데이터 없음")
                        
                        # 추출된 모든 데이터 삽입
                        st.write(f":material/looks_3: {len(extracted_data)}개의 문서 삽입 중...")
                        
                        for idx, data in enumerate(extracted_data, 1):
                            st.caption(f"저장 중 {idx}/{len(extracted_data)}: {data['file_name']}")
                            # 텍스트 내 작은따옴표 이스케이프 처리
                            safe_text = data['extracted_text'].replace("'", "''")
                            
                            # [실습] Snowflake 테이블에 데이터를 삽입하세요.
                            # 힌트: session.sql(insert_sql).collect()
                            
                            insert_sql = f"""
                            INSERT INTO {database}.{schema}.{table_name}
                            (FILE_NAME, FILE_TYPE, FILE_SIZE, EXTRACTED_TEXT, WORD_COUNT, CHAR_COUNT)
                            VALUES ('{data['file_name']}', '{data['file_type']}', {data['file_size']}, 
                                    '{safe_text}', {data['word_count']}, {data['char_count']})
                            """
                            
                            # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
                            # session.sql(insert_sql).collect() # 이 줄의 주석을 해제하세요
                            
                            # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요.
                            pass
                        
                        status.update(label=":material/check_circle: 모든 문서가 저장되었습니다!", state="complete", expanded=False)
                        
                        mode_msg = "교체되었습니다" if replace_mode else "저장되었습니다"
                        st.success(f":material/check_circle: `{database}.{schema}.{table_name}`에 성공적으로 {mode_msg}\n\n:material/description: 현재 테이블에 {len(extracted_data)}개의 문서가 있습니다")
                        
                        # 다운스트림 앱을 위해 세션 상태에 참조 저장
                        st.session_state.rag_source_table = f"{database}.{schema}.{table_name}"
                        st.session_state.rag_source_database = database
                        st.session_state.rag_source_schema = schema
                        
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Snowflake 저장 중 오류 발생: {str(e)}")
            else:
                st.warning("어떤 파일에서도 텍스트가 성공적으로 추출되지 않았습니다.")

st.divider()

# 저장된 모든 문서 보기 섹션
with st.container(border=True):
    st.subheader(":material/search: 저장된 문서 보기 (View Saved Documents)")
    
    # 테이블이 존재하는지 확인하고 레코드 수 표시
    try:
        count_result = session.sql(f"""
            SELECT COUNT(*) as CNT FROM {database}.{schema}.{table_name}
        """).collect()
        
        if count_result:
            record_count = count_result[0]['CNT']
            if record_count > 0:
                st.warning(f":material/warning: 현재 `{database}.{schema}.{table_name}` 테이블에 **{record_count}개의 레코드**가 있습니다.")
            else:
                st.info(":material/inbox: **테이블이 비어 있습니다** - 아직 업로드된 문서가 없습니다.")
    except:
        st.info(":material/inbox: **테이블이 아직 존재하지 않습니다** - 문서를 업로드하고 저장하여 생성하세요.")
    
    query_button = st.button("테이블 조회 (Query Table)", type="secondary", use_container_width=True)
    
    if query_button:
        try:
            full_table_name = f"{database}.{schema}.{table_name}"
            
            # 테이블 조회
            query_sql = f"""
            SELECT DOC_ID, FILE_NAME, FILE_TYPE, FILE_SIZE, UPLOAD_TIMESTAMP, WORD_COUNT, CHAR_COUNT
            FROM {full_table_name}
            ORDER BY UPLOAD_TIMESTAMP DESC
            """
            df = session.sql(query_sql).to_pandas()
        
            # 지속성을 위해 세션 상태에 저장
            st.session_state.queried_docs = df
            st.session_state.full_table_name = full_table_name
            st.rerun()
                
        except Exception as e:
            st.error(f"오류: {str(e)}")
            st.info(":material/lightbulb: 테이블이 아직 존재하지 않을 수 있습니다. 문서를 먼저 업로드하고 저장하세요!")
    
    # 가능한 경우 조회 결과 표시
    if 'queried_docs' in st.session_state and 'full_table_name' in st.session_state:
        # 동적 테이블 이름 표시를 위해 현재 세션 상태 값 사용
        current_full_table_name = f"{st.session_state.database}.{st.session_state.schema}.{st.session_state.table_name}"
        
        # 현재 테이블과 일치하는 경우에만 결과 표시 (다른 테이블의 오래된 데이터 표시 방지)
        if st.session_state.full_table_name == current_full_table_name:
            df = st.session_state.queried_docs
            
            if len(df) > 0:
                st.code(f"{current_full_table_name}", language="sql")
                
                # 요약 메트릭
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Documents", len(df))
                with col2:
                    st.metric("Words", f"{df['WORD_COUNT'].sum():,}")
                with col3:
                    st.metric("Characters", f"{df['CHAR_COUNT'].sum():,}")
                
                st.divider()
                
                # 문서 테이블 표시
                st.dataframe(
                    df[['DOC_ID', 'FILE_NAME', 'FILE_TYPE', 'WORD_COUNT', 'UPLOAD_TIMESTAMP']],
                    use_container_width=True
                )
                
                # 문서 전체 텍스트 보기 옵션
                with st.expander(":material/menu_book: 문서 전체 텍스트 보기"):
                    doc_id = st.selectbox(
                        "문서 ID 선택 (Select Document ID):",
                        options=df['DOC_ID'].tolist(),
                        format_func=lambda x: f"Doc #{x} - {df[df['DOC_ID']==x]['FILE_NAME'].values[0]}"
                    )
                    
                    if st.button("텍스트 로드 (Load Text)"):
                        text_sql = f"SELECT EXTRACTED_TEXT, FILE_NAME FROM {current_full_table_name} WHERE DOC_ID = {doc_id}"
                        text_result = session.sql(text_sql).to_pandas()
                        if len(text_result) > 0:
                            doc = text_result.iloc[0]
                            # 세션 상태에 저장
                            st.session_state.loaded_doc_text = doc['EXTRACTED_TEXT']
                            st.session_state.loaded_doc_name = doc['FILE_NAME']
                    
                    # 로드된 텍스트가 있는 경우 표시
                    if 'loaded_doc_text' in st.session_state:
                        st.text_area(
                            st.session_state.loaded_doc_name,
                            value=st.session_state.loaded_doc_text,
                            height=400
                        )
            else:
                st.info(":material/inbox: 테이블이 비어 있습니다. 위에서 파일을 업로드하세요!")
        else:
            st.info(f":material/sync: 다른 테이블에 대한 결과를 표시하고 있습니다. '테이블 조회 (Query Table)'를 클릭하여 새로 고치세요.")
    else:
        st.info(":material/inbox: 아직 조회된 문서가 없습니다. 저장된 문서를 보려면 '테이블 조회 (Query Table)'를 클릭하세요.")

st.divider()
st.caption("Day 16: RAG를 위한 배치 문서 텍스트 추출기 (Batch Document Text Extractor for RAG) | 30 Days of AI")
