# Batch Document Text Extractor for RAG (RAG를 위한 배치 문서 텍스트 추출기)

# 0. 목표

<aside>
💡

**여러 문서를 한번에 업로드하여 텍스트를 추출하고 Snowflake에 저장**

1. 배치 파일 업로드 (TXT, MD, PDF 지원)
2. 여러 파일에서 텍스트 추출
3. Snowflake 데이터베이스 테이블에 저장 (RAG 파이프라인 준비)

</aside>

# 1. 개요 및 필요성 (Overview)

- **Week 3(RAG)**의 첫 단계로, RAG 파이프라인 구축을 위해 문서에서 텍스트를 추출하고 데이터베이스에 저장하는 과정입니다.
- 100개의 고객 리뷰 파일을 한번에 업로드하여 처리할 수 있는 **배치 처리 시스템**을 구축합니다.
- 추출된 텍스트는 Day 17에서 청크(Chunk)로 분할되어 임베딩 및 검색에 활용됩니다.

# 2. Streamlit 앱 구현 (Implementation)

## 2-1. 라이브러리 임포트 및 데이터베이스 설정

```python
import streamlit as st
from pypdf import PdfReader
import io
import pandas as pd

# Snowflake 연결 설정
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 데이터베이스 구성을 위한 세션 상태 초기화
if 'database' not in st.session_state:
    st.session_state.database = "RAG_DB"
    st.session_state.schema = "RAG_SCHEMA"
    st.session_state.table_name = "EXTRACTED_DOCUMENTS"
```

- `pypdf`: PDF 파일에서 텍스트를 추출하기 위한 라이브러리
- `st.session_state`: 앱이 재실행되어도 데이터베이스 설정을 유지하기 위해 사용

## 2-2. 샘플 데이터 다운로드

```python
st.link_button(
    ":material/download: Download review.zip",
    "https://github.com/streamlit/30DaysOfAI/raw/refs/heads/main/assets/review.zip",
    use_container_width=True
)
```

- Avalanche 겨울 스포츠 장비에 대한 100개의 고객 리뷰 파일(`review-001.txt` ~ `review-100.txt`) 제공
- 각 리뷰에는 제품명, 날짜, 리뷰 요약, 감정 점수, 주문 ID가 포함되어 있습니다

## 2-3. 배치 파일 업로드

```python
# 파일 업로더
uploaded_files = st.file_uploader(
    "Choose file(s)",
    type=["txt", "md", "pdf"],
    accept_multiple_files=True,
    help="Supported formats: TXT, MD, PDF. Upload multiple files at once!"
)

if uploaded_files:
    st.success(f":material/check_circle: {len(uploaded_files)} file(s) uploaded")
```

- `accept_multiple_files=True`: 여러 파일을 한번에 선택할 수 있도록 설정
- `type=["txt", "md", "pdf"]`: 지원하는 파일 형식 제한
- 사용자가 100개 파일을 한번에 업로드할 수 있습니다

## 2-4. Replace Table Mode (테이블 교체 모드)

```python
# replace_mode 기본값 설정을 위해 테이블 존재 확인
try:
    check_result = session.sql(f"SELECT COUNT(*) as CNT FROM {table_name}").collect()
    table_exists = True  # 쿼리 성공 시 테이블 존재
except:
    table_exists = False  # 테이블이 존재하지 않음

replace_mode = st.checkbox(
    f":material/sync: Replace Table Mode for `{st.session_state.table_name}`",
    value=table_exists,
    help="When enabled, replaces all existing data"
)
```

- 테이블이 이미 존재하면 체크박스가 기본으로 체크됨 (교체 모드 제안)
- 체크되면 기존 데이터를 삭제하고 새 데이터 삽입
- 체크 해제하면 기존 데이터에 추가 (Append 모드)

## 2-5. 텍스트 추출 및 진행 상황 표시

```python
for idx, uploaded_file in enumerate(uploaded_files):
    progress_pct = (idx + 1) / len(uploaded_files)
    progress_bar.progress(progress_pct, 
        text=f"Processing {idx+1}/{len(uploaded_files)}: {uploaded_file.name}")
    
    # 파일 형식에 따라 텍스트 추출
    if uploaded_file.name.lower().endswith(('.txt', '.md')):
        # TXT 및 Markdown 파일 처리
        extracted_text = uploaded_file.read().decode("utf-8")
    
    elif uploaded_file.name.lower().endswith('.pdf'):
        # PDF 파일 처리
        pdf_reader = PdfReader(io.BytesIO(uploaded_file.read()))
        extracted_text = ""
        # 모든 페이지에서 텍스트 추출
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n\n"
```

- `progress_bar`: 진행 상황을 시각적으로 표시 (예: "Processing 15/100: review-015.txt")
- `enumerate()`: 인덱스와 파일 객체를 함께 제공
- TXT/MD 파일은 UTF-8로 디코딩, PDF는 페이지별로 텍스트 추출

## 2-6. Snowflake에 저장

