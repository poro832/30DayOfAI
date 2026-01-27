# Day 23
# LLM 평가 및 AI 관찰 가능성 (LLM Evaluation & AI Observability)

import streamlit as st
from snowflake.core import Root
import json

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 실행 카운터를 위한 세션 상태 초기화
if 'run_counter' not in st.session_state:
    st.session_state.run_counter = 1

# TruLens 설치 확인
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

st.title(":material/analytics: LLM 평가 및 AI 관찰 가능성")
st.write("TruLens와 Snowflake AI Observability를 사용하여 RAG 애플리케이션 품질을 평가합니다.")

# 평가 정보
with st.expander("왜 LLM을 평가해야 하나요?", expanded=False):
    st.markdown("""
    RAG 애플리케이션(Day 21-22)을 구축한 후에는 품질을 측정해야 합니다:
    
    **RAG 3대 지표 (The RAG Triad Metrics):**
    1. **컨텍스트 관련성 (Context Relevance)** - 올바른 문서를 검색했는가?
    2. **근거성 (Groundedness)** - 답변이 컨텍스트에 기반하는가 (환각 없음)?
    3. **답변 관련성 (Answer Relevance)** - 답변이 질문을 해결하는가?
    
    **TruLens:** LLM 애플리케이션을 자동으로 평가하고, 실험을 추적하며, 비교를 위해 결과를 Snowflake AI Observability에 저장하는 오픈 소스 라이브러리입니다.
    
    더 알아보기: [Snowflake AI Observability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability)
    """)

# TruLens 상태 표시
if trulens_available:
    st.success(":material/check_circle: TruLens 패키지가 설치되어 준비되었습니다!")
else:
    st.error(f":material/cancel: TruLens 패키지를 찾을 수 없습니다: {trulens_error}")
    st.info("""
    **필요한 패키지:**
    - `trulens-core`
    - `trulens-providers-cortex`
    - `trulens-connectors-snowflake`
    
    TruLens 평가를 활성화하려면 Streamlit 앱의 패키지 구성에 이들을 추가하세요.
    """)

