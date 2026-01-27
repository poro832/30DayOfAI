# Day 17
# RAG를 위한 고객 리뷰 로드 및 변환 (Loading and Transforming Customer Reviews for RAG)

import streamlit as st
import pandas as pd
import re

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

st.title(":material/sync: RAG를 위한 데이터 준비 및 청킹 (Prepare and Chunk Data for RAG)")
st.write("Day 16의 고객 리뷰를 로드하고 처리하여 RAG를 위한 검색 가능한 청크(Chunk)를 준비합니다.")

# 데이터베이스 구성을 위한 세션 상태 초기화
if 'day17_database' not in st.session_state:
    # Day 16에서 테이블 참조가 있는지 확인
    if 'rag_source_database' in st.session_state:
        st.session_state.day17_database = st.session_state.rag_source_database
        st.session_state.day17_schema = st.session_state.rag_source_schema
        st.session_state.day17_table_name = "EXTRACTED_DOCUMENTS"
    else:
        st.session_state.day17_database = "RAG_DB"
        st.session_state.day17_schema = "RAG_SCHEMA"
        st.session_state.day17_table_name = "EXTRACTED_DOCUMENTS"

if 'day17_chunk_table' not in st.session_state:
    st.session_state.day17_chunk_table = "REVIEW_CHUNKS"

# 데이터베이스 구성 및 로드 섹션
with st.container(border=True):
    st.subheader(":material/analytics: 원본 데이터 구성 (Source Data Configuration)")
    
    # 데이터베이스 구성
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.day17_database = st.text_input(
            "Database", 
            value=st.session_state.day17_database, 
            key="day17_db_input"
        )
    with col2:
        st.session_state.day17_schema = st.text_input(
            "Schema", 
            value=st.session_state.day17_schema, 
            key="day17_schema_input"
        )
    with col3:
        st.session_state.day17_table_name = st.text_input(
            "Source Table", 
            value=st.session_state.day17_table_name, 
            key="day17_table_input"
    )
    
    st.info(f":material/location_on: 로딩 위치: `{st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}`")
    st.caption(":material/lightbulb: 이것은 Day 16의 EXTRACTED_DOCUMENTS 테이블을 가리켜야 합니다.")
    
    # 기존 로드된 데이터 확인
    if 'loaded_data' in st.session_state:
        st.success(f":material/check_circle: **{len(st.session_state.loaded_data)}개의 문서**가 이미 로드되었습니다.")

    # 문서 로드 버튼
    if st.button(":material/folder_open: 리뷰 로드 (Load Reviews)", type="primary", use_container_width=True):
        try:
            with st.status("Snowflake에서 리뷰 로딩 중...", expanded=True) as status:
                st.write(":material/wifi: 데이터베이스 쿼리 중...")
                
                query = f"""
                SELECT 
                    DOC_ID,
                    FILE_NAME,
                    FILE_TYPE,
                    EXTRACTED_TEXT,
                    UPLOAD_TIMESTAMP,
                    WORD_COUNT,
                    CHAR_COUNT
                FROM {st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}
                ORDER BY FILE_NAME
                """
                df = session.sql(query).to_pandas()
                
                st.write(f":material/check_circle: {len(df)}개의 리뷰 로드됨")
                status.update(label="리뷰 로드 성공!", state="complete", expanded=False)
                
                # 세션 상태에 저장
                st.session_state.loaded_data = df
                st.session_state.source_table = f"{st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}"
                st.rerun()
                
        except Exception as e:
            st.error(f"리뷰 로드 중 오류 발생: {str(e)}")
            st.info(":material/lightbulb: Day 16에서 리뷰 파일을 먼저 업로드했는지 확인하세요!")

