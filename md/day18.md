이번 챌린지에서는 RAG 시스템에서 시맨틱 검색(semantic search)이 가능하도록 Day 17의 리뷰 청크에 대한 임베딩(embedding)을 생성하는 작업을 수행합니다. Snowflake Cortex의 `embed_text_768` 함수를 사용하여 텍스트 청크를 768차원 벡터로 변환한 다음, 이를 `VECTOR` 데이터 유형이 있는 Snowflake 테이블에 저장해야 합니다. 이 작업이 완료되면 Day 19에서 시맨틱 검색을 위한 벡터 임베딩이 준비됩니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 어떤 역할을 하는지 살펴보겠습니다.

#### 1. Day 17의 청크 로드

```python
import streamlit as st
from snowflake.cortex import embed_text_768
import pandas as pd
import json

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize with Day 17's table location
if 'day18_database' not in st.session_state:
    if 'chunks_database' in st.session_state:
        st.session_state.day18_database = st.session_state.chunks_database
        st.session_state.day18_schema = st.session_state.chunks_schema
    else:
        st.session_state.day18_database = "RAG_DB"
        st.session_state.day18_schema = "RAG_SCHEMA"

if st.button(":material/folder_open: Load Chunks", type="primary"):
    query = f"""
    SELECT 
        CHUNK_ID, DOC_ID, FILE_NAME, CHUNK_TEXT, CHUNK_SIZE, CHUNK_TYPE
    FROM {st.session_state.day18_database}.{st.session_state.day18_schema}.{st.session_state.day18_chunk_table}
    ORDER BY CHUNK_ID
    """
    df = session.sql(query).to_pandas()
    st.session_state.chunks_data = df
    st.rerun()
```

* **`from snowflake.cortex import embed_text_768`**: 768차원 임베딩을 생성하는 Cortex 함수를 임포트합니다.
* **세션 상태 통합**: Day 17의 `chunks_database`와 `chunks_schema`에서 청크 테이블 위치를 자동으로 감지합니다.
* **Load 버튼**: `SELECT`를 사용하여 Day 17 테이블에서 모든 청크를 쿼리합니다.
* **`st.rerun()`**: 로드된 청크를 표시하기 위해 즉시 새로고침을 강제합니다.

#### 2. 배치 프로세싱으로 임베딩 생성

```python
batch_size = st.selectbox("Batch Size", [10, 25, 50, 100], index=1)

if st.button(":material/calculate: Generate Embeddings", type="primary"):
    embeddings = []
    total_chunks = len(df)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(0, total_chunks, batch_size):
        batch_end = min(i + batch_size, total_chunks)
        status_text.text(f"Processing chunks {i+1} to {batch_end} of {total_chunks}")
        
        for idx, row in df.iloc[i:batch_end].iterrows():
            emb = embed_text_768(
                model='snowflake-arctic-embed-m', 
                text=row['CHUNK_TEXT']
            )
            embeddings.append({
                'chunk_id': row['CHUNK_ID'],
                'embedding': emb
            })
        
        progress_pct = batch_end / total_chunks
        progress_bar.progress(progress_pct)
    
    st.session_state.embeddings_data = embeddings
```

* **배치 크기 선택**: 더 나은 성능 제어를 위해 청크를 10, 25, 50 또는 100개씩 배치로 프로세싱할 수 있게 합니다.
* **진행 상황 추적**: 실시간 프로세싱 상태를 보여주기 위해 진행 바와 상태 텍스트를 생성합니다.
* **`embed_text_768(...)`**: 텍스트를 768차원 벡터로 변환하는 핵심 Cortex 함수입니다. `model='snowflake-arctic-embed-m'` 매개변수는 사용할 임베딩 모델을 지정합니다(Arctic Embed M은 시맨틱 검색에 최적화되어 있습니다).
* **임베딩 구조**: 텍스트의 시맨틱 의미를 나타내는 768개의 부동 소수점 숫자 리스트를 반환합니다.
* **저장**: 임베딩은 청크 ID와 임베딩 벡터를 포함하는 딕셔너리 리스트로 세션 상태에 저장됩니다.

