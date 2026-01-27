이번 챌린지에서는 RAG 파이프라인의 첫 번째 단계인 문서에서 텍스트를 추출하고 **Snowflake에 저장**하는 작업을 수행합니다. 여러 개의 TXT, MD(마크다운), PDF 파일을 한 번에 수락하는 **배치 파일 업로더**를 만들고, 원시 텍스트 콘텐츠를 추출하여 데이터베이스 테이블에 저장해야 합니다. 이 작업이 완료되면 청킹(chunking), 임베딩(embedding) 및 RAG 프로세싱을 위한 깨끗한 텍스트가 준비됩니다.

---

### :material/download: 샘플 리뷰 데이터 다운로드

빠른 시작을 위해 Avalanche 겨울 스포츠 장비의 고객 리뷰 100개가 포함된 샘플 데이터셋을 다운로드하세요.

**📥 다운로드 링크**: [review.zip](https://github.com/streamlit/30DaysOfAI/raw/refs/heads/main/assets/review.zip)

**사용 방법:**
1. 위의 다운로드 링크를 클릭하여 `review.zip`을 받습니다.
2. 컴퓨터에서 다운로드한 파일의 압축을 풉니다.
3. 100개의 리뷰 파일(`review-001.txt`에서 `review-100.txt`)을 찾을 수 있습니다.
4. 앱의 파일 업로더를 사용하여 100개 파일을 한 번에 모두 선택합니다.
5. **Extract Text**를 클릭하여 프로세싱하고 Snowflake에 저장합니다.

**포함된 내용:**
- TXT 형식의 고객 리뷰 파일 100개
- 각 리뷰에는 제품명, 날짜, 리뷰 요약, 감정 점수 및 주문 ID가 포함되어 있습니다.
- 배치 프로세싱 테스트 및 RAG 애플리케이션 구축에 최적화되어 있습니다.

**💡 팁:** 100개 파일을 한 번에 업로드하여 배치 프로세싱이 작동하는 모습을 확인해 보세요!

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 어떤 역할을 하는지 살펴보겠습니다.

#### 1. 데이터베이스 구성 및 세션 상태

```python
import streamlit as st
from pypdf import PdfReader
import io

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize session state for persistence
if 'database' not in st.session_state:
    st.session_state.database = "RAG_DB"
    st.session_state.schema = "RAG_SCHEMA"
    st.session_state.table_name = "EXTRACTED_DOCUMENTS"
```

* **`import streamlit as st`**: 웹 인터페이스 구축을 위해 Streamlit 라이브러리를 임포트합니다.
* **`from pypdf import PdfReader`**: PDF 파일에서 텍스트를 추출하기 위해 PDF 읽기 라이브러리를 임포트합니다.
* **`try/except` 블록**: 환경을 자동으로 감지하고 적절하게 연결합니다(SiS vs 로컬/커뮤니티 클라우드).
* **`session`**: 테이블을 생성하고 데이터를 삽입하는 데 사용할 설정된 Snowflake 연결입니다.
* **세션 상태 초기화**: 데이터베이스, 스키마 및 테이블 이름을 `st.session_state`에 저장하여 앱 재실행 및 사용자 상호 작용 전반에 걸쳐 유지되도록 합니다.

#### 2. 배치 파일 업로드

```python
uploaded_files = st.file_uploader(
    "Choose file(s)",
    type=["txt", "md", "pdf"],
    accept_multiple_files=True,
    help="Supported formats: TXT, MD, PDF. Upload multiple files at once!"
)

if uploaded_files:
    st.success(f":material/check_circle: {len(uploaded_files)} file(s) uploaded")
```

* **`accept_multiple_files=True`**: 배치 업로드를 가능하게 하는 핵심 매개변수입니다. 사용자는 파일을 하나씩 업로드하는 대신 20개, 50개 또는 100개 파일을 한 번에 선택할 수 있습니다.
* **`type=["txt", "md", "pdf"]`**: 업로드를 이러한 파일 유형으로 제한하여 잘못된 파일 형식을 방지합니다.
* **`uploaded_files`**: 파일 객체 리스트를 반환합니다(업로드된 것이 없으면 빈 리스트).
* **상태 메시지**: 몇 개의 파일이 선택되었는지 확인하기 위해 "X file(s) uploaded"를 표시합니다.

#### 3. 프로세스 버튼 및 진행 상황 추적

```python
# Process files button
process_button = st.button(
    f":material/sync: Extract Text from {len(uploaded_files)} File(s)",
    type="primary",
    use_container_width=True
)

if process_button:
    # Initialize progress tracking
    success_count = 0
    error_count = 0
    extracted_data = []
    
    progress_bar = st.progress(0, text="Starting extraction...")
    status_container = st.empty()
```

* **`st.button(...)`**: 추출 프로세스를 시작하는 기본 버튼을 생성합니다.
* **동적 라벨**: 버튼 텍스트에 프로세싱될 정확한 파일 수가 표시됩니다.
* **`type="primary"`**: 버튼을 시각적으로 돋보이게 만듭니다.
* **범위 변수**: `success_count`, `error_count` 및 `extracted_data`는 버튼 블록 내부에서 초기화되므로 버튼을 클릭한 후에만 사용할 수 있습니다.
* **진행 표시기**: `progress_bar`와 `status_container`는 프로세싱 중에 실시간 피드백을 제공합니다.

#### 4. 테이블 교체 모드

```python
# Check if table exists
try:
    result = session.sql(f"SELECT COUNT(*) as count FROM {full_table_name}").collect()
    table_exists = True
except:
    table_exists = False

replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.table_name}`",
    value=table_exists,
    help=f"When enabled, replaces all existing data in {full_table_name}"
)
```

* **테이블 존재 여부 확인**: 대상 테이블에 이미 데이터가 있는지 데이터베이스에 쿼리합니다.
* **스마트 기본값**: 테이블에 데이터가 있으면 체크박스가 기본적으로 선택되어 교체를 제안합니다. 새 테이블인 경우 체크박스가 해제되어 추가를 제안합니다.
* **동적 라벨**: 체크박스 라벨이 현재 테이블 이름을 보여주도록 업데이트되어 무엇이 교체될지 명확하게 해줍니다.
* **교체 vs 추가**: 선택 시 새 업로드 전에 기존 데이터를 삭제합니다. 선택 해제 시 새 파일이 기존 데이터에 추가됩니다.

#### 5. 파일에서 텍스트 추출

```python
for idx, uploaded_file in enumerate(uploaded_files):
    progress_pct = (idx + 1) / len(uploaded_files)
    progress_bar.progress(progress_pct, text=f"Processing {idx+1}/{len(uploaded_files)}: {uploaded_file.name}")
    
    # Extract text based on file extension
    if uploaded_file.name.lower().endswith(('.txt', '.md')):
        extracted_text = uploaded_file.read().decode("utf-8")
    elif uploaded_file.name.lower().endswith('.pdf'):
        pdf_reader = PdfReader(io.BytesIO(uploaded_file.read()))
        extracted_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n\n"
