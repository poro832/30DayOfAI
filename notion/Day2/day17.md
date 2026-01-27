# Loading and Transforming Customer Reviews for RAG (고객 리뷰 로드 및 변환)

# 0. 목표

<aside>
💡

**Day 16에서 저장한 고객 리뷰를 로드하고 검색 가능한 청크로 변환**

1. Snowflake에서 고객 리뷰 데이터 로드
2. 두 가지 처리 전략 제공 (리뷰를 그대로 유지 vs 긴 리뷰 분할)
3. 청크를 Snowflake 테이블에 저장하여 Day 18 임베딩 생성 준비

</aside>

# 1. 개요 및 필요성 (Overview)

- RAG 파이프라인의 **두 번째 단계**로, 추출된 문서를 임베딩에 적합한 크기의 청크로 분할합니다.
- 고객 리뷰는 보통 짧기 때문에(~50-150단어), 각 리뷰를 하나의 청크로 유지하는 것을 권장합니다.
- 필요시 긴 리뷰를 중복(overlap)이 있는 작은 청크로 분할할 수도 있습니다.

# 2. Streamlit 앱 구현 (Implementation)

## 2-1. Day 16 데이터 로드

```python
import streamlit as st
import pandas as pd

# Snowflake 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Day 16의 테이블 참조 확인
if 'day17_database' not in st.session_state:
    if 'rag_source_database' in st.session_state:
        st.session_state.day17_database = st.session_state.rag_source_database
        st.session_state.day17_schema = st.session_state.rag_source_schema
    else:
        st.session_state.day17_database = "RAG_DB"
        st.session_state.day17_schema = "RAG_SCHEMA"

# 문서 로드 버튼
if st.button(":material/folder_open: Load Reviews", type="primary"):
    query = f"""
    SELECT DOC_ID, FILE_NAME, FILE_TYPE, EXTRACTED_TEXT,
           UPLOAD_TIMESTAMP, WORD_COUNT, CHAR_COUNT
    FROM {st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}
    ORDER BY FILE_NAME
    """
    df = session.sql(query).to_pandas()
    # 세션 상태에 저장
    st.session_state.loaded_data = df
    st.rerun()
```

- Day 16에서 저장한 `rag_source_database`와 `rag_source_schema`를 자동으로 감지
- `EXTRACTED_TEXT` 컬럼에서 전체 리뷰 텍스트를 가져옴
- `.to_pandas()`: Snowflake 결과를 Pandas DataFrame으로 변환하여 Python에서 쉽게 처리

## 2-2. 처리 전략 선택

```python
processing_option = st.radio(
    "Select processing strategy:",
    ["Keep each review as a single chunk (Recommended)", 
     "Chunk reviews longer than threshold"],
    index=0
)

# 청크 크기 컨트롤 추가 (청크 옵션 선택 시에만 표시)
if "Chunk reviews" in processing_option:
    chunk_size = st.slider("Chunk Size (words):", 50, 500, 200, 50)
    overlap = st.slider("Overlap (words):", 0, 100, 50, 10)
```

- **옵션 1 (권장)**: 각 리뷰를 하나의 청크로 유지 - 짧은 고객 리뷰에 최적
- **옵션 2**: 긴 리뷰를 분할 - 200단어 이상의 리뷰를 중복이 있는 작은 청크로 나눔
- `index=0`: 첫 번째 옵션(리뷰 그대로 유지)을 기본값으로 설정
- 슬라이더는 두 번째 옵션을 선택했을 때만 표시됨

## 2-3. 청크 생성

```python
chunks = []

if "Keep each review" in processing_option:
    # 옵션 1: 리뷰 1개 = 청크 1개
    for idx, row in df.iterrows():
        chunks.append({
            'chunk_id': idx + 1,
            'doc_id': row['DOC_ID'],
            'file_name': row['FILE_NAME'],
            'chunk_text': row['EXTRACTED_TEXT'],
            'chunk_size': row['WORD_COUNT'],
            'chunk_type': 'full_review'
        })
else:
    # 옵션 2: 긴 리뷰를 청크로 분할
    chunk_id = 1
    for idx, row in df.iterrows():
        text = row['EXTRACTED_TEXT']
        words = text.split()
        
        if len(words) <= chunk_size:
            # 짧은 리뷰는 그대로 유지
            chunks.append({
                'chunk_id': chunk_id,
                'chunk_text': text,
                'chunk_size': len(words),
                'chunk_type': 'full_review'
            })
            chunk_id += 1
        else:
            # 긴 리뷰 분할
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                chunk_text = ' '.join(chunk_words)
                chunks.append({
                    'chunk_id': chunk_id,
                    'chunk_text': chunk_text,
                    'chunk_size': len(chunk_words),
                    'chunk_type': 'chunked_review'
                })
                chunk_id += 1
```

- **옵션 1**: 각 리뷰의 `EXTRACTED_TEXT`를 그대로 하나의 청크로 복사 (100개 리뷰 = 100개 청크)
- **옵션 2**: 텍스트를 단어로 분할한 후 `range(0, len(words), chunk_size - overlap)`로 중복 청크 생성
- **중복 계산**: chunk_size=200, overlap=50이면 150단어씩 이동 (200-50=150)
- `chunk_type`: 추적을 위해 `'full_review'` 또는 `'chunked_review'`로 레이블 지정

