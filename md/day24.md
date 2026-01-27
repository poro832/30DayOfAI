이번 챌린지에서는 비전(vision) 기능이 있는 모델과 Snowflake의 `AI_COMPLETE` 함수를 사용하여 완전한 이미지 분석 애플리케이션을 구축하는 작업을 수행합니다. 사용자는 테두리가 있는 컨테이너 내에서 이미지를 업로드하고, 별도의 결과 컨테이너에서 설명, OCR(문자 인식), 객체 식별, 차트 분석 또는 커스텀 쿼리를 포함한 AI 기반 분석 결과를 확인할 수 있습니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 어떤 역할을 하는지 살펴보겠습니다.

#### 1. 세션 상태 초기화

```python
# Initialize state
if "image_database" not in st.session_state:
    st.session_state.image_database = "RAG_DB"
    st.session_state.image_schema = "RAG_SCHEMA"

# Configure stage path
database = st.session_state.image_database
schema = st.session_state.image_schema
full_stage_name = f"{database}.{schema}.IMAGE_ANALYSIS"
stage_name = f"@{full_stage_name}"
```

* **구성 가능한 위치**: 사이드바 설정에서 데이터베이스와 스키마를 변경할 수 있습니다.
* **스테이지 명명**: `DATABASE.SCHEMA.IMAGE_ANALYSIS` 패턴을 따릅니다.
* **스테이지 참조**: Snowflake 스테이지 경로에 대해 `@` 접두사를 사용합니다.
* **지속 가능한 상태**: 구성 정보가 재실행 시에도 유지됩니다.

#### 2. 사이드바 구성

```python
with st.sidebar:
    st.header(":material/settings: Settings")
    
    # Database configuration
    with st.expander("Database Configuration", expanded=False):
        database = st.text_input("Database", value=st.session_state.image_database)
        schema = st.text_input("Schema", value=st.session_state.image_schema)
    
    # Model selection
    model = st.selectbox(
        "Select a Model",
        ["claude-3-5-sonnet", "openai-gpt-4.1", "openai-o4-mini", "pixtral-large"],
        help="Select a vision-capable model"
    )
```

* **Material 아이콘**: `:material/settings:`를 사용하여 현대적인 UI를 구현합니다.
* **접이식 설정**: 데이터베이스 구성을 익스팬더에 배치합니다.
* **모델 드롭다운**: Claude, OpenAI, Pixtral을 포함한 비전 기능 모델들입니다.
* **동적 업데이트**: 변경 사항은 `st.rerun()`을 트리거하여 스테이지 경로를 업데이트합니다.

#### 3. 서버 측 암호화가 적용된 스테이지 구성

```python
# Create stage with server-side encryption (required for AI_COMPLETE)
session.sql(f"""
CREATE STAGE {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
""").collect()
```

* **서버 측 암호화**: 이미지를 사용하는 `AI_COMPLETE`에는 `SNOWFLAKE_SSE`가 **필수**입니다.
* **클라이언트 측 암호화**: 비전 모델에서는 지원되지 않습니다.
* **디렉토리 테이블**: 파일 추적을 위해 활성화됩니다.
* **자동 재생성**: 올바른 암호화를 보장하기 위해 스테이지가 존재하는 경우 삭제 후 다시 생성합니다.
* **상태 표시**: 사이드바에 Material 아이콘과 함께 성공/오류를 표시합니다.

#### 4. 테두리가 있는 UI의 업로드 컨테이너

```python
with st.container(border=True):
    st.subheader(":material/upload: Upload an Image")
    uploaded_file = st.file_uploader(
        "Choose an image", 
        type=["jpg", "jpeg", "png", "gif", "webp"],
        help="Supported formats: JPG, JPEG, PNG, GIF, WebP (max 10 MB)"
    )
```

* **테두리가 있는 컨테이너**: 업로드 섹션에 대한 깨끗한 시각적 구분을 제공합니다.
* **Material 아이콘 헤더**: 현대적인 느낌을 위해 `:material/upload:`를 사용합니다.
* **파일 유형 제한**: 비전 모델에서 지원하는 이미지 형식만 허용합니다.
* **도움말 텍스트**: 사용자를 위한 인라인 안내를 제공합니다.

#### 5. 이미지 미리보기 및 파일 정보

```python
if uploaded_file:
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(uploaded_file, caption="Your Image", use_container_width=True)
    
    with col2:
        st.write(f"**File:** {uploaded_file.name}")
        
        # Format file size intelligently
        size_bytes = uploaded_file.size
        if size_bytes >= 1_048_576:  # 1 MB
            size_display = f"{size_bytes / 1_048_576:.2f} MB"
        elif size_bytes >= 1_024:  # 1 KB
            size_display = f"{size_bytes / 1_024:.2f} KB"
        else:
            size_display = f"{size_bytes} bytes"
        
        st.write(f"**Size:** {size_display}")
```