#### 3. 생성된 임베딩 보기

```python
if 'embeddings_data' in st.session_state:
    with st.container(border=True):
        st.subheader(":material/looks_3: View Embeddings")
        
        embeddings = st.session_state.embeddings_data

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Embeddings Generated", len(embeddings))
        with col2:
            st.metric("Dimensions per Embedding", 768)
        
        # Show sample embedding
        with st.expander(":material/search: View Sample Embedding"):
            sample_emb = embeddings[0]['embedding']
            st.write("**First 10 values:**")
            st.write(sample_emb[:10])
```

* **컨테이너 구조**: 뷰는 서브헤더와 함께 테두리가 있는 컨테이너로 감싸져 있습니다.
* **지표 표시**: 생성된 총 임베딩 수를 보여주고 768차원 벡터 크기를 확인합니다.
* **샘플 미리보기**: 샘플 임베딩 벡터의 처음 10개 값(예: `[0.234, -0.456, 0.123, ...]`)을 표시합니다.
* **확인**: Snowflake에 저장하기 전에 임베딩이 성공적으로 생성되었는지 확인할 수 있게 합니다.

#### 4. Snowflake에 임베딩 저장

```python
# Table status check
try:
    check_query = f"""
    SELECT COUNT(*) as count 
    FROM {full_embedding_table}
    """
    result = session.sql(check_query).collect()
    current_count = result[0]['COUNT']
    
    if current_count > 0:
        st.warning(f":material/warning: **{current_count:,} embedding(s)** currently in table")
        embedding_table_exists = True
    else:
        st.info(":material/inbox: **Embedding table is empty**")
        embedding_table_exists = False
except:
    st.info(":material/inbox: **Embedding table doesn't exist yet**")
    embedding_table_exists = False

# Replace mode checkbox
replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.day18_embedding_table}`",
    key="day18_replace_mode"
)

