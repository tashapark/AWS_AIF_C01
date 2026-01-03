import json
import re

def parse_choices(question_text):
    """질문 텍스트에서 선택지를 파싱"""
    if not question_text:
        return {}
    
    text = question_text.replace('\u0000', '').strip()
    
    if text.upper().startswith('HOTSPOT'):
        return {}
    
    pattern = r'[•·]\s*([A-E])\.\s+'
    matches = list(re.finditer(pattern, text))
    
    if len(matches) < 2:
        return {}
    
    choices = {}
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
    
    return choices

def load_translations_dict():
    """번역 사전 파일 로드"""
    try:
        with open('data/choices_translations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"번역 사전 파일 로드 오류: {e}")
        return {}

# 번역 사전 (전역 변수로 캐시)
_translations_dict = None

def get_translations_dict():
    """번역 사전 가져오기 (캐시 사용)"""
    global _translations_dict
    if _translations_dict is None:
        _translations_dict = load_translations_dict()
    return _translations_dict

def translate_choice_simple(choice_en):
    """번역 사전 기반 선택지 번역 (사전에 없으면 규칙 기반 번역)"""
    if not choice_en:
        return choice_en
    
    # 먼저 번역 사전에서 확인
    translations_dict = get_translations_dict()
    if choice_en in translations_dict and translations_dict[choice_en]:
        return translations_dict[choice_en]
    
    # AWS 제품명과 기술 용어 리스트 (영문 유지)
    aws_products = [
        'Amazon', 'SageMaker', 'Bedrock', 'Rekognition', 'Comprehend', 'Polly', 'Lex',
        'QuickSight', 'Ground Truth', 'Kendra', 'Textract', 'Transcribe', 'Translate',
        'Forecast', 'Personalize', 'Fraud Detector', 'CodeGuru', 'DevOps Guru',
        'Lookout', 'Monitron', 'Panorama', 'DeepLens', 'DeepRacer', 'DeepComposer',
        'S3', 'EC2', 'Lambda', 'CloudFormation', 'CloudWatch', 'IAM', 'VPC', 'SNS', 'SQS',
        'EKS', 'ECS', 'Fargate', 'Glue', 'EMR', 'Redshift', 'DynamoDB', 'RDS',
        'Aurora', 'ElastiCache', 'Elasticsearch', 'OpenSearch', 'Athena', 'Kinesis',
        'MSK', 'EventBridge', 'Step Functions', 'AppSync', 'API Gateway', 'Model Monitor',
        'Studio', 'Canvas', 'Notebook', 'Experiments', 'Debugger', 'Profiler', 'Clarify',
        'Feature Store', 'MLOps', 'AutoPilot', 'Batch Transform', 'Multi-Model Endpoints'
    ]
    
    # AWS 제품명에 대한 한글 설명 사전
    aws_product_descriptions = {
        'Amazon Comprehend': '자연어 처리 서비스',
        'Amazon Personalize': '개인화 추천 서비스',
        'Amazon Polly': '음성 합성 서비스',
        'Amazon Lex': '대화형 챗봇 서비스',
        'Amazon Rekognition': '이미지 및 비디오 분석 서비스',
        'Amazon Textract': '문서 텍스트 추출 서비스',
        'Amazon Transcribe': '음성-텍스트 변환 서비스',
        'Amazon Translate': '번역 서비스',
        'Amazon Forecast': '시계열 예측 서비스',
        'Amazon Kendra': '엔터프라이즈 검색 서비스',
        'Amazon QuickSight': '비즈니스 인텔리전스 서비스',
        'Amazon OpenSearch Service': '검색 및 분석 서비스',
        'Amazon SageMaker': '머신러닝 플랫폼',
        'Amazon Bedrock': '생성형 AI 서비스',
        'Amazon SageMaker Ground Truth': '데이터 라벨링 서비스',
        'Amazon SageMaker Ground Truth Plus': '데이터 라벨링 서비스',
        'Amazon SageMaker Feature Store': '피처 스토어',
        'Amazon SageMaker Model Monitor': '모델 모니터링 서비스',
        'Amazon SageMaker Clarify': '모델 편향성 분석 서비스',
        'Amazon Fraud Detector': '사기 탐지 서비스',
        'Amazon CodeGuru': '코드 리뷰 및 성능 분석 서비스',
        'Amazon DevOps Guru': '운영 인사이트 서비스',
        'Amazon Lookout': '산업용 AI 서비스',
        'Amazon Monitron': '설비 모니터링 서비스',
        'Amazon Panorama': '엣지 컴퓨터 비전 서비스',
        'Amazon Athena': '서버리스 쿼리 서비스',
        'Amazon Kinesis': '실시간 스트리밍 데이터 서비스',
        'Amazon S3': '객체 스토리지 서비스',
        'Amazon EC2': '가상 서버 서비스',
        'Amazon Lambda': '서버리스 컴퓨팅 서비스',
        'Amazon RDS': '관계형 데이터베이스 서비스',
        'Amazon DynamoDB': 'NoSQL 데이터베이스 서비스',
        'Amazon Redshift': '데이터 웨어하우스 서비스',
        'Amazon EKS': 'Kubernetes 관리 서비스',
        'Amazon ECS': '컨테이너 오케스트레이션 서비스',
        'Amazon API Gateway': 'API 관리 서비스',
        'Amazon CloudWatch': '모니터링 서비스',
        'Amazon EventBridge': '이벤트 버스 서비스',
        'Amazon Step Functions': '워크플로우 오케스트레이션 서비스',
        'Amazon AppSync': 'GraphQL API 서비스',
        'Amazon Glue': 'ETL 서비스',
        'Amazon EMR': '빅데이터 처리 서비스',
        'Amazon MSK': 'Apache Kafka 관리 서비스',
        'Amazon ElastiCache': '인메모리 캐시 서비스',
        'Amazon Aurora': '관계형 데이터베이스 서비스',
        'Amazon Elasticsearch': '검색 및 분석 엔진',
        'Amazon OpenSearch': '검색 및 분석 엔진',
    }
    
    # 전체 패턴 번역 사전 (우선순위: 긴 패턴부터)
    pattern_translations = [
        # 기본 AI 프로세스
        ('Training', '학습'),
        ('Inference', '추론'),
        ('Model deployment', '모델 배포'),
        ('Bias correction', '편향 보정'),
        ('Data labeling', '데이터 라벨링'),
        ('Data encoding', '데이터 인코딩'),
        ('Data normalization', '데이터 정규화'),
        ('Data balancing', '데이터 균형 조정'),
        
        # 프롬프트 엔지니어링
        ('Few-shot prompting', 'Few-shot 프롬프팅 (소수 샘플 프롬프팅)'),
        ('Zero-shot prompting', 'Zero-shot 프롬프팅 (샘플 없음 프롬프팅)'),
        ('Directional stimulus prompting', '방향성 자극 프롬프팅'),
        ('Chain-of-thought prompting', 'Chain-of-thought 프롬프팅 (사고 과정 프롬프팅)'),
        
        # 추론 관련
        ('Real-time inference', '실시간 추론'),
        ('Serverless inference', '서버리스 추론'),
        ('Asynchronous inference', '비동기 추론'),
        ('Batch transform', '배치 변환'),
        ('Batch inference', '배치 추론'),
        ('Multi-Model Endpoints', 'Multi-Model Endpoints (다중 모델 엔드포인트)'),
        
        # 모델 학습 관련
        ('Increase the number of epochs', '에폭 수 증가'),
        ('Decrease the number of epochs', '에폭 수 감소'),
        ('Use transfer learning', '전이 학습 사용'),
        ('Use unsupervised learning', '비지도 학습 사용'),
        ('Re-train the model with fresh data', '최신 데이터로 모델 재학습'),
        ('Retrain the model', '모델 재학습'),
        ('Train a new model', '새 모델 학습'),
        ('Fine-tune the model', '모델 파인튜닝'),
        
        # LLM 관련
        ('Adjust the prompt', '프롬프트 조정'),
        ('Choose an LLM of a different size', '다른 크기의 LLM 선택'),
        ('Increase the temperature', '온도 증가'),
        ('Increase the Top K value', 'Top K 값 증가'),
        ('Deploy optimized small language models (SLMs) on edge devices', '엣지 디바이스에 최적화된 소형 언어 모델(SLM) 배포'),
        ('Deploy optimized large language models (LLMs) on edge devices', '엣지 디바이스에 최적화된 대형 언어 모델(LLM) 배포'),
        ('Incorporate a centralized small language model (SLM) API for asynchronous communication', '비동기 통신을 위한 중앙화된 소형 언어 모델(SLM) API 통합'),
        ('Incorporate a centralized large language model (LLM) API for asynchronous communication', '비동기 통신을 위한 중앙화된 대형 언어 모델(LLM) API 통합'),
        
        # 모델 설명 가능성
        ('Code for model training', '모델 학습용 코드'),
        ('Partial dependence plots (PDPs)', '부분 의존성 플롯 (PDPs)'),
        ('Sample data for training', '학습용 샘플 데이터'),
        ('Model convergence tables', '모델 수렴 테이블'),
        ('Decision trees', '의사결정 나무'),
        ('Linear regression', '선형 회귀'),
        ('Logistic regression', '로지스틱 회귀'),
        ('Neural networks', '신경망'),
        
        # 평가 지표
        ('R-squared score', 'R-제곱 점수'),
        ('Accuracy', '정확도'),
        ('Root mean squared error (RMSE)', '평균 제곱근 오차 (RMSE)'),
        ('Learning rate', '학습률'),
        ('F1 score', 'F1 점수'),
        ('Precision', '정밀도'),
        ('Recall', '재현율'),
        ('Confusion matrix', '혼동 행렬'),
        
        # 애플리케이션 타입
        ('Build an automatic named entity recognition system', '자동 명명된 개체 인식 시스템 구축'),
        ('Create a recommendation engine', '추천 엔진 생성'),
        ('Develop a summarization chatbot', '요약 챗봇 개발'),
        ('Develop a multi-language translation system', '다국어 번역 시스템 개발'),
        
        # AWS 서비스 사용 패턴
        ('Human-in-the-loop validation by using Amazon SageMaker Ground Truth Plus', 'Amazon SageMaker Ground Truth Plus를 사용한 인간 개입 검증'),
        ('Data augmentation by using an Amazon Bedrock knowledge base', 'Amazon Bedrock 지식 베이스를 사용한 데이터 증강'),
        ('Image recognition by using Amazon Rekognition', 'Amazon Rekognition을 사용한 이미지 인식'),
        ('Data summarization by using Amazon QuickSight Q', 'Amazon QuickSight Q를 사용한 데이터 요약'),
        ('Ensure that the role that Amazon Bedrock assumes has permission to decrypt data', 'Amazon Bedrock이 가정하는 역할이 데이터 복호화 권한을 갖도록 설정'),
        ('Set the access permissions for the S3 buckets to allow public access', 'S3 버킷의 액세스 권한을 공개 액세스 허용으로 설정'),
        ('Use prompt engineering techniques to tell the model to look for information', '프롬프트 엔지니어링 기법을 사용하여 모델에 정보를 찾도록 지시'),
        ('Ensure that the S3 data does not contain sensitive information', 'S3 데이터에 민감한 정보가 포함되지 않도록 보장'),
        ('Restart the SageMaker AI endpoint', 'SageMaker AI 엔드포인트 재시작'),
        ('Adjust the monitoring sensitivity', '모니터링 민감도 조정'),
        ('Set up experiments tracking', '실험 추적 설정'),
        
        # 데이터 관리
        ('Store training data', '학습 데이터 저장'),
        ('Store model artifacts', '모델 아티팩트 저장'),
        ('Store inference results', '추론 결과 저장'),
        ('Data preprocessing', '데이터 전처리'),
        ('Data validation', '데이터 검증'),
        ('Data drift detection', '데이터 드리프트 감지'),
        
        # 모니터링 및 운영
        ('Model monitoring', '모델 모니터링'),
        ('Performance monitoring', '성능 모니터링'),
        ('Monitor model performance', '모델 성능 모니터링'),
        ('Track model metrics', '모델 메트릭 추적'),
        ('Set up alerts', '알림 설정'),
        ('Configure monitoring', '모니터링 구성'),
        
        # 파라미터 조정
        ('Decrease the batch size', '배치 크기 감소'),
        ('Decrease the epochs', '에폭 감소'),
        ('Decrease the number of input tokens on invocations of the LLM', 'LLM 호출 시 입력 토큰 수 감소'),
        ('Define a higher number for the temperature parameter', '온도 파라미터에 더 높은 값 정의'),
        ('Choose a lower temperature value', '더 낮은 온도 값 선택'),
        ('Auto scaling inference endpoints', '자동 확장 추론 엔드포인트'),
        
        # 시스템 타입
        ('Anomaly detection', '이상 탐지'),
        ('Analyzing financial data to forecast stock market trends', '주식 시장 동향 예측을 위한 금융 데이터 분석'),
        ('Building an application by using an existing third-party generative AI foundation model (FM)', '기존 서드파티 생성형 AI 기반 모델(FM)을 사용한 애플리케이션 구축'),
        ('Building and training a generative AI model from scratch by using specific data that a customer owns', '고객이 소유한 특정 데이터를 사용하여 처음부터 생성형 AI 모델 구축 및 학습'),
        ('Creating photorealistic images from text descriptions for digital marketing', '디지털 마케팅을 위한 텍스트 설명에서 사실적 이미지 생성'),
        ('Enhancing database performance by using optimized indexing', '최적화된 인덱싱을 사용한 데이터베이스 성능 향상'),
        ('Avoid using LLMs that are not listed in Amazon SageMaker', 'Amazon SageMaker에 나열되지 않은 LLM 사용 피하기'),
        
        # 일반 동사/명사 패턴 (짧은 패턴은 마지막에)
        ('Deploy', '배포'),
        ('Train', '학습'),
        ('Monitor', '모니터링'),
        ('Track', '추적'),
        ('Configure', '구성'),
        ('Optimize', '최적화'),
        ('Scale', '확장'),
        ('Restart', '재시작'),
        ('Create', '생성'),
        ('Build', '구축'),
        ('Develop', '개발'),
        ('Set up', '설정'),
        ('Ensure', '보장'),
        ('Use', '사용'),
        ('Adjust', '조정'),
        ('Increase', '증가'),
        ('Decrease', '감소'),
    ]
    
    # 제품명 보호
    protected = {}
    protected_text = choice_en
    for i, product in enumerate(aws_products):
        if product in protected_text:
            placeholder = f"__AWS_PRODUCT_{i}__"
            protected[placeholder] = product
            protected_text = protected_text.replace(product, placeholder)
    
    # 패턴 매칭 번역 (긴 패턴부터)
    translated = protected_text
    pattern_translations_sorted = sorted(pattern_translations, key=lambda x: len(x[0]), reverse=True)
    
    for pattern_en, pattern_ko in pattern_translations_sorted:
        # 제품명이 포함된 패턴은 제품명을 보호한 상태에서 매칭
        pattern_protected = pattern_en
        for placeholder, product in protected.items():
            pattern_protected = pattern_protected.replace(product, placeholder)
        
        # 정확한 단어 경계 매칭 (부분 문자열이 아닌 전체 단어 매칭)
        import re as re_module
        # 단어 경계를 고려한 패턴 (단어 전체 매칭)
        # 선택지가 짧은 경우 정확히 일치하는지 확인
        if pattern_protected.lower() == translated.lower().strip():
            # 완전히 일치하는 경우
            translated = pattern_ko
            break
        else:
            # 단어 경계를 고려한 매칭
            pattern_regex = r'\b' + re_module.escape(pattern_protected) + r'\b'
            match = re_module.search(pattern_regex, translated, re_module.IGNORECASE)
            if match:
                start, end = match.span()
                translated = translated[:start] + pattern_ko + translated[end:]
                break
    
    # 제품명 복원
    for placeholder, product in protected.items():
        translated = translated.replace(placeholder, product)
    
    # 번역이 안 된 경우 원문 반환
    if translated == protected_text:
        translated = choice_en
    
    # 번역 후 불필요한 영어 접미사 제거 (예: "학습ing", "배포ment" 등)
    # 한글 뒤에 영어 접미사가 붙은 경우 제거
    import re as re_module
    translated = re_module.sub(r'([가-힣]+)(ing|ment|tion|sion|ness|ity|ly|ed|er|est)\b', r'\1', translated, flags=re_module.IGNORECASE)
    
    # AWS 제품명에 한글 설명 추가 (제품명만 있는 경우)
    # 이미 한글이 포함되어 있지 않은 경우에만 설명 추가
    has_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in translated)
    if not has_korean:
        # 전체 선택지가 AWS 제품명과 일치하는지 확인
        translated_stripped = translated.strip()
        for product_name, description in aws_product_descriptions.items():
            if translated_stripped == product_name or translated_stripped == product_name + ' Service':
                # 설명 추가 (이미 괄호가 있으면 추가하지 않음)
                if '(' not in translated and '（' not in translated:
                    translated = f"{product_name} ({description})"
                break
    
    return translated

