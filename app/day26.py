# Day 26: Cortex Agent 소개 (Introduction to Cortex Agents)
import streamlit as st

# Snowflake 연결 설정
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

st.title(":material/smart_toy: Cortex Agents 소개")
st.write("영업 대화(Sales Conversations)를 대상으로 Cortex Search를 활용한 Cortex Agent를 생성하는 방법을 배웁니다.")

st.session_state.setdefault("agent_created", False)

# 사이드바 설정
with st.sidebar:
    st.header(":material/settings: 설정 (Configuration)")
    db_name, schema_name, agent_name, search_service = "CHANINN_SALES_INTELLIGENCE", "DATA", "SALES_CONVERSATION_AGENT", "SALES_CONVERSATION_SEARCH"
    st.text_input("데이터베이스:", db_name, disabled=True)
    st.text_input("스키마:", schema_name, disabled=True)
    st.text_input("에이전트 이름:", agent_name, disabled=True)
    st.text_input("검색 서비스:", search_service, disabled=True)
    st.caption("이 값들은 27일차의 에이전트 설정과 일치합니다.")
    st.divider()
    if st.button(":material/refresh: 채팅 초기화"):
        st.session_state.messages = []
        st.rerun()

# 탭 구성
tab0, tab1 = st.tabs([":material/database: 데이터 설정", ":material/build: 에이전트 생성"])

