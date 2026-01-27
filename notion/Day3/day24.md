# 이미지 작업 (멀티모달리티) (Working with Images)

# 0. 목표

<aside>
💡

**이미지 입력을 처리하고 분석하는 멀티모달(Vision) AI 구현**

1. 이미지 업로드 및 Snowflake 스테이지 저장
2. `AI_COMPLETE` 함수와 비전 모델(Vision Model) 활용
3. 이미지 분석, OCR, 객체 탐지 등 다양한 유스케이스 구현

</aside>

# 1. 개요 (Overview)

- **멀티모달(Multimodal)**: 텍스트뿐만 아니라 이미지, 오디오 등 다양한 모달리티를 이해하는 AI 모델을 의미합니다.
- Snowflake Cortex는 `claude-3-5-sonnet`, `gpt-4o` 등 강력한 비전 모델을 지원합니다.
- 이미지를 분석하려면 이미지를 먼저 Snowflake 스테이지에 업로드해야 합니다.

# 2. 구현 내용 (Implementation)

## 2-1. 보안 스테이지 설정

이미지를 AI 모델에 전달하기 위해서는 **서버 측 암호화(Server-Side Encryption)**가 설정된 스테이지가 필수적입니다.

```sql
CREATE STAGE IF NOT EXISTS IMAGE_ANALYSIS
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' ); -- 필수 설정
```

## 2-2. 이미지 업로드

Streamlit 업로더로 받은 파일을 스테이지에 저장합니다.

```python
# 파일 업로드
uploaded_file = st.file_uploader("이미지 선택", type=["jpg", "png", ...])

if uploaded_file:
    # 스테이지에 저장
    session.file.put_stream(
        io.BytesIO(uploaded_file.getvalue()),
        f"@{database}.{schema}.IMAGE_ANALYSIS/{filename}",
        overwrite=True,
        auto_compress=False
    )
```

- `put_stream`: 메모리 상의 파일 객체를 로컬 파일 저장 없이 바로 스테이지로 업로드합니다.

## 2-3. 비전 모델 호출 (TO_FILE 문법)

`AI_COMPLETE` 함수에서 `TO_FILE` 함수를 사용하여 스테이지의 이미지를 참조합니다.

```python
prompt = "Describe this image in detail."

sql_query = f"""
SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
    'claude-3-5-sonnet',    -- 비전 지원 모델
    '{prompt}',             -- 텍스트 프롬프트
    TO_FILE('@{database}.{schema}.IMAGE_ANALYSIS', '{filename}') -- 이미지 참조
) as analysis
"""

result = session.sql(sql_query).collect()
```

- `TO_FILE(스테이지, 파일명)`: 프롬프트에 이미지 파일을 첨부하는 문법입니다.
- **모델 선택**: 비전 기능이 있는 모델(예: Claude 3.5 Sonnet, GPT-4o, Llama 3.2 Vision 등)을 선택해야 합니다.

# 3. 활용 사례 (Use Cases)

앱에서는 프롬프트를 변경하여 다양한 분석을 수행합니다:

1. **일반 설명 (General Description)**: 이미지의 전반적인 내용을 묘사합니다.
2. **OCR (Text Extraction)**: 이미지 내의 텍스트를 추출합니다. (영수증, 간판 등)
3. **객체 식별 (Identify Objects)**: 이미지에 있는 물건들을 리스트업합니다.
4. **차트 분석 (Chart Analysis)**: 그래프나 차트의 데이터를 해석하고 인사이트를 도출합니다.

# 4. 실행 결과

## 실행 코드

`python -m streamlit run app/day24.py`

## 결과

- 사용자가 이미지를 업로드하고 분석 유형을 선택하면, AI가 이미지를 "보고" 답변합니다.
- 예: 식당 메뉴판 사진을 올리고 텍스트 추출을 요청하면 메뉴 항목들을 텍스트로 반환합니다.
