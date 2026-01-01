import streamlit as st
import json
import re
import random
from datetime import datetime

# 1. 데이터 로드
@st.cache_data
def load_data():
    with open("data/questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

def parse_choices(question_text):
    """질문 텍스트에서 선택지(A, B, C, D, E)를 파싱하여 분리"""
    if not question_text:
        return question_text, {}
    
    text = question_text.replace('\u0000', '').strip()
    
    if text.upper().startswith('HOTSPOT'):
        return text, {}
    
    pattern = r'[•·]\s*([A-E])\.\s+'
    matches = list(re.finditer(pattern, text))
    
    if len(matches) < 2:
        return text, {}
    
    choices = {}
    question_end_pos = matches[0].start() if matches else len(text)
    
    for i, match in enumerate(matches):
        letter = match.group(1)
        start_pos = match.end()
        
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        
        choice_text = text[start_pos:end_pos].strip()
        choice_text = re.sub(r'[•·\s]+$', '', choice_text)
        
        if choice_text:
            choices[letter] = choice_text
    
    question_body = text[:question_end_pos].strip()
    question_body = re.sub(r'\s+', ' ', question_body)
    
    return question_body, choices

def translate_choice_to_korean(choice_en, question_context=""):
    """영어 선택지를 한글로 번역 (간단한 규칙 기반, AWS 제품명은 영문 유지)"""
    # AWS 제품명 리스트 (영문 유지)
    aws_products = [
        'Amazon', 'SageMaker', 'Bedrock', 'Rekognition', 'Comprehend', 'Polly', 'Lex',
        'QuickSight', 'Ground Truth', 'Kendra', 'Textract', 'Transcribe', 'Translate',
        'Forecast', 'Personalize', 'Fraud Detector', 'CodeGuru', 'DevOps Guru',
        'Lookout', 'Monitron', 'Panorama', 'DeepLens', 'DeepRacer', 'DeepComposer',
        'S3', 'EC2', 'Lambda', 'CloudFormation', 'CloudWatch', 'IAM', 'VPC'
    ]
    
    # 간단한 번역 규칙 (실제로는 더 복잡한 번역이 필요하지만 기본 구조 제공)
    # 실제 구현 시 Google Translate API나 다른 번역 서비스 사용 권장
    choice_lower = choice_en.lower()
    
    # AWS 제품명은 영문으로 유지하면서 번역
    translated = choice_en
    
    # 간단한 키워드 번역 예시 (실제로는 완전한 번역 필요)
    # 여기서는 기본 구조만 제공하고, 실제로는 번역 API 사용 또는 사전 기반 번역 필요
    
    return translated  # 일단 원문 반환 (추후 번역 로직 추가 필요)

def get_choices_for_language(question_en, question_ko, lang_mode, use_random_mix=False, q_data=None):
    """언어 모드에 따라 질문 본문과 선택지를 반환"""
    # 영어 질문에서 선택지 파싱
    en_body, en_choices = parse_choices(question_en)
    
    # 한글 질문에서 선택지 파싱 (대부분 한글 질문에는 선택지가 없음)
    ko_body, ko_choices = parse_choices(question_ko)
    
    # choices_ko 필드에서 한글 선택지 가져오기
    ko_choices_from_data = q_data.get('choices_ko', {}) if q_data else {}
    
    if lang_mode == "한글":
        # 한글 질문 본문 사용
        body = ko_body if ko_body else en_body
        # 한글 선택지 우선 사용 (choices_ko 필드 또는 파싱된 한글 선택지)
        choices = ko_choices_from_data if ko_choices_from_data else (ko_choices if ko_choices else en_choices)
        return body, choices
    elif lang_mode == "영어":
        # 영어로만 표시
        return en_body, en_choices
    else:  # "섞기"
        # 랜덤으로 언어 선택
        use_korean = random.choice([True, False]) if use_random_mix else False
        if use_korean and ko_body:
            body = ko_body
            choices = ko_choices_from_data if ko_choices_from_data else (ko_choices if ko_choices else en_choices)
        else:
            body = en_body
            choices = en_choices
        return body, choices

def is_multiple_choice(question_text):
    """질문이 복수 선택인지 확인"""
    return bool(re.search(r'\(Choose\s+two\)|\(2개\s*선택\)|\(Choose\s+three\)|\(3개\s*선택\)', question_text, re.IGNORECASE))

def extract_correct_answers(answer_text):
    """정답 텍스트에서 정답 문자들 추출 (복수 선택 지원)"""
    if not answer_text:
        return None
    matches = re.findall(r'\b([A-E])\b', answer_text)
    return matches if matches else None

# PDF 생성 함수 (위로 이동)
def generate_pdf(wrong_questions):
    """오답 노트를 PDF로 생성 (문제, 답, 해설 포함)"""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        return None
    
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # 페이지 너비 (기본값: 210mm에서 마진 제외)
        page_width = pdf.w - 2 * pdf.l_margin
        
        # 기본 폰트 사용 (Helvetica - fpdf2의 기본 폰트)
        pdf.set_font("helvetica", size=12)
        
        # 제목
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(page_width, 10, text="AWS AIF-C01 Wrong Answer Notes", align='C')
        pdf.ln(5)
        
        # 날짜
        date_str = datetime.now().strftime("%Y-%m-%d")
        pdf.set_font("helvetica", size=10)
        pdf.cell(page_width, 8, text=f"Date: {date_str}", align='R')
        pdf.ln(10)

        # 텍스트를 ASCII로 변환하는 헬퍼 함수
        def to_ascii_safe(text, max_len=500):
            """텍스트를 ASCII로 변환 (유니코드 문자는 ?로 대체)"""
            if not text:
                return ""
            # 특수 문자 제거 및 ASCII 변환
            safe = ''.join(c if ord(c) < 128 and c.isprintable() else '?' for c in str(text)[:max_len])
            # 불필요한 특수 문자 제거
            safe = safe.replace('•', '-').replace('·', '-').replace('…', '...')
            return safe
        
        # 각 문제 작성
        for i, q in enumerate(wrong_questions):
            # 문제 번호
            pdf.set_font("helvetica", 'B', 14)
            pdf.cell(page_width, 10, text=f"Question {i+1} (Original ID: {q['id']})", ln=True)
            pdf.ln(5)
            
            # 문제 본문
            question_ko = q.get('question_ko', '').replace('\u0000', '').strip()
            question_en = q.get('question_en', '').replace('\u0000', '').strip()
            
            pdf.set_font("helvetica", 'B', 11)
            pdf.cell(page_width, 8, text="[Question - Korean]", ln=True)
            pdf.set_font("helvetica", size=10)
            safe_text = to_ascii_safe(question_ko, 200)
            if safe_text:
                pdf.multi_cell(page_width, 6, text=safe_text)
            
            pdf.ln(3)
            pdf.set_font("helvetica", 'B', 11)
            pdf.cell(page_width, 8, text="[Question - English]", ln=True)
            pdf.set_font("helvetica", size=10)
            safe_en = to_ascii_safe(question_en, 500)
            if safe_en:
                pdf.multi_cell(page_width, 6, text=safe_en)
            pdf.ln(5)
            
            # 선택지
            choices_ko = q.get('choices_ko', {})
            en_body, en_choices = parse_choices(question_en)
            
            if choices_ko or en_choices:
                pdf.set_font("helvetica", 'B', 11)
                pdf.cell(page_width, 8, text="[Choices]", ln=True)
                pdf.set_font("helvetica", size=10)
                
                choices_to_show = choices_ko if choices_ko else en_choices
                for letter in sorted(choices_to_show.keys()):
                    choice_text = str(choices_to_show[letter])
                    safe_choice = to_ascii_safe(choice_text, 100)
                    if safe_choice:
                        pdf.multi_cell(page_width, 5, text=f"{letter}. {safe_choice}")
                pdf.ln(5)
            
            # 정답 및 해설
            answer = q.get('answer', '')
            pdf.set_font("helvetica", 'B', 11)
            pdf.cell(page_width, 8, text="[Answer and Explanation]", ln=True)
            pdf.set_font("helvetica", size=10)
            safe_answer = to_ascii_safe(answer, 500)
            if safe_answer:
                pdf.multi_cell(page_width, 6, text=safe_answer)
            pdf.ln(10)
            
            # 구분선 (페이지 너비 기준)
            line_start_x = pdf.l_margin
            line_end_x = pdf.w - pdf.r_margin
            pdf.line(line_start_x, pdf.get_y(), line_end_x, pdf.get_y())
            pdf.ln(10)
        
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except Exception as e:
        # 에러 발생 시 None 반환 (디버깅용: 에러 메시지 출력 가능)
        import sys
        print(f"PDF 생성 오류: {type(e).__name__}: {e}", file=sys.stderr)
        return None

data = load_data()

# 세션 상태 초기화
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.wrong_answers = []
    st.session_state.show_answer = False
    st.session_state.selected_answer = None
    st.session_state.selected_answers = []
    st.session_state.last_index = -1
    st.session_state.exam_mode = False
    st.session_state.exam_questions = []
    st.session_state.exam_answers = {}
    st.session_state.exam_current_index = 0
    st.session_state.exam_finished = False
    st.session_state.lang_mode = "한글"  # "한글", "영어", "섞기"

# 시험 모드 확인
if st.session_state.exam_mode and st.session_state.exam_questions:
    exam_data = st.session_state.exam_questions
    exam_idx = st.session_state.exam_current_index
    q = exam_data[exam_idx] if exam_idx < len(exam_data) else data[0]
    total_exam = len(exam_data)
else:
    exam_data = None
    exam_idx = None
    q = data[st.session_state.current_index]
    total_exam = None

# 문제 인덱스가 변경되면 선택한 답 초기화
current_idx = st.session_state.exam_current_index if st.session_state.exam_mode else st.session_state.current_index
if current_idx != st.session_state.last_index:
    st.session_state.selected_answer = None
    st.session_state.selected_answers = []
    st.session_state.show_answer = False
    st.session_state.last_index = current_idx

# CSS 스타일링
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    
    .question-text {
        font-size: 1.3rem !important;
        line-height: 1.8 !important;
        margin-bottom: 2rem !important;
        color: #FAFAFA !important;
        font-weight: 400 !important;
    }
    
    .stRadio > div > label {
        font-size: 1.15rem !important;
        line-height: 2.2 !important;
        padding: 0.8rem 0 !important;
        color: #FAFAFA !important;
    }
    
    .stCheckbox > label {
        font-size: 1.15rem !important;
        line-height: 2 !important;
        padding: 0.6rem 0 !important;
        color: #FAFAFA !important;
    }
    
    .stButton > button {
        font-size: 1.1rem;
        padding: 0.6rem 2rem;
        font-weight: 500;
    }
    
    h1 {
        font-size: 2.5rem !important;
    }
    
    h2 {
        font-size: 1.8rem !important;
    }
    
    h3 {
        font-size: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ AWS AI Practitioner (AIF-C01) 연습장")

# 사이드바: 시험 모드 설정
st.sidebar.title("⚙️ 설정")

# 언어 모드 선택
lang_mode = st.sidebar.radio(
    "🌐 언어 모드",
    options=["한글", "English", "섞기"],
    index=["한글", "English", "섞기"].index(st.session_state.lang_mode) if st.session_state.lang_mode in ["한글", "English", "섞기"] else 0,
    help="한글: 모든 문제를 한글로 표시\n영어: 모든 문제를 영어로 표시\n섞기: 한글과 영어를 랜덤으로 섞어 표시"
)
st.session_state.lang_mode = lang_mode

# 시험 모드 시작 버튼
if not st.session_state.exam_mode:
    if st.sidebar.button("📝 시험 모드 시작 (65문제)", use_container_width=True, type="primary"):
        # 랜덤으로 65문제 선택 (실제 시험 형식)
        num_questions = min(65, len(data))
        st.session_state.exam_questions = random.sample(data, num_questions)
        st.session_state.exam_current_index = 0
        st.session_state.exam_answers = {}
        st.session_state.exam_finished = False
        st.session_state.exam_mode = True
        st.session_state.show_answer = False
        st.session_state.selected_answer = None
        st.session_state.selected_answers = []
        st.rerun()

# 시험 모드일 때
if st.session_state.exam_mode:
    st.sidebar.markdown("---")
    st.sidebar.warning(f"**시험 모드 진행 중**\n\n문제: {st.session_state.exam_current_index + 1} / {len(st.session_state.exam_questions)}")
    
    if st.sidebar.button("⏹️ 시험 모드 종료", use_container_width=True):
        st.session_state.exam_mode = False
        st.session_state.exam_finished = True
        st.rerun()
    
    q = st.session_state.exam_questions[st.session_state.exam_current_index]
    total_exam = len(st.session_state.exam_questions)
else:
    total_exam = None

st.markdown(f"### Question {q['id']}")

# 질문 텍스트 선택 (언어 모드에 따라)
question_en = q.get('question_en', '')
question_ko = q.get('question_ko', '')

# 언어 모드에 따라 질문 본문과 선택지 가져오기
# 섞기 모드에서는 문제 ID 기반으로 고정 (같은 문제는 항상 같은 언어)
question_body, choices = get_choices_for_language(question_en, question_ko, lang_mode, (lang_mode == "섞기"), q)

# 선택지가 없으면 영어에서 다시 파싱 시도
if not choices:
    _, choices = parse_choices(question_en)

is_multiple = is_multiple_choice(question_en) or is_multiple_choice(question_ko)

# 질문 본문 표시
st.markdown(f'<div class="question-text">{question_body}</div>', unsafe_allow_html=True)

# 선택지 표시
if choices and len(choices) > 0:
    st.markdown("---")
    st.markdown("### 📋 답변 선택")
    
    sorted_keys = sorted(choices.keys())
    
    if is_multiple:
        selected_list = st.multiselect(
            "답변을 선택하세요 (여러 개 선택 가능):",
            options=sorted_keys,
            default=st.session_state.selected_answers if st.session_state.selected_answers else [],
            format_func=lambda x: f"**{x}.** {choices[x]}",
            key=f"multiselect_{current_idx}_{st.session_state.exam_mode}"
        )
        st.session_state.selected_answers = selected_list
        st.session_state.selected_answer = None
    else:
        # 시험 모드에서는 정답을 보여주지 않음
        default_idx = None
        if st.session_state.exam_mode and str(current_idx) in st.session_state.exam_answers:
            saved_answer = st.session_state.exam_answers[str(current_idx)]
            if saved_answer in sorted_keys:
                default_idx = sorted_keys.index(saved_answer)
        
        selected = st.radio(
            "답변을 선택하세요:",
            options=sorted_keys,
            format_func=lambda x: f"**{x}.** {choices[x]}",
            index=default_idx,
            key=f"radio_{current_idx}_{st.session_state.exam_mode}"
        )
        st.session_state.selected_answer = selected
        st.session_state.selected_answers = []
        
        # 시험 모드에서는 선택한 답 저장
        if st.session_state.exam_mode and selected:
            st.session_state.exam_answers[str(current_idx)] = selected
else:
    st.info("⚠️ 이 문제는 선택지가 없거나 특수 형식입니다 (예: HOTSPOT 문제)")
    st.markdown(f'<div class="question-text">{question_body}</div>', unsafe_allow_html=True)
    st.session_state.selected_answer = None
    st.session_state.selected_answers = []

# 시험 모드가 아닐 때만 정답 확인 버튼 표시
if not st.session_state.exam_mode:
    st.markdown("---")
    check_disabled = (len(st.session_state.selected_answers) == 0 if is_multiple else st.session_state.selected_answer is None)
    
    if st.button("✅ 정답 확인", disabled=check_disabled, type="primary", use_container_width=True):
        st.session_state.show_answer = True

# 정답 표시 (시험 모드가 아닐 때만)
if not st.session_state.exam_mode and st.session_state.show_answer:
    st.markdown("---")
    answer_text = q.get('answer', '')
    correct_answers = extract_correct_answers(answer_text)
    
    if is_multiple:
        user_selected = sorted(st.session_state.selected_answers)
        correct_sorted = sorted(correct_answers) if correct_answers else []
        is_correct = user_selected == correct_sorted
    else:
        correct_letter = correct_answers[0] if correct_answers else None
        is_correct = st.session_state.selected_answer == correct_letter
    
    if is_correct:
        st.success(f"✅ **정답입니다!**\n\n{q['answer']}")
    else:
        st.error(f"❌ **틀렸습니다.**\n\n**정답:** {q['answer']}")
        if is_multiple:
            if st.session_state.selected_answers:
                st.warning(f"**선택하신 답:** {', '.join(st.session_state.selected_answers)}")
        else:
            if st.session_state.selected_answer:
                st.warning(f"**선택하신 답:** {st.session_state.selected_answer}")
        
        if q not in st.session_state.wrong_answers:
            st.session_state.wrong_answers.append(q)
            st.info("💡 오답 노트에 자동으로 추가되었습니다.")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⭕ 다음 문제", use_container_width=True, type="primary"):
            if st.session_state.exam_mode:
                st.session_state.exam_current_index = (st.session_state.exam_current_index + 1) % len(st.session_state.exam_questions)
            else:
                st.session_state.current_index = (st.session_state.current_index + 1) % len(data)
            st.session_state.show_answer = False
            st.session_state.selected_answer = None
            st.session_state.selected_answers = []
            st.rerun()
    with col2:
        if st.button("🔄 다시 풀기", use_container_width=True):
            st.session_state.show_answer = False
            st.session_state.selected_answer = None
            st.session_state.selected_answers = []
            st.rerun()

# 시험 모드 네비게이션
if st.session_state.exam_mode and not st.session_state.exam_finished:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("◀ 이전 문제", use_container_width=True, disabled=(st.session_state.exam_current_index == 0)):
            if st.session_state.exam_current_index > 0:
                st.session_state.exam_current_index -= 1
                st.session_state.show_answer = False
                saved_answer = st.session_state.exam_answers.get(str(st.session_state.exam_current_index))
                st.session_state.selected_answer = saved_answer
                st.session_state.selected_answers = []
                st.rerun()
    with col2:
        if st.button("다음 문제 ▶", use_container_width=True, disabled=(st.session_state.exam_current_index >= len(st.session_state.exam_questions) - 1)):
            if st.session_state.exam_current_index < len(st.session_state.exam_questions) - 1:
                st.session_state.exam_current_index += 1
                st.session_state.show_answer = False
                saved_answer = st.session_state.exam_answers.get(str(st.session_state.exam_current_index))
                st.session_state.selected_answer = saved_answer
                st.session_state.selected_answers = []
                st.rerun()
    with col3:
        if st.button("✅ 시험 완료", use_container_width=True, type="primary"):
            st.session_state.exam_finished = True
            st.rerun()

# 시험 결과 표시
if st.session_state.exam_finished and st.session_state.exam_mode:
    st.markdown("---")
    st.markdown("## 🎯 시험 결과")
    
    # 정답 채점
    correct_count = 0
    total_count = len(st.session_state.exam_questions)
    
    for idx, exam_q in enumerate(st.session_state.exam_questions):
        user_answer = st.session_state.exam_answers.get(str(idx))
        if user_answer:
            correct_answers = extract_correct_answers(exam_q.get('answer', ''))
            if correct_answers and user_answer == correct_answers[0]:
                correct_count += 1
    
    score_percent = (correct_count / total_count * 100) if total_count > 0 else 0
    passing_score = 70.0
    passed = score_percent >= passing_score
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("정답 수", f"{correct_count} / {total_count}")
    with col2:
        st.metric("점수", f"{score_percent:.1f}%")
    with col3:
        st.metric("합격 기준", f"{passing_score}%")
    
    if passed:
        st.success(f"🎉 **합격입니다!** ({score_percent:.1f}%)")
    else:
        st.error(f"❌ **불합격입니다.** ({score_percent:.1f}% / 합격 기준: {passing_score}%)")
    
    if st.button("🔁 새 시험 시작", use_container_width=True, type="primary"):
        st.session_state.exam_mode = False
        st.session_state.exam_finished = False
        st.session_state.exam_questions = []
        st.session_state.exam_answers = {}
        st.session_state.exam_current_index = 0
        st.rerun()

# 오답 노트 관리
st.sidebar.markdown("---")
st.sidebar.title("📝 오답 노트")
st.sidebar.metric("현재 오답 개수", f"{len(st.session_state.wrong_answers)}개")

# PDF 다운로드 버튼
if len(st.session_state.wrong_answers) > 0:
    try:
        pdf_data = generate_pdf(st.session_state.wrong_answers)
        if pdf_data:
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{date_str}_오답.pdf"
            st.sidebar.download_button(
                label="📥 PDF 다운로드",
                data=pdf_data,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.sidebar.info("💡 PDF 생성 라이브러리(fpdf2)가 필요합니다.\n`pip install fpdf2` 실행해주세요.")
    except Exception as e:
        st.sidebar.error(f"PDF 생성 오류: {str(e)}")

if st.sidebar.button("🗑️ 오답 노트 초기화", use_container_width=True):
    st.session_state.wrong_answers = []
    st.rerun()

# 일반 모드 네비게이션
if not st.session_state.exam_mode:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 문제 이동")
    prev_col, next_col = st.sidebar.columns(2)
    with prev_col:
        if st.sidebar.button("◀ 이전", use_container_width=True):
            st.session_state.current_index = (st.session_state.current_index - 1) % len(data)
            st.session_state.show_answer = False
            st.session_state.selected_answer = None
            st.session_state.selected_answers = []
            st.rerun()
    with next_col:
        if st.sidebar.button("다음 ▶", use_container_width=True):
            st.session_state.current_index = (st.session_state.current_index + 1) % len(data)
            st.session_state.show_answer = False
            st.session_state.selected_answer = None
            st.session_state.selected_answers = []
            st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"**현재 문제:** {st.session_state.current_index + 1} / {len(data)}")