# 메인 콘텐츠 - 리뷰 요약
if 'loaded_data' in st.session_state:
    with st.container(border=True):
        st.subheader(":material/looks_one: 리뷰 요약 (Review Summary)")
        
        df = st.session_state.loaded_data
                
        # 통계 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Reviews", len(df))
        with col2:
            st.metric("Total Words", f"{df['WORD_COUNT'].sum():,}")
        with col3:
            st.metric("Avg Words/Review", f"{df['WORD_COUNT'].mean():.0f}")
            
        # 리뷰 요약 표시
        st.dataframe(df[['DOC_ID', 'FILE_NAME', 'FILE_TYPE', 'UPLOAD_TIMESTAMP', 'WORD_COUNT']], 
                    use_container_width=True)
                
    # 처리 옵션
    with st.container(border=True):
        st.subheader(":material/looks_two: 처리 전략 선택 (Choose Processing Strategy)")
        
        st.info("""
        **고객 리뷰 처리 옵션:**
        
        고객 리뷰는 일반적으로 짧으므로(각각 약 150단어), 두 가지 옵션이 있습니다:
        - **옵션 1**: 각 리뷰를 그대로 사용 (리뷰에 권장됨)
        - **옵션 2**: 긴 리뷰를 청크로 분할 (200단어 이상의 리뷰용)
        """)
        
        processing_option = st.radio(
            "처리 전략 선택:",
            ["Keep each review as a single chunk (Recommended)", 
             "Chunk reviews longer than threshold"],
            index=0
        )
        
        # 청크 크기 제어 추가 (청킹 옵션 선택 시에만 표시)
        if "Chunk reviews" in processing_option:
            col1, col2 = st.columns(2)
            with col1:
                chunk_size = st.slider(
                    "청크 크기 (words):",
                    min_value=50,
                    max_value=500,
                    value=200,
                    step=50,
                    help="청크당 최대 단어 수"
                )
            with col2:
                overlap = st.slider(
                    "오버랩 (words):",
                    min_value=0,
                    max_value=100,
                    value=50,
                    step=10,
                    help="청크 간 중복되는 단어 수"
                )
            st.caption(f"{chunk_size}단어보다 긴 리뷰는 {overlap}단어의 오버랩을 두고 {chunk_size}단어 단위의 청크로 분할됩니다.")
        else:
            # 청킹하지 않는 경우 기본값
            chunk_size = 200
            overlap = 50
        
        if st.button(":material/flash_on: 리뷰 처리 (Process Reviews)", type="primary", use_container_width=True):
            chunks = []
            
            with st.status("리뷰 처리 중...", expanded=True) as status:
                if "Keep each review" in processing_option:
                    # 옵션 1: 리뷰 1개 = 청크 1개
                    st.write(":material/edit_note: 리뷰당 하나의 청크 생성 중...")
                    
                    for idx, row in df.iterrows():
                        chunks.append({
                            'doc_id': row['DOC_ID'],
                            'file_name': row['FILE_NAME'],
                            'chunk_id': idx + 1,
                            'chunk_text': row['EXTRACTED_TEXT'],
                            'chunk_size': row['WORD_COUNT'],
                            'chunk_type': 'full_review'
                        })
                    
                    st.write(f":material/check_circle: {len(chunks)}개의 청크 생성 완료 (리뷰당 1개)")
                    
                else:
                    # 옵션 2: 긴 리뷰 분할
                    st.write(f":material/edit_note: {chunk_size}단어보다 긴 리뷰 분할 중...")
                    chunk_id = 1
                    
                    for idx, row in df.iterrows():
                        text = row['EXTRACTED_TEXT']
                        words = text.split()
                        
                        if len(words) <= chunk_size:
                            # 짧은 리뷰는 그대로 유지
                            chunks.append({
                                'doc_id': row['DOC_ID'],
                                'file_name': row['FILE_NAME'],
                                'chunk_id': chunk_id,
                                'chunk_text': text,
                                'chunk_size': len(words),
                                'chunk_type': 'full_review'
                            })
                            chunk_id += 1
                        else:
                            # [실습] 긴 리뷰를 청크 사이즈와 오버랩을 고려하여 분할하세요.
                            # 힌트: range(0, len(words), chunk_size - overlap)을 사용하세요.
                            
                            # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
                            # for i in range(0, len(words), chunk_size - overlap):
                            #     chunk_words = words[i:i + chunk_size]
                            #     chunk_text = ' '.join(chunk_words)
                            #     
                            #     chunks.append({
                            #         'doc_id': row['DOC_ID'],
                            #         'file_name': row['FILE_NAME'],
                            #         'chunk_id': chunk_id,
                            #         'chunk_text': chunk_text,
                            #         'chunk_size': len(chunk_words),
                            #         'chunk_type': 'chunked_review'
                            #     })
                            #     chunk_id += 1
                            
                            # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요. 
                            pass # 이 부분을 수정하여 루프를 구현하세요 (주석 해제)
                            
                            # [실습 정답용 코드 - 학생에게 제공하지 않음 / 실제 동작을 위해 아래 코드를 사용하지만, 학생 버전에서는 가려야 합니다]
                            # 학생이 코드를 채우기 전에는 Split 기능이 동작하지 않습니다. 
                            # 데모가 동작하게 하려면 아래 코드를 'active' 상태로 두거나, 아니면 학생이 무조건 채워야 합니다.
                            # 여기서는 '작성용' 파일을 요청했으므로 pass만 남겨두고 주석처리합니다.
                            # 하지만 앱의 기능이 마비되면 안되므로, 데모 시연시에는 "Keep each review" 옵션을 사용하라고 가이드하거나,
                            # 아래 정답 코드를 주석으로 숨겨두되, 기본적으로는 동작하지 않게 합니다.
                            
                            # 원래 동작 코드 (현재는 주석처리됨, 학생이 작성해야 함):
                            # for i in range(0, len(words), chunk_size - overlap):
                            #    chunk_words = words[i:i + chunk_size]
                            #    chunk_text = ' '.join(chunk_words)
                            #    chunks.append({
                            #        'doc_id': row['DOC_ID'],
                            #        'file_name': row['FILE_NAME'],
                            #        'chunk_id': chunk_id,
                            #        'chunk_text': chunk_text,
                            #        'chunk_size': len(chunk_words),
                            #        'chunk_type': 'chunked_review'
                            #    })
                            #    chunk_id += 1
                    
                    st.write(f":material/check_circle: {len(df)}개의 리뷰에서 {len(chunks)}개의 청크 생성 완료")
                
                status.update(label="처리 완료!", state="complete", expanded=False)
                    
            # 세션 상태에 청크 저장
            st.session_state.review_chunks = chunks
            st.session_state.processing_option = processing_option
            
            st.success(f":material/check_circle: {len(df)}개의 리뷰를 {len(chunks)}개의 검색 가능한 청크로 처리했습니다!")
    
    # 청크가 존재하면 표시
    if 'review_chunks' in st.session_state:
        with st.container(border=True):
            st.subheader(":material/looks_3: 처리된 리뷰 청크 (Processed Review Chunks)")
            
            chunks = st.session_state.review_chunks
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Chunks", len(chunks))
            with col2:
                full_reviews = len([c for c in chunks if c['chunk_type'] == 'full_review'])
                st.metric("Full Reviews", full_reviews)
            with col3:
                split_reviews = len([c for c in chunks if c['chunk_type'] == 'chunked_review'])
                st.metric("Split Reviews", split_reviews)
            
            # 청크 표시
            with st.expander(":material/description: 청크 보기"):
                chunks_df = pd.DataFrame(chunks)
                st.dataframe(chunks_df[['chunk_id', 'file_name', 'chunk_size', 'chunk_type', 'chunk_text']], 
                            use_container_width=True)
        
        # 4단계: Snowflake에 청크 저장
        with st.container(border=True):
            st.subheader(":material/looks_4: Snowflake에 청크 저장 (Save Chunks to Snowflake)")
            
            chunks = st.session_state.review_chunks
            
            # 청크 테이블 이름
            col1, col2 = st.columns([2, 1])
            with col1:
                st.session_state.day17_chunk_table = st.text_input(
                    "Chunk Table Name",
                    value=st.session_state.day17_chunk_table,
                    help="리뷰 청크를 저장할 테이블 이름",
                    key="day17_chunk_table_input"
                )
            
            full_chunk_table = f"{st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_chunk_table}"
            st.code(full_chunk_table, language="sql")
            
            # 청크 테이블 존재 여부 확인 및 상태 표시
            chunk_table_exists = False  # 기본값 False (체크 해제)
            try:
                count_result = session.sql(f"""
                    SELECT COUNT(*) as CNT FROM {full_chunk_table}
                """).collect()
                
                if count_result:
                    record_count = count_result[0]['CNT']
                    if record_count > 0:
                        st.warning(f":material/warning: 현재 `{full_chunk_table}` 테이블에 **{record_count}개의 청크**가 있습니다.")
                        chunk_table_exists = True  # 데이터가 있으면 체크
                    else:
                        st.info(":material/inbox: **청크 테이블이 비어 있습니다** - 아직 저장된 청크가 없습니다.")
                        chunk_table_exists = False
            except:
                st.info(":material/inbox: **청크 테이블이 아직 없습니다** - 청크를 저장하면 생성됩니다.")
                chunk_table_exists = False
            
            # 테이블 상태에 따라 체크박스 상태 초기화 또는 업데이트
            # 체크박스가 현재 테이블 상태를 반영하도록 함
            if 'day17_replace_mode' not in st.session_state:
                # 처음 - 테이블 존재 여부에 따라 초기화
                st.session_state.day17_replace_mode = chunk_table_exists
            else:
                # 테이블 이름이 변경되었는지 확인 - 변경되었다면 새 테이블 상태에 따라 재설정
                if 'day17_last_chunk_table' not in st.session_state or st.session_state.day17_last_chunk_table != full_chunk_table:
                    st.session_state.day17_replace_mode = chunk_table_exists
                    st.session_state.day17_last_chunk_table = full_chunk_table
            
            # 교체 모드 체크박스
            replace_mode = st.checkbox(
                f":material/sync: `{st.session_state.day17_chunk_table}` 테이블 교체 모드 (Replace Table Mode)",
                help=f"활성화하면 새 청크를 저장하기 전에 {full_chunk_table}의 모든 기존 데이터를 지웁니다.",
                key="day17_replace_mode"
            )
            
            if replace_mode:
                st.warning("**교체 모드 활성**: 새 청크를 저장하기 전에 기존 청크가 삭제됩니다.")
            else:
                st.success("**추가 모드 활성**: 새 청크가 기존 데이터에 추가됩니다.")
            
            # 테이블에 청크 저장
            if st.button(":material/save: Snowflake에 청크 저장 (Save Chunks to Snowflake)", type="primary", use_container_width=True):
                try:
                    with st.status("Snowflake에 청크 저장 중...", expanded=True) as status:
                        # 1단계: 테이블이 없으면 생성
                        st.write(":material/looks_one: 테이블 확인 중...")
                        create_table_sql = f"""
                        CREATE TABLE IF NOT EXISTS {full_chunk_table} (
                            CHUNK_ID NUMBER,
                            DOC_ID NUMBER,
                            FILE_NAME VARCHAR,
                            CHUNK_TEXT VARCHAR,
                            CHUNK_SIZE NUMBER,
                            CHUNK_TYPE VARCHAR,
                            CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                        )
                        """
                        session.sql(create_table_sql).collect()
                        
                        # 2단계: 교체 모드 - 기존 청크 삭제
                        if replace_mode:
                            st.write(":material/sync: 교체 모드: 기존 청크 지우는 중...")
                            try:
                                session.sql(f"TRUNCATE TABLE {full_chunk_table}").collect()
                                st.write("   :material/check_circle: 기존 청크 삭제됨")
                            except Exception as e:
                                st.write(f"   :material/warning: 지울 기존 청크 없음")
                        
                        # 3단계: 청크 삽입
                        st.write(f":material/looks_3: {len(chunks)}개의 청크 삽입 중...")
                        chunks_df = pd.DataFrame(chunks)
                        
                        # Snowflake 테이블과 일치하도록 컬럼명을 대문자로 변경
                        chunks_df_upper = chunks_df[['chunk_id', 'doc_id', 'file_name', 'chunk_text', 
                                                       'chunk_size', 'chunk_type']].copy()
                        chunks_df_upper.columns = ['CHUNK_ID', 'DOC_ID', 'FILE_NAME', 'CHUNK_TEXT', 
                                                   'CHUNK_SIZE', 'CHUNK_TYPE']
                        
                        if replace_mode:
                            # 교체 모드에서는 overwrite 사용 (이미 truncate했지만)
                            session.write_pandas(chunks_df_upper,
                                               table_name=st.session_state.day17_chunk_table,
                                               database=st.session_state.day17_database,
                                               schema=st.session_state.day17_schema,
                                               overwrite=True)
                        else:
                            # 추가 모드
                            session.write_pandas(chunks_df_upper,
                                               table_name=st.session_state.day17_chunk_table,
                                               database=st.session_state.day17_database,
                                               schema=st.session_state.day17_schema,
                                               overwrite=False)
                        
                        status.update(label=":material/check_circle: 청크 저장됨!", state="complete", expanded=False)
                    
                    mode_msg = "교체되었습니다" if replace_mode else "저장되었습니다"
                    st.success(f":material/check_circle: `{full_chunk_table}`에 성공적으로 {mode_msg}\n\n:material/description: 현재 테이블에 {len(chunks)}개의 청크가 있습니다")
                    
                    # Day 18을 위해 저장
                    st.session_state.chunks_table = full_chunk_table
                    st.session_state.chunks_database = st.session_state.day17_database
                    st.session_state.chunks_schema = st.session_state.day17_schema
                    st.session_state.chunk_table_saved = True
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"청크 저장 중 오류 발생: {str(e)}")

