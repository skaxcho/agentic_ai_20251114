# Knowledge Base

이 디렉토리는 RAG (Retrieval-Augmented Generation) 시스템의 지식 베이스 데이터를 포함합니다.

## 디렉토리 구조

```
knowledge-base/
├── manuals/          # 시스템 매뉴얼 및 기술 문서
├── incidents/        # 장애 사례 및 해결 방법
├── schemas/          # 데이터베이스 스키마 정보
└── contacts/         # 담당자 및 연락처 정보
```

## 데이터 설명

### 1. Manuals (매뉴얼)
시스템 사용 가이드 및 기술 문서

- `azure_openai_guide.md`: Azure OpenAI Service 사용 가이드
- `postgresql_database_guide.md`: PostgreSQL 데이터베이스 운영 가이드
- `qdrant_vector_db_guide.md`: Qdrant Vector Database 운영 가이드

**형식**: Markdown (.md)

### 2. Incidents (장애 사례)
과거 발생한 장애 사례 및 해결 방법

- `incidents.json`: 12개의 실제 장애 사례 데이터

**포함 정보**:
- 장애 ID, 제목, 심각도
- 발생 시간, 해결 시간
- 근본 원인 분석
- 해결 방법
- 예방 대책

**형식**: JSON

### 3. Schemas (데이터베이스 스키마)
데이터베이스 테이블 구조 및 설명

- `database_schema.json`: PostgreSQL 테이블 스키마 정보

**포함 테이블**:
- tasks
- agent_executions
- users
- api_keys
- knowledge_base_metadata
- audit_logs

**형식**: JSON

### 4. Contacts (담당자 정보)
팀원 및 담당자 연락처

- `team_contacts.json`: 12명의 팀원 정보

**포함 정보**:
- 이름, 역할, 부서
- 이메일, 전화번호, Slack
- 담당 업무 및 전문 분야
- 근무 시간 및 긴급 연락 가능 여부

**형식**: JSON

## 지식 베이스 구축

### 1. 환경 준비

Docker Compose로 필요한 서비스 시작:
```bash
docker-compose up -d
```

### 2. 환경 변수 설정

`.env` 파일 생성 (`.env.example` 참고):
```bash
cp .env.example .env
# .env 파일을 편집하여 Azure OpenAI 설정 추가
```

### 3. 지식 베이스 인덱싱

```bash
# 기본 실행
python scripts/build_knowledge_base.py

# 기존 데이터 삭제 후 재구축
python scripts/build_knowledge_base.py --reset

# Dry run (실제 인덱싱 없이 데이터만 확인)
python scripts/build_knowledge_base.py --dry-run
```

### 4. 성능 테스트

```bash
python scripts/test_rag_performance.py
```

## Qdrant 컬렉션

인덱싱 후 생성되는 컬렉션:

| 컬렉션 이름 | 설명 | 문서 수 (예상) |
|------------|------|---------------|
| `agentic_ai_system_manuals` | 시스템 매뉴얼 | 3+ |
| `agentic_ai_incident_history` | 장애 사례 | 12 |
| `agentic_ai_database_schemas` | DB 스키마 | 6 |
| `agentic_ai_contact_information` | 담당자 정보 | 12 |

**벡터 설정**:
- 차원: 1536 (text-embedding-ada-002)
- 거리 측정: Cosine similarity

## 문서 추가 방법

### Markdown 문서 (매뉴얼)

1. `manuals/` 디렉토리에 `.md` 파일 추가
2. 첫 줄을 `# 제목` 형식으로 작성
3. `build_knowledge_base.py` 재실행

예시:
```markdown
# 새로운 기능 사용 가이드

## 개요
...
```

### JSON 데이터 (장애 사례, 스키마, 담당자)

1. 해당 JSON 파일에 새로운 항목 추가
2. JSON 형식 검증
3. `build_knowledge_base.py` 재실행

## 검색 쿼리 예시

### Python 코드
```python
from src.core.services.rag_service import get_rag_service

rag_service = get_rag_service()

# 의미 검색
results = rag_service.semantic_search(
    collection_type="manuals",
    query="Azure OpenAI 사용 방법",
    limit=5,
    score_threshold=0.7
)

# RAG 기반 질의응답
answer = rag_service.rag_query(
    query="데이터베이스 연결이 안 될 때 어떻게 하나요?",
    collection_types=["manuals", "incidents"]
)
```

## 데이터 업데이트 가이드라인

### 매뉴얼
- 기술 변경사항이 있을 때 즉시 업데이트
- 명확하고 구체적인 예시 포함
- 문제 해결(Troubleshooting) 섹션 필수

### 장애 사례
- 모든 중요 장애는 24시간 이내 문서화
- 근본 원인 분석(Root Cause Analysis) 필수
- 재발 방지 대책 포함

### 스키마 정보
- 데이터베이스 스키마 변경 시 즉시 업데이트
- 샘플 쿼리 포함

### 담당자 정보
- 인사 이동, 조직 변경 시 즉시 업데이트
- 긴급 연락처 정보 최신 상태 유지

## 성능 목표

- **검색 응답 시간**: < 3초
- **검색 정확도 (Top Score)**: > 0.8
- **관련성 점수**: > 0.7
- **시스템 가용성**: > 99%

## 문의

- 지식 베이스 관리: data-team@company.com
- 기술 지원: tech-support@company.com
