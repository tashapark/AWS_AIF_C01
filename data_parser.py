import re
import json
import os
from pypdf import PdfReader

def clean_text(text):
    # 특수 문자 및 깨진 기호 정리
    text = text.replace('㏙', '(').replace('㏚', ')').replace('㎿', '-')
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_images_from_pdf(pdf_path, question_id, question_text="", output_dir="data/images"):
    """PDF에서 HOTSPOT 문제의 이미지를 추출하여 저장"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(f"PyMuPDF not installed. Skipping image extraction for question {question_id}")
        return None
    
    try:
        doc = fitz.open(pdf_path)
        images_found = []
        
        # 문제 텍스트가 있는 페이지 찾기 (선택적)
        target_pages = []
        if question_text:
            # 문제의 첫 몇 단어로 페이지 찾기
            keywords = question_text[:100].strip().split()[:5]
            search_terms = " ".join(keywords).lower()
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text().lower()
                if search_terms in page_text:
                    target_pages.append(page_num)
                    break
        
        # 대상 페이지가 없으면 모든 페이지 검색
        if not target_pages:
            target_pages = list(range(len(doc)))
        else:
            # 찾은 페이지 주변 페이지도 포함 (최대 3페이지)
            start_page = max(0, target_pages[0] - 1)
            end_page = min(len(doc), target_pages[0] + 2)
            target_pages = list(range(start_page, end_page))
        
        # 대상 페이지들에서 이미지 찾기
        for page_num in target_pages:
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            if len(image_list) > 0:
                # 첫 번째 이미지만 추출 (HOTSPOT 문제는 보통 하나의 이미지만 사용)
                img = image_list[0]
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # 이미지 파일명: question_{id}.{ext}
                image_filename = f"question_{question_id}.{image_ext}"
                image_path = os.path.join(output_dir, image_filename)
                
                # 이미지 저장
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                images_found.append(image_path)
                break  # 첫 이미지를 찾으면 중단
        
        doc.close()
        
        # 첫 번째 이미지만 반환
        return images_found[0] if images_found else None
        
    except Exception as e:
        print(f"Error extracting image for question {question_id}: {e}")
        return None

def find_question_page(pdf_path, question_text):
    """PDF에서 특정 문제 텍스트가 있는 페이지 번호 찾기"""
    try:
        reader = PdfReader(pdf_path)
        # 문제의 첫 몇 단어를 검색 키워드로 사용
        keywords = question_text[:50].split()[:3]  # 첫 3개 단어
        search_text = " ".join(keywords).lower()
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text().lower()
            if search_text in page_text:
                return page_num
        return 0  # 기본값: 첫 페이지
    except Exception as e:
        print(f"Error finding page: {e}")
        return 0

def parse_aws_dump(pdf_path, extract_hotspot_images=True):
    reader = PdfReader(pdf_path)
    full_text = ""
    
    # 이미지 저장 디렉토리 생성
    if extract_hotspot_images:
        os.makedirs("data/images", exist_ok=True)
    
    # 1. 페이지별로 텍스트 추출 및 정리
    for page in reader.pages:
        full_text += page.extract_text() + "\n"

    # 2. 문제 단위로 쪼개기
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
            question_en = en_match.group(1).strip()
            is_hotspot = 'HOTSPOT' in question_en.upper()
            
            # 한글 질문 끝에 남아있는 숫자 제거 (예: "14", "•" 등)
            question_ko_clean = ko_match.group(1).strip()
            # 끝에 있는 숫자나 특수문자 제거
            question_ko_clean = re.sub(r'[\s•·]*\d+[\s•·]*$', '', question_ko_clean).strip()
            # 끝에 남은 불필요한 문자 제거
            question_ko_clean = re.sub(r'[•·\s]+$', '', question_ko_clean).strip()
            
            question_data = {
                "id": q_id,
                "question_en": question_en,
                "question_ko": question_ko_clean,
                "answer": ans_match.group(1).strip()
            }
            
            # HOTSPOT 문제의 이미지 추출
            if extract_hotspot_images and is_hotspot:
                image_path = extract_images_from_pdf(pdf_path, q_id, question_en)
                if image_path:
                    # 상대 경로로 저장 (data/images/question_xxx.png)
                    question_data["image_path"] = image_path
                    print(f"✅ Question {q_id}: 이미지 추출 완료 - {image_path}")
                else:
                    print(f"⚠️ Question {q_id}: 이미지를 찾을 수 없음")
            
            parsed_data.append(question_data)
            
    return parsed_data

if __name__ == "__main__":
    test_files = ["data/ai_dump_1_120.pdf", "data/ai_dump_121_240.pdf", "data/ai_dump_241_329.pdf"]
    total_results = []
    
    for file in test_files:
        try:
            results = parse_aws_dump(file, extract_hotspot_images=True)
            print(f"{file}: {len(results)}문제 추출 성공")
            total_results.extend(results)
        except Exception as e:
            print(f"{file} 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()

    # 결과를 JSON 파일로 저장 (나중에 app.py에서 쓰기 위함)
    with open("data/questions.json", "w", encoding="utf-8") as f:
        json.dump(total_results, f, ensure_ascii=False, indent=4)
        
    # 이미지가 추출된 문제 수 확인
    image_count = sum(1 for q in total_results if q.get("image_path"))
    print(f"--- 최종 결과: 총 {len(total_results)}문제가 questions.json에 저장되었습니다. ---")
    print(f"--- 이미지가 추출된 HOTSPOT 문제: {image_count}개 ---")
