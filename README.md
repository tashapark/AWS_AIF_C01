# AWS Certified AI Practitioner (AIF-C01) 학습 도우미

이 프로젝트는 제공된 덤프 PDF 데이터를 기반으로 퀴즈를 풀고, 오답 노트를 생성할 수 있는 **Streamlit** 기반 학습 애플리케이션입니다.

## 주요 기능
- **한/영 토글**: 문제를 영어 원문과 한글 번역본으로 전환하여 확인 가능
- **퀴즈 모드**: 덤프 문제를 랜덤하게 풀이
- **오답 노트 생성**: 틀린 문제를 모아서 PDF 파일로 다운로드

## 설치 및 실행 방법
1. 저장소 클론
2. 가상환경 생성 및 패키지 설치
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install streamlit pypdf fpdf