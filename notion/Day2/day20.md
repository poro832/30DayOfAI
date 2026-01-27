# Querying Cortex Search (Cortex Search 조회)

# 0. 목표

<aside>
💡

**Cortex Search 서비스를 사용하여 관련 리뷰 청크 검색 및 조회**

1. Day 19에서 생성한 검색 서비스 구성
2. 의미 기반 쿼리 실행
3. 관련성 높은 리뷰 결과 표시

</aside>

# 1. 개요 (Overview)

- Day 19에서 생성한 Cortex Search 서비스를 실제로 사용하는 단계입니다.
- 키워드가 아닌 **의미**를 기반으로 검색합니다.
- RAG 파이프라인의 **다섯 번째 단계**로, 사용자 질문에 대한 관련 문맥을 찾습니다.

## 의미 기반 검색의 작동 방식

- 검색어: "따뜻한 열 장갑"
- 찾는 리뷰: "손을 포근하게 유지", "추운 날씨에 완벽", "보온성 우수"
- **키워드 일치 불필요**: "따뜻한" 단어가 없어도 의미가 비슷하면 검색됨

# 2. Streamlit 앱 구현 (Implementation)

## 2-1. 검색 서비스 구성

```python
import streamlit as st
from snowflake.core import Root

# Snowflake 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Day 19의 기본 검색 서비스
default_service = 'RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH'

# 사용 가능한 서비스 가져오기 시도
try:
    services_result = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
    available_services = [f"{row['database_name']}.{row['schema_name']}.{row['name']}" 
                         for row in services_result]
except:
    available_services = []

# 기본 서비스를 항상 처음에 배치
if default_service in available_services:
    available_services.remove(default_service)
available_services.insert(0, default_service)

# 검색 서비스 선택
search_service = st.selectbox(
    "Search Service:",
    options=available_services,
    index=0,
    help="Select your Cortex Search service from Day 19"
)
```

- 사용 가능한 모든 Cortex Search 서비스를 자동으로 찾음
- Day 19에서 생성한 서비스를 기본값으로 설정
- 사용자가 다른 서비스를 선택할 수도 있음

## 2-2. 검색 쿼리 입력

```python
# 검색 쿼리 입력
query = st.text_input(
    "Enter your search query:",
    value="warm thermal gloves",
    placeholder="e.g., durability issues, comfortable helmet"
)

num_results = st.slider("Number of results:", 1, 20, 5)

search_clicked = st.button(":material/search: Search", type="primary")
```

- 기본 쿼리: "warm thermal gloves" (따뜻한 열 장갑)
- 반환할 결과 개수 선택 (1~20개, 기본 5개)

## 2-3. 검색 실행

```python
if search_clicked:
    if query and search_service:
        root = Root(session)
        parts = search_service.split(".")
        
        # 서비스 접근
        svc = (root
            .databases[parts[0]]
            .schemas[parts[1]]
            .cortex_search_services[parts[2]])
        
        # 검색 실행
        results = svc.search(
            query=query,
            columns=["CHUNK_TEXT", "FILE_NAME", "CHUNK_TYPE", "CHUNK_ID"],
            limit=num_results
        )
        
        st.success(f":material/check_circle: Found {len(results.results)} result(s)!")
```

- `Root(session)`: Snowflake API 계층 구조 접근
- `svc.search()`: 검색 서비스로 쿼리 실행
- `columns`: 결과에 포함할 컬럼 지정
- `limit`: 최대 결과 개수

## 2-4. 결과 표시

```python
# 결과 표시
for i, item in enumerate(results.results, 1):
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**Result {i}** - {item.get('FILE_NAME', 'N/A')}")
        with col2:
            st.caption(f"Type: {item.get('CHUNK_TYPE', 'N/A')}")
        with col3:
            st.caption(f"Chunk: {item.get('CHUNK_ID', 'N/A')}")
        
        st.write(item.get("CHUNK_TEXT", "No text found"))
        
        # 사용 가능한 경우 관련성 점수 표시
        if hasattr(item, 'score') or 'score' in item:
            score = item.get('score', item.score if hasattr(item, 'score') else None)
            if score is not None:
                st.caption(f"Relevance Score: {score:.4f}")
```

- 각 결과를 별도 컨테이너에 표시
- 파일명, 청크 타입, 청크 ID 표시
- 리뷰의 전체 텍스트 표시
- 관련성 점수(있는 경우) 표시

## 2-5. 검색 예시

```python
# 예시 쿼리들

# 쿼리 1: "warm thermal gloves"
# 결과: "keeps hands toasty", "great warmth", "cold weather protection"

# 쿼리 2: "durability issues"  
# 결과: "fell apart", "broke after 2 weeks", "poor quality materials"

# 쿼리 3: "comfortable helmet"
# 결과: "fits perfectly", "no pressure points", "all-day comfort"
```

# 3. 핵심 포인트 및 고려사항

## 의미 기반 검색의 장점

- **동의어 처리**: "따뜻한" → "포근한", "토스티한", "보온"
- **맥락 이해**: "품질 문제" → "부서짐", "찢어짐", "오래 못감"
- **다국어 지원**: 임베딩 모델이 여러 언어 이해 가능

## 검색 서비스 상태

- 인덱싱이 완료되어야 검색 가능
- `TARGET_LAG` 설정에 따라 새 데이터 반영
- 서비스가 없으면 오류 메시지와 트러블슈팅 가이드 표시

## Day 21과의 통합

- Day 21에서 이 검색 결과를 LLM에 전달하여 답변 생성
- 검색된 청크들이 LLM의 컨텍스트가 됨

# 실행 결과

## 실행 코드

Streamlit 실행 코드 = python -m streamlit run 파일명.py

예시 : `python -m streamlit run app/day20.py`

## 결과 예시

### 쿼리: "warm thermal gloves"

```
Result 1 - review-042.txt
"These gloves are amazing! They kept my hands toasty warm even in -20°C weather..."
Type: full_review | Chunk: 42

Result 2 - review-087.txt  
"Great warmth and insulation. Perfect for cold winter days..."
Type: full_review | Chunk: 87

Result 3 - review-015.txt
"Excellent heat retention. My hands stayed warm throughout the ski trip..."
Type: full_review | Chunk: 15
```

- 정확한 키워드 "따뜻한 열 장갑"이 없어도 의미적으로 관련된 리뷰를 찾음
- 각 결과에 파일명, 타입, 청크 ID 표시
- 관련성 점수로 결과 순위 결정

---

# 💡 실습 과제 (Hands-on Practice)

Cortex Search 서비스 객체의 `.search()` 메서드를 사용하여 의미 기반 검색을 수행해 봅니다.

1. `svc.search()` 메서드를 호출하세요.
2. `query`, `columns`, `limit` 인자를 적절하게 전달하세요.
3. 결과는 `results` 변수에 저장하세요.

# ✅ 정답 코드 (Solution)

```python
# Cortex Search 조회 실습
results = svc.search(
    query=query,
    columns=["CHUNK_TEXT", "FILE_NAME", "CHUNK_TYPE", "CHUNK_ID"],
    limit=num_results
)
```
