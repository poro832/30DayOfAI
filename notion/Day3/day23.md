# LLM 평가 및 AI 관찰 가능성 (LLM Evaluation & AI Observability)

# 0. 목표

<aside>
💡

**RAG 애플리케이션의 품질을 정량적으로 평가하고 모니터링**

1. **TruLens** 라이브러리 연동
2. **RAG 3대 지표** (Triad Metrics) 측정
3. Snowflake AI Observability로 결과 저장 및 추적

</aside>

# 1. 개요 (Overview)

- RAG 시스템을 구축한 후에는 "얼마나 잘 작동하는가?"를 파악해야 합니다.
- **TruLens**는 오픈 소스 평가 도구로, LLM 앱을 계측(Instrument)하고 평가 지표를 계산해줍니다.
- 결과는 Snowflake 테이블에 저장되어 장기적인 성능 추적과 비교가 가능합니다.

## RAG 3대 지표 (The RAG Triad)

1. **컨텍스트 관련성 (Context Relevance)**: 검색된 문서가 질문과 관련이 있는가? (Retrieve 품질)
2. **근거성 (Groundedness)**: 답변이 검색된 문서의 내용에만 기반하는가? (환각 여부)
3. **답변 관련성 (Answer Relevance)**: 답변이 사용자의 질문에 유용하고 적절한가? (생성 품질)

# 2. 구현 내용 (Implementation)

## 2-1. 스테이지 및 환경 설정

TruLens는 평가 결과를 저장하기 위해 Snowflake 스테이지(Stage)를 사용합니다. 보안을 위해 **서버 측 암호화(SSE)**가 활성화된 스테이지가 필요합니다.

```sql
CREATE STAGE IF NOT EXISTS RAG_DB.RAG_SCHEMA.TRULENS_STAGE
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );
```

## 2-2. RAG 앱 계측 (Instrumentation)

`@instrument` 데코레이터를 사용하여 RAG 파이프라인의 각 단계를 추적합니다.

```python
class CustomerReviewRAG:
    # ... 초기화 ...

    @instrument()
    def retrieve_context(self, query: str) -> str:
        # Cortex Search 검색 로직
        # ...
        return context
    
    @instrument()
    def generate_completion(self, query: str, context: str) -> str:
        # Cortex Complete LLM 호출 로직
        # ...
        return response
    
    @instrument()
    def query(self, query: str) -> str:
        context = self.retrieve_context(query)
        answer = self.generate_completion(query, context)
        return answer
```

- 클래스 기반 구조로 RAG 로직을 캡슐화합니다.
- `@instrument()`: 입력과 출력을 기록하여 평가에 사용합니다.

## 2-3. 평가 실행

```python
# 1. TruLens 세션 설정
tru_session = TruSession(connector=SnowflakeConnector(snowpark_session=session))

# 2. 앱 등록
tru_rag = tru_session.App(
    rag_app,
    app_name="customer_review_rag",
    app_version="v1",
    main_method=rag_app.query
)

# 3. 평가 실행
run_config = RunConfig(
    dataset_name="CUSTOMER_REVIEW_TEST_QUESTIONS",
    # ... 설정 ...
)
run = tru_rag.add_run(run_config=run_config)
run.start()

# 4. 메트릭 계산
run.compute_metrics(["answer_relevance", "context_relevance", "groundedness"])
```

- 테스트 질문 세트를 준비하여 일괄적으로 평가를 수행합니다.
- 평가가 완료되면 3대 지표 점수가 계산됩니다.

# 3. 핵심 포인트

- **피드백 루프**: 평가 결과가 낮다면 프롬프트나 검색 설정(청크 수 등)을 수정하고 다시 평가하여 개선 효과를 측정할 수 있습니다.
- **Snowflake 통합**: 별도의 인프라 없이 Snowflake 내에서 평가 데이터를 관리하고 분석할 수 있습니다.
- **LLM-as-a-Judge**: 평가는 또 다른 LLM(평가자 모델)이 수행하여 점수를 매깁니다.

# 4. 실행 결과

## 실행 코드

`python -m streamlit run app/day23.py`

## 결과

- 앱에서 "Run TruLens Evaluation" 버튼을 클릭하면 평가가 시작됩니다.
- 각 질문에 대한 처리 과정과 답변이 생성됩니다.
- 평가 완료 후 Snowsight(웹 콘솔)의 **AI & ML -> Evaluations** 메뉴에서 상세한 리포트와 점수를 확인할 수 있습니다.
