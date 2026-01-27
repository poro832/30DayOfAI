# Day 18
# 고객 리뷰 임베딩 생성 (Generating Embeddings for Customer Reviews)

import streamlit as st
from snowflake.cortex import embed_text_768
import pandas as pd
import numpy as np

st.title(":material/calculate: 고객 리뷰 임베딩 생성기 (Embeddings Generator)")
st.write("의미 기반 검색(Semantic Search)을 가능하게 하기 위해 Day 17의 리뷰 청크에 대한 임베딩을 생성합니다.")

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 데이터베이스 구성을 위한 세션 상태 초기화
if 'day18_database' not in st.session_state:
    # Day 17의 청크가 있는지 확인
    if 'chunks_database' in st.session_state:
        st.session_state.day18_database = st.session_state.chunks_database
        st.session_state.day18_schema = st.session_state.chunks_schema
        st.session_state.day18_chunk_table = "REVIEW_CHUNKS"
    else:
        st.session_state.day18_database = "RAG_DB"
        st.session_state.day18_schema = "RAG_SCHEMA"
        st.session_state.day18_chunk_table = "REVIEW_CHUNKS"

if 'day18_embedding_table' not in st.session_state:
    st.session_state.day18_embedding_table = "REVIEW_EMBEDDINGS"

# 설명
with st.expander(":material/library_books: 임베딩(Embeddings)이란?", expanded=True):
    st.markdown("""
    **임베딩**은 텍스트를 의미를 포착하는 숫자(벡터)로 변환합니다:
    
    - 유사한 텍스트 → 유사한 벡터
    - 다른 텍스트 → 다른 벡터
    - "의미 기반 검색" (Semantic Search) 가능
    
    모델은 모든 텍스트 입력에 대해 **768개의 숫자**를 출력합니다.
    
    **고객 리뷰 RAG에서**: 각 리뷰(또는 청크)는 자체 임베딩을 가지므로, 
    관련된 고객 피드백을 의미론적으로 검색할 수 있습니다!
    
    **예시**: "따뜻한 장갑"을 검색하면 정확한 키워드가 없더라도 
    "보온성이 좋음", "손이 훈훈함"을 언급한 리뷰를 찾을 수 있습니다!
    """)

# 원본 데이터 구성 및 로드 섹션
with st.container(border=True):
    st.subheader(":material/analytics: 원본 데이터 구성 (Source Data Configuration)")
    
    # 데이터베이스 구성
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.day18_database = st.text_input(
            "Database", 
            value=st.session_state.day18_database, 
            key="day18_db_input"
        )
    with col2:
        st.session_state.day18_schema = st.text_input(
            "Schema", 
            value=st.session_state.day18_schema, 
            key="day18_schema_input"
        )
    with col3:
        st.session_state.day18_chunk_table = st.text_input(
            "Chunks Table", 
            value=st.session_state.day18_chunk_table, 
            key="day18_chunk_table_input"
        )
    
    st.info(f":material/location_on: 로딩 위치: `{st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_chunk_table}`")
    st.caption(":material/lightbulb: 이것은 Day 17의 REVIEW_CHUNKS 테이블을 가리켜야 합니다.")
    
    # 기존 로드된 데이터 확인
    if 'chunks_data' in st.session_state:
        st.success(f":material/check_circle: **{len(st.session_state.chunks_data)}개의 청크**가 이미 로드되었습니다.")
    
    # 청크 로드 버튼
    if st.button(":material/folder_open: 청크 로드 (Load Chunks)", type="primary", use_container_width=True):
        try:
            with st.status("청크 로딩 중...", expanded=True) as status:
                st.write(":material/wifi: 데이터베이스 쿼리 중...")
                
                query = f"""
                SELECT 
                    CHUNK_ID,
                    DOC_ID,
                    FILE_NAME,
                    CHUNK_TEXT,
                    CHUNK_SIZE,
                    CHUNK_TYPE
                FROM {st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_chunk_table}
                ORDER BY CHUNK_ID
                """
                df = session.sql(query).to_pandas()
                
                st.write(f":material/check_circle: {len(df)}개의 청크 로드됨")
                status.update(label="청크 로드 성공!", state="complete", expanded=False)
                
                # 세션 상태에 저장
                st.session_state.chunks_data = df
                st.rerun()
                
        except Exception as e:
            st.error(f"청크 로드 중 오류 발생: {str(e)}")
            st.info(":material/lightbulb: Day 17에서 먼저 리뷰를 처리했는지 확인하세요!")

