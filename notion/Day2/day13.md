# Day 13: Adding a System Prompt

# 0. 목표

<aside>
💡 **"시스템 프롬프트(System Prompt)"를 사용하여 챗봇에게 성격(Persona) 부여하기**

1. LLM의 최상위 지침인 시스템 프롬프트의 역할을 이해합니다.
2. 사용자가 버튼을 클릭하면 챗봇의 성격(해적, 선생님 등)이 바뀌도록 만듭니다.
3. 바뀐 성격이 대화 내내 유지되도록 상태 관리와 프롬프트 주입을 구현합니다.

</aside>

# 1. 개념 및 이론 (Theory)

### 시스템 프롬프트 (System Prompt)
LLM에게 "너는 지금부터 ~한 역할을 맡아"라고 최면을 거는 것과 같습니다. 이 지시사항은 사용자에게는 보이지 않지만, LLM이 답을 생성할 때 가장 강력한 기준이 됩니다.

### 프롬프트 주입 (Injection)
우리가 만드는 `full_prompt` 문자열의 **가장 윗부분**에 시스템 프롬프트를 넣어서 LLM에게 보냅니다. LLM은 글을 읽을 때 앞부분의 지시를 '대전제'로 받아들이기 때문입니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 페르소나 저장소 만들기

`day13.py`에서 초기 상태를 설정합니다.

```python
# 기본 성격은 평범한 AI 비서로 설정
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful AI assistant."
```

### Step 2: 성격 변경 버튼 (Presets)

사이드바에 버튼을 만들어, 클릭 시 `system_prompt` 값을 바꾸고 앱을 새로고침합니다.

```python
with st.sidebar:
    st.header("🎭 Choose Persona")
    
    # 1. 해적
    if st.button("🏴‍☠️ Pirate Captain"):
        st.session_state.system_prompt = """
        You are Captain Blackbeard, a notorious pirate. 
        Speak in pirate slang (Arr, Matey!). be rude but helpful.
        """
        st.rerun()
        
    # 2. 유치원 선생님
    if st.button("🧸 Kindergarten Teacher"):
        st.session_state.system_prompt = """
        You are a kind kindergarten teacher. 
        Explain everything simply and use emojis. Call the user 'little star'.
        """
        st.rerun()
```

### Step 3: 프롬프트 조립

LLM에게 보낼 전체 문자열을 만들 때, `system_prompt`를 **맨 앞에** 붙입니다.

```python
# [시스템 프롬프트] + [대화 기록]
full_prompt = f"""
[System Instruction]
{st.session_state.system_prompt}

[Conversation History]
{conversation_history}

Assistant:
"""

response = call_cortex_llm(full_prompt)
```

# 3. 핵심 포인트 (Key Takeaways)

- **Interaction Design**: 사용자가 텍스트로 "너는 이제부터 해적이야"라고 치게 할 수도 있지만, **버튼(Preset)** 을 제공하는 것이 훨씬 편리한 UX입니다.
- **Top Priority**: 시스템 프롬프트는 LLM이 혼란스러워할 때(예: 사용자가 "해적 그만해"라고 할 때) 기준점이 되어주므로 항상 프롬프트 최상단에 배치해야 합니다.

---

# 💡 실습 과제 (Hands-on Practice)

챗봇에게 특정한 성격을 부여하는 시스템 프롬프트 주입 로직을 완성해 봅니다.

1. `st.session_state`에 `system_prompt`라는 키가 없으면 기본값("You are a helpful assistant.")을 넣어주세요.
2. 최종 프롬프트를 만들 때, 맨 앞에 `st.session_state.system_prompt` 내용을 포함시키세요.

# ✅ 정답 코드 (Solution)

```python
# 시스템 프롬프트 주입 실습
# 1. 초기화
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful assistant."

# ... (중략) ...

# 2. 프롬프트 구성 시 가장 상단에 배치
full_prompt = f"""
System Instruction: {st.session_state.system_prompt}

Context: {conversation_history}
User: {prompt}
Assistant:
"""
```