# 데이터 설정 탭 (Data Setup Tab)
with tab0:
    # 1단계: 데이터베이스 및 스키마 생성
    st.markdown("---\n### 1단계: 데이터베이스 및 스키마 생성")
    setup_step1 = f"""-- 데이터베이스 및 스키마 생성 (26-28일차용)
CREATE OR REPLACE DATABASE "{db_name}";
CREATE OR REPLACE SCHEMA "{db_name}"."{schema_name}";
USE DATABASE "{db_name}"; USE SCHEMA "{schema_name}"; USE WAREHOUSE COMPUTE_WH;"""
    st.code(setup_step1, language="sql")
    
    if st.button(":material/play_arrow: 1단계 실행", key="run_step1", use_container_width=True):
        with st.spinner("데이터베이스와 스키마를 생성 중입니다..."):
            try:
                for sql in [f'CREATE OR REPLACE DATABASE "{db_name}"', f'CREATE OR REPLACE SCHEMA "{db_name}"."{schema_name}"',
                           f'USE DATABASE "{db_name}"', f'USE SCHEMA "{schema_name}"', "USE WAREHOUSE COMPUTE_WH"]:
                    session.sql(sql).collect()
                st.success("✓ 1단계 완료!")
            except Exception as e:
                st.error(f"오류 발생: {e}")
    
    # 2단계: 영업 대화 테이블 생성
    st.markdown("---\n### 2단계: 영업 대화 테이블 생성")
    setup_step2 = f"""-- 대화 녹취록을 저장할 테이블 생성
CREATE OR REPLACE TABLE "{db_name}"."{schema_name}".SALES_CONVERSATIONS (
    conversation_id VARCHAR, transcript_text TEXT, customer_name VARCHAR, deal_stage VARCHAR,
    sales_rep VARCHAR, conversation_date TIMESTAMP, deal_value FLOAT, product_line VARCHAR
);
-- 10개의 상세 영업 대화 녹취록 삽입 (전체 코드는 파일 참조)"""
    st.code(setup_step2, language="sql")
    
    if st.button(":material/play_arrow: 2단계 실행", key="run_step2", use_container_width=True):
        with st.spinner("테이블 생성 및 데이터 삽입 중..."):
            try:
                session.sql(f"""CREATE OR REPLACE TABLE "{db_name}"."{schema_name}".SALES_CONVERSATIONS (
                    conversation_id VARCHAR, transcript_text TEXT, customer_name VARCHAR, deal_stage VARCHAR,
                    sales_rep VARCHAR, conversation_date TIMESTAMP, deal_value FLOAT, product_line VARCHAR)""").collect()
                
                session.sql(f"""INSERT INTO "{db_name}"."{schema_name}".SALES_CONVERSATIONS 
                (conversation_id, transcript_text, customer_name, deal_stage, sales_rep, conversation_date, deal_value, product_line) VALUES
                ('CONV001', 'TechCorp Inc의 IT 디렉터 및 솔루션 아키텍트와의 초기 디스커버리 콜. 고객은 당사의 엔터프라이즈 솔루션 기능, 특히 자동화된 워크플로우 기능에 강한 관심을 보임. 주요 논의 내용은 통합 일정과 복잡성에 집중됨. 현재 핵심 운영에 Legacy System X를 사용 중이며 마이그레이션 중 잠재적 중단에 대한 우려를 표명함. 팀은 API 호환성 및 데이터 마이그레이션 도구에 대해 상세한 질문을 함. 후속 작업: 1) 상세 통합 일정 문서 제공 2) 인프라 팀과 기술 심층 분석 일정 예약 3) 유사한 Legacy System X 마이그레이션 사례 공유. 고객은 디지털 전환 이니셔티브를 위한 2분기 예산 할당을 언급함. 전반적으로 명확한 다음 단계가 있는 긍정적인 참여였음.', 'TechCorp Inc', 'Discovery', 'Sarah Johnson', '2024-01-15 10:30:00', 75000, 'Enterprise Suite'),
                ('CONV002', 'SmallBiz Solutions의 운영 매니저 및 재무 디렉터와의 후속 콜. 주요 초점은 가격 구조와 ROI 타임라인이었음. 당사의 기본 패키지 가격을 Competitor Y의 중소기업 상품과 비교함. 주요 논의 사항: 월별 vs 연간 결제 옵션, 사용자 라이선스 제한, 프로세스 자동화를 통한 잠재적 비용 절감. 고객은 다음 사항에 초점을 맞춘 상세 ROI 분석을 요청함: 1) 일일 운영에서 절약된 시간 2) 리소스 할당 개선 3) 예상 효율성 이득. 예산 제약이 명확하게 전달됨 - 올해 최대 예산은 $30K. 4분기에 업그레이드 가능성이 있는 기본 패키지로 시작하는 데 관심을 보임. 다음 주까지 경쟁 분석 및 맞춤형 ROI 계산기 제공 필요.', 'SmallBiz Solutions', 'Negotiation', 'Mike Chen', '2024-01-16 14:45:00', 25000, 'Basic Package'),
                ('CONV003', 'SecureBank Ltd의 CISO 및 보안 운영 팀과의 전략 세션. 프리미엄 보안 패키지에 대한 매우 긍정적인 90분 심층 분석. 고객은 최근 업계 규정 업데이트로 인해 즉각적인 구현 필요성을 강조함. 당사의 고급 보안 기능, 특히 다요소 인증 및 암호화 프로토콜이 요구 사항에 완벽하게 부합하는 것으로 확인됨. 기술 팀은 특히 제로 트러스트 아키텍처 접근 방식과 실시간 위협 모니터링 기능에 깊은 인상을 받음. 이미 예산 승인을 받았으며 경영진의 지지를 얻음. 규정 준수 문서는 검토 준비 완료. 후속 작업: 구현 타임라인 확정, 보안 감사 일정 예약, 리스크 평가 팀을 위한 필요한 문서 준비. 고객은 계약 논의를 진행할 준비가 됨.', 'SecureBank Ltd', 'Closing', 'Rachel Torres', '2024-01-17 11:20:00', 150000, 'Premium Security'),
                ('CONV004', 'GrowthStart Up의 CTO 및 부서장들과의 종합 디스커버리 콜. 3개 대륙에 걸친 500명 이상의 직원 팀이 기존 솔루션의 현재 과제에 대해 논의함. 확인된 주요 문제점: 피크 시간대의 시스템 다운, 제한된 부서 간 보고 기능, 원격 팀을 위한 낮은 확장성. 현재 워크플로우를 심층 분석한 결과 데이터 공유 및 협업의 병목 현상이 발견됨. 각 부서별 기술 요구 사항 수집됨. 플랫폼 데모는 확장성 기능과 글로벌 팀 관리 기능에 집중함. 고객은 특히 당사의 API 에코시스템과 맞춤형 보고 엔진에 관심을 보임. 다음 단계: 부서별 워크플로우 분석 일정 예약 및 상세 플랫폼 마이그레이션 계획 준비.', 'GrowthStart Up', 'Discovery', 'Sarah Johnson', '2024-01-18 09:15:00', 100000, 'Enterprise Suite'),
                ('CONV005', 'DataDriven Co의 분석 팀 및 비즈니스 인텔리전스 매니저들과의 심층 데모 세션. 고급 분석 기능, 맞춤형 대시보드 생성 및 실시간 데이터 처리 기능에 초점을 맞춘 쇼케이스. 팀은 특히 당사의 머신러닝 통합 및 예측 분석 모델에 깊은 인상을 받음. Market Leader Z 및 Innovative Start-up X와 구체적인 경쟁사 비교 요청됨. 가격대는 할당된 예산 범위 내에 있지만, 팀은 상응하는 할인 구조가 있는 다년 계약에 관심을 보임. 기술 질문은 데이터 웨어하우스 통합 및 맞춤형 시각화 기능에 집중됨. 후속 작업: 상세 경쟁사 기능 비교 매트릭스 준비 및 다양한 할인 시나리오가 포함된 다년 가격 제안서 초안 작성.', 'DataDriven Co', 'Demo', 'James Wilson', '2024-01-19 13:30:00', 85000, 'Analytics Pro'),
                ('CONV006', 'HealthTech Solutions의 IT 보안 팀, 규정 준수 책임자 및 시스템 아키텍트와의 연장된 기술 심층 분석. API 인프라, 데이터 보안 프로토콜 및 규정 준수 요구 사항에 집중한 4시간 세션. 팀은 HIPAA 준수, 데이터 암호화 표준 및 API 속도 제한에 대해 구체적인 우려를 제기함. 종단 간 암호화, 감사 로깅 및 재해 복구 프로토콜을 포함한 당사의 보안 아키텍처에 대한 상세 논의. 고객은 특히 SOC 2 및 HITRUST와 같은 규정 준수 인증에 대한 광범위한 문서를 요구함. 보안 팀은 초기 아키텍처 검토를 수행하고 데이터베이스 격리, 백업 절차 및 침해 사고 대응 프로토콜에 대한 추가 정보를 요청함. 다음 주에 규정 준수 팀과 후속 세션 예약됨.', 'HealthTech Solutions', 'Technical Review', 'Rachel Torres', '2024-01-20 15:45:00', 120000, 'Premium Security'),
                ('CONV007', 'LegalEase Corp의 법무 실장, 구매 디렉터 및 IT 매니저와의 계약 검토 회의. 가동 시간 보장 및 지원 응답 시간에 초점을 맞춘 SLA 약관 상세 분석. 법무 팀은 책임 조항 및 데이터 처리 합의에 대한 특정 수정을 요청함. 구매 팀은 결제 조건 및 서비스 크레딧 구조에 대해 질문함. 주요 논의 사항: 재해 복구 약속, 데이터 보관 정책 및 계약 종료 조항 사양. IT 매니저는 최종 보안 평가가 완료될 때까지 기술 요구 사항이 충족됨을 확인했음. 대부분의 약관에 합의했으며 SLA 수정 사항만 논의가 남았음. 법무 팀은 주말까지 수정된 계약 문구를 제공하기로 함. 전반적으로 폐쇄로 가는 명확한 경로가 있는 긍정적인 세션이었음.', 'LegalEase Corp', 'Negotiation', 'Mike Chen', '2024-01-21 10:00:00', 95000, 'Enterprise Suite'),
                ('CONV008', 'GlobalTrade Inc의 현재 구현 팀 및 잠재적 확장 이해관계자들과의 분기별 비즈니스 리뷰. 재무 부서의 현재 구현 사례가 높은 채택률과 40%의 처리 시간 개선을 보여줌. 솔루션을 운영 및 인사(HR) 부서로 확장하는 것에 대해 논의함. 사용자들은 고객 지원 및 플랫폼 안정성에 대한 긍정적인 경험을 강조함. 현재 사용상의 과제: 추가 맞춤 보고서 필요성 및 워크플로우 프로세스의 자동화 증가. 운영 디렉터로부터 수집된 확장 요구 사항: 재고 관리 통합, 공급업체 포털 액세스 및 강화된 추적 기능. HR 팀은 채용 및 온보딩 워크플로우 자동화에 관심을 보임. 다음 단계: 부서별 구현 계획 및 확장 ROI 분석 준비.', 'GlobalTrade Inc', 'Expansion', 'James Wilson', '2024-01-22 14:20:00', 45000, 'Basic Package'),
                ('CONV009', 'FastTrack Ltd의 경영진 및 프로젝트 매니저들과의 비상 계획 세션. 현재 시스템 장애로 인해 신속한 구현이 절실함. 팀은 빠른 배포와 전담 지원 팀을 위해 프리미엄을 지불할 의사가 있음. 가속화된 구현 타임라인 및 리소스 요구 사항에 대한 상세 논의. 주요 요구 사항: 운영 중단 최소화, 단계적 데이터 마이그레이션 및 비상 지원 프로토콜. 기술 팀은 추가 리소스를 통해 공격적인 타임라인을 맞출 수 있다고 자신함. 실행 스폰서는 30일 이내 가동의 중요성을 강조함. 즉각적인 다음 단계: 가속화된 구현 계획 확정, 전담 지원 팀 배정 및 비상 온보딩 절차 시작. 팀은 진행 상황 업데이트를 위해 매일 재소집하기로 함.', 'FastTrack Ltd', 'Closing', 'Sarah Johnson', '2024-01-23 16:30:00', 180000, 'Premium Security'),
                ('CONV010', 'UpgradeNow Corp의 부서장 및 분석 팀과의 분기별 전략 검토. 현재 구현이 기본적인 요구 사항은 충족하지만 팀은 더 정교한 분석 기능을 요구함. 현재 사용 패턴을 심층 분석한 결과 워크플로우 최적화 및 고급 보고 요구 사항의 기회를 발견함. 사용자들은 플랫폼 안정성과 기본 기능에 만족을 표했으나, 강화된 데이터 시각화 및 예측 분석 기능을 요구함. 분석 팀은 맞춤형 대시보드 생성, 고급 데이터 모델링 도구 및 통합 BI 기능과 같은 특정 요구 사항을 제시함. 현재 패키지에서 Analytics Pro 티어로의 업그레이드 경로에 대해 논의함. 보고 효율성이 60% 향상될 가능성이 있는 ROI 분석 결과 발표됨. 팀은 다음 달에 경영 위원회에 업그레이드 제안서를 제출하기로 함.', 'UpgradeNow Corp', 'Expansion', 'Rachel Torres', '2024-01-24 11:45:00', 65000, 'Analytics Pro')
                """).collect()
                st.success("✓ 2단계 완료! 10개의 상세 영업 대화 녹취록이 포함된 테이블이 생성되었습니다.")
            except Exception as e:
                st.error(f"오류 발생: {e}")
    
    # 3단계: Cortex Search
    st.markdown("---\n### 3단계: Cortex Search 서비스 생성")
    st.info("**Cortex Search**는 텍스트 데이터에 시맨틱 검색 인덱스를 생성합니다.\n이를 통해 에이전트는 키워드뿐만 아니라 의미를 바탕으로 관련 대화를 찾을 수 있습니다.")
    setup_step3 = f"""-- 변경 내용 추적 활성화 (Cortex Search에 필수)
ALTER TABLE "{db_name}"."{schema_name}".SALES_CONVERSATIONS SET CHANGE_TRACKING = TRUE;
-- Cortex Search 서비스 생성 (존재하지 않는 경우)
CREATE CORTEX SEARCH SERVICE IF NOT EXISTS "{db_name}"."{schema_name}".{search_service}
  ON transcript_text ATTRIBUTES customer_name, deal_stage, sales_rep WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
  AS (SELECT transcript_text, customer_name, deal_stage, sales_rep, conversation_date
      FROM "{db_name}"."{schema_name}".SALES_CONVERSATIONS WHERE conversation_date >= '2024-01-01');"""
    st.code(setup_step3, language="sql")
    
    if st.button(":material/play_arrow: 3단계 실행", key="run_step3", use_container_width=True):
        with st.status("Cortex Search 설정 중...", expanded=True) as status:
            try:
                # 3.1단계: 서비스 존재 여부 확인
                st.write(":material/search: 기존 검색 서비스 확인 중...")
                try:
                    existing = session.sql(f'SHOW CORTEX SEARCH SERVICES IN SCHEMA "{db_name}"."{schema_name}"').collect()
                    service_exists = any(row['name'] == search_service for row in existing)
                except:
                    service_exists = False
                
                if service_exists:
                    st.write(f":material/check_circle: '{search_service}' 검색 서비스가 이미 존재합니다.")
                    status.update(label="✓ 3단계 완료 (서비스가 이미 존재함)!", state="complete")
                else:
                    # 3.2단계: 변경 내용 추적 활성화
                    st.write(":material/update: 테이블에서 변경 내용 추적 활성화 중...")
                    session.sql(f'ALTER TABLE "{db_name}"."{schema_name}".SALES_CONVERSATIONS SET CHANGE_TRACKING = TRUE').collect()
                    
                    # 3.3단계: 검색 서비스 생성
                    st.write(":material/build: Cortex Search 서비스 생성 중 (약 30-60초 소요)...")
                    session.sql(f"""CREATE CORTEX SEARCH SERVICE "{db_name}"."{schema_name}".{search_service}
                        ON transcript_text ATTRIBUTES customer_name, deal_stage, sales_rep WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
                        AS (SELECT transcript_text, customer_name, deal_stage, sales_rep, conversation_date
                            FROM "{db_name}"."{schema_name}".SALES_CONVERSATIONS WHERE conversation_date >= '2024-01-01')""").collect()
                    
                    st.write(":material/check_circle: 검색 서비스가 성공적으로 생성되었습니다.")
                    status.update(label="✓ 3단계 완료! 서비스가 백그라운드에서 인덱싱 중입니다 (1-2분 소요)", state="complete")
            except Exception as e:
                st.error(f"오류 발생: {e}")
                status.update(label="실패", state="error")
    
    # 4단계: 영업 지표 테이블 생성
    st.markdown("---\n### 4단계: 영업 지표 테이블 생성")
    st.info("**영업 지표 테이블**은 Cortex Analyst가 쿼리할 정형화된 거래 데이터를 포함합니다.\n이 데이터는 28일차에 자연어 SQL 생성을 위해 사용됩니다.")
    setup_step4 = f"""-- 영업 지표 테이블 생성
CREATE OR REPLACE TABLE "{db_name}"."{schema_name}".SALES_METRICS (
    deal_id VARCHAR, customer_name VARCHAR, deal_value FLOAT, close_date DATE,
    sales_stage VARCHAR, win_status BOOLEAN, sales_rep VARCHAR, product_line VARCHAR);
-- 샘플 영업 지표 데이터 삽입 (10개 거래)"""
    st.code(setup_step4, language="sql")
    
    if st.button(":material/play_arrow: 4단계 실행", key="run_step4", use_container_width=True):
        with st.spinner("영업 지표 테이블 생성 중..."):
            try:
                session.sql(f"""CREATE OR REPLACE TABLE "{db_name}"."{schema_name}".SALES_METRICS (
                    deal_id VARCHAR, customer_name VARCHAR, deal_value FLOAT, close_date DATE,
                    sales_stage VARCHAR, win_status BOOLEAN, sales_rep VARCHAR, product_line VARCHAR)""").collect()
                session.sql(f"""INSERT INTO "{db_name}"."{schema_name}".SALES_METRICS VALUES
                    ('DEAL001', 'TechCorp Inc', 75000, '2024-02-15', 'Closed', true, 'Sarah Johnson', 'Enterprise Suite'),
                    ('DEAL002', 'SmallBiz Solutions', 25000, '2024-02-01', 'Lost', false, 'Mike Chen', 'Basic Package'),
                    ('DEAL003', 'SecureBank Ltd', 150000, '2024-01-30', 'Closed', true, 'Rachel Torres', 'Premium Security'),
                    ('DEAL004', 'GrowthStart Up', 100000, '2024-02-10', 'Pending', false, 'Sarah Johnson', 'Enterprise Suite'),
                    ('DEAL005', 'DataDriven Co', 85000, '2024-02-05', 'Closed', true, 'James Wilson', 'Analytics Pro'),
                    ('DEAL006', 'HealthTech Solutions', 120000, '2024-02-20', 'Pending', false, 'Rachel Torres', 'Premium Security'),
                    ('DEAL007', 'LegalEase Corp', 95000, '2024-01-25', 'Closed', true, 'Mike Chen', 'Enterprise Suite'),
                    ('DEAL008', 'GlobalTrade Inc', 45000, '2024-02-08', 'Closed', true, 'James Wilson', 'Basic Package'),
                    ('DEAL009', 'FastTrack Ltd', 180000, '2024-02-12', 'Closed', true, 'Sarah Johnson', 'Premium Security'),
                    ('DEAL010', 'UpgradeNow Corp', 65000, '2024-02-18', 'Pending', false, 'Rachel Torres', 'Analytics Pro')""").collect()
                st.success("✓ 4단계 완료! 10개의 거래 데이터가 포함된 영업 지표 테이블이 생성되었습니다.")
            except Exception as e:
                st.error(f"오류 발생: {e}")
    
    # 5단계: 시맨틱 모델 YAML 업로드
    st.markdown("---\n### 5단계: 시맨틱 모델 YAML 업로드")
    st.info("**시맨틱 모델**은 Cortex Analyst에게 데이터베이스 스키마를 어떻게 해석할지 알려줍니다.\nYAML 파일을 다운로드하여 다음 단계에서 Snowflake 스테이지에 업로드하세요.")
    
    semantic_model_yaml = f"""name: sales_metrics
description: 영업 지표 및 분석 모델
tables:
  - name: SALES_METRICS
    base_table:
      database: {db_name}
      schema: {schema_name}
      table: SALES_METRICS
    dimensions:
      - name: DEAL_ID
        expr: DEAL_ID
        data_type: VARCHAR(16777216)
        sample_values: [DEAL001, DEAL002, DEAL003]
        description: 영업 거래의 고유 식별자입니다.
        synonyms: [거래 ID, 계약 ID, 주문 번호]
      - name: CUSTOMER_NAME
        expr: CUSTOMER_NAME
        data_type: VARCHAR(16777216)
        sample_values: [TechCorp Inc, SmallBiz Solutions, SecureBank Ltd]
        description: 판매와 관련된 고객의 이름입니다.
        synonyms: [고객사, 클라이언트, 구매자]
      - name: SALES_STAGE
        expr: SALES_STAGE
        data_type: VARCHAR(16777216)
        sample_values: [Closed, Lost, Pending]
        description: 영업 기회의 현재 단계입니다.
        synonyms: [거래 상태, 판매 단계, 파이프라인 위치]
      - name: WIN_STATUS
        expr: WIN_STATUS
        data_type: BOOLEAN
        sample_values: ['TRUE', 'FALSE']
        description: 판매 성공 여부를 나타냅니다.
        synonyms: [성사 여부, 성공, 종료]
      - name: SALES_REP
        expr: SALES_REP
        data_type: VARCHAR(16777216)
        sample_values: [Sarah Johnson, Mike Chen, Rachel Torres]
        description: 해당 판매를 담당하는 영업 사원입니다.
        synonyms: [영업 담당자, 계정 관리자]
      - name: PRODUCT_LINE
        expr: PRODUCT_LINE
        data_type: VARCHAR(16777216)
        sample_values: [Enterprise Suite, Basic Package, Premium Security]
        description: 제품 또는 서비스의 유형을 구분합니다.
        synonyms: [제품군, 상품 카테고리]
    time_dimensions:
      - name: CLOSE_DATE
        expr: CLOSE_DATE
        data_type: DATE
        sample_values: ['2024-02-15', '2024-02-01', '2024-01-30']
        description: 판매가 종료되거나 확정된 날짜입니다.
        synonyms: [완료일, 판매일, 거래 마감일]
    measures:
      - name: DEAL_VALUE
        expr: DEAL_VALUE
        data_type: FLOAT
        sample_values: ['75000', '25000', '150000']
        description: 영업 거래의 총 금전적 가치입니다.
        synonyms: [매출, 판매 금액, 거래 가액]
"""
    
    st.code(semantic_model_yaml, language="yaml")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(":material/download: YAML 다운로드", semantic_model_yaml, "sales_metrics_model.yaml", 
                          "application/x-yaml", use_container_width=True)
    with col2:
        if st.button(":material/cloud_upload: 스테이지로 자동 업로드", key="run_step5", use_container_width=True, type="primary"):
            with st.spinner("스테이지 생성 및 YAML 업로드 중..."):
                try:
                    import tempfile, os
                    session.sql(f'CREATE STAGE IF NOT EXISTS "{db_name}"."{schema_name}".MODELS').collect()
                    
                    # 기존 파일 정리
                    try:
                        files = session.sql(f'LIST @"{db_name}"."{schema_name}".MODELS').collect()
                        for row in files:
                            fname = str(row['name']).split('/')[-1]
                            if 'sales_metrics_model' in fname.lower():
                                session.sql(f'REMOVE @"{db_name}"."{schema_name}".MODELS/{fname}').collect()
                    except: pass
                    
                    # 새 파일 업로드
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = os.path.join(temp_dir, 'sales_metrics_model.yaml')
                    try:
                        with open(temp_file_path, 'w', encoding='utf-8') as f:
                            f.write(semantic_model_yaml)
                        session.file.put(temp_file_path, f'@"{db_name}"."{schema_name}".MODELS', auto_compress=False, overwrite=True)
                        
                        # 확인
                        files = session.sql(f'LIST @"{db_name}"."{schema_name}".MODELS').collect()
                        uploaded_files = [str(row['name']).split('/')[-1] for row in files]
                        if 'sales_metrics_model.yaml' in uploaded_files:
                            st.success("✓ 5단계 완료! `sales_metrics_model.yaml`로 업로드되었습니다.")
                        else:
                            st.error("업로드는 성공했으나 스테이지 탐지 실패")
                    finally:
                        try:
                            if os.path.exists(temp_file_path): os.remove(temp_file_path)
                            if os.path.exists(temp_dir): os.rmdir(temp_dir)
                        except: pass
                except Exception as e:
                    st.error(f"자동 업로드 실패: {str(e)}")
                    st.info("💡 'YAML 다운로드' 버튼을 사용해 수동으로 업로드하세요.")
    
    with st.expander("📋 수동 업로드 방법 (자동 업로드 실패 시)"):
        st.markdown("""
        1. 위의 **"YAML 다운로드"** 버튼 클릭
        2. Snowsight에서: **Data** → **Databases** → **CHANINN_SALES_INTELLIGENCE** → **DATA**
        3. **"Stages"** 탭 클릭 → **MODELS** 스테이지 선택
        4. **"+ Files"** 클릭 → `sales_metrics_model.yaml` 업로드
        """)
    
    # 6단계: 설정 완료 확인
    st.markdown("---\n### 6단계: 모든 설정 확인")
    if st.button(":material/verified: 데이터 준비 상태 확인", type="primary", use_container_width=True):
        with st.status("설정 확인 중...", expanded=True) as status:
            all_good = True
            checks = [
                (f'USE DATABASE "{db_name}"', "데이터베이스 존재"),
                (f'SELECT COUNT(*) as cnt FROM "{db_name}"."{schema_name}".SALES_CONVERSATIONS', "대화 기록 테이블 데이터 확인", True),
                (f'SHOW CORTEX SEARCH SERVICES IN SCHEMA "{db_name}"."{schema_name}"', "Cortex Search 서비스 확인", False, search_service),
                (f'SELECT COUNT(*) as cnt FROM "{db_name}"."{schema_name}".SALES_METRICS', "영업 지표 테이블 데이터 확인", True, None, True),
                (f'SHOW STAGES IN SCHEMA "{db_name}"."{schema_name}"', "MODELS 스테이지 확인", False, "MODELS", True)
            ]
            
            for check in checks:
                sql, name = check[0], check[1]
                try:
                    result = session.sql(sql).collect()
                    if len(check) > 2 and check[2]:  # Count 쿼리
                        st.write(f":material/check_circle: {name} ({result[0]['CNT']}개 레코드 발견)")
                    elif len(check) > 3 and check[3]:  # 특정 값 확인
                        found = any(check[3] in str(r) for r in result)
                        if found: st.write(f":material/check_circle: {name}")
                        else: 
                            st.write(f":material/cancel: {name} 찾을 수 없음")
                            all_good = False
                    else:
                        st.write(f":material/check_circle: {name}")
                except:
                    st.write(f":material/cancel: {name} 확인 실패")
                    all_good = False
            
            if all_good:
                status.update(label=":material/celebration: 모든 데이터가 준비되었습니다!", state="complete")
                st.balloons()
            else:
                status.update(label="일부 설정이 누락되었습니다.", state="error")