* **2컬럼 레이아웃**: 왼쪽에 이미지 미리보기, 오른쪽에 메타데이터를 배치합니다.
* **반응형 이미지**: 적절한 스케일링을 위해 `use_container_width=True`를 사용합니다.
* **스마트한 파일 크기 표시**: 바이트, KB 또는 MB로 자동 포맷팅합니다.
* **사용자 피드백**: 업로드된 내용에 대한 명확한 표시를 제공합니다.

#### 6. 분석 유형 선택

```python
# Analysis type selection (full width, above button)
analysis_type = st.selectbox("Analysis type:", [
    "General description",
    "Extract text (OCR)",
    "Identify objects",
    "Analyze chart/graph",
    "Custom prompt"
])

# Custom prompt input if selected
custom_prompt = None
if analysis_type == "Custom prompt":
    custom_prompt = st.text_area(
        "Enter your prompt:",
        placeholder="What would you like to know about this image?",
        help="Ask anything about the image content"
    )
```

* **전체 너비 배치**: 컬럼 밖에 위치하며 분석 버튼 위에 배치합니다.
* **사전 정의된 프롬프트**: 최적화된 프롬프트와 함께 일반적인 사용 사례를 제공합니다.
* **커스텀 옵션**: 사용자가 이미지에 대해 무엇이든 질문할 수 있습니다.
* **조건부 입력**: 커스텀 프롬프트인 경우에만 텍스트 영역이 나타납니다.

#### 7. Snowflake 스테이지에 이미지 업로드

```python
# Create unique filename
timestamp = int(time.time())
file_extension = uploaded_file.name.split('.')[-1]
filename = f"image_{timestamp}.{file_extension}"

# Upload to stage
image_bytes = uploaded_file.getvalue()
image_stream = io.BytesIO(image_bytes)

session.file.put_stream(
    image_stream,
    f"{stage_name}/{filename}",
    overwrite=True,
    auto_compress=False
)
```

* **고유 명명**: 타임스탬프 기반 파일명으로 충돌을 방지합니다.
* **확장자 보존**: 원본 형식(`.jpg`, `.png` 등)을 유지합니다.
* **`BytesIO` 래퍼**: `put_stream`을 위해 바이트를 파일 형태 객체로 래핑합니다.
* **압축 안 함**: `auto_compress=False`를 통해 이미지를 있는 그대로 유지합니다.
* **업로드 피드백**: `:material/upload:` 스피너가 업로드 진행 상황을 보여줍니다.

#### 8. AI_COMPLETE를 사용한 이미지 분석

```python
# Use AI_COMPLETE with TO_FILE syntax
sql_query = f"""
SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
    '{model}',
    '{prompt.replace("'", "''")}',
    TO_FILE('{stage_name}', '{filename}')
) as analysis
"""

result = session.sql(sql_query).collect()
response = result[0]['ANALYSIS']

# Store results in session state
st.session_state.analysis_response = response
st.session_state.analysis_model = model
st.session_state.analysis_prompt = prompt
st.session_state.analysis_stage = stage_name
```

* **`AI_COMPLETE` 구문**: `AI_COMPLETE(model, prompt, file_reference)`
* **`TO_FILE()`**: 비전 모델을 위해 스테이징된 파일을 참조합니다.
* **3개 인자**: 모델 이름, 텍스트 프롬프트, 이미지 파일 참조입니다.
* **SQL 이스케이프**: 프롬프트 내의 작은따옴표를 중첩(`''`) 처리합니다.
* **세션 상태 저장**: 별도의 컨테이너에 표시하기 위해 결과를 유지합니다.
* **분석 피드백**: `:material/psychology:` 스피너가 AI가 분석 중임을 보여줍니다.

이것은 [Snowflake 공식 문서의 구문](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-file)을 따릅니다:

```sql
AI_COMPLETE(
    <model>, <predicate>, <file> [, <model_parameters> ]
)
```

#### 9. 별도 컨테이너에 결과 표시

```python
# Display results in a separate bordered container
if "analysis_response" in st.session_state:
    with st.container(border=True):
        st.subheader(":material/auto_awesome: Analysis Result")
        st.markdown(st.session_state.analysis_response)
        
        with st.expander(":material/info: Technical Details"):
            st.write(f"**Model:** {st.session_state.analysis_model}")
            st.write(f"**Prompt:** {st.session_state.analysis_prompt}")
            st.write(f"**Stage:** {st.session_state.analysis_stage}")
```

* **별도 컨테이너**: 결과는 업로드 섹션 아래의 새로운 테두리 컨테이너에 나타납니다.
* **세션 상태 기반**: 분석이 완료된 후에만 컨테이너가 나타납니다.
* **Material 아이콘**: 결과에는 `:material/auto_awesome:`, 상세 정보에는 `:material/info:`를 사용합니다.
* **마크다운 렌더링**: 포맷팅된 모델 응답을 지원합니다.
* **확장 가능한 상세 정보**: 기술 정보는 기본적으로 숨겨져 있습니다.
* **지속적인 표시**: 결과가 재실행 시에도 계속 표시됩니다.

#### 10. 도움말 섹션