# 저장된 청크 보기 섹션
with st.container(border=True):
    st.subheader(":material/search: 저장된 청크 보기 (View Saved Chunks)")
    
    # 쿼리 중인 테이블 표시 (4단계 구성에서)
    full_chunk_table = f"{st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_chunk_table}"
    st.caption(f":material/analytics: 청크 테이블 쿼리 중: `{full_chunk_table}`")
    
    query_button = st.button(":material/analytics: 청크 테이블 조회 (Query Chunk Table)", type="secondary", use_container_width=True)
    
    if query_button:
        try:
            query_sql = f"""
            SELECT 
                CHUNK_ID,
                FILE_NAME,
                CHUNK_SIZE,
                CHUNK_TYPE,
                LEFT(CHUNK_TEXT, 100) AS TEXT_PREVIEW,
                CREATED_TIMESTAMP
            FROM {full_chunk_table}
            ORDER BY CHUNK_ID
            """
            chunks_df = session.sql(query_sql).to_pandas()
            
            # 지속성을 위해 세션 상태에 저장
            st.session_state.queried_chunks = chunks_df
            st.session_state.queried_chunks_table = full_chunk_table
            st.rerun()
                
        except Exception as e:
            st.error(f"청크 조회 중 오류 발생: {str(e)}")
    
    # 세션 상태에 결과가 있으면 표시
    if 'queried_chunks' in st.session_state and st.session_state.get('queried_chunks_table') == full_chunk_table:
        chunks_df = st.session_state.queried_chunks
        
        if len(chunks_df) > 0:
            st.code(full_chunk_table, language="sql")
            
            # 요약 메트릭
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Chunks", len(chunks_df))
            with col2:
                full_count = len(chunks_df[chunks_df['CHUNK_TYPE'] == 'full_review'])
                st.metric("Full Reviews", full_count)
            with col3:
                split_count = len(chunks_df[chunks_df['CHUNK_TYPE'] == 'chunked_review'])
                st.metric("Split Reviews", split_count)
            
            # 테이블 표시
            st.dataframe(
                chunks_df[['CHUNK_ID', 'FILE_NAME', 'CHUNK_SIZE', 'CHUNK_TYPE', 'TEXT_PREVIEW']],
                use_container_width=True
            )
            
            # 청크 전체 텍스트 보기 옵션
            with st.expander(":material/menu_book: 청크 전체 텍스트 보기"):
                chunk_id = st.selectbox(
                    "청크 ID 선택:",
                    options=chunks_df['CHUNK_ID'].tolist(),
                    format_func=lambda x: f"Chunk #{x} - {chunks_df[chunks_df['CHUNK_ID']==x]['FILE_NAME'].values[0]}",
                    key="chunk_text_selector"
                )
                
                if st.button("청크 텍스트 로드 (Load Chunk Text)", key="load_chunk_text_btn"):
                    # 선택 사항 세션 상태에 저장
                    st.session_state.selected_chunk_id = chunk_id
                    st.session_state.load_chunk_text = True
                    st.rerun()
                
                # 로드된 경우 청크 텍스트 표시
                if st.session_state.get('load_chunk_text') and st.session_state.get('selected_chunk_id'):
                    text_sql = f"SELECT CHUNK_TEXT, FILE_NAME FROM {full_chunk_table} WHERE CHUNK_ID = {st.session_state.selected_chunk_id}"
                    text_result = session.sql(text_sql).to_pandas()
                    if len(text_result) > 0:
                        chunk = text_result.iloc[0]
                        st.text_area(
                            chunk['FILE_NAME'],
                            value=chunk['CHUNK_TEXT'],
                            height=300,
                            key=f"chunk_text_display_{st.session_state.selected_chunk_id}"
                        )
        else:
            st.info(":material/inbox: 테이블에 청크가 없습니다.")
    else:
        st.info(":material/inbox: 아직 조회된 청크가 없습니다. 저장된 청크를 보려면 '청크 테이블 조회 (Query Chunk Table)'를 클릭하세요.")

st.divider()
st.caption("Day 17: RAG를 위한 고객 리뷰 로드 및 변환 (Loading and Transforming Customer Reviews for RAG) | 30 Days of AI")
