# Generating Embeddings for Customer Reviews (고객 리뷰를 위한 임베딩 생성)

# 0. 목표

<aside>
💡

**Day 17의 청크들을 벡터 임베딩으로 변환하여 의미 기반 검색 가능하게 만들기**

1. Day 17에서 생성한 리뷰 청크 로드
2. Snowflake Cortex의 embed_text_768 함수로 임베딩 생성
3. 768차원 벡터를 Snowflake 테이블에 저장 (Day 19 검색 서비스 준비)

</aside>

# 1. 개요 및 필요성 (Overview)

- **임베딩(Embeddings)**은 텍스트를 숫자 벡터로 변환하여 의미를 수치화합니다.
- 비슷한 의미의 텍스트는 비슷한 벡터가 되고, 다른 의미의 텍스트는 다른 벡터가 됩니다.
- RAG 파이프라인의 **세 번째 단계**로, 각 리뷰 청크를 768개의 숫자로 변환합니다.

## 임베딩이란?

- **의미 기반 검색 가능**: "따뜻한 장갑"을 검색하면 "손을 포근하게", "추위를 막아줌"과 같은 리뷰도 찾음
- **키워드 불필요**: 정확한 단어가 없어도 의미가 비슷하면 검색 가능
- **768차원**: 각 텍스트는 768개의 숫자로 표현됨

# 2. Streamlit 앱 구현 (Implementation)

## 2-1. Day 17 청크 로드

```python
import streamlit as st
from snowflake.cortex import embed_text_768
import pandas as pd

# Snowflake 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Day 17의 청크 확인
if 'day18_database' not in st.session_state:
    if 'chunks_database' in st.session_state:
        st.session_state.day18_database = st.session_state.chunks_database
        st.session_state.day18_schema = st.session_state.chunks_schema

# 청크 로드 버튼
if st.button(":material/folder_open: Load Chunks", type="primary"):
    query = f"""
    SELECT CHUNK_ID, DOC_ID, FILE_NAME, CHUNK_TEXT, CHUNK_SIZE, CHUNK_TYPE
    FROM {st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_chunk_table}
    ORDER BY CHUNK_ID
    """
    df = session.sql(query).to_pandas()
    # 세션 상태에 저장
    st.session_state.chunks_data = df
    st.rerun()
```

- Day 17의 `chunks_database`와 `chunks_schema`를 자동으로 감지
- `CHUNK_TEXT` 컬럼에서 임베딩할 텍스트를 가져옴

## 2-2. 배치 임베딩 생성

```python
# 배치 크기 선택
batch_size = st.selectbox("Batch Size", [10, 25, 50, 100], index=1,
                          help="Number of chunks to process at once")

if st.button(":material/calculate: Generate Embeddings", type="primary"):
    embeddings = []
    total_chunks = len(df)
    progress_bar = st.progress(0)
    
    for i in range(0, total_chunks, batch_size):
        batch_end = min(i + batch_size, total_chunks)
        st.write(f"Processing chunks {i+1} to {batch_end} of {total_chunks}...")
        
        for idx, row in df.iloc[i:batch_end].iterrows():
            # 정확한 함수 시그니처를 사용하여 임베딩 생성
            emb = embed_text_768(model='snowflake-arctic-embed-m', 
                                text=row['CHUNK_TEXT'])
            embeddings.append({
                'chunk_id': row['CHUNK_ID'],
                'embedding': emb
            })
        
        # 진행 상황 업데이트
        progress = batch_end / total_chunks
        progress_bar.progress(progress)
    
    # 세션 상태에 저장
    st.session_state.embeddings_data = embeddings
```

- `batch_size`: 한번에 처리할 청크 수 (기본값: 25)
- `embed_text_768()`: Snowflake Cortex 함수로 768차원 벡터 생성
- `model='snowflake-arctic-embed-m'`: Snowflake의 중간 크기 임베딩 모델 사용
- 진행 상황 표시줄로 실시간 피드백 제공

## 2-3. 임베딩 확인

```python
# 샘플 임베딩 표시
with st.expander(":material/search: View Sample Embedding"):
    sample_emb = embeddings[0]['embedding']
    st.write("**First 10 values:**")
    st.write(sample_emb[:10])
```

- 첫 번째 임베딩의 처음 10개 값을 표시하여 구조 확인
- 각 값은 -1과 1 사이의 소수

## 2-4. Snowflake에 임베딩 저장