def enhance_answer_explanation(answer_text, question_text=""):
    """정답 해설을 더 자세하게 개선"""
    if not answer_text:
        return answer_text
    
    # 이미 상세한 해설이 있으면 그대로 유지
    if len(answer_text) > 100 and '(' in answer_text and ':' in answer_text:
        return answer_text
    
    # 간단한 해설만 있으면 더 자세하게 개선
    match = re.match(r'([A-E])\.\s*(.+?)(?:\s*\(|$)', answer_text)
    if match:
        letter = match.group(1)
        answer_text_clean = match.group(2).strip()
        
        # 해설 추가
        explanation = ""
        answer_lower = answer_text_clean.lower()
        question_lower = question_text.lower() if question_text else ""
        
        # 모델 설명 가능성 및 해석 가능성
        if 'pdp' in answer_lower or 'partial dependence' in answer_lower:
            explanation = "부분 의존성 플롯(PDPs): 특정 특성이 모델 예측에 미치는 영향을 시각화하여 모델의 설명 가능성과 투명성을 높입니다. 이해관계자들에게 모델이 어떻게 작동하는지 설명하는 데 유용합니다."
        elif 'decision tree' in answer_lower or '의사결정 나무' in answer_text_clean:
            explanation = "의사결정 나무: 모델의 내부 의사결정 과정을 트리 구조로 시각화할 수 있어 해석 가능성이 높습니다. 각 노드에서의 분기 조건과 결과를 명확히 추적할 수 있어 설명 가능성을 제공합니다."
        elif 'model convergence tables' in answer_lower:
            explanation = "모델 수렴 테이블: 모델 학습 과정에서의 수렴 상태를 보여주지만, 모델의 예측 메커니즘 자체를 설명하지는 않습니다. 설명 가능성을 위해서는 PDPs나 의사결정 나무가 더 적합합니다."
        
        # LLM 및 생성형 AI
        elif 'summarization' in answer_lower or '요약' in answer_text_clean:
            explanation = "요약 챗봇: 문서에서 핵심 포인트를 추출하고 요약하는 작업에 적합합니다. LLM의 강력한 텍스트 이해 및 생성 능력을 활용하여 법률 문서와 같은 긴 문서의 핵심 내용을 빠르게 파악할 수 있습니다."
        elif 'prompt' in answer_lower or '프롬프트' in answer_text_clean:
            explanation = "프롬프트 조정: LLM의 출력 길이와 언어를 제어하는 가장 직접적인 방법입니다. 프롬프트에 명확한 지시를 추가하여 원하는 형식과 언어로 응답을 유도할 수 있습니다."
        elif 'temperature' in answer_lower:
            if 'increase' in answer_lower or 'higher' in answer_lower:
                explanation = "온도 증가: LLM의 출력 다양성을 높입니다. 더 높은 온도는 더 창의적이고 무작위적인 응답을 생성하지만, 일관성은 떨어질 수 있습니다."
            elif 'decrease' in answer_lower or 'lower' in answer_lower:
                explanation = "온도 감소: LLM의 출력 일관성을 높입니다. 더 낮은 온도는 더 결정론적이고 일관된 응답을 생성하지만, 다양성은 줄어듭니다."
        elif 'llm' in answer_lower and 'size' in answer_lower:
            explanation = "LLM 크기 선택: 모델 크기에 따라 성능과 리소스 요구사항이 달라집니다. 더 큰 모델은 일반적으로 더 나은 성능을 제공하지만, 더 많은 컴퓨팅 자원과 비용이 필요합니다."
        elif 'slm' in answer_lower and 'edge' in answer_lower:
            explanation = "엣지 디바이스에 SLM 배포: 엣지 환경에서는 네트워크 지연 없이 빠른 응답이 필요하며, 리소스 제약이 있습니다. 소형 언어 모델(SLM)은 엣지 디바이스에 최적화되어 실시간 추론을 가능하게 합니다."
        
        # 추론 타입
        elif 'asynchronous inference' in answer_lower or ('비동기' in answer_text_clean and '추론' in answer_text_clean):
            explanation = "비동기 추론: 대용량 데이터와 긴 처리 시간이 필요한 작업에 적합합니다. 1GB의 데이터와 1시간의 처리 시간을 요구하는 경우, 비동기 추론이 실시간에 가까운 지연 시간을 제공하면서도 대량 처리를 가능하게 합니다."
        elif 'real-time inference' in answer_lower or '실시간 추론' in answer_text_clean:
            explanation = "실시간 추론: 낮은 지연 시간이 필요한 애플리케이션에 적합합니다. 사용자 요청에 즉시 응답해야 하는 대화형 애플리케이션에서 사용됩니다."
        elif 'serverless inference' in answer_lower or '서버리스 추론' in answer_text_clean:
            explanation = "서버리스 추론: 서버 관리 없이 추론을 실행할 수 있습니다. 트래픽이 불규칙한 워크로드에 적합하며, 사용한 만큼만 비용을 지불합니다."
        elif 'batch transform' in answer_lower or '배치 변환' in answer_text_clean:
            explanation = "배치 변환: 대량의 데이터를 한 번에 처리하는 데 적합합니다. 실시간 응답이 필요하지 않고 대량 데이터 처리에 효율적입니다."
        
        # 모델 학습
        elif 're-train' in answer_lower or 'retrain' in answer_lower or ('재학습' in answer_text_clean and '모델' in answer_text_clean):
            explanation = "모델 재학습: 데이터 드리프트가 감지되었을 때, 최신 데이터로 모델을 재학습하는 것이 가장 효과적인 해결책입니다. 새로운 데이터 분포에 맞게 모델을 업데이트하여 성능을 유지하거나 개선할 수 있습니다."
        elif 'transfer learning' in answer_lower or '전이 학습' in answer_text_clean:
            explanation = "전이 학습: 사전 학습된 모델을 새로운 관련 작업에 적응시키는 기법입니다. 처음부터 모델을 학습하는 것보다 적은 데이터와 계산 자원으로 높은 성능을 달성할 수 있습니다."
        elif 'unsupervised learning' in answer_lower or '비지도 학습' in answer_text_clean:
            explanation = "비지도 학습: 레이블이 없는 데이터에서 패턴을 찾는 학습 방법입니다. 클러스터링, 이상 탐지 등에 사용됩니다."
        elif 'fine-tune' in answer_lower or '파인튜닝' in answer_text_clean:
            explanation = "파인튜닝: 사전 학습된 모델을 특정 작업에 맞게 미세 조정하는 과정입니다. 전체 모델을 처음부터 학습하는 것보다 효율적입니다."
        elif 'epoch' in answer_lower:
            if 'increase' in answer_lower:
                explanation = "에폭 수 증가: 모델이 데이터를 더 많이 학습하게 하여 성능을 개선할 수 있지만, 과적합(overfitting)의 위험이 있습니다."
            elif 'decrease' in answer_lower:
                explanation = "에폭 수 감소: 학습 시간은 줄어들지만 모델 성능이 저하될 수 있습니다. 충분한 학습이 이루어지지 않을 수 있습니다."
        
        # 평가 지표
        elif 'accuracy' in answer_lower or '정확도' in answer_text_clean:
            explanation = "정확도(Accuracy): 전체 예측 중 올바른 예측의 비율을 나타냅니다. 분류 문제에서 가장 직관적인 평가 지표이지만, 클래스 불균형이 있을 때는 부정확할 수 있습니다."
        elif 'rmse' in answer_lower or 'root mean squared error' in answer_lower:
            explanation = "평균 제곱근 오차(RMSE): 회귀 문제에서 예측값과 실제값 사이의 평균 오차를 측정합니다. 값이 낮을수록 모델 성능이 좋습니다."
        elif 'r-squared' in answer_lower or 'r-제곱' in answer_text_clean:
            explanation = "R-제곱 점수: 모델이 데이터의 분산을 얼마나 잘 설명하는지를 나타냅니다. 0과 1 사이의 값을 가지며, 1에 가까울수록 좋습니다."
        elif 'f1' in answer_lower and 'score' in answer_lower:
            explanation = "F1 점수: 정밀도와 재현율의 조화 평균입니다. 클래스 불균형이 있는 경우 정확도보다 더 신뢰할 수 있는 지표입니다."
        
        # 모니터링 및 데이터 드리프트
        elif 'model monitor' in answer_lower or '모니터링' in answer_text_clean:
            if 'sensitivity' in answer_lower or '민감도' in answer_text_clean:
                explanation = "모니터링 민감도 조정: 임계값을 변경하는 것은 데이터 드리프트가 발생했다는 사실을 변경하지 않습니다. 드리프트 자체를 해결하지 못하므로 적절한 해결책이 아닙니다."
            else:
                explanation = "Amazon SageMaker Model Monitor: 프로덕션 환경에서 모델의 성능과 데이터 품질을 지속적으로 모니터링합니다. 데이터 드리프트, 개념 드리프트, 데이터 품질 문제 등을 감지하고 알림을 제공합니다."
        elif 'data drift' in answer_lower or '데이터 드리프트' in answer_text_clean:
            explanation = "데이터 드리프트: 프로덕션 환경의 데이터 분포가 학습 데이터와 달라지는 현상입니다. 모델 성능 저하의 주요 원인 중 하나이며, 정기적인 모니터링과 재학습이 필요합니다."
        elif 'endpoint' in answer_lower and ('restart' in answer_lower or '재시작' in answer_text_clean):
            explanation = "엔드포인트 재시작: 데이터 드리프트 문제를 해결하지 못합니다. 재시작은 임시적인 조치일 뿐이며, 근본적인 문제인 데이터 분포 변화를 해결하지 않습니다."
        
        # AWS 서비스
        elif 'ground truth' in answer_lower:
            explanation = "Amazon SageMaker Ground Truth Plus: 사람이 개입하는 검증(Human-in-the-loop) 방식을 통해 높은 정확도와 잘못된 주석의 위험을 최소화합니다. 복잡한 작업에서 사람의 검증을 통해 품질을 보장합니다."
        elif 'bedrock' in answer_lower and 'knowledge base' in answer_lower:
            explanation = "Amazon Bedrock 지식 베이스: 기업의 데이터를 검색 가능한 형태로 저장하고 LLM과 통합하여 정확한 응답을 생성합니다. RAG(Retrieval-Augmented Generation) 패턴을 구현합니다."
        elif 'rekognition' in answer_lower:
            explanation = "Amazon Rekognition: 이미지와 비디오에서 객체, 얼굴, 텍스트, 장면을 감지하고 분석하는 서비스입니다. 컴퓨터 비전 작업에 활용됩니다."
        elif 'comprehend' in answer_lower:
            explanation = "Amazon Comprehend: 자연어 처리 서비스로 텍스트에서 인사이트, 관계, 감정을 추출합니다. 문서 분석, 감정 분석 등에 사용됩니다."
        elif 'sagemaker clarify' in answer_lower:
            explanation = "Amazon SageMaker Clarify: 모델의 편향성과 설명 가능성을 분석하는 서비스입니다. 모델 예측의 공정성을 평가하고 이해관계자에게 투명성을 제공합니다."
        elif 'lex' in answer_lower and 'chatbot' in answer_lower:
            explanation = "Amazon Lex: 대화형 챗봇을 구축하는 서비스입니다. 음성 및 텍스트 인터페이스를 제공하며, 자연어 이해(NLU) 기능을 포함합니다."
        
        # 애플리케이션 타입
        elif 'recommendation' in answer_lower or '추천' in answer_text_clean:
            explanation = "추천 엔진: 사용자의 과거 행동과 선호도를 기반으로 개인화된 추천을 제공합니다. 협업 필터링, 콘텐츠 기반 필터링 등의 기법을 사용합니다."
        elif 'named entity recognition' in answer_lower or '개체 인식' in answer_text_clean:
            explanation = "명명된 개체 인식(NER): 텍스트에서 사람, 조직, 위치 등의 명명된 개체를 식별하고 분류하는 작업입니다. 정보 추출의 기본 기술입니다."
        elif 'anomaly detection' in answer_lower or '이상 탐지' in answer_text_clean:
            explanation = "이상 탐지: 정상 패턴과 다른 이상한 데이터나 행동을 감지하는 시스템입니다. 사기 탐지, 시스템 모니터링 등에 사용됩니다."
        elif 'fraud' in answer_lower or '사기' in answer_text_clean:
            explanation = "사기 예측 시스템: 이상 탐지와 머신러닝을 활용하여 사기 거래를 식별합니다. 실시간 거래 모니터링과 위험 점수 계산을 제공합니다."
        
        # 데이터 관리
        elif 's3' in answer_lower and 'permission' in answer_lower:
            explanation = "S3 권한 설정: 보안을 위해 최소 권한 원칙을 따라야 합니다. 공개 액세스는 민감한 데이터에 위험할 수 있습니다."
        elif 'iam' in answer_lower or 'role' in answer_lower:
            explanation = "IAM 역할 및 정책: AWS 리소스에 대한 접근을 제어합니다. 최소 권한 원칙에 따라 필요한 권한만 부여해야 합니다."
        elif 'encrypt' in answer_lower or '복호화' in answer_text_clean:
            explanation = "데이터 암호화: 민감한 데이터를 보호하기 위해 저장 및 전송 중 암호화가 필요합니다. AWS KMS를 사용하여 암호화 키를 관리할 수 있습니다."
        
        # 실험 및 추적
        elif 'experiment' in answer_lower or '실험' in answer_text_clean:
            explanation = "실험 추적: 다양한 모델 하이퍼파라미터와 구성을 시도하고 결과를 비교하는 과정입니다. 모델 성능을 최적화하는 데 필수적입니다."
        
        # 기본 해설
        else:
            explanation = "이 답변이 정답인 이유를 설명하는 상세한 해설입니다."
        
        if explanation:
            return f"{letter}. {answer_text_clean} ({explanation})"
    
    return answer_text