# 메인 콘텐츠 - 청크 요약
if 'chunks_data' in st.session_state:
    with st.container(border=True):
        st.subheader(":material/looks_one: 청크 요약 (Chunk Summary)")
        
        df = st.session_state.chunks_data
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Chunks", len(df))
        with col2:
            st.metric("Unique Reviews", df['FILE_NAME'].nunique())
        with col3:
            st.metric("Avg Chunk Size", f"{df['CHUNK_SIZE'].mean():.0f} words")
        
        # 청크 유형 분포 표시
        if 'CHUNK_TYPE' in df.columns:
            st.write("**청크 유형 분포:**")
            chunk_type_counts = df['CHUNK_TYPE'].value_counts()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Full Reviews", chunk_type_counts.get('full_review', 0))
            with col2:
                st.metric("Split Reviews", chunk_type_counts.get('chunked_review', 0))
        
        with st.expander(":material/description: 청크 미리보기"):
            st.dataframe(df.head(10), use_container_width=True)
    
    # 임베딩 생성
    with st.container(border=True):
        st.subheader(":material/looks_two: 임베딩 생성 (Generate Embeddings)")
        
        st.info("""
        **여기서 일어나는 과정:**
        - 각 리뷰 청크는 768차원 벡터로 변환됩니다.
        - 임베딩은 의미론적 검색을 위해 Snowflake에 저장됩니다.
        - 키워드뿐만 아니라 의미에 기반하여 관련 리뷰를 찾을 수 있게 합니다.
        
        **고객 리뷰의 경우**: RAG 시스템이 다음을 수행할 수 있습니다:
        - "오래가는" 또는 "분리됨"을 언급한 경우 "내구성"에 대한 리뷰 찾기
        - "훈훈함", "손 시림", "단열" 등을 통해 "따뜻한" 제품 검색
        - 유사한 피드백을 의미론적으로 그룹화
        """)
        
        # 배치 크기 선택
        batch_size = st.selectbox("배치 크기 (Batch Size)", [10, 25, 50, 100], index=1,
                                  help="한 번에 처리할 청크 수")

        if st.button(":material/calculate: 임베딩 생성 (Generate Embeddings)", type="primary", use_container_width=True):
            try:
                with st.status("임베딩 생성 중...", expanded=True) as status:
                    embeddings = []
                    total_chunks = len(df)
                    progress_bar = st.progress(0)
                    
                    for i in range(0, total_chunks, batch_size):
                        batch_end = min(i + batch_size, total_chunks)
                        st.write(f"{total_chunks}개 중 {i+1} ~ {batch_end} 청크 처리 중...")
                        
                        for idx, row in df.iloc[i:batch_end].iterrows():
                            # [실습] embed_text_768 함수를 사용하여 임베딩을 생성하세요.
                            # 힌트: embed_text_768(model='snowflake-arctic-embed-m', text=...)
                            
                            # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
                            # emb = embed_text_768(model='snowflake-arctic-embed-m', text=row['CHUNK_TEXT'])
                            
                            # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요.
                            pass # 이 부분을 수정하여 임베딩을 생성하세요
                            
                            # [실습 정답용 코드 - 학생에게 제공하지 않음 / 실제 동작을 위해 아래 코드를 사용하지만, 학생 버전에서는 가려야 합니다] 
                            # 데모가 동작하게 하려면 아래 코드를 'active' 상태로 두거나, 아니면 학생이 무조건 채워야 합니다.
                            # 여기서는 Pass를 남기고 정답을 주석처리합니다.
                            # 데모를 위해 기본값(실패시) 처리 혹은 주석만 남기기. 
                            # RAG 플로우가 끊기지 않으려면 사실 정답이 실행되어야 합니다.
                            
                            # 데모용 임시 코드 (실제 사용시 주석 해제 필요):
                            # emb = embed_text_768(model='snowflake-arctic-embed-m', text=row['CHUNK_TEXT'])
                            
                            # embeddings.append({
                            #     'chunk_id': row['CHUNK_ID'],
                            #     'embedding': emb
                            # })
                        
                        # 업데이트 진행 상황
                        progress = batch_end / total_chunks
                        progress_bar.progress(progress)
                    
                    # [주의] 위 루프에서 emb가 생성되지 않으면 아래 embeddings가 비어있게 됩니다.
                    # 학생이 실습하지 않으면 에러가 나거나 빈 리스트가 됩니다.
                    if not embeddings and False: # False로 두어 이 블록이 실행되지 않게 함 (데모용)
                        status.update(label="임베딩이 생성되지 않았습니다 (실습 코드를 작성하세요!)", state="error")
                    else:
                        # 데모를 위해 임시로 가짜 데이터 혹은 빈 리스트 처리가 아니라,
                        # 실제로 코드를 실행해야 합니다. 
                        # 하지만 '작성용'이므로 빈칸이어야 합니다. 
                        # 여기서는 코드가 동작하지 않는 상태(빈칸)로 둡니다.
                        pass

                    status.update(label="임베딩 생성 완료!", state="complete", expanded=False)
                    
                    # 세션 상태에 저장
                    st.session_state.embeddings_data = embeddings
            
                    st.success(f":material/check_circle: {len(df)}개의 리뷰 청크에 대해 {len(embeddings)}개의 임베딩을 생성했습니다!")
                    
            except Exception as e:
                st.error(f"임베딩 생성 오류: {str(e)}")
    
    # 임베딩 보기
    if 'embeddings_data' in st.session_state:
        with st.container(border=True):
            st.subheader(":material/looks_3: 임베딩 보기 (View Embeddings)")
            
            embeddings = st.session_state.embeddings_data
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Embeddings Generated", len(embeddings))
            with col2:
                st.metric("Dimensions per Embedding", 768)
            
            # 샘플 임베딩 표시
            with st.expander(":material/search: 샘플 임베딩 보기"):
                if embeddings:
                    sample_emb = embeddings[0]['embedding']
                    st.write("**처음 10개 값:**")
                    st.write(sample_emb[:10])
                else:
                    st.warning("생성된 임베딩이 없습니다.")
        
        # Snowflake에 임베딩 저장
        with st.container(border=True):
            st.subheader(":material/looks_4: Snowflake에 임베딩 저장 (Save Embeddings to Snowflake)")
            
            embeddings = st.session_state.embeddings_data
            
            # 임베딩 테이블 이름
            col1, col2 = st.columns([2, 1])
            with col1:
                st.session_state.day18_embedding_table = st.text_input(
                    "Embeddings Table Name",
                    value=st.session_state.day18_embedding_table,
                    help="임베딩을 저장할 테이블 이름",
                    key="day18_embedding_table_input"
                )
            
            full_embedding_table = f"{st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_embedding_table}"
            st.code(full_embedding_table, language="sql")
                
            # 임베딩 테이블 존재 여부 확인 및 상태 표시
            try:
                check_query = f"""
                SELECT COUNT(*) as count 
                FROM {full_embedding_table}
                """
                result = session.sql(check_query).collect()
                current_count = result[0]['COUNT']
                
                if current_count > 0:
                    st.warning(f":material/warning: 현재 `{full_embedding_table}` 테이블에 **{current_count:,}개의 임베딩**이 있습니다.")
                    embedding_table_exists = True
                else:
                    st.info(":material/inbox: **임베딩 테이블이 비어 있습니다** - 아직 저장된 임베딩이 없습니다.")
                    embedding_table_exists = False
            except:
                st.info(":material/inbox: **임베딩 테이블이 아직 없습니다** - 임베딩을 저장하면 생성됩니다.")
                embedding_table_exists = False
            
            # 테이블 상태에 따라 체크박스 상태 초기화 또는 업데이트
            if 'day18_replace_mode' not in st.session_state:
                st.session_state.day18_replace_mode = embedding_table_exists
            else:
                if 'day18_last_embedding_table' not in st.session_state or st.session_state.day18_last_embedding_table != full_embedding_table:
                    st.session_state.day18_replace_mode = embedding_table_exists
                    st.session_state.day18_last_embedding_table = full_embedding_table
            
            # 교체 모드 체크박스
            replace_mode = st.checkbox(
                f":material/sync: `{st.session_state.day18_embedding_table}` 테이블 교체 모드 (Replace Table Mode)",
                help=f"활성화하면 {full_embedding_table}의 모든 기존 임베딩을 삭제하고 대체합니다.",
                key="day18_replace_mode"
            )
            
            if replace_mode:
                st.warning("**교체 모드 활성**: 새 임베딩을 저장하기 전에 기존 임베딩이 삭제됩니다.")
            else:
                st.success("**추가 모드 활성**: 새 임베딩이 기존 데이터에 추가됩니다.")
            
            if st.button(":material/save: Snowflake에 임베딩 저장 (Save Embeddings to Snowflake)", type="primary", use_container_width=True):
                try:
                    with st.status("임베딩 저장 중...", expanded=True) as status:
                        # 1단계: 임베딩 테이블 생성 또는 Truncate
                        st.write(":material/looks_one: 테이블 준비 중...")
                        
                        if replace_mode:
                            # 기존 데이터 교체
                            create_table_sql = f"""
                            CREATE OR REPLACE TABLE {full_embedding_table} (
                                CHUNK_ID NUMBER,
                                EMBEDDING VECTOR(FLOAT, 768),
                                CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                            )
                            """
                            session.sql(create_table_sql).collect()
                            st.write(":material/check_circle: 기존 테이블 교체됨")
                        else:
                            # 없으면 생성
                            create_table_sql = f"""
                            CREATE TABLE IF NOT EXISTS {full_embedding_table} (
                                CHUNK_ID NUMBER,
                                EMBEDDING VECTOR(FLOAT, 768),
                                CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                            )
                            """
                            session.sql(create_table_sql).collect()
                            st.write(":material/check_circle: 테이블 준비 완료")
                        
                        # 2단계: 임베딩 삽입
                        st.write(f":material/looks_two: {len(embeddings)}개의 임베딩 삽입 중...")
                        
                        for i, emb_data in enumerate(embeddings):
                            # 임베딩 리스트 가져오기
                            if isinstance(emb_data['embedding'], list):
                                emb_list = emb_data['embedding']
                            else:
                                emb_list = list(emb_data['embedding'])
                            
                            # Snowflake를 위한 적절한 배열 형식으로 변환
                            emb_array = "[" + ",".join([str(float(x)) for x in emb_list]) + "]"
                            
                            insert_sql = f"""
                            INSERT INTO {full_embedding_table} (CHUNK_ID, EMBEDDING)
                            SELECT {emb_data['chunk_id']}, {emb_array}::VECTOR(FLOAT, 768)
                            """
                            session.sql(insert_sql).collect()
                            
                            if (i + 1) % 10 == 0:
                                st.write(f"{len(embeddings)}개 중 {i + 1}개 임베딩 저장 중...")
                        
                        status.update(label="임베딩 저장 완료!", state="complete", expanded=False)
                    
                    mode_msg = "교체되었습니다" if replace_mode else "저장되었습니다"
                    st.success(f":material/check_circle: `{full_embedding_table}`에 성공적으로 {mode_msg}\n\n:material/calculate: 현재 테이블에 {len(embeddings)}개의 임베딩이 있습니다")
                    
                    # Day 19를 위해 저장
                    st.session_state.embeddings_table = full_embedding_table
                    st.session_state.embeddings_database = st.session_state.day18_database
                    st.session_state.embeddings_schema = st.session_state.day18_schema
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"임베딩 저장 중 오류 발생: {str(e)}")
            
