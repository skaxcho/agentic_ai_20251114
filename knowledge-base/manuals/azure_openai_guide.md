# Azure OpenAI Service 사용 가이드

## 개요
Azure OpenAI Service는 Microsoft Azure에서 제공하는 OpenAI의 강력한 언어 모델에 대한 REST API 액세스를 제공합니다.

## 주요 기능
- GPT-4, GPT-3.5-Turbo 등 최신 언어 모델 지원
- 텍스트 생성, 요약, 번역 등 다양한 자연어 처리 작업
- 임베딩 생성 (text-embedding-ada-002)
- Function Calling 지원

## 시작하기

### 1. Azure OpenAI 리소스 생성
1. Azure Portal에 로그인
2. "리소스 만들기" 선택
3. "Azure OpenAI" 검색 및 선택
4. 구독, 리소스 그룹, 지역 선택
5. 가격 책정 계층 선택 (Standard)

### 2. 모델 배포
1. Azure OpenAI Studio 접속
2. "배포" 메뉴 선택
3. 배포할 모델 선택 (예: gpt-4, text-embedding-ada-002)
4. 배포 이름 지정
5. 배포 생성

### 3. API 키 및 엔드포인트 확인
1. Azure Portal에서 리소스 선택
2. "키 및 엔드포인트" 메뉴 선택
3. KEY 1 또는 KEY 2 복사
4. 엔드포인트 URL 복사

## API 사용 예시

### Python에서 사용하기
```python
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key="your-api-key",
    api_version="2024-02-01",
    azure_endpoint="https://your-resource.openai.azure.com/"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

## 모범 사례
1. **API 키 보안**: 환경 변수나 Azure Key Vault 사용
2. **Rate Limiting**: 요청 속도 제한 준수
3. **오류 처리**: Retry 로직 구현
4. **비용 관리**: 토큰 사용량 모니터링

## 문제 해결

### Rate Limit 초과
- 증상: 429 오류 발생
- 해결: 요청 간격 조정, Exponential backoff 적용

### Timeout 발생
- 증상: 응답 지연 또는 타임아웃
- 해결: timeout 파라미터 증가, 비동기 처리 고려

### 잘못된 API 키
- 증상: 401 Unauthorized 오류
- 해결: API 키 및 엔드포인트 재확인

## 관련 문서
- Azure OpenAI 공식 문서: https://learn.microsoft.com/azure/ai-services/openai/
- OpenAI API Reference: https://platform.openai.com/docs/

## 담당자
- 기술 지원: tech-support@company.com
- Azure 관리자: azure-admin@company.com
