이번 챌린지에서는 Day 16에서 업로드한 고객 리뷰를 로드하고, 이를 프로세싱하여 RAG 애플리케이션을 위한 검색 가능한 청크(chunk)를 만드는 작업을 수행합니다. 두 가지 프로세싱 전략을 제공해야 합니다. 각 리뷰를 하나의 청크로 그대로 유지하거나(짧은 리뷰에 권장), 긴 리뷰를 겹치는 부분이 있는 작은 청크로 분할하는 것입니다. 이 작업이 완료되면 적절한 크기의 텍스트 청크가 Snowflake에 저장되어 Day 18에서 임베딩 생성 준비를 마치게 됩니다.

**데이터셋**: Day 16에서 업로드되어 `EXTRACTED_DOCUMENTS` 테이블에 저장된 고객 리뷰를 사용합니다. 각 리뷰는 약 50-150개의 단어로 구성되어 있으며 제품 피드백을 포함하고 있습니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 어떤 역할을 하는지 살펴보겠습니다.

#### 1. Day 16 리뷰 로드

```python
import streamlit as st
import pandas as pd

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize session state with Day 16's table location
if 'day17_database' not in st.session_state:
    if 'rag_source_database' in st.session_state:
        st.session_state.day17_database = st.session_state.rag_source_database
        st.session_state.day17_schema = st.session_state.rag_source_schema
    else:
        st.session_state.day17_database = "RAG_DB"
        st.session_state.day17_schema = "RAG_SCHEMA"

if st.button(":material/folder_open: Load Reviews", type="primary"):
    query = f"""
    SELECT 
        DOC_ID, FILE_NAME, FILE_TYPE, EXTRACTED_TEXT,
        UPLOAD_TIMESTAMP, WORD_COUNT, CHAR_COUNT
    FROM {st.session_state.day17_database}.{st.session_state.day17_schema}.{st.session_state.day17_table_name}
    ORDER BY FILE_NAME
    """
    df = session.sql(query).to_pandas()
    st.session_state.loaded_data = df
    st.rerun()
```

* **세션 상태 통합**: 가능한 경우 Day 16의 `rag_source_database`에서 데이터베이스와 스키마를 자동으로 감지합니다.
* **Load 버튼**: 클릭 시 `SELECT`를 사용하여 Day 16 테이블에서 모든 문서를 쿼리합니다.
* **`.to_pandas()`**: Snowflake 결과를 Python에서 더 쉽게 프로세싱할 수 있도록 Pandas DataFrame으로 변환합니다.
* **`st.rerun()`**: 다른 상호 작용을 기다리지 않고 즉시 새로고침하여 로드된 데이터를 보여줍니다.

#### 2. 프로세싱 전략 선택

```python
processing_option = st.radio(
    "Select processing strategy:",
    ["Keep each review as a single chunk (Recommended)", 
     "Chunk reviews longer than threshold"],
    index=0
)

if "Chunk reviews" in processing_option:
    chunk_size = st.slider("Chunk Size (words):", 50, 500, 200, 50)
    overlap = st.slider("Overlap (words):", 0, 100, 50, 10)
```

* **라디오 버튼**: 두 가지 명확한 옵션을 제공합니다. 첫 번째 옵션은 리뷰를 그대로 유지합니다(짧은 고객 리뷰에 가장 적합).
* **`index=0`**: 첫 번째 옵션을 기본값으로 설정합니다(각 리뷰를 단일 청크로 유지).
* **조건부 슬라이더**: 두 번째 옵션이 선택된 경우에만 청크 크기와 겹침(overlap) 제어기가 나타납니다.
* **Chunk size**: 각 청크에 포함될 수 있는 단어 수를 제어합니다(기본값: 200단어).
* **Overlap**: 연속된 청크 간에 겹치는 단어 수를 설정합니다(기본값: 50단어). 이는 문맥의 연속성을 유지합니다.

#### 3. 리뷰에서 청크 생성

