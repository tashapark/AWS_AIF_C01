#!/usr/bin/env python3
"""
HOTSPOT 문제의 이미지를 추출하고 OCR로 텍스트를 추출하는 스크립트
"""
import json
import os
import re
import fitz  # PyMuPDF

def extract_images_from_pdf(pdf_path, question_id, question_text="", output_dir="data/images"):
    """PDF에서 HOTSPOT 문제의 이미지를 추출하여 저장"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        doc = fitz.open(pdf_path)
        images_found = []
        
        # 문제 텍스트가 있는 페이지 찾기
        target_pages = []
        if question_text:
            # 문제 ID나 키워드로 페이지 찾기
            keywords = question_text[:200].strip().split()[:5]
            search_terms = " ".join(keywords).lower()
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text().lower()
                # 문제 ID가 페이지에 있거나 키워드가 있으면
                if str(question_id) in page_text or search_terms in page_text:
                    target_pages.append(page_num)
                    if len(target_pages) >= 3:  # 최대 3페이지만
                        break
        
        # 대상 페이지가 없으면 질문 번호 기준으로 추정 (문제 ID가 페이지 번호와 관련 있을 수 있음)
        if not target_pages:
            # 질문 번호를 기반으로 대략적인 페이지 추정 (각 문제가 2-3페이지 정도라고 가정)
            try:
                q_num = int(question_id)
                estimated_page = max(0, (q_num - 1) * 2)
                target_pages = list(range(estimated_page, min(len(doc), estimated_page + 5)))
            except:
                target_pages = list(range(len(doc)))
        
        # 대상 페이지들에서 이미지 찾기
        for page_num in target_pages:
            page = doc[page_num]
            image_list = page.get_images(full=True)
            
            if len(image_list) > 0:
                # 모든 이미지 추출 시도
                for img_idx, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # 이미지 파일명: question_{id}_page_{page_num}_img_{img_idx}.{ext}
                        image_filename = f"question_{question_id}_page_{page_num}_img_{img_idx}.{image_ext}"
                        image_path = os.path.join(output_dir, image_filename)
                        
                        # 이미지 저장
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        
                        images_found.append(image_path)
                    except Exception as e:
                        print(f"  ⚠️ 이미지 추출 실패: {e}")
                        continue
                
                if images_found:
                    break  # 이미지를 찾으면 중단
        
        doc.close()
        
        # 첫 번째 이미지만 반환
        return images_found[0] if images_found else None
        
    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return None

def main():
    pdf_path = "data/ai_dump_1_120.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    # questions.json 읽기
    with open('data/questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    # HOTSPOT 문제 찾기
    hotspot_questions = []
    for q in questions:
        if 'HOTSPOT' in q.get('question_en', '').upper() or 'HOTSPOT' in q.get('question_ko', '').upper():
            hotspot_questions.append(q)
    
    print(f"HOTSPOT 문제 총 {len(hotspot_questions)}개 발견\n")
    
    updated_count = 0
    for q in hotspot_questions:
        q_id = q.get('id')
        question_en = q.get('question_en', '')
        
        # 이미 이미지가 있는지 확인
        existing_image = q.get('image_path', '')
        if existing_image and os.path.exists(existing_image):
            print(f"Question {q_id}: 이미지 이미 존재 - {existing_image}")
            continue
        
        print(f"Question {q_id}: 이미지 추출 시도...")
        image_path = extract_images_from_pdf(pdf_path, q_id, question_en)
        
        if image_path:
            q['image_path'] = image_path
            updated_count += 1
            print(f"  ✅ 이미지 추출 완료: {image_path}")
        else:
            print(f"  ⚠️ 이미지를 찾을 수 없음")
    
    # questions.json 저장
    if updated_count > 0:
        with open('data/questions.json', 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print(f"\n✅ {updated_count}개 문제에 이미지 추가 완료")
    else:
        print("\n이미지 추가 없음")

if __name__ == "__main__":
    main()

