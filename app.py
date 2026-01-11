import streamlit as st
import json
import re
import random
import os
from datetime import datetime

# 1. 데이터 로드
@st.cache_data
def load_data():
    with open("data/questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

def clean_question_text(text):
    """문제 텍스트에서 끝의 숫자 및 불필요한 문자 제거"""
    if not text:
        return text
    # 끝의 숫자 제거 (공백 포함)
    text = re.sub(r'[\s•·]*\d+[\s•·]*$', '', text)
    return text.strip()

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
    # 끝의 숫자 제거
    question_body = clean_question_text(question_body)
    
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
        # ko_choices_from_data가 비어있지 않은 경우에만 사용
        if ko_choices_from_data and len(ko_choices_from_data) > 0:
            choices = ko_choices_from_data
        elif ko_choices and len(ko_choices) > 0:
            choices = ko_choices
        else:
            # 한글 선택지가 없으면 영어 선택지를 사용 (임시)
            choices = en_choices
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
    """오답 노트를 PDF로 생성 (문제, 답, 해설 포함) - reportlab 사용"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
        from io import BytesIO
        import os
    except ImportError:
        return None
    
    try:
        # 메모리 버퍼에 PDF 생성
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               rightMargin=20*mm, leftMargin=20*mm,
                               topMargin=20*mm, bottomMargin=20*mm)
        
        # 스타일 설정
        styles = getSampleStyleSheet()
        
        # 한글 폰트 등록 (macOS의 경우)
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", # 리눅스 서버용 나눔폰트 예시
            "NanumGothic.ttf", # 현재 폴더에 폰트를 넣었을 경우
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf", # 기존 맥용
        ]
        
        korean_font_name = "AppleGothic"
        korean_font_bold_name = "AppleGothic-Bold"
        korean_font_registered = False
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("AppleGothic", font_path))
                    # Bold 폰트도 같은 파일로 등록 (대부분의 TTF는 regular와 bold가 같은 파일에 있음)
                    pdfmetrics.registerFont(TTFont("AppleGothic-Bold", font_path))
                    korean_font_registered = True
                    break
                except:
                    continue
        
        # 한글 폰트를 사용할 수 없으면 기본 폰트 사용 (한글이 깨질 수 있음)
        if not korean_font_registered:
            korean_font_name = "Helvetica"
            korean_font_bold_name = "Helvetica-Bold"
        
        # 커스텀 스타일 정의
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=korean_font_name,
            fontSize=18,
            textColor='black',
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        
        date_style = ParagraphStyle(
            'CustomDate',
            parent=styles['Normal'],
            fontName=korean_font_name,
            fontSize=10,
            alignment=TA_RIGHT,
            spaceAfter=15,
        )
        
        question_title_style = ParagraphStyle(
            'QuestionTitle',
            parent=styles['Heading2'],
            fontName=korean_font_name,
            fontSize=11,  # 9pt 기준으로 2pt 크게 (bold 효과)
            textColor='black',
            spaceAfter=6,
            spaceBefore=8,
        )
        
        question_text_style = ParagraphStyle(
            'QuestionText',
            parent=styles['Normal'],
            fontName=korean_font_name,
            fontSize=9,
            alignment=TA_LEFT,
            spaceAfter=6,
            leading=12,
        )
        
        choice_style = ParagraphStyle(
            'Choice',
            parent=styles['Normal'],
            fontName=korean_font_name,
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=4,
            leftIndent=8,
            leading=11,
        )
        
        answer_title_style = ParagraphStyle(
            'AnswerTitle',
            parent=styles['Heading3'],
            fontName=korean_font_name,
            fontSize=10,  # 9pt 기준으로 1pt 크게 (bold 효과)
            textColor='black',
            spaceAfter=4,
            spaceBefore=6,
        )
        
        answer_text_style = ParagraphStyle(
            'AnswerText',
            parent=styles['Normal'],
            fontName=korean_font_name,
            fontSize=8,
            alignment=TA_LEFT,
            spaceAfter=10,
            leading=11,
        )
        
        # Bold 스타일 (가독성을 위해 fontSize를 약간 크게)
        bold_style = ParagraphStyle(
            'Bold',
            parent=styles['Normal'],
            fontName=korean_font_name,
            fontSize=12,  # 일반보다 1pt 크게
            alignment=TA_LEFT,
        )
        
        question_bold_style = ParagraphStyle(
            'QuestionBold',
            parent=styles['Normal'],
            fontName=korean_font_name,
            fontSize=11,  # 9pt 기준으로 1pt 크게 (bold 효과)
            alignment=TA_LEFT,
            spaceAfter=6,
            leading=13,
        )
        
        answer_bold_style = ParagraphStyle(
            'AnswerBold',
            parent=styles['Normal'],
            fontName=korean_font_name,
            fontSize=10,  # 8pt 기준으로 1pt 크게 (bold 효과)
            alignment=TA_LEFT,
            spaceAfter=10,
            leading=12,
        )
        
        # 스토리 (PDF 콘텐츠) 구성
        story = []
        
        # 제목
        date_str = datetime.now().strftime("%Y-%m-%d")
        story.append(Paragraph("AWS AIF-C01 오답 노트", title_style))
        story.append(Paragraph(f"날짜: {date_str}", date_style))
        story.append(Spacer(1, 8))
        
        # 각 문제 작성
        for i, q in enumerate(wrong_questions):
            # 문제 번호 (Bold - fontSize를 크게)
            question_title = f"문제 {i+1} (원본 ID: {q['id']})"
            story.append(Paragraph(question_title, question_title_style))
            
            # 문제 본문 (한글, Bold - fontSize를 크게)
            question_ko = q.get('question_ko', '').replace('\u0000', '').strip()
            if question_ko:
                # 끝의 숫자 제거
                question_ko = clean_question_text(question_ko)
                # HTML 엔티티 및 특수 문자 처리
                question_ko_clean = question_ko.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(question_ko_clean, question_bold_style))
            
            story.append(Spacer(1, 4))
            
            # 선택지 (한글)
            choices_ko = q.get('choices_ko', {})
            en_body, en_choices = parse_choices(q.get('question_en', ''))
            
            if choices_ko or en_choices:
                choices_to_show = choices_ko if choices_ko else en_choices
                for letter in sorted(choices_to_show.keys()):
                    choice_text = str(choices_to_show[letter])
                    # HTML 엔티티 처리
                    choice_text_clean = choice_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(f"<b>{letter}.</b> {choice_text_clean}", choice_style))
                story.append(Spacer(1, 4))
            
            # HOTSPOT 문제 처리
            question_en = q.get('question_en', '').replace('\u0000', '').strip()
            is_hotspot = 'HOTSPOT' in question_en.upper() or 'HOTSPOT' in question_ko.upper()
            if is_hotspot:
                story.append(Paragraph("<i>※ 이 문제는 HOTSPOT 문제입니다. 원본 PDF의 이미지/다이어그램을 참조하세요.</i>", 
                                      ParagraphStyle('HotspotNote', parent=styles['Normal'], 
                                                    fontName=korean_font_name, fontSize=9, 
                                                    textColor='gray', spaceAfter=8)))
            
            # 정답 및 해설
            answer = q.get('answer', '').replace('\u0000', '').strip()
            if answer:
                # 기본 해설 텍스트 제거
                default_explanation = "이 답변이 정답인 이유를 설명하는 상세한 해설입니다."
                if default_explanation in answer:
                    # 기본 해설 텍스트가 포함된 경우 제거 (괄호 포함)
                    answer = answer.replace(f" ({default_explanation})", "").replace(f"({default_explanation})", "").strip()
                
                story.append(Paragraph("정답 및 해설", answer_title_style))
                # HTML 엔티티 처리
                answer_clean = answer.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(answer_clean, answer_bold_style))
            
            # 문제 간 구분선
            if i < len(wrong_questions) - 1:
                story.append(Spacer(1, 6))
                story.append(Paragraph("<hr/>", styles['Normal']))
                story.append(Spacer(1, 6))
        
        # PDF 생성
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        # 에러 발생 시 None 반환
        import sys
        print(f"PDF 생성 오류: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
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
    st.session_state.lang_mode = "한글"  # "한글", "English"
    st.session_state.show_english_toggle = {}  # 문제별 영어/한글 토글 상태

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
        max-width: 2000px;
    }
    
    .question-text {
        font-size: 1.3rem !important;
        line-height: 2.2 !important;
        margin-bottom: 2rem !important;
        color: #FAFAFA !important;
        font-weight: 400 !important;
        word-spacing: 0.1em !important;
        letter-spacing: 0.02em !important;
    }
    
    /* 라디오 버튼 선택지 텍스트 크기 */
    .stRadio > div > label,
    .stRadio label,
    div[data-testid*="stRadio"] label,
    div[data-testid*="stRadio"] > div > label,
    .stRadio > div > div > label {
        font-size: 1.3rem !important;
        line-height: 2.2rem !important;
        padding: 0.6rem 0 !important;
        color: #FAFAFA !important;
    }
    
    /* 라디오 버튼 내부 텍스트 요소 - 문제 텍스트와 동일한 크기 */
    .stRadio label span,
    .stRadio label p,
    .stRadio label div,
    .stRadio label strong,
    div[data-testid*="stRadio"] label span,
    div[data-testid*="stRadio"] label p,
    div[data-testid*="stRadio"] label div,
    div[data-testid*="stRadio"] label strong {
        font-size: 1.3rem !important;
        line-height: 2.2rem !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
        color: #FAFAFA !important;
    }
    
    /* 체크박스 선택지 */
    .stCheckbox > label,
    .stCheckbox label,
    div[data-testid*="stCheckbox"] label {
        font-size: 1.3rem !important;
        line-height: 2.2rem !important;
        padding: 0.5rem 0 !important;
        color: #FAFAFA !important;
        white-space: nowrap !important;
        min-width: fit-content !important;
    }
    
    /* 멀티셀렉트도 포함 */
    .stMultiSelect label,
    div[data-testid*="stMultiSelect"] label {
        font-size: 1.3rem !important;
        line-height: 2.2rem !important;
        color: #FAFAFA !important;
    }
    
    /* EN 체크박스 줄바꿈 방지 */
    div[data-testid*="stCheckbox"] label {
        white-space: nowrap !important;
        word-break: keep-all !important;
    }
    
    .stButton > button {
        font-size: 1.1rem !important;
        padding: 0.6rem 2rem !important;
        font-weight: 500 !important;
    }
    
    h1 {
        font-size: 2.5rem !important;
    }
    
    h2 {
        font-size: 2.0rem !important;
    }
    
    h3 {
        font-size: 2.0rem !important;
    }
    
    /* 선택지 라디오/체크박스 텍스트 크기 */
    .stRadio label, .stCheckbox label, div[data-testid*="stRadio"] label p, div[data-testid*="stCheckbox"] label p {
        font-size: 1.3rem !important;
        line-height: 2.2rem !important;
        color: #FAFAFA !important;
    }

    /* 정답/오답 알림 박스 전체 스타일 */
    div[data-testid="stAlert"] {
        padding: 1.5rem !important;
        border-radius: 0.5rem !important;
    }

    /* 알림 박스 내부의 모든 텍스트 크기를 문제와 동일하게 (1.3rem) */
    div[data-testid="stAlert"] font, 
    div[data-testid="stAlert"] p, 
    div[data-testid="stAlert"] li, 
    div[data-testid="stAlert"] div {
        font-size: 1.3rem !important;
        line-height: 2.2rem !important;
        color: #FAFAFA !important; /* 글씨는 밝은색으로 통일 */
    }

    /* [오답 처리] 빨간 글씨 대신 테두리만 강조 */
    div[data-testid="stStatusWidget"] + div div[class*="st-emotion-cache-"] , 
    .stError {
        border: 3px solid #FF4444 !important; /* 빨간 테두리 강조 */
        background-color: rgba(255, 68, 68, 0.1) !important;
        color: #FAFAFA !important;
    }

    /* [정답 처리] 녹색 테두리 */
    .stSuccess {
        border: 3px solid #28A745 !important;
        background-color: rgba(40, 167, 69, 0.1) !important;
    }

    /* 경고/정보 박스 텍스트 색상 유지 */
    .stWarning, .stInfo {
        border: 2px solid #FFA500 !important;
    }
    
    /* EN 체크박스 줄바꿈 방지 */
    label[data-testid*="baseButton"] {
        white-space: nowrap !important;
    }
    
    div[data-baseweb="checkbox"] label {
        white-space: nowrap !important;
        min-width: fit-content !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ AWS AI Practitioner (AIF-C01) 연습장")

# 사이드바: 시험 모드 설정
st.sidebar.title("⚙️ 설정")

# 언어 모드 선택
lang_mode = st.sidebar.radio(
    "🌐 언어 모드",
    options=["한글", "English"],
    index=["한글", "English"].index(st.session_state.lang_mode) if st.session_state.lang_mode in ["한글", "English"] else 0,
    help="한글: 모든 문제를 한글로 표시\n영어: 모든 문제를 영어로 표시"
)
st.session_state.lang_mode = lang_mode

# 시험 모드 시작 버튼
if not st.session_state.exam_mode:
    st.sidebar.caption("📝 시험 모드 시작")
    if st.sidebar.button("시험 모드 시작 (65문제)", use_container_width=True, type="primary"):
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
question_body, choices = get_choices_for_language(question_en, question_ko, lang_mode, False, q)

# 선택지가 없으면 영어에서 다시 파싱 시도
if not choices:
    _, choices = parse_choices(question_en)

is_multiple = is_multiple_choice(question_en) or is_multiple_choice(question_ko)

# 문제 텍스트 끝 숫자 제거
question_body = clean_question_text(question_body)

# 영어/한글 토글 버튼
toggle_key = f"toggle_{q['id']}"
if toggle_key not in st.session_state.show_english_toggle:
    st.session_state.show_english_toggle[toggle_key] = False

col_toggle1, col_toggle2 = st.columns([3, 50])
with col_toggle1:
    toggle_label = "EN" if lang_mode == "한글" else "KO"
    toggle_help = "영어 원문 보기" if lang_mode == "한글" else "한글 원문 보기"
    show_english = st.checkbox(toggle_label, key=f"lang_toggle_{current_idx}", 
                               value=st.session_state.show_english_toggle.get(toggle_key, False),
                               help=toggle_help,
                               label_visibility="visible")
    st.session_state.show_english_toggle[toggle_key] = show_english

# 질문 본문 표시 (토글에 따라 반대로 표시)
# 한글 모드일 때: EN 체크 → 영어 표시
# 영어 모드일 때: EN 체크 → 한글 표시
if show_english:
    if lang_mode == "한글":
        # 한글 모드에서 EN 체크 → 영어 표시
        en_body, en_choices_for_display = parse_choices(question_en)
        display_question = clean_question_text(en_body) if en_body else question_en
        if en_choices_for_display:
            choices = en_choices_for_display
    else:
        # 영어 모드에서 EN 체크 → 한글 표시
        display_question = question_ko if question_ko else question_body
        # 한글 선택지 사용
        ko_choices_from_data = q.get('choices_ko', {})
        if ko_choices_from_data:
            choices = ko_choices_from_data
else:
    display_question = question_body

st.markdown(f'<div class="question-text">{display_question}</div>', unsafe_allow_html=True)

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
    
    # 영어/한글 토글 버튼 (선택지가 없는 경우에도)
    toggle_key_no_choice = f"toggle_{q['id']}_no_choice"
    if toggle_key_no_choice not in st.session_state.show_english_toggle:
        st.session_state.show_english_toggle[toggle_key_no_choice] = False
    
    col_toggle1_no_choice, col_toggle2_no_choice = st.columns([3, 50])
    with col_toggle1_no_choice:
        toggle_label_no_choice = "EN" if lang_mode == "한글" else "KO"
        toggle_help_no_choice = "영어 원문 보기" if lang_mode == "한글" else "한글 원문 보기"
        show_english_no_choice = st.checkbox(toggle_label_no_choice, key=f"lang_toggle_no_choice_{current_idx}",
                                             value=st.session_state.show_english_toggle.get(toggle_key_no_choice, False),
                                             help=toggle_help_no_choice,
                                             label_visibility="visible")
        st.session_state.show_english_toggle[toggle_key_no_choice] = show_english_no_choice
    
    if show_english_no_choice:
        if lang_mode == "한글":
            # 한글 모드에서 EN 체크 → 영어 표시
            en_body, _ = parse_choices(question_en)
            display_question_no_choice = clean_question_text(en_body) if en_body else question_en
        else:
            # 영어 모드에서 EN 체크 → 한글 표시
            display_question_no_choice = question_ko if question_ko else question_body
    else:
        display_question_no_choice = question_body
    
    st.markdown(f'<div class="question-text">{display_question_no_choice}</div>', unsafe_allow_html=True)
    
    # HOTSPOT 문제의 이미지 표시
    image_path = q.get('image_path')
    if image_path and os.path.exists(image_path):
        st.markdown("---")
        st.markdown("### 🖼️ 문제 이미지")
        st.image(image_path, use_container_width=True, caption=f"Question {q['id']} Image")
    
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
    
    # 결과 출력
    if is_correct:
        st.success(f"✅ **정답입니다!**\n\n{answer_text}")
    else:
        # 빨간 테두리 박스 안에 흰색 글씨로 표시됨
        st.error(f"❌ **틀렸습니다.**\n\n**정답:** {answer_text}")
        
        # 사용자가 선택한 답 표시
        if is_multiple:
            if st.session_state.selected_answers:
                st.info(f"🧐 **선택하신 답:** {', '.join(st.session_state.selected_answers)}")
        else:
            if st.session_state.selected_answer:
                st.info(f"🧐 **선택하신 답:** {st.session_state.selected_answer}")
        
        if q not in st.session_state.wrong_answers:
            st.session_state.wrong_answers.append(q)
            st.toast("오답 노트에 추가되었습니다.", icon="📝")

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
        # 답변을 선택해야만 다음 문제로 넘어갈 수 있음
        # 단, HOTSPOT 문제나 선택지가 없는 문제는 답변 없이도 넘어갈 수 있음
        has_answer = st.session_state.selected_answer is not None or len(st.session_state.selected_answers) > 0
        
        # HOTSPOT 문제나 선택지가 없는 경우 확인
        current_q = st.session_state.exam_questions[st.session_state.exam_current_index] if st.session_state.exam_current_index < len(st.session_state.exam_questions) else None
        if current_q:
            question_en = current_q.get('question_en', '')
            question_ko = current_q.get('question_ko', '')
            is_hotspot = 'HOTSPOT' in question_en.upper() or 'HOTSPOT' in question_ko.upper()
            _, current_choices = parse_choices(question_en)
            # 선택지가 없거나 HOTSPOT 문제면 답변 없이도 넘어갈 수 있음
            if not current_choices or len(current_choices) == 0 or is_hotspot:
                has_answer = True
        
        is_last = st.session_state.exam_current_index >= len(st.session_state.exam_questions) - 1
        if st.button("다음 문제 ▶", use_container_width=True, disabled=(is_last or not has_answer)):
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
    
    # 정답 채점 및 오답 노트에 추가
    correct_count = 0
    total_count = len(st.session_state.exam_questions)
    wrong_questions = []
    
    for idx, exam_q in enumerate(st.session_state.exam_questions):
        user_answer = st.session_state.exam_answers.get(str(idx))
        if user_answer:
            correct_answers = extract_correct_answers(exam_q.get('answer', ''))
            if correct_answers and user_answer == correct_answers[0]:
                correct_count += 1
            else:
                # 오답인 경우 오답 노트에 추가
                if exam_q not in st.session_state.wrong_answers:
                    st.session_state.wrong_answers.append(exam_q)
                    wrong_questions.append(exam_q)
        else:
            # 답을 선택하지 않은 문제도 오답으로 처리
            if exam_q not in st.session_state.wrong_answers:
                st.session_state.wrong_answers.append(exam_q)
                wrong_questions.append(exam_q)
    
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
    
    # 오답 노트에 추가된 문제 수 표시
    if wrong_questions:
        st.info(f"💡 {len(wrong_questions)}개 오답이 오답 노트에 자동으로 추가되었습니다.")
    
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