```

* **진행 상황 추적**: `enumerate()`는 인덱스와 파일 객체를 모두 제공하여 "Processing 15/30: review-015.txt"와 같이 표시할 수 있게 해줍니다.
* **`.progress(progress_pct, ...)`**: 완료 백분율과 현재 파일 이름을 보여주는 시각적 진행 바를 업데이트합니다.
* **파일 확장자 감지**: MIME 유형을 확인하는 것보다 신뢰할 수 있는 `.endswith()`를 사용하여 파일 유형을 결정합니다.
* **텍스트 추출**: TXT/MD 파일의 경우 읽어서 UTF-8로 디코딩합니다. PDF의 경우 모든 페이지를 루프하며 텍스트를 추출합니다.
* **`io.BytesIO(...)`**: 업로드된 파일 바이트를 PdfReader가 프로세싱할 수 있는 파일 형태의 객체로 래핑합니다.

#### 6. 교체 모드 처리

```python
# If replace mode enabled, truncate table first
if replace_mode:
    try:
        session.sql(f"TRUNCATE TABLE {full_table_name}").collect()
        st.success(f":material/check_circle: Cleared existing data from `{full_table_name}`")
    except:
        pass  # Table doesn't exist yet, that's fine
```

* **`TRUNCATE TABLE`**: 테이블 구조는 유지하면서 테이블의 모든 행을 삭제합니다. 이는 대량 작업에서 `DELETE`보다 빠릅니다.
* **조건부 실행**: 체크박스가 선택된 경우에만 실행됩니다.
* **Try/except**: 테이블이 아직 존재하지 않으면 truncate가 실패하지만, 어차피 테이블을 생성할 것이므로 해당 오류를 포착하고 무시합니다.

#### 7. Snowflake에 저장

```python
# Create database, schema, and table if needed
session.sql(f"CREATE DATABASE IF NOT EXISTS {st.session_state.database}").collect()
session.sql(f"CREATE SCHEMA IF NOT EXISTS {st.session_state.database}.{st.session_state.schema}").collect()