# 에이전트 생성 탭 (Create Agent Tab)
with tab1:
    st.markdown("### 영업 지능형 에이전트 생성")
    
    instructions = """당신은 두 가지 데이터 소스에 접근할 수 있는 영업 지능형 어시스턴트입니다:
1. 영업 대화 녹취록 (ConversationSearch 도구 활용)
2. 영업 지표 및 거래 데이터 (SalesAnalyst 도구 활용)

중요 제약 사항:
- 영업 데이터, 대화, 거래, 고객 및 영업 지표에 관한 질문에만 답변하세요.
- 날씨, 코딩, 일반 상식, 시사 이슈 등 영업과 관련 없는 질문은 정중히 거절하세요.
- 도구에서 제공된 데이터만 사용하고 정보를 지어내지 마세요.
- 데이터를 찾을 수 없는 경우 사실대로 답변하세요.
- 통계, 평균, 개수 등 지표 질문은 SalesAnalyst 도구를 사용하세요.
- 대화 요약, 논의 내용 등은 ConversationSearch 도구를 사용하세요."""
    
    create_sql = f"""CREATE OR REPLACE AGENT "{db_name}"."{schema_name}".{agent_name}
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: '{instructions.replace("'", "''")}'
    orchestration: '지표 질문에는 SalesAnalyst를, 대화 내용 질문에는 ConversationSearch를 사용하세요.'
    system: '당신은 유능하고 제약이 엄격한 영업 지능형 어시스턴트입니다.'
  tools:
    - tool_spec:
        type: "cortex_search"
        name: "ConversationSearch"
        description: "영업 대화 녹취록을 검색합니다."
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "SalesAnalyst"
        description: "영업 지표에 대한 SQL 쿼리를 생성하고 실행합니다."
  tool_resources:
    ConversationSearch:
      name: "{db_name}.{schema_name}.{search_service}"
      max_results: "5"
    SalesAnalyst:
      semantic_model_file: "@chaninn_sales_intelligence.data.models/sales_metrics_model.yaml"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
        query_timeout: 60
  $$;"""
    
    st.code(create_sql, language="sql")
    
    if st.button(":material/play_arrow: 에이전트 생성", type="primary", use_container_width=True):
        try:
            with st.status("에이전트 생성 중...") as status:
                try:
                    session.sql("SHOW AGENTS").collect()
                    st.write(":material/check: Cortex Agents 기능 사용 가능")
                except Exception as e:
                    st.error(":material/error: 해당 계정에서 Cortex Agents 기능을 사용할 수 없습니다.")
                    st.stop()
                
                st.write(":material/check: 에이전트 생성 중...")
                # [실습] CREATE AGENT SQL 문을 세션에서 실행하여 에이전트를 생성하세요.
                # 힌트: session.sql(create_sql).collect()
                
                # 여기에 코드를 작성하세요
                # session.sql(create_sql).collect()
                
                st.info("코드를 완성하고 실행 버튼을 눌러주세요.")
                st.stop() # 실습을 위해 여기서 중단 (코드를 완성하면 이 라인을 삭제하거나 주석 처리하세요)

                # 아래는 실제 실행될 코드입니다 (실습 시 참고)
                session.sql(create_sql).collect()
                st.write(f"  에이전트 생성 완료: {db_name}.{schema_name}.{agent_name}")
                st.session_state.agent_created = True
                status.update(label=":material/check_circle: 에이전트 준비 완료!", state="complete")
                st.balloons()
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
            # status는 with block 안에서만 유효함. try/except가 with block 밖에 있으면 여기서 status 접근 안됨.
            # but in turn 431 it was outside too. fixed by moving into the block if possible or removing.
            # I will ensure status is defined or handled.
            # Actually, the with block at 367 ends at 380.
            # I'll move the logic to handle status update.

st.divider()
st.caption("Day 26: Cortex Agent 소개 | 첫 번째 에이전트 만들기 | Streamlit과 함께하는 30일간의 AI 챌린지")