```python
# 임베딩 테이블 존재 확인 및 상태 표시
try:
    check_query = f"SELECT COUNT(*) as count FROM {full_embedding_table}"
    result = session.sql(check_query).collect()
    current_count = result[0]['COUNT']
    embedding_table_exists = current_count > 0
except:
    embedding_table_exists = False

# 교체 모드 체크박스
replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.day18_embedding_table}`",
    value=embedding_table_exists,
    key="day18_replace_mode"
)

if st.button(":material/save: Save Embeddings to Snowflake", type="primary"):
    if replace_mode:
        # 기존 데이터 교체
        create_table_sql = f"""
        CREATE OR REPLACE TABLE {full_embedding_table} (
            CHUNK_ID NUMBER,
            EMBEDDING VECTOR(FLOAT, 768),
            CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
    else:
        # 존재하지 않으면 생성
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {full_embedding_table} (
            CHUNK_ID NUMBER,
            EMBEDDING VECTOR(FLOAT, 768),
            CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
    session.sql(create_table_sql).collect()
    
    # 2단계: 임베딩 삽입
    for i, emb_data in enumerate(embeddings):
        # Snowflake을 위한 적절한 배열 형식으로 변환
        emb_array = "[" + ",".join([str(float(x)) for x in emb_data['embedding']]) + "]"
        
        insert_sql = f"""
        INSERT INTO {full_embedding_table} (CHUNK_ID, EMBEDDING)
        SELECT {emb_data['chunk_id']}, {emb_array}::VECTOR(FLOAT, 768)
        """
        session.sql(insert_sql).collect()
```

- `VECTOR(FLOAT, 768)`: Snowflake의 벡터 데이터 타입으로 768차원 부동소수점 벡터 저장
- `CREATE OR REPLACE`: Replace 모드일 때 테이블을 완전히 새로 생성
- `::VECTOR(FLOAT, 768)`: JSON 배열을 Snowflake 벡터 타입으로 캐스팅

## 2-5. 저장된 임베딩 확인

```python
if st.button(":material/analytics: Query Embedding Table"):
    query = f"""
    SELECT CHUNK_ID, EMBEDDING, CREATED_TIMESTAMP,
           VECTOR_L2_DISTANCE(EMBEDDING, EMBEDDING) as SELF_DISTANCE
    FROM {full_embedding_table}
    ORDER BY CHUNK_ID
    """
    result_df = session.sql(query).to_pandas()
    st.session_state.queried_embeddings = result_df
    st.rerun()

# 개별 임베딩 벡터 보기
chunk_ids = emb_df['CHUNK_ID'].tolist()
selected_chunk = st.selectbox("Select CHUNK_ID", chunk_ids)

if st.button(":material/analytics: Load Embedding Vector"):
    selected_emb = emb_df[emb_df['CHUNK_ID'] == selected_chunk]['EMBEDDING'].iloc[0]
    st.code(selected_emb, language="python")
```

- `VECTOR_L2_DISTANCE(EMBEDDING, EMBEDDING)`: 자기 자신과의 거리 계산 (0이어야 정상)
- 특정 청크의 전체 768차원 벡터를 확인할 수 있는 옵션

# 3. 핵심 포인트 및 고려사항

## 임베딩 모델

- `snowflake-arctic-embed-m`: 품질과 성능의 균형을 맞춘 중간 크기 모델
- 768차원: 대부분의 RAG 시스템에 적합한 벡터 크기

## 배치 처리

- 대량의 청크를 효율적으로 처리하기 위해 배치 단위로 처리
- 진행 상황 표시로 사용자 경험 향상

## Day 19와의 통합

```python
st.session_state.embeddings_table = full_embedding_table
st.session_state.embeddings_database = st.session_state.day18_database
st.session_state.embeddings_schema = st.session_state.day18_schema
```

- Day 19 Cortex Search 서비스가 이 임베딩 테이블을 사용

# 실행 결과

## 실행 코드

Streamlit 실행 코드 = python -m streamlit run 파일명.py

예시 : `python -m streamlit run app/day18.py`

## 결과

- 100개의 리뷰 청크를 100개의 768차원 벡터로 변환
- Snowflake의 `REVIEW_EMBEDDINGS` 테이블에 저장
- Day 19에서 이 벡터들을 사용하여 의미 기반 검색 서비스 생성
- "따뜻한 장갑" 검색 시 "손을 포근하게" 같은 의미적으로 유사한 리뷰 찾기 가능