```python
# Option 1: One review = one chunk
for idx, row in df.iterrows():
    chunks.append({
        'chunk_id': idx + 1,
        'doc_id': row['DOC_ID'],
        'file_name': row['FILE_NAME'],
        'chunk_text': row['EXTRACTED_TEXT'],
        'chunk_size': row['WORD_COUNT'],
        'chunk_type': 'full_review'
    })

# Option 2: Split longer reviews
words = row['EXTRACTED_TEXT'].split()
if len(words) > chunk_size:
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        chunks.append({
            'chunk_id': len(chunks) + 1,
            'chunk_text': chunk_text,
            'chunk_size': len(chunk_words),
            'chunk_type': 'split_chunk'
        })
```

* **옵션 1 (전체 리뷰)**: 각 리뷰의 `EXTRACTED_TEXT`를 단일 청크로 복사하기만 합니다. 100개 리뷰의 경우 100개 청크를 생성합니다.
* **옵션 2 (분할)**: `.split()`을 사용하여 텍스트를 단어로 분할한 다음, `range(0, len(words), chunk_size - overlap)`을 사용하여 겹치는 청크를 생성합니다.
* **Overlap 계산**: chunk_size=200이고 overlap=50이면 매번 150단어씩 이동합니다(200-50=150). 즉, 이전 청크의 마지막 50단어가 다음 청크의 첫 50단어가 됩니다.
* **`chunk_type`**: 추적을 위해 청크가 `'full_review'`(그대로 유지)인지 `'split_chunk'`(분할됨)인지 표시합니다.

#### 4. 청크 테이블 존재 여부 확인

```python
try:
    result = session.sql(f"SELECT COUNT(*) as count FROM {full_chunk_table}").collect()
    record_count = result[0]['COUNT']
    
    if record_count > 0:
        chunk_table_exists = True
    else:
        chunk_table_exists = False
except:
    chunk_table_exists = False
```

* **존재 여부 확인**: 청크 테이블이 존재하고 데이터가 있는지 쿼리합니다.
* **`COUNT(*)`**: 테이블의 행 수를 반환합니다.
* **Try/except**: 테이블이 없으면 쿼리가 실패하며, 이를 "테이블이 아직 없음"으로 간주합니다.
* **스마트 기본값**: 이 불리언(boolean) 값은 교체 모드 체크박스의 기본 상태를 설정하는 데 사용됩니다.

#### 5. 청크 교체 모드

```python
# Initialize checkbox state based on table status
if 'day17_replace_mode' not in st.session_state:
    st.session_state.day17_replace_mode = chunk_table_exists
else:
    # Reset if table name changed
    if st.session_state.get('day17_last_chunk_table') != full_chunk_table:
        st.session_state.day17_replace_mode = chunk_table_exists
        st.session_state.day17_last_chunk_table = full_chunk_table

replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.day17_chunk_table}`",
    key="day17_replace_mode"
)
```

* **세션 상태 관리**: 테이블에 데이터가 있는지 여부에 따라 체크박스를 초기화합니다(있으면 체크, 없으면 해제).
* **테이블 이름 추적**: 사용자가 청크 테이블 이름을 변경하면 새 테이블 상태에 따라 체크박스 상태가 재설정됩니다.
* **`key="day17_replace_mode"`**: 체크박스를 세션 상태에 바인딩하여 사용자의 클릭을 존중하면서도 프로그램에서 제어할 수 있게 합니다.
* **동적 라벨**: 체크박스 라벨이 현재 청크 테이블 이름을 보여주도록 업데이트됩니다.

#### 6. Snowflake에 청크 저장

```python
# Create chunk table
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

# Convert DataFrame columns to uppercase
chunks_df_upper = chunks_df.copy()
chunks_df_upper.columns = ['CHUNK_ID', 'DOC_ID', 'FILE_NAME', 'CHUNK_TEXT', 'CHUNK_SIZE', 'CHUNK_TYPE']

# Write to Snowflake
session.write_pandas(chunks_df_upper, table_name=chunk_table, 
                     database=database, schema=schema, 
                     overwrite=replace_mode)