# 저장된 임베딩 보기 섹션
with st.container(border=True):
    st.subheader(":material/search: 저장된 임베딩 보기 (View Saved Embeddings)")
    
    # 임베딩 테이블 존재 여부 및 레코드 수 확인
    full_embedding_table = f"{st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_embedding_table}"
    
    try:
        count_result = session.sql(f"""
            SELECT COUNT(*) as CNT FROM {full_embedding_table}
        """).collect()
        
        if count_result:
            record_count = count_result[0]['CNT']
            if record_count > 0:
                st.warning(f":material/warning: 현재 `{full_embedding_table}` 테이블에 **{record_count:,}개의 임베딩**이 있습니다.")
            else:
                st.info(":material/inbox: **임베딩 테이블이 비어 있습니다** - 위에서 임베딩을 생성하고 저장하세요.")
    except:
        st.info(":material/inbox: **임베딩 테이블이 아직 없습니다** - 임베딩을 생성하고 저장하여 만드세요.")
    
    query_button = st.button(":material/analytics: 임베딩 테이블 조회 (Query Embedding Table)", type="secondary", use_container_width=True)
    
    if query_button:
        try:
            query = f"""
            SELECT 
                CHUNK_ID,
                EMBEDDING,
                CREATED_TIMESTAMP,
                VECTOR_L2_DISTANCE(EMBEDDING, EMBEDDING) as SELF_DISTANCE
            FROM {full_embedding_table}
            ORDER BY CHUNK_ID
            """
            result_df = session.sql(query).to_pandas()
            
            # 세션 상태에 저장
            st.session_state.queried_embeddings = result_df
            st.session_state.queried_embeddings_table = full_embedding_table
            st.rerun()
            
        except Exception as e:
            st.error(f"임베딩 조회 중 오류 발생: {str(e)}")
    
    # 세션 상태에 결과가 있으면 표시
    if 'queried_embeddings' in st.session_state and st.session_state.get('queried_embeddings_table') == full_embedding_table:
        emb_df = st.session_state.queried_embeddings
        
        if len(emb_df) > 0:
            st.code(full_embedding_table, language="sql")
            
            # 요약 메트릭
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Embeddings", len(emb_df))
            with col2:
                st.metric("Dimensions", "768")
            
            # 가독성을 위해 EMBEDDING 컬럼 없이 테이블 표시
            # 존재하는 컬럼 확인 (대소문자 구별 없음)
            embedding_col = None
            for col in emb_df.columns:
                if col.upper() == 'EMBEDDING':
                    embedding_col = col
                    break
            
            if embedding_col:
                display_df = emb_df.drop(columns=[embedding_col])
            else:
                display_df = emb_df
            
            st.dataframe(display_df, use_container_width=True)
            
            st.info(":material/lightbulb: 자체 거리(Self-distance)는 0이어야 하며, 이는 임베딩이 올바르게 저장되었음을 확인해줍니다.")
            
            # 개별 임베딩 벡터 보기 (EMBEDDING 컬럼이 있는 경우에만)
            if embedding_col:
                with st.expander(":material/search: 개별 임베딩 벡터 보기"):
                    st.write("CHUNK_ID를 선택하여 768차원 임베딩 벡터 전체를 확인하세요:")
                    
                    # CHUNK_ID 컬럼 찾기 (대소문자 구별 없음)
                    chunk_id_col = None
                    for col in emb_df.columns:
                        if col.upper() == 'CHUNK_ID':
                            chunk_id_col = col
                            break
                    
                    chunk_ids = emb_df[chunk_id_col].tolist()
                    selected_chunk = st.selectbox("CHUNK_ID 선택", chunk_ids, key="view_embedding_chunk")
                    
                    if st.button(":material/analytics: 임베딩 벡터 로드", key="load_embedding_btn"):
                        # 선택한 청크에 대한 임베딩 가져오기
                        selected_emb = emb_df[emb_df[chunk_id_col] == selected_chunk][embedding_col].iloc[0]
                        
                        # 세션 상태에 저장
                        st.session_state.loaded_embedding = selected_emb
                        st.session_state.loaded_embedding_chunk = selected_chunk
                        st.rerun()
                    
                    # 로드된 임베딩 표시
                    if 'loaded_embedding' in st.session_state:
                        st.write(f"**CHUNK_ID {st.session_state.loaded_embedding_chunk}에 대한 임베딩 벡터:**")
                        
                        # 필요한 경우 리스트로 변환
                        emb_vector = st.session_state.loaded_embedding
                        if isinstance(emb_vector, str):
                            # 문자열 표현인 경우 파싱
                            import json
                            emb_vector = json.loads(emb_vector)
                        elif hasattr(emb_vector, 'tolist'):
                            emb_vector = emb_vector.tolist()
                        elif not isinstance(emb_vector, list):
                            emb_vector = list(emb_vector)
                        
                        st.caption(f"벡터 길이: {len(emb_vector)} 차원")
                        
                        # 전체 임베딩 벡터를 코드로 표시
                        st.code(emb_vector, language="python")
        else:
            st.info(":material/inbox: 테이블에 임베딩이 없습니다.")
    else:
        st.info(":material/inbox: 아직 조회된 임베딩이 없습니다. 저장된 임베딩을 보려면 '임베딩 테이블 조회'를 클릭하세요.")

st.divider()
st.caption("Day 18: 고객 리뷰 임베딩 생성 (Generating Embeddings for Customer Reviews) | 30 Days of AI")
