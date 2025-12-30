import streamlit as st
import json
import random

# 1. 데이터 로드
@st.cache_data
def load_data():
    with open("data/questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# 세션 상태 초기화
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.wrong_answers = []
    st.session_state.show_answer = False

st.title("🛡️ AWS AI Practitioner (AIF-C01) 연습장")

# 문제 선택
q = data[st.session_state.current_index]

# 2. UI 토글 (한/영 전환)
lang_mode = st.toggle("🇰🇷 한국어 번역 보기", value=False)

# 3. 문제 화면 표시
st.subheader(f"Question {q['id']}")

if lang_mode:
    st.write(q['question_ko'])
else:
    st.write(q['question_en'])

# 4. 정답 확인 로직
if st.button("정답 확인"):
    st.session_state.show_answer = True

if st.session_state.show_answer:
    st.success(f"정답: {q['answer']}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⭕ 맞았어요"):
            st.session_state.current_index = (st.session_state.current_index + 1) % len(data)
            st.session_state.show_answer = False
            st.rerun()
    with col2:
        if st.button("❌ 틀렸어요 (오답노트 추가)"):
            st.session_state.wrong_answers.append(q)
            st.session_state.current_index = (st.session_state.current_index + 1) % len(data)
            st.session_state.show_answer = False
            st.rerun()

# 5. 오답 노트 관리
st.sidebar.title("📝 오답 노트")
st.sidebar.write(f"현재 오답 개수: {len(st.session_state.wrong_answers)}개")

if st.sidebar.button("오답 노트 초기화"):
    st.session_state.wrong_answers = []
    st.rerun()

# 6. 다음 단계: PDF 다운로드 (이후 구현 예정)
def generate_pdf(wrong_questions):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # 한글 폰트가 프로젝트 폴더에 있다고 가정 (예: NanumGothic.ttf)
    # 만약 파일이 없다면 이 부분은 에러가 날 수 있으니 파일명을 확인해주세요!
    try:
        pdf.add_font('Nanum', '', 'NanumGothic.ttf', unicode=True)
        pdf.set_font('Nanum', size=12)
    except:
        # 폰트 파일이 없을 경우 기본 Arial 사용 (한글 깨짐 발생 가능)
        pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="AWS AIF-C01 Wrong Answer Notes", ln=True, align='C')
    pdf.ln(10)

    for i, q in enumerate(wrong_questions):
        # 문제 번호 및 ID
        pdf.cell(0, 10, txt=f"Q{i+1}. (Original ID: {q['id']})", ln=True)
        
        # 영어 질문
        pdf.multi_cell(0, 10, txt=f"EN: {q['question_en']}")
        
        # 한국어 번역 (한글 폰트가 있어야 제대로 나옵니다)
        pdf.multi_cell(0, 10, txt=f"KO: {q['question_ko']}")
        
        # 정답
        pdf.cell(0, 10, txt=f"Correct Answer: {q['answer']}", ln=True)
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1', errors='ignore')