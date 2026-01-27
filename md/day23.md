이번 챌린지에서는 **TruLens**와 Snowflake의 AI 관측성(Observability) 프레임워크를 사용하여 **본인이 만든 RAG 애플리케이션의 품질을 평가**하는 작업을 수행합니다. Day 21-22에서 완전한 RAG 시스템을 구축한 후에는, 그것이 정확하고 근거 있으며 관련 있는 답변을 생성하고 있는지 측정하는 것이 매우 중요합니다. TruLens를 사용하여 **RAG Triad** 지표(문맥 관련성, 근거성, 답변 관련성)를 통해 RAG 애플리케이션을 자동으로 평가할 것입니다. 앱은 평가 설정을 구성하고, 평가를 실행하며, 결과를 Snowsight에서 직접 볼 수 있는 대화형 인터페이스를 제공합니다.

> :material/warning: **전제 조건:** TruLens 패키지가 설치되어 있어야 하며 Day 19의 Cortex Search 서비스가 필요합니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 어떤 역할을 하는지 살펴보겠습니다.

#### 1. RAG Triad: 세 가지 필수 지표

[Snowflake의 RAG 평가 가이드](https://www.snowflake.com/en/engineering-blog/eval-guided-optimization-llm-judges-rag-triad/)에 따르면, RAG를 평가하려면 세 가지 차원을 측정해야 합니다.

| 지표 | 질문 | 중요한 이유 |
|--------|----------|----------------|
| **문맥 관련성 (Context Relevance)** | 관련 있는 문서를 검색했는가? | 잘못된 검색 → 잘못된 답변 |
| **근거성 (Groundedness)** | 답변이 문맥에 기반하고 있는가? | 할루시네이션(환각) 방지 |
| **답변 관련성 (Answer Relevance)** | 질문에 적절히 답변했는가? | 유용성 보장 |

* **문맥 관련성**: 검색 시스템(Cortex Search)이 사용자의 질문과 실제로 관련된 문서를 검색했는지 측정합니다. 점수가 낮으면 검색 기능을 튜닝해야 함을 의미합니다.
* **근거성**: LLM의 답변이 제공된 문맥에서 비롯된 것인지, 아니면 내용을 지어내고 있는지(할루시네이션) 확인합니다. 높은 근거성 = 할루시네이션 없음.
* **답변 관련성**: 최종 답변이 실제 사용자가 질문한 내용을 다루고 있는지 평가합니다. 문맥과 근거성이 훌륭하더라도 관련 없는 답변을 줄 수 있기 때문입니다.

#### 2. 패키지 가용성 확인 및 UI 설정

```python
import streamlit as st

# Check TruLens installation
try:
    from trulens.connectors.snowflake import SnowflakeConnector
    from trulens.core.run import Run, RunConfig
    from trulens.core import TruSession
    from trulens.core.otel.instrument import instrument
    import pandas as pd
    import time
    trulens_available = True
except ImportError as e:
    trulens_available = False
    trulens_error = str(e)

st.title(":material/analytics: LLM Evaluation & AI Observability")
st.write("Evaluate your RAG application quality using TruLens and Snowflake AI Observability.")

# Display TruLens status
if trulens_available:
    st.success(":material/check_circle: TruLens packages are installed and ready!")
else:
    st.error(f":material/cancel: TruLens packages not found: {trulens_error}")
    st.info("""
    **Required packages:**
    - `trulens-core`
    - `trulens-providers-cortex`
    - `trulens-connectors-snowflake`
    
    Add these to your Streamlit app's package configuration to enable TruLens evaluations.
    """)
```

* **임포트 확인**: 진행하기 전에 모든 필수 TruLens 패키지가 설치되어 있는지 확인합니다.
* **사용자 피드백**: 패키지가 누락된 경우 필수 패키지 목록과 함께 명확한 상태 메시지를 보여줍니다.
* **부드러운 기능 저하(Graceful degradation)**: 패키지가 없더라도 앱이 로드되도록 허용합니다(대신 지침을 보여줌).

#### 3. 사이드바 구성 및 스테이지 설정

```python
# Configuration
with st.sidebar:
    st.header(":material/settings: Configuration")
    
    with st.expander("Search Service", expanded=True):
        search_service = st.text_input(
            "Cortex Search Service:",
            value="RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH",
            help="Format: database.schema.service_name (created in Day 19)"
        )
    
    with st.expander("Location", expanded=False):
        obs_database = st.text_input("Database:", value="RAG_DB")
        obs_schema = st.text_input("Schema:", value="RAG_SCHEMA")
    
    num_results = st.slider("Results to retrieve:", 1, 5, 3)
    
    # Stage Status - create early
    with st.expander("Stage Status", expanded=False):
        full_stage_name = f"{obs_database}.{obs_schema}.TRULENS_STAGE"
        
        try:
            # Check if stage exists
            stage_info = session.sql(f"SHOW STAGES LIKE 'TRULENS_STAGE' IN SCHEMA {obs_database}.{obs_schema}").collect()
            
            if stage_info:
                st.info(f":material/autorenew: Recreating stage with server-side encryption...")
                session.sql(f"DROP STAGE IF EXISTS {full_stage_name}").collect()
            
            # Create stage with server-side encryption
            session.sql(f"""
            CREATE STAGE {full_stage_name}
                DIRECTORY = ( ENABLE = true )
                ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
            """).collect()
            st.success(f":material/check_box: TruLens stage ready")
            
        except Exception as e:
            st.error(f":material/cancel: Could not create stage: {str(e)}")
```

* **체계적인 구성**: 익스팬더(expanders)를 사용하여 관련 설정을 그룹화합니다.
* **기본값**: Day 19 설정의 값으로 미리 채워 넣습니다.
* **자동 스테이지 생성**: 페이지 로드 시 적절한 암호화가 설정된 필수 TruLens 스테이지를 생성합니다.
* **스테이지 검증**: 올바른 구성을 보장하기 위해 스테이지를 확인하고 다시 생성합니다.
* **수동 수정 옵션**: 자동 생성이 실패할 경우를 대비하여 SQL 코드를 제공합니다.

#### 4. 평가 구성 UI

```python
with st.container(border=True):
    st.markdown("##### :material/settings_suggest: Evaluation Configuration")
    
    app_name = st.text_input(
        "App Name:",
        value="customer_review_rag",
        help="Name for your RAG application"
    )
    
    app_version = st.text_input(
        "App Version:",
        value=f"v{st.session_state.run_counter}",
        help="Version identifier for this experiment"
    )
    
    rag_model = st.selectbox(
        "RAG Model:",
        ["claude-3-5-sonnet", "mixtral-8x7b", "llama3-70b", "llama3.1-8b"],
        help="Model for generating answers"
    )
    
    st.markdown("##### :material/dataset: Test Questions")
    test_questions_text = st.text_area(
        "Questions (one per line):",
        value="What do customers say about thermal gloves?\nAre there any durability complaints?\nWhich products get the best reviews?",
        height=150
    )
    
    run_evaluation = st.button(":material/science: Run TruLens Evaluation", type="primary")
```

* **실행 카운터**: 각 평가 실행마다 버전 번호를 자동으로 증가시킵니다.
* **모델 선택**: 평가할 Cortex LLM을 선택합니다.
* **유연한 질문 설정**: UI에서 직접 테스트 질문을 편집합니다.
* **한 줄 형식**: 편집하기 쉽도록 질문들을 개행으로 구분합니다.

#### 5. TruLens란 무엇인가요?

TruLens는 다음과 같은 기능을 위해 Snowflake AI 관측성과 통합되는 오픈 소스 라이브러리입니다:
- LLM 애플리케이션을 자동으로 추적(trace)하고 평가
- RAG Triad 지표를 자동으로 계산
- 분석 및 비교를 위해 결과를 Snowflake에 저장
- 시간에 따른 실험 내용 추적

#### 6. RAG 애플리케이션 계측(Instrumenting)

첫 번째 단계는 TruLens가 추적할 수 있도록 계측된 RAG 클래스를 만드는 것입니다.

```python
from trulens.core.otel.instrument import instrument

class CustomerReviewRAG:
    def __init__(self, snowpark_session):
        self.session = snowpark_session
        self.search_service = search_service
        self.num_results = num_results
        self.model = rag_model
    
    @instrument()
    def retrieve_context(self, query: str) -> str:
        """Retrieve context from Cortex Search."""
        root = Root(self.session)
        parts = self.search_service.split(".")
        svc = root.databases[parts[0]].schemas[parts[1]].cortex_search_services[parts[2]]
        results = svc.search(query=query, columns=["CHUNK_TEXT"], limit=self.num_results)
        context = "\n\n".join([r["CHUNK_TEXT"] for r in results.results])
        return context
    
    @instrument()
    def generate_completion(self, query: str, context: str) -> str:
        """Generate answer using LLM."""
        prompt = f"""Based on this context from customer reviews:

{context}

Question: {query}

Provide a helpful answer based on the context above:"""
        
        prompt_escaped = prompt.replace("'", "''")
        response = self.session.sql(
            f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{self.model}', '{prompt_escaped}')"
        ).collect()[0][0]
        return response.strip()
    
    @instrument()
    def query(self, query: str) -> str:
        """Main RAG query method."""
        context = self.retrieve_context(query)
        answer = self.generate_completion(query, context)
        return answer
```

* **`@instrument()` 데코레이터**: TruLens가 이 메서드들을 추적하도록 지시합니다.
* **관심사 분리**: 더 나은 추적을 위해 검색(retrieval)과 생성(generation)을 별도의 메서드로 나눕니다.
* **메인 엔트리 포인트**: `query()` 메서드가 전체 RAG 파이프라인을 조율합니다.

#### 7. TruLens 세션 설정

```python
from trulens.core import TruSession
from trulens.connectors.snowflake import SnowflakeConnector

# Always clear singleton to ensure fresh session
if hasattr(TruSession, '_singleton_instances'):
    TruSession._singleton_instances.clear()

# Create new connector and session
tru_connector = SnowflakeConnector(snowpark_session=session)
tru_session = TruSession(connector=tru_connector)

# Create RAG app instance
rag_app = CustomerReviewRAG(session)

# Register the RAG app with unique version for each run
unique_app_version = f"{app_version}_{st.session_state.run_counter}"

tru_rag = tru_session.App(
    rag_app,
    app_name=app_name,
    app_version=unique_app_version,
    main_method=rag_app.query
)
```

* **싱글톤(Singleton) 제거**: Streamlit 재실행 시 이전 TruLens 세션과의 충돌을 방지합니다.
* **신규 세션**: 각 평가 실행마다 새로운 TruSession을 생성합니다.
* **SnowflakeConnector**: TruLens를 Snowflake 세션에 연결합니다.
* **고유 버전 관리**: 충돌을 방지하기 위해 사용자 버전과 실행 카운터를 결합합니다.
* **앱 등록**: 메타데이터(이름, 버전)와 함께 RAG 앱을 등록합니다.
* **main_method**: 각 쿼리에 대해 TruLens가 호출해야 할 메서드를 지정합니다.

#### 8. 테스트 데이터셋 생성

```python
# Parse questions from text area
test_questions = [q.strip() for q in test_questions_text.split('\n') if q.strip()]

# Set database and schema context (required for TruLens)
session.use_database(obs_database)
session.use_schema(obs_schema)

# Create a DataFrame from test questions
test_data = []
for idx, question in enumerate(test_questions):
    test_data.append({
        "QUERY": question,
        "QUERY_ID": idx + 1
    })

test_df = pd.DataFrame(test_data)

# Save to Snowflake table for TruLens
test_snowpark_df = session.create_dataframe(test_df)
dataset_table = "CUSTOMER_REVIEW_TEST_QUESTIONS"

# Drop table if exists and recreate
session.sql(f"DROP TABLE IF EXISTS {dataset_table}").collect()
test_snowpark_df.write.mode("overwrite").save_as_table(dataset_table)
```

* **UI에서 파싱**: 사용자가 입력한 텍스트 영역의 내용을 줄바꿈으로 나눕니다.
* **쿼리 ID**: 추적을 위해 고유 식별자를 추가합니다.
* **데이터베이스 문맥**: 테이블 생성을 위해 작업 중인 데이터베이스/스키마를 설정합니다.
* **Snowflake 테이블**: TruLens는 인메모리 DataFrame이 아닌 Snowflake 테이블에서 테스트 데이터를 읽습니다.
* **깨끗한 시작**: 충돌을 피하기 위해 테이블을 삭제하고 다시 생성합니다.
* **재사용 가능한 데이터셋**: 이 테이블을 향후 평가 실행에서도 참조할 수 있습니다.

#### 9. 평가 구성 및 실행

```python
from trulens.core.run import Run, RunConfig
import time

# Configure the evaluation run
run_config = RunConfig(
    run_name=f"{unique_app_version}_{int(time.time())}",
    dataset_name=dataset_table,
    description=f"Customer review RAG evaluation using {rag_model}",
    label="customer_review_eval",
    source_type="TABLE",
    dataset_spec={
        "input": "QUERY",
    },
)

# Add run to TruLens
run: Run = tru_rag.add_run(run_config=run_config)

# Start the evaluation
run.start()

# Show progress and generate answers
generated_answers = {}
for idx, question in enumerate(test_questions, 1):
    st.write(f"  :orange[:material/check:] Question {idx}/{len(test_questions)}: {question[:60]}...")
    answer = rag_app.query(question)
    generated_answers[question] = answer

# Wait for invocations to complete
max_wait = 180  # 3 minutes
start_time = time.time()
while run.get_status() != "INVOCATION_COMPLETED":
    if time.time() - start_time > max_wait:
        st.warning("Run taking longer than expected, continuing...")
        break
    time.sleep(3)

# Compute RAG Triad metrics
run.compute_metrics([
    "answer_relevance",
    "context_relevance",
    "groundedness",
])

# Show completion message
st.write(":orange[:material/check:] Evaluation complete!")
```

* **고유 실행 이름**: 실행 간 충돌을 방지하기 위해 타임스탬프를 사용합니다.
* **RunConfig**: 무엇을 어떻게 평가할지 지정합니다.
* **진행 추적**: 어떤 질문이 프로세싱되고 있는지 실시간으로 보여줍니다.
* **답변 캡처**: 표시를 위해 생성된 답변을 저장합니다.
* **배치 프로세싱**: 모든 질문이 자동으로 처리됩니다.
* **타임아웃 보호**: 문제가 발생했을 때 무한 대기를 방지합니다.
* **지표 계산**: TruLens는 모든 쿼리가 완료된 후 RAG Triad 점수를 계산합니다.
* **완료 메시지**: 평가가 끝나면 명확한 표시기를 보여줍니다.

#### 10. 결과 표시

```python
# Display results
with st.container(border=True):
    st.markdown("#### :material/analytics: Evaluation Results")
    
    st.success(f"""
:material/check: **Evaluation Run Complete!**

**Run Details:**
- App Name: **{app_name}**
- App Version: **{unique_app_version}**
- Run Name: **{run_config.run_name}**
- Questions Evaluated: **{len(test_questions)}**
- Model: **{rag_model}**

**View Results in Snowsight:**
Navigate to: **AI & ML → Evaluations → {app_name}**
    """)
    
    # Show generated answers
    with st.expander("Generated Answers", expanded=True):
        for idx, question in enumerate(test_questions, 1):
            st.markdown(f"**Question {idx}:** {question}")
            st.info(generated_answers.get(question, "No answer generated"))
            if idx < len(test_questions):
                st.markdown("---")
```

* **성공 요약**: 완료된 평가에 대한 주요 세부 정보를 보여줍니다.
* **Snowsight 탐색**: 상세한 RAG Triad 지표를 볼 수 있는 위치에 대한 명확한 설명을 제공합니다.
* **생성된 답변**: Streamlit에서 즉시 검토할 수 있도록 모든 Q&A 쌍을 보여줍니다.
* **확장 가능한 섹션**: 답변을 접을 수 있게 하여 UI를 깔끔하게 유지합니다.
* **구분선**: 읽기 쉽도록 Q&A 쌍 사이에 구분선을 추가합니다.
* **투명성**: 사용자는 지표를 보기 전에 RAG 시스템이 정확히 무엇을 생성했는지 확인할 수 있습니다.

#### 11. Snowsight에서 평가 결과 확인하기

앱에서 평가가 완료되었다는 성공 메시지가 나타나면, 다음 단계에 따라 상세 지표를 확인하세요.

**단계별 지침:**

1. **Snowsight를 열고** Snowflake 계정에 로그인합니다.

2. **Evaluations 페이지로 이동합니다:**
   - 왼쪽 사이드바에서 **AI & ML**을 클릭합니다.
   - 그런 다음 **Evaluations**를 클릭합니다.
   - 또는 이 직접 링크를 사용하세요: [Snowflake AI Evaluations](https://app.snowflake.com/_deeplink/#/ai-evaluations)

3. **본인의 평가를 찾습니다:**
   - 표시된 데이터 테이블에서 **Name** 컬럼을 확인합니다.
   - **CUSTOMER_REVIEW_RAG**(또는 변경한 커스텀 앱 이름)를 찾습니다.
   - 앱 이름을 클릭하여 평가 상세 내용을 엽니다.

4. **상세 결과 확인:**
   - 각 질문에 대한 **RAG Triad 점수**:
     - 문맥 관련성 (검색 품질)
     - 근거성 (할루시네이션 탐지)
     - 답변 관련성 (답변 품질)
   - **응답 지표**: 각 쿼리에 대한 길이 및 소요 시간
   - **상세 추적(Trace)**: 검색 및 생성의 단계별 보기
   - **버전 비교**: 여러 실행/버전 간의 지표 비교
   - **개별 쿼리 상세**: 질문을 클릭하여 전체 추적 내용 보기

**확인해야 할 사항:**
- 점수 범위는 0에서 1입니다(높을수록 좋음).
- 0.7 미만의 점수는 개선이 필요한 영역임을 나타냅니다.
- 개선 사항을 추적하기 위해 여러 버전의 점수를 비교합니다.

---

### :material/adjust: 핵심 개념

**왜 TruLens를 사용하나요?**
- **자동화된 평가**: 수동 점수 산정이 필요 없습니다.
- **운영 준비 완료**: 수천 개의 평가로 확장 가능합니다.
- **통합 저장**: 결과가 Snowflake에 자동으로 저장됩니다.
- **실험 추적**: 다른 모델, 프롬프트 및 구성을 비교합니다.
- **상세 추적**: 각 단계에서 일어난 일을 정확히 확인합니다.

**TruLens vs 수동 평가:**

| 측면 | TruLens | 수동 LLM 평가 (LLM-as-a-Judge) |
|--------|---------|----------------------|
| 설정 | 계측(instrumentation) 필요 | 커스텀 프롬프트 필요 |
| 지표 | RAG Triad 공식 내장 | 평가용 프롬프트를 직접 정의해야 함 |
| 저장 | Snowflake에 자동 저장 | 직접 구현해야 함 |
| 추적 | 메서드 추적 자동화 | 수동 로깅 필요 |
| 비교 | Snowsight에 내장된 UI | 대시보드를 직접 구축해야 함 |

**권장 사항:**
- **고유한 앱 버전**: 실험 추적을 위해 버전 번호를 사용합니다.
- **대표성 있는 질문**: 테스트 세트에 엣지 케이스(edge cases)를 포함합니다.
- **정기적인 평가**: 변경 사항을 배포하기 전에 실행합니다.
- **패턴 분석**: 지속적으로 낮은 점수를 받는 질문 유형을 찾습니다.
- **지표 기반 반복 개선**: 점수를 가이드로 삼아 개선을 진행합니다.

**평가 실행 시점:**
- **개발 중**: 프롬프트, 모델 또는 검색 설정을 변경한 후
- **배포 전**: 운영 환경에 릴리스하기 전
- **회귀 테스트**: 품질이 저하되지 않았는지 확인
- **A/B 테스트**: 다른 구성 간의 비교

**RAG Triad 점수 해석:**
- **문맥 관련성 < 0.7**: 검색 품질 개선이 필요합니다.
  - 해결책: 청크 크기 튜닝, 임베딩 개선 또는 검색 매개변수 조정
- **근거성 < 0.7**: LLM이 할루시네이션을 일으키거나 내용을 추론하고 있습니다.
  - 해결책: 프롬프트에 더 강력한 근거 기반 지시사항 추가
- **답변 관련성 < 0.7**: 답변이 질문을 다루지 못하고 있습니다.
  - 해결책: 프롬프트 지시사항 상세화 또는 예시 제공

---

### :material/library_books: 주요 기술 개념

**TruLens 아키텍처:**
1. **계측(Instrumentation)**: `@instrument()` 데코레이터가 메서드 호출을 추적합니다.
2. **세션 관리**: `TruSession`이 평가 수명 주기를 관리합니다.
3. **앱 등록**: 메타데이터와 함께 애플리케이션을 등록합니다.
4. **데이터셋 사양**: 입력/출력 컬럼을 정의합니다.
5. **실행(Run) 구성**: 평가 매개변수를 지정합니다.
6. **지표 계산**: 쿼리 완료 후 RAG Triad를 계산합니다.

**필수 의존성:**

**pyproject.toml**의 경우:
```toml
[project]
dependencies = [
    \"trulens-core>=1.0.0\",
    \"trulens-connectors-snowflake>=1.0.0\",
    \"trulens-providers-cortex>=1.0.0\",
    \"snowflake-snowpark-python>=1.18.0,<2.0\",
    \"pandas>=1.5.0\"
]
```

또는 **requirements.txt**의 경우:
```
trulens-core>=1.0.0
trulens-connectors-snowflake>=1.0.0
trulens-providers-cortex>=1.0.0
snowflake-snowpark-python>=1.18.0,<2.0
pandas>=1.5.0
```

**TruLens 패키지 세부 내용:**
- `trulens-core` - 핵심 TruLens 기능 (TruSession, @instrument 데코레이터)
- `trulens-connectors-snowflake` - 평가 결과 저장을 위한 Snowflake 커넥터
- `trulens-providers-cortex` - 평가 지표를 위한 Cortex LLM 프로바이더
- `pandas` - 테스트 데이터셋의 DataFrame 작업에 필수

**Snowflake 스테이지 요건:**
TruLens에는 다음 조건의 스테이지가 필요합니다:
- 서버 측 암호화: `ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )`
- 디렉토리 테이블 활성화: `DIRECTORY = ( ENABLE = true )`

```sql
CREATE STAGE TRULENS_STAGE
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );
```

**세션 상태 관리:**
Streamlit 재실행 간 충돌을 방지하려면:
```python
# Clear TruSession singleton before each run
from trulens.core import TruSession
if hasattr(TruSession, '_singleton_instances'):
    TruSession._singleton_instances.clear()

# Use run counter for unique versions
st.session_state.run_counter = st.session_state.get('run_counter', 1)
app_version = f"v{st.session_state.run_counter}"
st.session_state.run_counter += 1
```

**운영 팁:**
- 이력 분석을 위해 평가 결과를 저장합니다.
- 품질 저하에 대한 알림을 설정합니다.
- 평가를 스케줄에 따라 실행합니다(예: 매일).
- 테스트 세트에 실제 운영 쿼리를 포함합니다.
- 앱 버전 간의 지표를 비교합니다.
- 평가 결과를 사용하여 개선 작업의 우선순위를 정합니다.

---

### :material/library_books: 리소스

- [Snowflake AI Observability Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability)
- [AI Observability Tutorial](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability/tutorial)
- [Getting Started with AI Observability](https://github.com/Snowflake-Labs/sfguide-getting-started-with-ai-observability)
- [RAG Triad Benchmarking Blog](https://www.snowflake.com/en/engineering-blog/eval-guided-optimization-llm-judges-rag-triad/)
- [TruLens Documentation](https://www.trulens.org/)
