# PostgreSQL 데이터베이스 운영 가이드

## 개요
PostgreSQL은 오픈소스 관계형 데이터베이스 관리 시스템입니다. 본 시스템에서는 메타데이터 및 작업 정보를 저장하는 데 사용됩니다.

## 시스템 구성
- **버전**: PostgreSQL 15
- **호스트**: localhost
- **포트**: 5432
- **데이터베이스**: agentic_ai
- **스키마**: agentic_ai

## 주요 테이블

### 1. tasks 테이블
Agent 작업 실행 기록을 저장합니다.

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    agent_name VARCHAR(100),
    task_type VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
);
```

**주요 컬럼**:
- `id`: 작업 고유 ID
- `agent_name`: Agent 이름
- `task_type`: 작업 유형
- `status`: 상태 (pending, running, completed, failed)
- `result`: 실행 결과 (JSONB)

### 2. agent_executions 테이블
상세한 Agent 실행 로그를 저장합니다.

**주요 컬럼**:
- `task_id`: 연결된 작업 ID
- `execution_start`: 실행 시작 시간
- `execution_end`: 실행 종료 시간
- `llm_calls`: LLM 호출 횟수
- `llm_total_tokens`: 총 토큰 사용량

### 3. users 테이블
시스템 사용자 정보를 저장합니다.

## 일반적인 쿼리

### 작업 상태 조회
```sql
SELECT agent_name, task_type, status, created_at
FROM tasks
WHERE status = 'pending'
ORDER BY created_at DESC;
```

### Agent 성능 통계
```sql
SELECT
    agent_name,
    COUNT(*) as total_executions,
    AVG(duration_seconds) as avg_duration,
    SUM(llm_total_tokens) as total_tokens
FROM agent_executions
WHERE execution_start >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY agent_name;
```

### 실패한 작업 조회
```sql
SELECT id, agent_name, task_type, error_message, created_at
FROM tasks
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

## 백업 및 복구

### 백업 생성
```bash
pg_dump -h localhost -U admin -d agentic_ai > backup_$(date +%Y%m%d).sql
```

### 백업 복구
```bash
psql -h localhost -U admin -d agentic_ai < backup_20240101.sql
```

## 성능 최적화

### 1. 인덱스 활용
주요 검색 컬럼에 인덱스가 생성되어 있습니다:
- `tasks.agent_name`
- `tasks.status`
- `tasks.created_at`

### 2. 쿼리 성능 분석
```sql
EXPLAIN ANALYZE
SELECT * FROM tasks WHERE agent_name = 'ReportAgent';
```

### 3. VACUUM 실행
정기적으로 VACUUM을 실행하여 성능을 유지합니다:
```sql
VACUUM ANALYZE tasks;
```

## 문제 해결

### 연결 실패
**증상**: "could not connect to server" 오류
**해결 방법**:
1. PostgreSQL 서비스 상태 확인
2. 방화벽 설정 확인
3. pg_hba.conf 설정 확인

### 느린 쿼리
**증상**: 쿼리 응답이 느림
**해결 방법**:
1. EXPLAIN ANALYZE로 실행 계획 확인
2. 필요한 인덱스 추가
3. 통계 정보 업데이트 (ANALYZE)

### 디스크 공간 부족
**증상**: "disk full" 오류
**해결 방법**:
1. 오래된 로그 정리
2. 불필요한 백업 파일 삭제
3. VACUUM FULL 실행

## 모니터링

### 활성 연결 수 확인
```sql
SELECT count(*) FROM pg_stat_activity;
```

### 데이터베이스 크기 확인
```sql
SELECT pg_size_pretty(pg_database_size('agentic_ai'));
```

### 테이블 크기 확인
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'agentic_ai'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 보안

### 1. 비밀번호 관리
- 강력한 비밀번호 사용
- 주기적인 비밀번호 변경
- .env 파일에 저장 (Git에 커밋 금지)

### 2. 접근 제어
- 최소 권한 원칙 적용
- IP 기반 접근 제어 (pg_hba.conf)

### 3. SSL 연결
프로덕션 환경에서는 SSL 연결 사용 권장

## 관련 문서
- PostgreSQL 공식 문서: https://www.postgresql.org/docs/
- 내부 DB 스키마 문서: knowledge-base/schemas/

## 담당자
- DB 관리자: dba@company.com
- 장애 대응: ops-team@company.com
