1일차의 목표는 Streamlit 앱과 Snowflake 데이터베이스 간의 연결을 설정하는 것입니다. 완료되면 간단한 쿼리를 실행하여 연결이 작동하는지 확인하고 앱에 Snowflake 버전을 표시합니다.

따라서 시작하려면 이 링크를 사용하여 [무료 Snowflake 체험 계정](https://signup.snowflake.com/?trial=student&cloud=aws&region=us-west-2&utm_source=streamlit-campaign&utm_campaign=30daysofai)에 등록하세요. 120일 동안 액세스할 수 있습니다. 체험판에는 30일 챌린지 전체를 진행하기에 충분한 크레딧이 포함되어 있으며, 다른 기능을 실험해 볼 수 있는 여유분도 있습니다.

> :orange[:material/lightbulb:] **참고:** **30 Days of AI** 챌린지의 핵심 학습 내용은 기술에 구애받지 않으므로 다른 플랫폼 및 LLM API 공급자와 함께 작동하도록 조정할 수 있습니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 연결 설정

1일차를 실행하기 전에 배포 위치에 따라 Snowflake 연결을 구성해야 합니다:

##### Streamlit in Snowflake (권장) :material/check_circle:

**설정이 필요 없습니다!** Snowsight에서 Streamlit 앱을 만들기만 하면 연결이 자동으로 작동합니다. 아래의 **1단계**로 건너뛰세요.

##### 로컬 개발 또는 Streamlit Community Cloud

**일회성 설정이 필요합니다.** 프로젝트 폴더에 `.streamlit/secrets.toml`을 생성하세요:

```toml
[connections.snowflake]
account = "xy12345.us-east-1"       # Snowsight → 계정 → 계정 세부 정보 보기에서 찾기
user = "yourusername"               # Snowflake 사용자 이름
password = "yourpassword"           # Snowflake 비밀번호
role = "ACCOUNTADMIN"               # 역할
warehouse = "COMPUTE_WH"            # 웨어하우스
database = "SNOWFLAKE_LEARNING_DB"  # 데이터베이스
schema = "PUBLIC"                   # 스키마
```

**중요:** `.streamlit/secrets.toml`을 `.gitignore` 파일에 추가하세요. 절대 시크릿을 Git에 커밋하지 마세요!

Streamlit Community Cloud의 경우 앱의 시크릿 설정에 동일한 값을 추가하세요.

#### 1. 라이브러리 가져오기

```python
import streamlit as st
```

* **`import streamlit as st`**: 웹 앱의 사용자 인터페이스(UI)를 구축하는 데 사용되는 Streamlit 라이브러리를 가져옵니다.

#### 2. Snowflake 연결

```python
# Auto-detect environment and connect
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
```

* **`from snowflake.snowpark.context import get_active_session`**: 현재 활성 Snowflake 세션을 가져오는 함수를 가져옵니다. 이는 Streamlit in Snowflake(SiS)에서 자동으로 작동합니다.
* **`session = get_active_session()`**: 인증된 Snowflake 세션을 설정합니다. 이 연결 객체는 `session` 변수에 저장됩니다.
* **`except` 블록**: `get_active_session()`이 실패하면(로컬 또는 Community Cloud에서 실행 중임을 의미) `.streamlit/secrets.toml` 파일의 시크릿을 사용하는 것으로 대체합니다.
* **`Session.builder.configs(...)`**: `st.secrets`의 연결 매개변수를 사용하여 Snowflake 세션을 생성합니다.

> :material/lightbulb: **try/except를 사용하는 이유는 무엇인가요?** 이 패턴을 사용하면 Streamlit in Snowflake(프로덕션), 로컬 개발, Streamlit Community Cloud의 세 가지 환경 모두에서 코드가 작동합니다. 하나의 코드베이스로 어디서나 작동합니다!

#### 3. Snowflake 버전 쿼리

```python
# Query and display Snowflake version
version = session.sql("SELECT CURRENT_VERSION()").collect()[0][0]
```

* **`session.sql(...)`**: `session` 객체를 사용하여 Snowflake 데이터베이스에서 원시 SQL 쿼리(`"SELECT CURRENT_VERSION()"`)를 실행합니다.
* **`.collect()[0][0]`**: 쿼리 결과를 가져옵니다. `.collect()`는 데이터(행 목록)를 스크립트로 가져옵니다. `[0]`은 첫 번째 행을 선택하고, 두 번째 `[0]`은 해당 행의 첫 번째 열(버전 번호 문자열 포함)을 선택합니다.

#### 4. 결과 표시

```python
st.success(f"Successfully connected! Snowflake Version: {version}")
```

* **`st.success(...)`**: f-문자열을 사용하여 포함된 Snowflake 버전 번호와 함께 녹색 성공 메시지를 표시합니다. 이는 연결이 작동함을 확인하고 단일 메시지로 버전을 표시합니다.

이 코드가 실행되면 Snowflake 버전을 표시하는 녹색 성공 메시지가 표시됩니다. 이는 연결이 올바르게 작동함을 확인합니다.

> :material/lightbulb: **실패하면 어떻게 하나요?** Streamlit in Snowflake에서 연결이 실패하면 앱을 새로 고치거나 역할 권한을 확인해 보세요. 로컬 개발의 경우 프로젝트 루트에 7개의 필수 매개변수(계정, 사용자, 비밀번호, 역할, 웨어하우스, 데이터베이스, 스키마)가 모두 포함된 `.streamlit/secrets.toml` 파일이 있는지 확인하세요.

---

### :material/library_books: 리소스
- [Streamlit in Snowflake 문서](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Streamlit 시크릿 관리](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [Snowpark Python API](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
- [Streamlit 시작하기](https://docs.streamlit.io/get-started)