```python
# 데이터베이스와 스키마가 존재하는지 확인
session.sql(f"CREATE DATABASE IF NOT EXISTS {database}").collect()
session.sql(f"CREATE SCHEMA IF NOT EXISTS {database}.{schema}").collect()

# 테이블이 없으면 생성
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
    session.sql(f"TRUNCATE TABLE {full_table_name}").collect()

# 모든 추출된 데이터 삽입
for data in extracted_data:
    # 텍스트의 작은따옴표 이스케이프
    safe_text = data['extracted_text'].replace("'", "''")
    insert_sql = f"""
    INSERT INTO {full_table_name}
    (FILE_NAME, FILE_TYPE, FILE_SIZE, EXTRACTED_TEXT, WORD_COUNT, CHAR_COUNT)
    VALUES ('{data['file_name']}', '{data['file_type']}', {data['file_size']}, 
            '{safe_text}', {data['word_count']}, {data['char_count']})
    """
    session.sql(insert_sql).collect()
```

- `AUTOINCREMENT`: `DOC_ID` 컬럼이 자동으로 고유 ID 생성 (1, 2, 3, ...)
- `EXTRACTED_TEXT VARCHAR`: 전체 문서 텍스트를 저장 (Day 17에서 사용)
- `DEFAULT CURRENT_TIMESTAMP()`: 업로드 시각 자동 기록
- `TRUNCATE TABLE`: Replace 모드일 때 기존 데이터를 빠르게 삭제

## 2-7. 저장된 문서 조회

```python
if st.button(":material/analytics: Query Table"):
    query_sql = f"""
    SELECT DOC_ID, FILE_NAME, FILE_TYPE, FILE_SIZE, 
           UPLOAD_TIMESTAMP, WORD_COUNT, CHAR_COUNT
    FROM {full_table_name}
    ORDER BY UPLOAD_TIMESTAMP DESC
    """
    df = session.sql(query_sql).to_pandas()
    st.session_state.queried_docs = df
    st.rerun()

# 문서의 전체 텍스트 보기 옵션
doc_id = st.selectbox("Select Document ID:", options=df['DOC_ID'].tolist())

if st.button("Load Text"):
    text_sql = f"SELECT EXTRACTED_TEXT, FILE_NAME FROM {full_table_name} WHERE DOC_ID = {doc_id}"
    text_result = session.sql(text_sql).to_pandas()
    doc = text_result.iloc[0]
    st.text_area(doc['FILE_NAME'], value=doc['EXTRACTED_TEXT'], height=400)
```

- 저장된 모든 문서를 테이블로 표시
- 특정 문서의 전체 텍스트를 확인할 수 있는 기능
- 완전한 내용(메타데이터뿐만 아니라)이 저장되었는지 확인

# 3. 핵심 포인트 및 고려사항

## 배치 처리 (Batch Processing)

- `accept_multiple_files=True`를 사용하여 100개 파일을 한번에 업로드
- 진행 상황 표시로 사용자 경험 향상

## 환경 호환성 (Cross-Environment Compatibility)

- `try-except` 구문으로 SiS 환경과 로컬 환경 모두 지원

## Day 17과의 통합

```python
st.session_state.rag_source_table = f"{database}.{schema}.{table_name}"
st.session_state.rag_source_database = database
st.session_state.rag_source_schema = schema
```

- Day 17이 자동으로 이 테이블을 찾아 문서를 로드할 수 있도록 세션 상태에 저장

# 실행 결과

## 실행 코드

Streamlit 실행 코드 = python -m streamlit run 파일명.py

예시 : `python -m streamlit run app/day16.py`

## 결과

- 100개의 리뷰 파일을 한번에 업로드하여 텍스트 추출
- Snowflake의 `EXTRACTED_DOCUMENTS` 테이블에 모든 텍스트와 메타데이터 저장
- Day 17에서 이 텍스트들을 청크로 분할하여 RAG 파이프라인 구축 준비 완료

---

# 💡 실습 과제 (Hands-on Practice)

추출된 문서의 텍스트와 메타데이터를 Snowflake 테이블에 하나씩 삽입하는 로직을 완성해 봅니다.

1. `INSERT INTO` SQL 구문을 작성하여 텍스트 데이터(`safe_text`)와 파일 정보들을 테이블에 저장하세요.
2. `session.sql().collect()`를 사용하여 파이썬에서 SQL 명령을 실행하세요.

# ✅ 정답 코드 (Solution)

```python
# Snowflake 테이블 데이터 삽입 실습
# 1. SQL 쿼리 구성
insert_sql = f"""
INSERT INTO {database}.{schema}.{table_name}
(FILE_NAME, FILE_TYPE, FILE_SIZE, EXTRACTED_TEXT, WORD_COUNT, CHAR_COUNT)
VALUES ('{data['file_name']}', '{data['file_type']}', {data['file_size']}, 
        '{safe_text}', {data['word_count']}, {data['char_count']})
"""

# 2. 실행
session.sql(insert_sql).collect()
```
