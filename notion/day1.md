# Connect to Snowflake

# 0. 목표

<aside>
💡

**Streamlit 앱과 Snowflake 데이터베이스 간의 연결 수립 및 확인**

1. Snowflake 연결 설정 (로컬 vs SiS)
2. `snowflake.snowpark` 라이브러리를 활용한 세션 생성
3. SQL 쿼리 실행을 통한 연결 상태 확인 (버전 조회)
</aside>

# 1. 환경 설정 (Connection Setup)

- Snowflake 가입
    
    ## Snowflake 회원가입
    
    1. Snowfalke 사이트 접속 : https://www.snowflake.com/ko/
    2. 우측 상단 무료로 시작하기 클릭
        
        ![snowflake회원가입.png](attachment:5b456aeb-18fd-45fc-a2ae-fec1871b3a1a:821865e2-aa1e-461a-944d-22e7344b1895.png)
        
    3. 이름 : 영어명 , 회사 명, 학교 명, 직책 : 학생 , 이후 나머지 설정은 스킵하기
    4. 이후 가입한 이메일로 가서 Account를 눌러 아이디와 비번 설정하기
        - 비밀번호 규칙
            
            비밀번호는 14~256자 이상이어야 하며, 숫자 1개, 특수 문자 0개, 대문자 1개, 소문자 1개 이상을 포함해야 합니다.
            
    5. 가입이 완료 되면 프로필을 눌러 계정 정보 확인하기
        - 계정 Account 확인
            
            ![내 프로필1.png](attachment:33c506ce-4987-4c95-bc9e-84ecd90d97a5:내_프로필1.png)
            
            좌측 하단에 내 프로필 클릭
            
            ![프로필2.png](attachment:57867dc8-2bfc-4d8e-9b57-4bd9cf845de9:프로필2.png)
            
            Account 클릭 후 `View account details` 확인
            
            ![Account 정보.png](attachment:8c94eff0-020f-46e9-97f0-640cdee68426:Account_정보.png)
            
            이후 Account name 확인 후 이름 값 복사
            

파이썬 버전 3.11.n 으로 다운그레이드(snowflake는 최신 버전과 구동 x )

에디터에 새 폴더를 제작한 뒤 터미널에 코드 입력

`git clone https://github.com/streamlit/30DaysOfAI`

- 배포되는 환경에 따라 Snowflake 연결 방식이 다르게 구성됨
- **Streamlit in Snowflake (SiS)**
    - 별도의 설정 없이 자동으로 연결됨 (`get_active_session` 사용)
- **Local Development / Community Cloud**
    - `.streamlit/secrets.toml` 파일에 접속 정보를 명시해야 함
    
    ```toml
    [connections.snowflake] 
    user = "내_스노우플레이크_아이디"
    password = "내_스노우플레이크_비밀번호"
    account = "내_계정_식별자"       : snowflake 프로필에서 확인 가능
    warehouse = "COMPUTE_WH"
    database = "DEMO_DB"
    schema = "PUBLIC"
    role = "ACCOUNTADMIN"
    
    ```
    
    - **주의**: `secrets.toml` 파일은 보안상 git에 커밋되지 않도록 `.gitignore`에 추가해야 함
    - 이후 .streamlit 폴더의 위치를 app폴더 내부로 옮기기

# 2. Streamlit 앱 구현

## 라이브러리 임포트 및 연결 시도

- 단일 코드베이스로 로컬과 운영 환경 모두를 지원하기 위해 `try-except` 패턴 사용
    
    ```python
    import streamlit as st
    
    # Auto-detect environment and connect
    try:
        # Streamlit in Snowflake (SiS) 환경
        from snowflake.snowpark.context import get_active_session
        session = get_active_session()
    except:
        # 로컬 또는 Community Cloud 환경
        from snowflake.snowpark import Session
        session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
    
    ```
    
    - `get_active_session()`: SiS 환경에서 현재 활성화된 세션을 가져옴
    - `Session.builder.configs(...)`: 로컬 환경에서 `secrets.toml` 정보를 이용해 세션을 새로 생성함

## 데이터 조회 및 결과 출력

- 연결된 세션을 통해 SQL 쿼리를 실행하고 결과를 받아옴
    
    ```python
    # Query Snowflake version
    version = session.sql("SELECT CURRENT_VERSION()").collect()[0][0]
    
    # Display results
    st.success(f"Successfully connected! Snowflake Version: {version}")
    
    ```
    
    - `session.sql(...)`: SQL 쿼리 작성 (Snowflake 버전 조회)
    - `.collect()`: 쿼리 실행 결과를 리스트 형태로 반환

# 3. 핵심 포인트 및 고려사항

## 환경 호환성 (Cross-Environment Compatibility)

- `try-except` 구문을 활용하여 **하나의 소스 코드**가 로컬 개발 환경과 실제 운영 환경(SiS) 모두에서 별도의 수정 없이 동작하도록 설계됨

## 보안 (Security)

- 아이디, 비밀번호와 같은 민감한 정보는 소스 코드에 직접 하드코딩하지 않고, 설정 파일(`secrets.toml`)이나 환경 변수로 분리하여 관리함
- 이는 클라우드 보안 모범 사례(Best Practice)를 따르는 것임

# 실행 결과

## 실행 코드

 Streamlit 실행 코드 =  python -m streamlit run 파일명.py

예시 : `python -m streamlit run day1.py`