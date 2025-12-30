import re
import json
from pypdf import PdfReader

def clean_text(text):
    # 특수 문자 및 깨진 기호 정리
    text = text.replace('㏙', '(').replace('㏚', ')').replace('㎿', '-')
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    return text

def parse_aws_dump(pdf_path):
    reader = PdfReader(pdf_path)
    full_text = ""
    
    # 1. 페이지별로 텍스트 추출 및 정리
    for page in reader.pages:
        full_text += page.extract_text() + "\n"

    # 2. 문제 단위로 쪼개기
    # 패턴이나 "숫자. " 패턴을 기준으로 분할 시도
    # 문제 번호가 시작되는 지점을 찾습니다 (예: 121. A manufacturing...)
    questions_raw = re.split(r'(\d{1,3}\.\s[A-Z])', full_text)
    
    parsed_data = []
    
    # split 결과가 [빈값, 번호, 본문, 번호, 본문...] 식이므로 합쳐서 처리
    for i in range(1, len(questions_raw), 2):
        if i+1 >= len(questions_raw): break
        
        q_num_part = questions_raw[i] # "121. A"
        q_content_part = questions_raw[i+1] # 나머지 내용
        q_block = q_num_part + q_content_part
        
        q_block = clean_text(q_block)
        
        # 정규표현식으로 각 필드 추출
        # 1. 문제 번호
        q_id = re.match(r'^(\d+)', q_block).group(1)
        
        # 2. 정답 (맨 마지막에 위치)
        ans_match = re.search(r'정답:\s*([A-E,\s\.]+.*?)(?=\s*\d{1,3}\.|$)', q_block)
        
        # 3. 한국어 번역
        ko_match = re.search(r'전체 번역:\s*(.*?)(?=\s*정답:)', q_block)
        
        # 4. 영어 질문 (문제 번호 다음부터 요약 전까지)
        en_match = re.search(r'^\d+\.\s*(.*?)(?=\s*요약:)', q_block)

        if q_id and ans_match and ko_match and en_match:
            parsed_data.append({
                "id": q_id,
                "question_en": en_match.group(1).strip(),
                "question_ko": ko_match.group(1).strip(),
                "answer": ans_match.group(1).strip()
            })
            
    return parsed_data

if __name__ == "__main__":
    test_files = ["data/ai_dump_1_120.pdf", "data/ai_dump_121_240.pdf", "data/ai_dump_241_329.pdf"]
    total_results = []
    
    for file in test_files:
        try:
            results = parse_aws_dump(file)
            print(f"{file}: {len(results)}문제 추출 성공")
            total_results.extend(results)
        except Exception as e:
            print(f"{file} 처리 중 오류: {e}")

    # 결과를 JSON 파일로 저장 (나중에 app.py에서 쓰기 위함)
    with open("data/questions.json", "w", encoding="utf-8") as f:
        json.dump(total_results, f, ensure_ascii=False, indent=4)
        
    print(f"--- 최종 결과: 총 {len(total_results)}문제가 questions.json에 저장되었습니다. ---")