## 2-4. Replace Mode (교체 모드) 관리

```python
# 테이블 상태에 따라 체크박스 상태 초기화 또는 업데이트
if 'day17_replace_mode' not in st.session_state:
    # 처음 - 테이블 존재 여부에 따라 초기화
    st.session_state.day17_replace_mode = chunk_table_exists
else:
    # 테이블 이름 변경 확인 - 변경 시 새 테이블 상태에 따라 리셋
    if st.session_state.get('day17_last_chunk_table') != full_chunk_table:
        st.session_state.day17_replace_mode = chunk_table_exists
        st.session_state.day17_last_chunk_table = full_chunk_table

# 교체 모드 체크박스
replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.day17_chunk_table}`",
    key="day17_replace_mode"
)
```

- 청크 테이블에 데이터가 있으면 체크박스가 기본으로 체크됨
- 테이블 이름이 변경되면 새 테이블의 상태에 따라 체크박스 리셋
- `key="day17_replace_mode"`: 세션 상태와 연결하여 프로그래밍 방식 제어 가능

## 2-5. Snowflake에 청크 저장

```python
# 1단계: 테이블이 없으면 생성
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
    session.sql(f"TRUNCATE TABLE {full_chunk_table}").collect()

# 3단계: 청크 삽입
chunks_df = pd.DataFrame(chunks)

# Snowflake 테이블과 일치하도록 열 이름을 대문자로 변경
chunks_df_upper = chunks_df[['chunk_id', 'doc_id', 'file_name', 
                              'chunk_text', 'chunk_size', 'chunk_type']].copy()
chunks_df_upper.columns = ['CHUNK_ID', 'DOC_ID', 'FILE_NAME', 
                            'CHUNK_TEXT', 'CHUNK_SIZE', 'CHUNK_TYPE']

# Snowflake에 쓰기
session.write_pandas(chunks_df_upper,
                    table_name=st.session_state.day17_chunk_table,
                    database=st.session_state.day17_database,
                    schema=st.session_state.day17_schema,
                    overwrite=replace_mode)
```

- `CHUNK_TEXT`: Day 18에서 임베딩할 실제 텍스트를 저장
- `session.write_pandas()`: 100개 이상의 청크를 개별 INSERT 문보다 훨씬 빠르게 일괄 삽입
- `overwrite=replace_mode`: True면 기존 데이터 삭제 후 삽입, False면 추가

## 2-6. 저장된 청크 확인

```python
if st.button(":material/analytics: Query Chunk Table"):
    chunks_df = session.sql(f"""
        SELECT CHUNK_ID, FILE_NAME, CHUNK_SIZE, CHUNK_TYPE,
               LEFT(CHUNK_TEXT, 100) AS TEXT_PREVIEW
        FROM {full_chunk_table}
        ORDER BY CHUNK_ID
    """).to_pandas()
    st.session_state.queried_chunks = chunks_df
    st.rerun()

# 전체 청크 텍스트 보기
chunk_id = st.selectbox("Select Chunk ID:", options=chunks_df['CHUNK_ID'].tolist())

if st.button("Load Chunk Text"):
    text_result = session.sql(f"""
        SELECT CHUNK_TEXT FROM {full_chunk_table} 
        WHERE CHUNK_ID = {chunk_id}
    """).collect()
    chunk_text = text_result[0]['CHUNK_TEXT']
    st.text_area("Full Chunk Text", value=chunk_text, height=300)
```

- `LEFT(CHUNK_TEXT, 100)`: 각 청크의 처음 100자만 미리보기로 표시
- 특정 청크의 전체 텍스트를 확인할 수 있는 옵션
- 청크가 올바르게 저장되었고 예상된 텍스트를 포함하는지 확인

# 3. 핵심 포인트 및 고려사항

## 청크 전략 (Chunking Strategy)

- 짧은 고객 리뷰(50-150단어)는 그대로 유지하는 것이 최적
- 긴 문서의 경우 중복(overlap)을 사용하여 문맥 연속성 유지

## Day 18과의 통합

```python
st.session_state.chunks_table = f"{database}.{schema}.{chunk_table}"
st.session_state.chunks_database = database
st.session_state.chunks_schema = schema
```

- Day 18이 자동으로 이 청크 테이블을 찾아 임베딩 생성

## 테이블 관리

- Replace vs Append 모드로 데이터 관리 전략 제공
- 테이블 상태에 따라 체크박스 기본값 자동 설정

# 실행 결과

## 실행 코드

Streamlit 실행 코드 = python -m streamlit run 파일명.py

예시 : `python -m streamlit run app/day17.py`

## 결과

- Day 16의 100개 리뷰를 100개 청크로 변환 (또는 필요시 더 작은 청크로 분할)
- Snowflake의 `REVIEW_CHUNKS` 테이블에 저장
- 각 청크는 적절한 크기로 임베딩 생성 준비 완료
- Day 18에서 이 청크들을 벡터로 변환하여 의미 기반 검색 가능