```

* **테이블 스키마**: 청크 저장을 위한 구조를 정의합니다. `CHUNK_TEXT` 컬럼은 Day 18에서 임베딩될 실제 텍스트를 보관합니다.
* **`CREATED_TIMESTAMP`**: 각 청크가 생성된 시간을 자동으로 기록합니다.
* **컬럼 이름 변환**: Snowflake는 대문자 컬럼 이름을 예상합니다. DataFrame을 복사하고 저장 전에 모든 컬럼 이름을 대문자로 변경합니다.
* **`session.write_pandas()`**: DataFrame을 Snowflake에 대량으로 기록합니다. 100개 이상의 청크를 개별 INSERT 문으로 처리하는 것보다 훨씬 빠릅니다.
* **`overwrite=replace_mode`**: True일 때 쓰기 전에 기존 테이블 데이터를 삭제합니다. False일 때 기존 데이터에 추가합니다.

#### 7. 저장된 청크 쿼리

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
```

* **Query 버튼**: 확인을 위해 테이블에서 모든 청크를 가져옵니다.
* **`LEFT(CHUNK_TEXT, 100)`**: 각 청크의 처음 100자만 미리보기로 보여주어 테이블을 읽기 쉽게 유지합니다.
* **`AS TEXT_PREVIEW`**: 명확성을 위해 잘린 컬럼의 이름을 바꿉니다.
* **세션 상태 유지**: 결과가 앱 재실행 시에도 유지되도록 저장합니다.

#### 8. 전체 청크 텍스트 보기

```python
chunk_id = st.selectbox("Select Chunk ID:", options=chunks_df['CHUNK_ID'].tolist())

if st.button("Load Chunk Text"):
    st.session_state.selected_chunk_id = chunk_id
    st.session_state.load_chunk_text = True
    st.rerun()

if st.session_state.get('load_chunk_text'):
    text_result = session.sql(f"""
        SELECT CHUNK_TEXT FROM {full_chunk_table} 
        WHERE CHUNK_ID = {st.session_state.selected_chunk_id}
    """).collect()
    
    chunk_text = text_result[0]['CHUNK_TEXT']
    st.text_area("Full Chunk Text", value=chunk_text, height=300)
```

* **선택 드롭다운**: 사용자가 검사할 청크를 선택할 수 있도록 모든 청크 ID를 나열합니다.
* **Load 버튼**: 선택된 청크 ID를 저장하고 세션 상태에 플래그를 설정합니다.
* **`st.rerun()`**: 즉시 새로고침하여 로드된 청크 텍스트를 표시합니다.
* **텍스트 영역 표시**: 전체 청크 텍스트를 스크롤 가능한 상자(높이 300픽셀)에 보여줍니다.
* **확인**: 청크가 올바르게 저장되었고 예상된 텍스트를 포함하고 있는지 확인합니다.

#### 9. Day 18과의 통합

```python
st.session_state.chunks_table = f"{database}.{schema}.{chunk_table}"
st.session_state.chunks_database = database
st.session_state.chunks_schema = schema
```

* **Day 18로 전달**: 내일의 임베딩 생성을 위해 청크 테이블 위치를 저장합니다.
* **원활한 인계**: Day 18은 이 테이블을 자동으로 찾아 각 청크에 대한 임베딩을 생성합니다.
* **벡터화 준비 완료**: 최적의 임베딩 품질을 위해 청크가 너무 길거나 짧지 않게 적절한 크기로 준비되었습니다.

이 코드가 실행되면 Day 16의 문서를 가져와 적절한 크기의 청크(리뷰를 유지하거나 겹침을 허용하며 분할)로 변환하고, Day 18의 임베딩 생성을 위해 Snowflake 테이블에 저장하는 청크 프로세싱 시스템을 갖게 됩니다.

---

### :material/library_books: 리소스
- [Snowpark DataFrames](https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes)
- [write_pandas Documentation](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/api/snowflake.snowpark.Session.write_pandas)
- [Text Chunking Best Practices](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search#chunking-strategies)
