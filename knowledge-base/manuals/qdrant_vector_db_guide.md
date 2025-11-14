# Qdrant Vector Database 운영 가이드

## 개요
Qdrant는 고성능 벡터 유사도 검색 엔진입니다. RAG(Retrieval-Augmented Generation) 시스템의 핵심 컴포넌트로 사용됩니다.

## 시스템 구성
- **버전**: Qdrant latest
- **호스트**: localhost
- **HTTP 포트**: 6333
- **gRPC 포트**: 6334
- **저장소**: /qdrant/storage

## 컬렉션 구조

### 1. system_manuals
시스템 매뉴얼 및 기술 문서를 저장합니다.

**벡터 설정**:
- 차원: 1536 (text-embedding-ada-002)
- 거리 측정: Cosine similarity

**Payload 구조**:
```json
{
    "content": "문서 내용",
    "title": "문서 제목",
    "type": "manual",
    "filename": "azure_openai_guide.md"
}
```

### 2. incident_history
과거 장애 사례 및 해결 방법을 저장합니다.

**Payload 구조**:
```json
{
    "content": "장애 내용 및 해결 방법",
    "incident_id": "INC-2024-001",
    "severity": "critical",
    "resolved_at": "2024-01-15T10:30:00Z"
}
```

### 3. database_schemas
데이터베이스 스키마 및 테이블 정보를 저장합니다.

**Payload 구조**:
```json
{
    "content": "테이블 설명",
    "table_name": "tasks",
    "schema_name": "agentic_ai"
}
```

### 4. contact_information
담당자 및 연락처 정보를 저장합니다.

## 기본 작업

### 컬렉션 생성
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(host="localhost", port=6333)

client.create_collection(
    collection_name="system_manuals",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
    )
)
```

### 문서 삽입
```python
from qdrant_client.models import PointStruct

points = [
    PointStruct(
        id="doc-001",
        vector=[0.1, 0.2, ...],  # 1536 dimensions
        payload={
            "content": "문서 내용",
            "title": "문서 제목"
        }
    )
]

client.upsert(
    collection_name="system_manuals",
    points=points
)
```

### 유사도 검색
```python
results = client.search(
    collection_name="system_manuals",
    query_vector=[0.1, 0.2, ...],
    limit=5,
    score_threshold=0.7
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.payload['content']}")
```

## 성능 최적화

### 1. 인덱싱 최적화
- **HNSW 파라미터 조정**: m=16, ef_construct=100
- **Quantization**: Scalar quantization 사용 (메모리 절약)

### 2. 배치 처리
대량 문서 삽입 시 배치 처리 사용:
```python
batch_size = 100
for i in range(0, len(points), batch_size):
    batch = points[i:i+batch_size]
    client.upsert(collection_name="system_manuals", points=batch)
```

### 3. 필터 활용
검색 시 필터를 사용하여 성능 향상:
```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

filter_condition = Filter(
    must=[
        FieldCondition(
            key="type",
            match=MatchValue(value="manual")
        )
    ]
)

results = client.search(
    collection_name="system_manuals",
    query_vector=query_vector,
    query_filter=filter_condition
)
```

## 모니터링

### 컬렉션 정보 조회
```python
collection_info = client.get_collection("system_manuals")
print(f"Points count: {collection_info.points_count}")
print(f"Vectors size: {collection_info.config.params.vectors.size}")
```

### 클러스터 상태 확인
```bash
curl http://localhost:6333/cluster
```

### 메트릭 조회
```bash
curl http://localhost:6333/metrics
```

## 백업 및 복구

### 스냅샷 생성
```python
client.create_snapshot(collection_name="system_manuals")
```

### 스냅샷 목록 조회
```bash
curl http://localhost:6333/collections/system_manuals/snapshots
```

### 스냅샷 복구
1. Qdrant 중지
2. 스냅샷 파일을 storage 디렉토리에 복사
3. Qdrant 재시작

## 문제 해결

### 연결 실패
**증상**: Connection refused 오류
**해결 방법**:
1. Qdrant 서비스 상태 확인
   ```bash
   docker ps | grep qdrant
   ```
2. 포트 확인 (6333, 6334)
3. 방화벽 설정 확인

### 검색 결과 없음
**증상**: 검색 시 결과가 반환되지 않음
**해결 방법**:
1. 컬렉션에 문서가 존재하는지 확인
2. score_threshold 값 조정 (낮춤)
3. 쿼리 벡터가 올바른지 확인

### 메모리 부족
**증상**: Out of memory 오류
**해결 방법**:
1. Quantization 활성화
2. 불필요한 컬렉션 삭제
3. Docker 메모리 제한 증가

## 보안

### 1. API 키 설정
프로덕션 환경에서는 API 키 사용 권장:
```yaml
service:
  api_key: "your-secure-api-key"
```

### 2. 네트워크 접근 제어
- 필요한 IP만 접근 허용
- VPC 내부에서만 접근 가능하도록 설정

## 관련 문서
- Qdrant 공식 문서: https://qdrant.tech/documentation/
- RAG Service 가이드: knowledge-base/manuals/rag_service_guide.md

## 담당자
- Vector DB 관리자: vector-admin@company.com
- RAG 시스템 담당: ml-team@company.com