```python
# Info section when no file is uploaded
if not uploaded_file:
    st.info(":material/arrow_upward: Upload an image to analyze!")
    
    st.subheader(":material/lightbulb: What Vision AI Can Do")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("- Describe photos\n- Read text (OCR)\n- Identify objects")
    with col2:
        st.markdown("- Analyze charts\n- Understand layouts\n- Describe art style")
```

* **조건부 표시**: 업로드된 파일이 없을 때만 나타납니다.
* **Material 아이콘**: `:material/arrow_upward:`와 `:material/lightbulb:`를 사용합니다.
* **사용 사례 예시**: 사용자가 기능을 이해하도록 돕습니다.
* **2컬럼 레이아웃**: 기능을 체계적으로 제시합니다.

---

### :material/adjust: 주요 기능

| 기능 | 구현 방식 |
|---------|----------------|
| **테두리 컨테이너** | 업로드와 결과를 별도의 테두리 섹션에 배치 |
| **Material 아이콘** | 전체적으로 현대적인 UI 적용 (이모지 대신 사용) |
| **스마트 파일 크기** | 바이트, KB 또는 MB로 자동 포맷팅 |
| **세션 상태** | 결과를 별도의 컨테이너에 유지 |
| **이미지 업로드** | 유형 제한이 있는 `st.file_uploader` 사용 |
| **스테이지 업로드** | 고유 명칭을 사용한 `session.file.put_stream()` 적용 |
| **비전 분석** | `TO_FILE()` 구문을 사용한 `AI_COMPLETE` 호출 |
| **다양한 모델** | Claude, OpenAI GPT-4, OpenAI O4, Pixtral |
| **분석 유형** | 설명, OCR, 객체, 차트, 커스텀 |
| **서버 측 암호화** | 이미지 기반 AI_COMPLETE에 필수 사항임 |
| **파일 관리** | 스테이징된 파일은 유지됨 (SQL을 통한 수동 정리 가능) |

---

### :material/library_books: 주요 기술 개념

**지원되는 비전 모델:**
- `claude-3-5-sonnet` - Claude의 최신 비전 모델
- `openai-gpt-4.1` - 비전 기능을 지원하는 OpenAI의 GPT-4
- `openai-o4-mini` - OpenAI의 효율적인 비전 모델
- `pixtral-large` - Mistral의 비전 모델

[Snowflake AI_COMPLETE 문서](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-file)에 따르면 추가로 지원되는 모델은 다음과 같습니다:
- `claude-4-opus`, `claude-4-sonnet`, `claude-3-7-sonnet`
- `llama4-maverick`, `llama4-scout`

**지원되는 이미지 형식:**
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- `.bmp` (Pixtral 및 Llama4 모델만 해당)

**이미지 크기 제한:**
- 대부분의 모델: 최대 10 MB
- Claude 모델: 최대 3.75 MB, 최대 해상도 8000x8000

**스테이지 요구 사항:**
- :material/check_circle: 서버 측 암호화 (`SNOWFLAKE_SSE`)
- :material/check_circle: 디렉토리 테이블 활성화
- :material/cancel: 클라이언트 측 암호화는 지원되지 않음

**분석 유형:**

| 유형 | 사용 사례 | 예시 프롬프트 |
|------|----------|----------------|
| **General Description** | 빠른 개요 파악 | "이 이미지를 상세히 설명해 주세요" |
| **OCR** | 텍스트 추출 | "이 이미지에 보이는 모든 텍스트를 추출해 주세요" |
| **Identify Objects** | 항목 나열 | "식별할 수 있는 모든 객체를 나열해 주세요" |
| **Analyze Chart/Graph** | 데이터 인사이트 | "이 차트를 분석하고 추세를 설명해 주세요" |
| **Custom** | 모든 질문 | 사용자가 직접 정의한 프롬프트 |

**UI 아키텍처:**

1. **컨테이너 1 (업로드)**: 파일 업로더, 이미지 미리보기, 분석 유형, 분석 버튼
2. **컨테이너 2 (결과)**: 분석 결과 및 기술적 상세 정보 (프로세싱 후 나타남)
3. **도움말 섹션**: 팁 및 기능 설명 (파일이 업로드되지 않았을 때)

**프로세싱 흐름:**
1. 사용자가 테두리가 있는 컨테이너 내에서 이미지 업로드
2. 이미지 바이트 → `BytesIO` 스트림 변환
3. 고유한 이름을 사용하여 Snowflake 스테이지에 업로드
4. `TO_FILE()` 참조를 사용하여 `AI_COMPLETE` 호출
5. 결과를 세션 상태에 저장
6. 별도의 테두리 컨테이너에 결과 표시
7. 스테이징된 파일은 유지됨 (필요시 SQL을 통해 수동으로 정리 가능)

---

### :material/library_books: 리소스

- [Snowflake AI_COMPLETE (Single File) Documentation](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-file)
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [st.file_uploader Documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [st.container Documentation](https://docs.streamlit.io/develop/api-reference/layout/st.container)
- [st.image Documentation](https://docs.streamlit.io/develop/api-reference/media/st.image)
- [Streamlit Material Icons](https://streamlit.io/components)