# 구성
with st.sidebar:
    st.header(":material/settings: 구성 (Configuration)")
    
    with st.expander("검색 서비스 (Search Service)", expanded=True):
        search_service = st.text_input(
            "Cortex Search 서비스:",
            value="RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH",
            help="형식: database.schema.service_name (Day 19에서 생성됨)"
        )
    
    with st.expander("위치 (Location)", expanded=False):
        obs_database = st.text_input(
            "데이터베이스:",
            value="RAG_DB",
            help="평가 결과를 저장할 데이터베이스"
        )
        
        obs_schema = st.text_input(
            "스키마:",
            value="RAG_SCHEMA",
            help="평가 결과를 저장할 스키마"
        )
    
    num_results = st.slider("검색할 결과 수:", 1, 5, 3)

    # 스테이지 상태 - Day 25처럼 미리 생성
    with st.expander("스테이지 상태 (Stage Status)", expanded=False):
        full_stage_name = f"{obs_database}.{obs_schema}.TRULENS_STAGE"
        
        try:
            # 스테이지 존재 확인
            stage_info = session.sql(f"SHOW STAGES LIKE 'TRULENS_STAGE' IN SCHEMA {obs_database}.{obs_schema}").collect()
            
            if stage_info:
                # 스테이지가 존재하면 드롭하고 다시 생성하여 올바른 구성 확인
                st.info(f":material/autorenew: 서버 측 암호화로 스테이지 재생성 중...")
                session.sql(f"DROP STAGE IF EXISTS {full_stage_name}").collect()
            
            # 서버 측 암호화로 스테이지 생성
            session.sql(f"""
            CREATE STAGE {full_stage_name}
                DIRECTORY = ( ENABLE = true )
                ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
            """).collect()
            st.success(f":material/check_box: TruLens 스테이지 준비됨")
            
        except Exception as e:
            st.error(f":material/cancel: 스테이지를 생성할 수 없습니다: {str(e)}")
            
            with st.expander(":material/build: 수동 수정"):
                st.code(f"""
DROP STAGE IF EXISTS {full_stage_name};
CREATE STAGE {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );
                """, language="sql")
        
        if st.button(":material/autorenew: 스테이지 재생성", help="스테이지 드롭 및 재생성"):
            try:
                session.sql(f"DROP STAGE IF EXISTS {full_stage_name}").collect()
                session.sql(f"""
                CREATE STAGE {full_stage_name}
                    DIRECTORY = ( ENABLE = true )
                    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
                """).collect()
                st.success(f":material/check_circle: 스테이지가 성공적으로 재생성되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"스테이지 재생성 실패: {str(e)}")

# TruLens 평가  
with st.container(border=True):
    st.markdown("##### :material/settings_suggest: 평가 구성 (Evaluation Configuration)")
    
    app_name = st.text_input(
        "앱 이름:",
        value="customer_review_rag",
        help="RAG 애플리케이션 이름"
    )
    
    app_version = st.text_input(
        "앱 버전:",
        value=f"v{st.session_state.run_counter}",
        help="이 실험의 버전 식별자"
    )
    
    rag_model = st.selectbox(
        "RAG 모델:",
        ["claude-3-5-sonnet", "mixtral-8x7b", "llama3-70b", "llama3.1-8b"],
        help="답변 생성을 위한 모델",
        key="trulens_model"
    )
    
    st.markdown("##### :material/dataset: 테스트 질문 (Test Questions)")
    test_questions_text = st.text_area(
        "질문 (한 줄에 하나씩):",
        value="What do customers say about thermal gloves?\nAre there any durability complaints?\nWhich products get the best reviews?",
        height=150,
        help="평가할 질문 입력"
    )
    
    run_evaluation = st.button(":material/science: TruLens 평가 실행", type="primary")

if run_evaluation:
    # 질문 파싱
    test_questions = [q.strip() for q in test_questions_text.split('\n') if q.strip()]
    
    if not test_questions:
        st.error("적어도 하나의 질문을 입력하세요.")
        st.stop()
    
    try:
        with st.status("TruLens 평가 실행 중...", expanded=True) as status:
            st.write(":orange[:material/check:] 필요한 라이브러리 가져오는 중...")
            
            from trulens.apps.app import TruApp
            from trulens.connectors.snowflake import SnowflakeConnector
            from trulens.core.run import Run, RunConfig
            import pandas as pd
            import time
            
            st.write(":orange[:material/check:] 테스트 데이터셋 준비 중...")
            
            # 데이터베이스 및 스키마 컨텍스트 설정 (TruLens에 필요)
            session.use_database(obs_database)
            session.use_schema(obs_schema)
            
            # 테스트 질문으로 DataFrame 생성
            test_data = []
            for idx, question in enumerate(test_questions):
                test_data.append({
                    "QUERY": question,
                    "QUERY_ID": idx + 1
                })
            
            test_df = pd.DataFrame(test_data)
            
            # TruLens용 Snowflake 테이블에 저장
            test_snowpark_df = session.create_dataframe(test_df)
            dataset_table = "CUSTOMER_REVIEW_TEST_QUESTIONS"
            
            # 테이블이 존재하면 드롭하고 다시 생성
            try:
                session.sql(f"DROP TABLE IF EXISTS {dataset_table}").collect()
            except:
                pass
            
            test_snowpark_df.write.mode("overwrite").save_as_table(dataset_table)
            
            st.write(f":orange[:material/check:] 데이터셋 테이블 생성됨: `{obs_database}.{obs_schema}.{dataset_table}`")
            
            st.write(":orange[:material/check:] RAG 애플리케이션 설정 중...")
            
            # 계측된 메서드로 RAG 클래스 정의 (작동 패턴 따름)
            class CustomerReviewRAG:
                def __init__(self, snowpark_session):
                    self.session = snowpark_session
                    self.search_service = search_service
                    self.num_results = num_results
                    self.model = rag_model
                
                @instrument()
                def retrieve_context(self, query: str) -> str:
                    """Cortex Search에서 컨텍스트 검색."""
                    root = Root(self.session)
                    parts = self.search_service.split(".")
                    svc = root.databases[parts[0]].schemas[parts[1]].cortex_search_services[parts[2]]
                    results = svc.search(query=query, columns=["CHUNK_TEXT"], limit=self.num_results)
                    context = "\n\n".join([r["CHUNK_TEXT"] for r in results.results])
                    return context
                
                @instrument()
                def generate_completion(self, query: str, context: str) -> str:
                    """LLM을 사용하여 답변 생성."""
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
                    """메인 RAG 쿼리 메서드."""
                    context = self.retrieve_context(query)
                    answer = self.generate_completion(query, context)
                    return answer
            
            st.write(":orange[:material/check:] TruLens에 앱 등록 중...")
            
            # 각 실행마다 새로운 TruLens 세션 생성 (재실행 시 지속되지 않음)
            from trulens.core import TruSession
            
            # 싱글톤 인스턴스 초기화하여 새 세션 보장
            if hasattr(TruSession, '_singleton_instances'):
                TruSession._singleton_instances.clear()
            
            # 새 커넥터 및 세션 생성
            tru_connector = SnowflakeConnector(snowpark_session=session)
            tru_session = TruSession(connector=tru_connector)
            
            # RAG 앱 인스턴스 생성
            rag_app = CustomerReviewRAG(session)
            
            # 각 실행마다 고유한 버전으로 RAG 앱 등록
            unique_app_version = f"{app_version}_{st.session_state.run_counter}"
            
            tru_rag = tru_session.App(
                rag_app,
                app_name=app_name,
                app_version=unique_app_version,
                main_method=rag_app.query
            )
            
            st.write(f":orange[:material/check:] {len(test_questions)}개 질문에 대해 평가 실행 중...")
            
            # 실행 구성
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
            
            # [실습] TruLens 실행을 추가하고 시작하세요.
            # 힌트: run = tru_rag.add_run(run_config=run_config)
            #       run.start()
            
            # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
            # run: Run = tru_rag.add_run(run_config=run_config)
            # run.start()
            
            # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요. 
            run = None
            pass # 이 부분을 수정하세요

            # [실습 정답용 코드 - 학생에게 제공하지 않음 / 실제 동작을 위해 아래 코드를 사용하지만, 학생 버전에서는 가려야 합니다]
            # 데모가 동작하게 하려면 아래 코드가 실행되어야 합니다.
            # 하지만 빈칸을 위해 주석처리합니다. (실제 실행시에는 이 부분이 활성화 되거나 학생이 작성해야 함)
            
            # run: Run = tru_rag.add_run(run_config=run_config)
            # run.start()
            
            if run: # 학생이 코드를 작성했을 때만 실행
                # 각 질문에 대한 진행 상황 표시 및 답변 생성
                generated_answers = {}
                for idx, question in enumerate(test_questions, 1):
                    st.write(f"  :orange[:material/check:] Question {idx}/{len(test_questions)}: {question[:60]}{'...' if len(question) > 60 else ''}")
                    # 이 질문에 대한 답변 생성
                    try:
                        answer = rag_app.query(question)
                        generated_answers[question] = answer
                    except Exception as e:
                        generated_answers[question] = f"Error: {str(e)}"
                
                st.write(":orange[:material/check:] 모든 호출 완료 대기 중...")
                
                # 호출 완료 대기
                max_wait = 180  # 3분
                start_time = time.time()
                while run.get_status() != "INVOCATION_COMPLETED":
                    if time.time() - start_time > max_wait:
                        st.warning("실행 시간이 예상보다 오래 걸립니다. 계속 진행합니다...")
                        break
                    time.sleep(3)
                
                st.write(":orange[:material/check:] RAG Triad 메트릭 계산 중...")
                
                # 실행에 대한 메트릭 계산
                try:
                    run.compute_metrics([
                        "answer_relevance",
                        "context_relevance",
                        "groundedness",
                    ])
                    metrics_computed = True
                    st.write(":orange[:material/check:] 메트릭 계산 완료!")
                except Exception as e:
                    st.warning(f"메트릭 계산 실패: {str(e)}")
                    metrics_computed = False
                
                st.write(":orange[:material/check: 평가 완료!")
                status.update(label="평가 완료", state="complete")
                
                # 실행 카운터 증가
                st.session_state.run_counter += 1
            
            else: # 실습 코드를 작성하지 않은 경우
                st.warning("실습 코드를 작성하여 평가를 실행하세요!")
                status.update(label="실습 필요", state="error")
        
        # 결과 표시 (run이 성공했을 때만)
        if 'generated_answers' in locals() and generated_answers:
            with st.container(border=True):
                st.markdown("#### :material/analytics: 평가 결과 (Evaluation Results)")
                
                st.success(f"""
:material/check: **평가 실행 완료!**

**실행 세부 정보:**
- 앱 이름: **{app_name}**
- 앱 버전: **{unique_app_version}**
- 실행 이름: **{run_config.run_name}**
- 평가된 질문 수: **{len(test_questions)}**
- 모델: **{rag_model}**

**Snowsight에서 결과 보기:**
이동: **AI & ML → Evaluations → {app_name}**
                """)
                
                # 생성된 답변 표시
                with st.expander("생성된 답변 (Generated Answers)", expanded=True):
                    for idx, question in enumerate(test_questions, 1):
                        st.markdown(f"**질문 {idx}:** {question}")
                        st.info(generated_answers.get(question, "답변 생성되지 않음"))
                        if idx < len(test_questions):
                            st.markdown("---")
        
    except Exception as e:
        st.error(f"평가 중 오류 발생: {str(e)}")
        
        with st.expander("전체 오류 세부 정보 보기"):
            st.exception(e)
        
        st.info("""
        **문제 해결:**
        - 필수 패키지가 설치되어 있는지 확인하세요 (아래 요건 참조)
        - Cortex Search 서비스에 액세스할 수 있는지 확인하세요
        - 데이터베이스 및 스키마 권한을 확인하세요
        - 관찰 가능성 스키마에 테이블을 생성할 권한이 있는지 확인하세요
        """)
        
        with st.expander(":material/code: 필수 패키지"):
            st.code("""# pyproject.toml에 추가하거나 환경에 설치:
trulens-connectors-snowflake>=2.5.0
snowflake-snowpark-python>=1.18.0,<2.0
pandas>=1.5.0""", language="txt")

# 바닥글
st.divider()
st.caption("Day 23: LLM 평가 및 AI 관찰 가능성 (LLM Evaluation & AI Observability) | 30 Days of AI")
