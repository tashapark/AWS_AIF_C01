#!/usr/bin/env python3
"""번역 사전 파일 생성 스크립트"""
import json
import re
import sys
sys.path.insert(0, '.')
from enhance_questions import parse_choices

def create_translations_dict():
    """모든 고유 선택지를 추출하여 번역 사전 파일 생성"""
    # 모든 고유 선택지 추출
    with open('data/questions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_choices = set()
    for q in data:
        question_en = q.get('question_en', '')
        if question_en:
            en_choices = parse_choices(question_en)
            for letter, choice_text in en_choices.items():
                if choice_text:
                    all_choices.add(choice_text)

    # 기존 번역된 선택지 수집
    existing_translations = {}
    for q in data:
        choices_ko = q.get('choices_ko', {})
        if choices_ko:
            question_en = q.get('question_en', '')
            en_choices = parse_choices(question_en)
            for letter, choice_en in en_choices.items():
                if choice_en in all_choices and letter in choices_ko:
                    choice_ko = choices_ko[letter]
                    # 한글이 포함된 경우만 기존 번역으로 인정
                    has_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in choice_ko)
                    # 잘못된 번역 패턴 제외 (예: "증가 the epochs" 같은 것)
                    has_wrong_pattern = bool(re.search(r'[가-힣]+\s+(the|a|an|to|for|with|by|of|in|on|at)\s+[a-zA-Z]', choice_ko))
                    if has_korean and not has_wrong_pattern and choice_en not in existing_translations:
                        existing_translations[choice_en] = choice_ko

    print(f"총 고유 선택지: {len(all_choices)}개")
    print(f"기존 번역된 선택지 (올바른 것만): {len(existing_translations)}개")
    print(f"번역 필요: {len(all_choices) - len(existing_translations)}개")

    # 번역 사전 파일 구조
    translations_dict = {}
    for choice_en in sorted(all_choices):
        translations_dict[choice_en] = existing_translations.get(choice_en, "")

    # JSON 파일로 저장
    with open('data/choices_translations.json', 'w', encoding='utf-8') as f:
        json.dump(translations_dict, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 번역 사전 파일 생성 완료: data/choices_translations.json")
    print(f"   - 총 {len(translations_dict)}개 선택지")
    print(f"   - {len(existing_translations)}개는 기존 번역 포함")
    print(f"   - {len(translations_dict) - len(existing_translations)}개는 빈 값 (번역 필요)")

if __name__ == '__main__':
    create_translations_dict()