def enhance_questions():
    """questions.json 파일을 읽어서 선택지 한글 번역과 해설을 추가"""
    with open('data/questions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    enhanced_count = 0
    
    for q in data:
        enhanced = False
        
        # 영어 선택지 파싱
        question_en = q.get('question_en', '')
        en_choices = parse_choices(question_en)
        
        # 한글 선택지 생성
        should_translate = False
        if en_choices:
            if 'choices_ko' not in q:
                should_translate = True
            elif q.get('choices_ko'):
                # choices_ko가 있지만 영어로 되어 있거나 잘못된 번역(예: "학습ing")이 있는지 확인
                first_choice = list(q['choices_ko'].values())[0] if q['choices_ko'] else ""
                if first_choice:
                    # 영어만 있거나, 한글 뒤에 영어 접미사가 붙은 경우(예: "학습ing", "배포ment") 재번역
                    has_korean = any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in first_choice)
                    has_wrong_suffix = any(
                        re.search(r'[가-힣]+(ing|ment|tion|sion|ness|ity|ly|ed|er|est)\b', choice, re.IGNORECASE)
                        for choice in q['choices_ko'].values()
                    )
                    if not has_korean or has_wrong_suffix:
                        should_translate = True
        
        if should_translate:
            ko_choices = {}
            for letter, choice_en in en_choices.items():
                ko_choices[letter] = translate_choice_simple(choice_en)
            
            q['choices_ko'] = ko_choices
            enhanced = True
        
        # 해설 개선
        if 'answer' in q:
            original_answer = q['answer']
            enhanced_answer = enhance_answer_explanation(original_answer, question_en)
            if enhanced_answer != original_answer:
                q['answer'] = enhanced_answer
                enhanced = True
        
        if enhanced:
            enhanced_count += 1
    
    # 저장
    with open('data/questions.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"✅ {enhanced_count}개 문제가 개선되었습니다.")
    print(f"✅ 총 {len(data)}개 문제 처리 완료")

if __name__ == '__main__':
    enhance_questions()