# Create table schema
create_table_sql = f"""
CREATE TABLE IF NOT EXISTS {full_table_name} (
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

# Insert extracted documents
for data in extracted_data:
    insert_sql = f"""
    INSERT INTO {full_table_name}
    (FILE_NAME, FILE_TYPE, FILE_SIZE, EXTRACTED_TEXT, WORD_COUNT, CHAR_COUNT)
    VALUES ('{data['file_name']}', '{data['file_type']}', {data['file_size']}, 
            '{data['text'].replace("'", "''")}', {data['word_count']}, {data['char_count']})
    """
    session.sql(insert_sql).collect()
```

* **자동 생성**: `IF NOT EXISTS` 구문을 사용하여 데이터베이스와 스키마가 없는 경우 생성합니다.
* **`AUTOINCREMENT`**: `DOC_ID` 컬럼은 각 문서에 대해 고유 ID(1, 2, 3, ...)를 자동으로 생성합니다.
* **`EXTRACTED_TEXT VARCHAR`**: 이 컬럼은 메타데이터만이 아닌 **전체 문서 텍스트**를 저장합니다. 이것이 Day 17에서 로드하고 청킹할 내용입니다.
* **`DEFAULT CURRENT_TIMESTAMP()`**: 각 문서가 언제 업로드되었는지 자동으로 기록합니다.
* **`.replace("'", "''")`**: 삽입 시 SQL 구문 오류를 방지하기 위해 텍스트의 작은따옴표를 이스케이프합니다.
* **루프 삽입**: 각 문서를 하나씩 삽입합니다. 100개 파일의 경우 100개의 INSERT 문을 의미합니다.

#### 8. 저장된 문서 쿼리 및 보기

```python
if st.button(":material/analytics: Query Table"):
    df = session.sql(f"SELECT * FROM {full_table_name}").to_pandas()
    st.session_state.queried_docs = df
    st.session_state.full_table_name = full_table_name
    st.rerun()

if 'queried_docs' in st.session_state:
    df = st.session_state.queried_docs
    st.dataframe(df)
    
    doc_id = st.selectbox("Select Document ID:", options=df['DOC_ID'].tolist())
    
    if st.button(":material/menu_book: Load Text"):
        doc = df[df['DOC_ID'] == doc_id].iloc[0]
        st.session_state.loaded_doc_text = doc['EXTRACTED_TEXT']
        st.session_state.loaded_doc_name = doc['FILE_NAME']
        st.rerun()
```

* **Query 버튼**: `SELECT *`를 사용하여 테이블에서 모든 문서를 가져오고 표시를 위해 Pandas DataFrame으로 변환합니다.
* **세션 상태 유지**: 앱 재실행 시에도 유지되도록 DataFrame을 `st.session_state.queried_docs`에 저장합니다. 이것이 없으면 "Load Text"를 클릭할 때 앱이 리셋되어 쿼리 결과를 잃게 됩니다.
* **`st.rerun()`**: 다른 사용자 상호 작용을 기다리지 않고 즉시 앱을 새로고침하여 새로 로드된 데이터를 보여줍니다.
* **`st.selectbox(...)`**: 모든 문서 ID가 포함된 드롭다운 메뉴를 생성하여 사용자가 어떤 문서의 전체 텍스트를 볼지 선택할 수 있게 합니다.
* **문서 뷰어**: "Load Text"를 클릭하면 전체 `EXTRACTED_TEXT` 컬럼 값을 추출하여 텍스트 영역에 표시함으로써 전체 콘텐츠(메타데이터만이 아닌)가 저장되었음을 확인시켜 줍니다.

#### 9. Day 17과의 통합

```python
st.session_state.rag_source_table = f"{database}.{schema}.{table_name}"
st.session_state.rag_source_database = database
st.session_state.rag_source_schema = schema
```

* **Day 17로 전달**: Day 17이 액세스할 수 있는 세션 상태 변수에 테이블 위치를 저장합니다.
* **원활한 워크플로우**: 내일의 앱은 이 테이블을 자동으로 감지하고 청킹을 위해 모든 문서를 로드합니다.
* **배치 병합**: 업로드된 모든 배치(50개씩 2번이든 33개씩 3번이든)가 동일한 테이블에 저장되어 함께 프로세싱될 준비를 마칩니다.

이 코드가 실행되면 100개의 파일을 배치로 업로드하고, 모든 텍스트 콘텐츠를 추출하며, 전체 메타데이터와 함께 Snowflake 테이블에 저장할 수 있는 문서 추출 도구를 갖게 됩니다. `EXTRACTED_TEXT` 컬럼에는 Day 17에서 RAG 파이프라인을 위해 청킹할 전체 문서 텍스트가 포함되어 있습니다.

---

### :material/library_books: 리소스
- [st.file_uploader Documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [pypdf Documentation](https://pypdf.readthedocs.io/en/stable/)
- [Snowflake AUTOINCREMENT](https://docs.snowflake.com/en/sql-reference/constraints-properties#autoincrement)
- [Session State Management](https://docs.streamlit.io/develop/concepts/architecture/session-state)