if st.button(":material/save: Save Embeddings to Snowflake", type="primary"):
    with st.status("Saving embeddings...", expanded=True) as status:
        # Create or replace table based on mode
        if replace_mode:
            create_table_sql = f"""
            CREATE OR REPLACE TABLE {full_embedding_table} (
                CHUNK_ID NUMBER,
                EMBEDDING VECTOR(FLOAT, 768),
                CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
            """
            session.sql(create_table_sql).collect()
            st.write(":material/check_circle: Replaced existing table")
        else:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {full_embedding_table} (
                CHUNK_ID NUMBER,
                EMBEDDING VECTOR(FLOAT, 768),
                CREATED_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
            """
            session.sql(create_table_sql).collect()
            st.write(":material/check_circle: Table ready")
        
        # Insert embeddings
        st.write(f":material/looks_two: Inserting {len(embeddings)} embeddings...")
        
        for i, emb_data in enumerate(embeddings):
            # Convert embedding to list
            if isinstance(emb_data['embedding'], list):
                emb_list = emb_data['embedding']
            else:
                emb_list = list(emb_data['embedding'])
            
            # Convert to proper array format for Snowflake
            emb_array = "[" + ",".join([str(float(x)) for x in emb_list]) + "]"
            
            insert_sql = f"""
            INSERT INTO {full_embedding_table} (CHUNK_ID, EMBEDDING)
            SELECT {emb_data['chunk_id']}, {emb_array}::VECTOR(FLOAT, 768)
            """
            session.sql(insert_sql).collect()
            
            if (i + 1) % 10 == 0:
                st.write(f"Saved {i + 1} of {len(embeddings)} embeddings...")
        
        status.update(label="Embeddings saved!", state="complete", expanded=False)
```

* **테이블 상태 확인**: 저장 전 임베딩 테이블 존재 여부를 확인하고 현재 레코드 수를 보여줍니다.
* **교체 모드**: 사용자가 모든 기존 임베딩을 교체(`CREATE OR REPLACE TABLE`)하거나 기존 데이터에 추가(`CREATE TABLE IF NOT EXISTS`)할지 선택할 수 있게 합니다.
* **`VECTOR(FLOAT, 768)`**: 벡터 연산 및 유사성 계산에 최적화된 임베딩 저장을 위한 Snowflake의 특수 데이터 유형입니다.
* **유형 처리**: 임베딩이 이미 리스트인지 또는 `list()`를 사용하여 변환해야 하는지 확인합니다.
* **배열 문자열 변환**: Python 리스트를 Snowflake가 파싱할 수 있는 `"[0.1, 0.2, 0.3, ...]" `와 같은 문자열 형식으로 변환합니다.
* **`::VECTOR(FLOAT, 768)`**: 이 SQL 캐스팅 구문은 문자열 배열을 Snowflake의 VECTOR 유형으로 변환합니다. 올바른 유형 변환을 위해 직접적인 `VALUES` 대신 `SELECT ... ::VECTOR`를 사용하는 것이 권장됩니다.
* **진행 업데이트**: `st.status()` 컨테이너를 사용하고 삽입된 임베딩 10개마다 진행 상황을 보여줍니다.
* **세션 상태 저장**: Day 19의 Cortex Search 생성을 위해 임베딩 테이블 위치를 저장합니다.

#### 5. 저장된 임베딩 보기

```python
# View Saved Embeddings Section
with st.container(border=True):
    st.subheader(":material/search: View Saved Embeddings")
    
    # Check if embeddings table exists and show record count
    try:
        count_result = session.sql(f"""
            SELECT COUNT(*) as CNT FROM {full_embedding_table}
        """).collect()
        
        if count_result:
            record_count = count_result[0]['CNT']
            if record_count > 0:
                st.warning(f":material/warning: **{record_count:,} embedding(s)** currently in table")
            else:
                st.info(":material/inbox: **Embedding table is empty**")
    except:
        st.info(":material/inbox: **Embedding table doesn't exist yet**")
    
    query_button = st.button(":material/analytics: Query Embedding Table", type="secondary")
    
    if query_button:
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
        st.session_state.queried_embeddings = result_df
        st.session_state.queried_embeddings_table = full_embedding_table
        st.rerun()
```

* **별도 뷰 섹션**: 테이블에 저장된 임베딩을 보기 위한 전용 컨테이너입니다.
* **레코드 수 확인**: 쿼리 전 테이블에 있는 현재 임베딩 수를 표시합니다.
* **Query 버튼**: 확인을 위해 테이블에서 모든 임베딩을 가져옵니다.
* **`VECTOR_L2_DISTANCE(EMBEDDING, EMBEDDING)`**: 각 임베딩과 자기 자신 사이의 거리를 계산하며, 항상 0이어야 합니다. 이는 임베딩이 올바르게 저장되었음을 검증합니다.
* **세션 상태 저장**: 앱 재실행 시에도 결과가 유지되도록 저장합니다.
* **표시 컬럼**: CHUNK_ID, CREATED_TIMESTAMP 및 SELF_DISTANCE를 보여줍니다(하지만 너무 커서 표시할 수 없는 전체 EMBEDDING 컬럼은 제외).

#### 6. 개별 임베딩 벡터 보기

```python
# Display results if available in session state
if 'queried_embeddings' in st.session_state:
    emb_df = st.session_state.queried_embeddings
    
    if len(emb_df) > 0:
        # Summary metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Embeddings", len(emb_df))
        with col2:
            st.metric("Dimensions", "768")
        
        # Display table without EMBEDDING column
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
        st.info(":material/lightbulb: Self-distance should be 0, confirming embeddings are stored correctly")
        
        # View individual embedding vectors
        if embedding_col:
            with st.expander(":material/search: View Individual Embedding Vectors"):
                # Find CHUNK_ID column (case-insensitive)
                chunk_id_col = None
                for col in emb_df.columns:
                    if col.upper() == 'CHUNK_ID':
                        chunk_id_col = col
                        break
                
                chunk_ids = emb_df[chunk_id_col].tolist()
                selected_chunk = st.selectbox("Select CHUNK_ID", chunk_ids, key="view_embedding_chunk")
                
                if st.button(":material/analytics: Load Embedding Vector", key="load_embedding_btn"):
                    selected_emb = emb_df[emb_df[chunk_id_col] == selected_chunk][embedding_col].iloc[0]
                    st.session_state.loaded_embedding = selected_emb
                    st.session_state.loaded_embedding_chunk = selected_chunk
                    st.rerun()
                
                # Display loaded embedding
                if 'loaded_embedding' in st.session_state:
                    st.write(f"**Embedding Vector for CHUNK_ID {st.session_state.loaded_embedding_chunk}:**")
                    
                    # Convert to list if needed
                    emb_vector = st.session_state.loaded_embedding
                    if isinstance(emb_vector, str):
                        import json
                        emb_vector = json.loads(emb_vector)
                    elif hasattr(emb_vector, 'tolist'):
                        emb_vector = emb_vector.tolist()
                    elif not isinstance(emb_vector, list):
                        emb_vector = list(emb_vector)
                    
                    st.caption(f"Vector length: {len(emb_vector)} dimensions")
                    st.code(emb_vector, language="python")
```

* **결과 표시**: 세션 상태에 저장된 임베딩이 있으면 보여줍니다.
* **대소문자 구분 없는 컬럼 처리**: Snowflake의 대문자 컬럼 이름을 처리하기 위해 'EMBEDDING' 및 'CHUNK_ID' 컬럼을 대소문자 구분 없이 검색합니다.
* **선택적 표시**: 너무 큰 EMBEDDING 컬럼(768차원)을 메인 데이터프레임 표시에서 제외합니다.
* **선택 드롭다운**: 사용자가 검사할 임베딩을 선택할 수 있도록 모든 청크 ID를 나열합니다.
* **Load 버튼**: 선택된 임베딩과 청크 ID를 세션 상태에 저장합니다.
* **유형 변환**: 여러 임베딩 형식(문자열, 리스트, numpy 배열)을 처리하고 표시를 위해 리스트로 변환합니다.
* **`st.code(...)`**: 전체 768차원 벡터를 포맷된 Python 리스트로 표시하여 쉽게 복사하거나 검사할 수 있게 합니다.
* **확인**: 시맨틱 검색에 사용하기 전에 임베딩이 완전하고 올바르게 포맷되었는지 확인합니다.

#### 7. Day 19와의 통합

```python
st.session_state.embeddings_table = f"{database}.{schema}.{embedding_table}"
st.session_state.embeddings_database = database
st.session_state.embeddings_schema = schema
```

* **Day 19로 전달**: 내일의 Cortex Search 서비스 생성을 위해 임베딩 테이블 위치를 저장합니다.
* **시맨틱 검색 준비 완료**: Day 19는 이러한 임베딩을 사용하여 정확한 단어 일치가 아닌 의미에 기반하여 유사한 리뷰를 찾을 수 있는 검색 서비스를 만듭니다.

이 코드가 실행되면 Day 17의 텍스트 청크를 768차원 벡터로 변환하고, Snowflake의 VECTOR 데이터 유형에 저장하며, 임베딩이 올바르게 생성되었는지 확인할 수 있는 도구를 제공하는 완전한 임베딩 생성 시스템을 갖게 됩니다. 이러한 벡터는 단순한 키워드 매칭이 아닌 의미를 이해하는 시맨틱 검색을 가능하게 합니다.

---

### :material/library_books: 리소스
- [Cortex EMBED_TEXT_768 Function](https://docs.snowflake.com/en/sql-reference/functions/embed_text_768-snowflake-cortex)
- [Understanding Embeddings](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ml-embeddings)
- [Snowflake VECTOR Data Type](https://docs.snowflake.com/en/sql-reference/data-types-vector)
- [Vector Distance Functions](https://docs.snowflake.com/en/sql-reference/functions-vector)
