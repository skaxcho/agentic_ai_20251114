# 유즈케이스 및 테스트 시나리오 상세 명세

## 목차
1. [Report Agent 유즈케이스](#1-report-agent-유즈케이스)
2. [Monitoring Agent 유즈케이스](#2-monitoring-agent-유즈케이스)
3. [ITS Agent 유즈케이스](#3-its-agent-유즈케이스)
4. [DB Extract Agent 유즈케이스](#4-db-extract-agent-유즈케이스)
5. [Change Management Agent 유즈케이스](#5-change-management-agent-유즈케이스)
6. [Biz Support Agent 유즈케이스](#6-biz-support-agent-유즈케이스)
7. [SOP Agent 유즈케이스](#7-sop-agent-유즈케이스)
8. [Infra Agent 유즈케이스](#8-infra-agent-유즈케이스)
9. [통합 E2E 시나리오](#9-통합-e2e-시나리오)

---

## 1. Report Agent 유즈케이스

### UC-R-01: 주간보고서 자동 작성

**목적**: 작업일지 파일들을 취합하여 주간보고서를 자동 생성

**사전 조건**:
- 작업일지 파일들이 OneDrive 또는 로컬에 존재
- 보고서 템플릿이 정의되어 있음

**입력**:
```json
{
  "task_type": "weekly_report",
  "source_files": [
    "/onedrive/work_logs/2025-11-06.md",
    "/onedrive/work_logs/2025-11-07.md",
    "/onedrive/work_logs/2025-11-08.md",
    "/onedrive/work_logs/2025-11-09.md",
    "/onedrive/work_logs/2025-11-10.md"
  ],
  "output_path": "/onedrive/reports/weekly_2025-W45.md",
  "template": "standard_weekly_report"
}
```

**처리 프로세스**:
1. 템플릿 로드 및 필요 데이터 항목 확인
2. 각 작업일지 파일 읽기 (OneDriveTool 사용)
3. 주요 작업 내용 추출 및 분류
4. 누락된 정보 확인 시 사용자에게 질의
5. 보고서 생성 (LLM을 통한 자연어 요약)
6. 사용자 검토 요청
7. 승인 후 OneDrive에 저장

**출력**:
```markdown
# 주간 업무 보고서 (2025년 11월 2주차)

## 주요 수행 업무
- AI Agent 플랫폼 설계 및 아키텍처 수립
- Monitoring Agent 개발 완료
- 테스트 시나리오 작성

## 주요 이슈 및 해결
- Azure OpenAI API Rate Limit 문제 → Retry 로직 추가로 해결
- Vector DB 검색 성능 저하 → 인덱스 최적화로 해결

## 다음 주 계획
- Report Agent 개발 착수
- RAG 성능 테스트 진행
```

**검증 기준**:
| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| 작업 내용 완전성 | 모든 작업일지 내용이 반영됨 | 수동 검토 |
| 문서 구조 | 템플릿 구조 준수 | 자동 검증 |
| 생성 시간 | 5분 이내 | 시간 측정 |
| 정확도 | 사용자 만족도 > 4/5 | 설문 조사 |

**테스트 시나리오**:

```python
# tests/agents/test_report_agent.py

async def test_weekly_report_generation():
    """주간보고서 자동 생성 테스트"""
    # Given
    agent = ReportAgent()
    input_data = {
        "task_type": "weekly_report",
        "source_files": [
            "tests/fixtures/work_log_mon.md",
            "tests/fixtures/work_log_tue.md",
            "tests/fixtures/work_log_wed.md",
            "tests/fixtures/work_log_thu.md",
            "tests/fixtures/work_log_fri.md"
        ],
        "output_path": "/tmp/test_weekly_report.md"
    }

    # When
    start_time = time.time()
    result = await agent.execute_task(input_data)
    elapsed_time = time.time() - start_time

    # Then
    assert result.success == True
    assert elapsed_time < 300  # 5분 이내
    assert os.path.exists(result.output_path)

    # 보고서 내용 검증
    with open(result.output_path, 'r') as f:
        content = f.read()
        assert "주요 수행 업무" in content
        assert "주요 이슈" in content
        assert "다음 주 계획" in content

    # 작업일지 내용이 포함되었는지 확인
    assert "AI Agent" in content  # 예상 키워드
```

---

### UC-R-02: 회의록 자동 생성

**목적**: 회의 녹음 파일을 텍스트로 변환하고 회의록 생성

**사전 조건**:
- 회의 녹음 파일 존재 (mp3/wav 등)
- Speech-to-Text API 사용 가능

**입력**:
```json
{
  "task_type": "meeting_minutes",
  "audio_file": "/onedrive/recordings/meeting_2025-11-10.mp3",
  "meeting_info": {
    "title": "AI Agent 프로젝트 킥오프 회의",
    "date": "2025-11-10",
    "attendees": ["홍길동", "김철수", "이영희"]
  },
  "output_path": "/onedrive/minutes/meeting_2025-11-10.md"
}
```

**처리 프로세스**:
1. 음성 파일을 텍스트로 변환 (Azure Speech-to-Text)
2. 발화자 분리 (Speaker Diarization)
3. 회의 내용 분석 및 구조화
   - 주요 논의 사항
   - 결정 사항
   - 액션 아이템
4. 회의록 작성
5. 사용자 검토 및 승인
6. 저장

**출력**:
```markdown
# AI Agent 프로젝트 킥오프 회의

**일시**: 2025-11-10 14:00-15:30
**참석자**: 홍길동, 김철수, 이영희

## 논의 사항
1. 프로젝트 목표 및 범위 확인
   - 8개 AI Agent 구축
   - 16주 개발 일정

2. 기술 스택 선정
   - Crew AI vs Dify 논의 → Crew AI 선정

## 결정 사항
- 프로젝트 시작일: 2025-11-13
- 주간 회의: 매주 월요일 10:00

## 액션 아이템
- [ ] 홍길동: 개발 환경 세팅 (2025-11-13까지)
- [ ] 김철수: Azure OpenAI 계정 생성 (2025-11-14까지)
- [ ] 이영희: 요구사항 상세 문서 작성 (2025-11-15까지)
```

**검증 기준**:
| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| 음성 인식 정확도 | > 95% | WER (Word Error Rate) |
| 발화자 분리 정확도 | > 90% | DER (Diarization Error Rate) |
| 핵심 내용 추출 | 주요 논의/결정/액션 포함 | 수동 검토 |
| 생성 시간 | 10분 이내 (60분 회의 기준) | 시간 측정 |

---

### UC-R-03: 시스템 현황 조사 보고서 작성

**목적**: 다양한 소스에서 시스템 정보를 취합하여 현황 보고서 생성

**입력**:
```json
{
  "task_type": "system_status_report",
  "data_sources": [
    {"type": "file", "path": "/shared/system_info.xlsx"},
    {"type": "rag", "query": "시스템 구성 정보"},
    {"type": "db", "query": "SELECT * FROM systems WHERE status='active'"},
    {"type": "its", "query": "최근 1주일 인시던트"}
  ],
  "output_path": "/reports/system_status_2025-11.md"
}
```

**처리 프로세스**:
1. 각 데이터 소스에서 정보 수집
   - 파일: FileReaderTool
   - RAG: RAGService
   - DB: DBExtractAgent 호출
   - ITS: ITSAgent 호출
2. 데이터 통합 및 정합성 검증
3. 누락 정보 확인 및 사용자 질의
4. 보고서 생성
5. 검토 및 저장

**출력**: 시스템별 현황 정보가 포함된 보고서

**검증 기준**:
- 모든 데이터 소스에서 정보 수집 완료
- 데이터 정합성 검증 통과
- 보고서 구조 완전성

---

## 2. Monitoring Agent 유즈케이스

### UC-M-01: 서비스 Health Check

**목적**: 등록된 모든 시스템의 Health Check URL을 호출하여 가용성 점검

**입력**:
```json
{
  "task_type": "health_check",
  "targets": "all"  // 또는 특정 시스템 목록
}
```

**처리 프로세스**:
1. RAG에서 시스템 목록 및 Health Check URL 조회
2. 각 시스템에 HTTP GET 요청
3. 응답 코드 확인 (200 OK 여부)
4. 응답 시간 측정
5. 결과 집계 및 보고서 생성
6. 이상 발견 시 SOP Agent 호출

**시스템 메타정보 (RAG 저장)**:
```json
{
  "system_id": "sys-001",
  "name": "주문관리 시스템",
  "health_check_url": "https://order.example.com/health",
  "expected_response_time": 500,  // ms
  "critical": true
}
```

**출력**:
```json
{
  "timestamp": "2025-11-10T10:00:00Z",
  "total_systems": 25,
  "healthy": 24,
  "unhealthy": 1,
  "details": [
    {
      "system_id": "sys-001",
      "name": "주문관리 시스템",
      "status": "healthy",
      "response_code": 200,
      "response_time_ms": 345
    },
    {
      "system_id": "sys-012",
      "name": "결제 시스템",
      "status": "unhealthy",
      "response_code": 503,
      "response_time_ms": null,
      "error": "Service Unavailable"
    }
  ],
  "actions_taken": [
    "SOP Agent 호출: sys-012 장애 조치"
  ]
}
```

**검증 기준**:
| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| 점검 완료율 | 100% | 모든 시스템 점검 완료 |
| 오탐률 (False Positive) | < 5% | 수동 확인 |
| 검출율 (True Positive) | > 95% | 의도적 장애 주입 테스트 |
| 점검 소요 시간 | < 5분 (30개 시스템 기준) | 시간 측정 |

**테스트 시나리오**:

```python
async def test_health_check_all_systems():
    """전체 시스템 Health Check 테스트"""
    # Given
    agent = MonitoringAgent()

    # Mock 시스템 준비 (25개)
    mock_systems = setup_mock_systems(count=25, healthy=24, unhealthy=1)

    # When
    start_time = time.time()
    result = await agent.execute_task({"task_type": "health_check"})
    elapsed_time = time.time() - start_time

    # Then
    assert result.total_systems == 25
    assert result.healthy == 24
    assert result.unhealthy == 1
    assert elapsed_time < 300  # 5분 이내

    # 불량 시스템 확인
    unhealthy_system = next(d for d in result.details if d.status == "unhealthy")
    assert unhealthy_system.system_id == "sys-012"
    assert "SOP Agent" in result.actions_taken[0]
```

---

### UC-M-02: DB 접속 및 데이터 검증

**목적**: 모든 데이터베이스 접속 가능 여부 및 특정 데이터 존재 확인

**입력**:
```json
{
  "task_type": "db_health_check",
  "checks": [
    {
      "db_id": "db-order",
      "check_type": "connection"
    },
    {
      "db_id": "db-order",
      "check_type": "data_exists",
      "query": "SELECT COUNT(*) FROM orders WHERE created_at > NOW() - INTERVAL 1 HOUR",
      "expected_condition": "> 0"
    },
    {
      "db_id": "db-payment",
      "check_type": "lock_check"
    }
  ]
}
```

**처리 프로세스**:
1. 각 DB 접속 정보 조회 (AuthService)
2. 연결 테스트
3. 쿼리 실행 (해당하는 경우)
4. 결과 검증
5. 이상 발견 시 알림

**출력**:
```json
{
  "timestamp": "2025-11-10T10:05:00Z",
  "total_checks": 3,
  "passed": 2,
  "failed": 1,
  "details": [
    {
      "db_id": "db-order",
      "check_type": "connection",
      "status": "passed",
      "latency_ms": 12
    },
    {
      "db_id": "db-order",
      "check_type": "data_exists",
      "status": "failed",
      "result_count": 0,
      "expected": "> 0",
      "alert": "최근 1시간 내 주문 데이터 없음"
    },
    {
      "db_id": "db-payment",
      "check_type": "lock_check",
      "status": "passed",
      "locks_found": 0
    }
  ]
}
```

**검증 기준**:
- DB 접속 성공률 > 99%
- 데이터 검증 정확도 100%
- 평균 점검 시간 < 30초 (DB당)

---

### UC-M-03: 로그 파일 이상 탐지

**목적**: 서버 로그 파일에서 에러 및 경고 메시지 탐지

**입력**:
```json
{
  "task_type": "log_analysis",
  "target_servers": ["web-01", "web-02", "api-01"],
  "log_path": "/var/log/application.log",
  "time_range": "last_1_hour",
  "patterns": ["ERROR", "WARN", "Exception", "Failed"]
}
```

**처리 프로세스**:
1. 각 서버에 SSH 접속 (ServerAccessTool)
2. 로그 파일 읽기 (tail -n 1000)
3. 패턴 매칭으로 이상 로그 추출
4. LLM을 통한 로그 분석 (심각도 판단)
5. 결과 요약 및 보고

**출력**:
```json
{
  "timestamp": "2025-11-10T10:10:00Z",
  "total_servers": 3,
  "total_errors": 15,
  "total_warnings": 42,
  "critical_issues": [
    {
      "server": "api-01",
      "log_entry": "ERROR [2025-11-10 09:55:12] Database connection timeout",
      "severity": "critical",
      "occurrences": 5,
      "recommendation": "DB 접속 상태 점검 필요"
    }
  ],
  "summary": "api-01 서버에서 DB 연결 타임아웃 반복 발생"
}
```

**검증 기준**:
- 에러 로그 검출률 > 98%
- 심각도 분류 정확도 > 90%
- 분석 시간 < 5분 (서버당)

---

### UC-M-04: 스케줄 Job 실패 점검

**목적**: 정기 실행 Job(배치 작업, 인터페이스 등)의 실행 상태 점검

**입력**:
```json
{
  "task_type": "job_status_check",
  "check_method": "log_file",  // 또는 "db_query"
  "jobs": [
    {
      "job_id": "daily-order-batch",
      "schedule": "0 2 * * *",  // 매일 02:00
      "log_path": "/var/log/batch/order.log",
      "success_pattern": "Batch completed successfully"
    }
  ]
}
```

**처리 프로세스**:
1. 각 Job의 실행 예정 시간 확인
2. 로그 파일 또는 DB에서 실행 결과 조회
3. 성공/실패 판단
4. 실패 Job에 대한 상세 정보 수집
5. 알림 발송

**출력**:
```json
{
  "timestamp": "2025-11-10T10:15:00Z",
  "total_jobs": 10,
  "succeeded": 9,
  "failed": 1,
  "failed_jobs": [
    {
      "job_id": "daily-order-batch",
      "expected_time": "2025-11-10 02:00:00",
      "status": "failed",
      "error_message": "Connection refused to database",
      "last_success": "2025-11-09 02:00:00",
      "actions_taken": ["알림 발송", "SOP Agent 호출"]
    }
  ]
}
```

**검증 기준**:
- Job 상태 확인 정확도 100%
- 점검 주기 준수 (매일 정해진 시간)
- 실패 Job 즉시 감지 (< 5분)

---

## 3. ITS Agent 유즈케이스

### UC-I-01: 구성정보 현행화

**목적**: ITS(ServiceNow)에서 시스템 구성정보(CI) 업데이트

**입력**:
```json
{
  "task_type": "update_ci",
  "system_id": "sys-001",
  "changes": {
    "cpu": "16 vCPU",
    "memory": "64GB",
    "os_version": "Ubuntu 22.04 LTS"
  }
}
```

**처리 프로세스**:
1. ServiceNow에서 현재 CI 정보 조회
2. 변경 사항 확인
3. 사용자에게 변경 내용 확인 요청
4. 승인 후 ServiceNow CI 업데이트
5. 변경 이력 기록

**출력**:
```json
{
  "success": true,
  "ci_id": "ci_12345",
  "updated_fields": ["cpu", "memory", "os_version"],
  "timestamp": "2025-11-10T10:20:00Z"
}
```

**검증 기준**:
- ServiceNow 업데이트 성공률 100%
- 변경 이력 기록 정확도 100%

---

### UC-I-02: SSL 인증서 발급 요청

**목적**: SSL 인증서 발급 요청 티켓 자동 생성

**입력**:
```json
{
  "task_type": "ssl_certificate_request",
  "domain": "api.example.com",
  "certificate_type": "wildcard",
  "validity_period": "1 year",
  "requester": "홍길동"
}
```

**처리 프로세스**:
1. 도메인 정보 확인 (RAG에서 기존 인증서 정보 조회)
2. 발급 요청서 작성
3. 필요한 추가 정보 사용자에게 질의
4. ServiceNow에 티켓 생성
5. 티켓 번호 반환

**출력**:
```json
{
  "success": true,
  "ticket_id": "RITM0001234",
  "status": "submitted",
  "estimated_completion": "2025-11-15"
}
```

**검증 기준**:
- 티켓 생성 성공률 100%
- 필수 정보 누락 없음

---

### UC-I-03: 인시던트 자동 접수

**목적**: 장애 발생 시 자동으로 인시던트 티켓 생성

**입력**:
```json
{
  "task_type": "create_incident",
  "source": "monitoring_agent",
  "incident_info": {
    "system_id": "sys-012",
    "system_name": "결제 시스템",
    "severity": "critical",
    "description": "Health Check 실패 - 503 Service Unavailable",
    "detected_at": "2025-11-10T10:00:00Z"
  }
}
```

**처리 프로세스**:
1. 유사 인시던트 검색 (중복 방지)
2. 인시던트 티켓 작성
3. 심각도에 따라 담당자 자동 배정
4. ServiceNow에 티켓 생성
5. 관련자에게 알림 발송

**출력**:
```json
{
  "success": true,
  "incident_id": "INC0001234",
  "assigned_to": "김철수",
  "priority": "P1",
  "status": "assigned",
  "notification_sent": ["김철수", "이영희"]
}
```

**검증 기준**:
- 티켓 생성 시간 < 1분
- 담당자 배정 정확도 > 95%
- 중복 티켓 방지율 > 98%

---

## 4. DB Extract Agent 유즈케이스

### UC-D-01: 자연어 쿼리 생성 및 실행

**목적**: 자연어 질문을 SQL 쿼리로 변환하여 실행

**입력**:
```json
{
  "task_type": "natural_language_query",
  "question": "최근 1주일간 주문 금액이 100만원 이상인 고객 목록을 조회해줘",
  "database": "order_db"
}
```

**처리 프로세스**:
1. RAG에서 order_db 스키마 조회
2. 자연어 → SQL 변환 (LLM 사용)
   ```sql
   SELECT c.customer_id, c.name, SUM(o.amount) as total_amount
   FROM customers c
   JOIN orders o ON c.customer_id = o.customer_id
   WHERE o.created_at >= NOW() - INTERVAL 7 DAY
   GROUP BY c.customer_id, c.name
   HAVING SUM(o.amount) >= 1000000
   ORDER BY total_amount DESC;
   ```
3. 생성된 SQL을 사용자에게 확인 요청
4. 승인 후 쿼리 실행
5. 결과 반환

**출력**:
```json
{
  "success": true,
  "query": "SELECT c.customer_id, c.name, SUM(o.amount) as total_amount ...",
  "execution_time_ms": 245,
  "row_count": 15,
  "results": [
    {
      "customer_id": 1001,
      "name": "홍길동",
      "total_amount": 2500000
    },
    {
      "customer_id": 1015,
      "name": "김철수",
      "total_amount": 1800000
    }
  ]
}
```

**검증 기준**:
| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| SQL 생성 정확도 | > 85% | 수동 검토 |
| SQL 실행 성공률 | > 95% | 자동 테스트 |
| 결과 정확도 | 100% | Ground truth 비교 |

**테스트 시나리오**:

```python
async def test_natural_language_query():
    """자연어 쿼리 생성 및 실행 테스트"""
    # Given
    agent = DBExtractAgent()
    question = "최근 1주일간 주문 금액이 100만원 이상인 고객 목록"

    # When
    result = await agent.execute_task({
        "task_type": "natural_language_query",
        "question": question,
        "database": "test_order_db"
    })

    # Then
    assert result.success == True
    assert "SELECT" in result.query.upper()
    assert "SUM" in result.query.upper()
    assert result.row_count > 0

    # SQL 구문 유효성 검증
    assert validate_sql_syntax(result.query) == True
```

---

### UC-D-02: 데이터 정합성 검증

**목적**: 테이블 간 참조 무결성 및 데이터 일관성 검증

**입력**:
```json
{
  "task_type": "data_integrity_check",
  "database": "order_db",
  "checks": [
    {
      "name": "orphan_orders",
      "description": "고객 정보가 없는 주문 확인",
      "query": "SELECT COUNT(*) FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id WHERE c.customer_id IS NULL"
    },
    {
      "name": "negative_amounts",
      "description": "음수 금액 주문 확인",
      "query": "SELECT COUNT(*) FROM orders WHERE amount < 0"
    }
  ]
}
```

**처리 프로세스**:
1. 각 검증 쿼리 실행
2. 결과 분석
3. 이상 데이터 발견 시 상세 정보 수집
4. 보고서 생성

**출력**:
```json
{
  "timestamp": "2025-11-10T10:30:00Z",
  "total_checks": 2,
  "passed": 1,
  "failed": 1,
  "details": [
    {
      "name": "orphan_orders",
      "status": "failed",
      "count": 5,
      "severity": "high",
      "sample_ids": [1234, 1235, 1236]
    },
    {
      "name": "negative_amounts",
      "status": "passed",
      "count": 0
    }
  ],
  "recommendations": [
    "orphan_orders: 5건의 고아 주문 데이터 정리 필요"
  ]
}
```

**검증 기준**:
- 정합성 검사 완료율 100%
- 이상 데이터 검출 정확도 > 99%

---

### UC-D-03: 복잡한 통계 쿼리 생성

**목적**: 월별 매출 분석 등 복잡한 통계 쿼리 자동 생성

**입력**:
```json
{
  "task_type": "statistical_query",
  "question": "2024년 월별 매출 추이와 전년 대비 증감률을 보여줘",
  "database": "order_db"
}
```

**처리 프로세스**:
1. 스키마 조회
2. 복잡한 SQL 생성 (WITH, WINDOW FUNCTION 등 활용)
3. 사용자 확인
4. 쿼리 실행
5. 결과를 차트로 시각화 (선택적)

**출력**:
```json
{
  "success": true,
  "query": "WITH monthly_sales AS (...) SELECT ...",
  "results": [
    {
      "month": "2024-01",
      "sales": 50000000,
      "yoy_growth": 15.2
    },
    {
      "month": "2024-02",
      "sales": 55000000,
      "yoy_growth": 18.5
    }
  ],
  "chart_url": "/charts/monthly_sales_2024.png"
}
```

**검증 기준**:
- 복잡한 쿼리 생성 정확도 > 80%
- 통계 결과 정확도 100%

---

## 5. Change Management Agent 유즈케이스

### UC-C-01: 성능 개선 배포 (End-to-End)

**목적**: 성능 이슈 분석부터 배포 완료까지 전체 프로세스 자동화

**입력**:
```json
{
  "task_type": "performance_improvement_deployment",
  "request": "A 시스템 CPU/MEM 조정 후 배포",
  "target_system": "sys-001",
  "changes": {
    "cpu": "16 vCPU → 24 vCPU",
    "memory": "32GB → 48GB"
  }
}
```

**처리 프로세스**:

**Step 1: 변경 분석**
- Infra Agent에게 현재 성능 분석 요청
- 변경 필요성 확인

**Step 2: 변경계획서 작성** (Report Agent 활용)
- 변경 목적, 범위, 절차, 롤백 계획 작성

**Step 3: 테스트 시나리오 생성**
- 배포 전 테스트 항목 정의

**Step 4: 승인 요청** (ITS Agent 활용)
- ServiceNow에 변경 요청 티켓 생성
- 승인자에게 알림

**Step 5: 테스트 실행**
- 개발 환경에서 테스트
- 결과 기록

**Step 6: 배포 승인 대기**
- 승인 완료 시 다음 단계 진행

**Step 7: 배포 실행**
- DevOps Tool을 통해 배포
- 배포 로그 기록

**Step 8: 배포 후 점검** (Monitoring Agent 활용)
- Health Check
- 성능 메트릭 확인
- 에러 로그 확인

**Step 9: 최종 보고서 작성** (Report Agent 활용)
- 전체 과정 요약
- 결과 및 성과 기록

**출력**:
```json
{
  "success": true,
  "change_id": "CHG0001234",
  "execution_time_minutes": 45,
  "steps_completed": [
    {
      "step": "분석",
      "agent": "infra",
      "status": "completed",
      "duration_minutes": 5
    },
    {
      "step": "계획서 작성",
      "agent": "report",
      "status": "completed",
      "duration_minutes": 3
    },
    {
      "step": "승인",
      "agent": "its",
      "status": "completed",
      "duration_minutes": 10
    },
    {
      "step": "배포",
      "agent": "infra",
      "status": "completed",
      "duration_minutes": 15
    },
    {
      "step": "점검",
      "agent": "monitoring",
      "status": "completed",
      "duration_minutes": 10
    },
    {
      "step": "보고서",
      "agent": "report",
      "status": "completed",
      "duration_minutes": 2
    }
  ],
  "performance_improvement": {
    "cpu_usage_before": "92%",
    "cpu_usage_after": "68%",
    "response_time_improvement": "35%"
  },
  "final_report_path": "/reports/change_CHG0001234.md"
}
```

**검증 기준**:
| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| 전체 프로세스 완료 | 모든 단계 성공 | 각 단계 status 확인 |
| 완료 시간 | < 60분 | 시간 측정 |
| Agent 협업 성공률 | 100% | Agent 간 데이터 전달 확인 |
| 배포 후 안정성 | 에러율 증가 없음 | 모니터링 데이터 비교 |

**테스트 시나리오**:

```python
async def test_e2e_change_management():
    """E2E 변경관리 프로세스 테스트"""
    # Given
    agent = ChangeManagementAgent()
    mock_approval_callback = lambda: approve_after_delay(10)  # 10초 후 자동 승인

    # When
    start_time = time.time()
    result = await agent.execute_task({
        "task_type": "performance_improvement_deployment",
        "target_system": "test-sys-001",
        "changes": {"cpu": "8 → 12", "memory": "16GB → 24GB"}
    })
    elapsed_time = time.time() - start_time

    # Then
    assert result.success == True
    assert elapsed_time < 3600  # 60분 이내
    assert len(result.steps_completed) == 6

    # 각 단계 검증
    for step in result.steps_completed:
        assert step.status == "completed"

    # 최종 보고서 존재 확인
    assert os.path.exists(result.final_report_path)
```

---

### UC-C-02: 긴급 패치 배포

**목적**: 보안 패치 등 긴급 배포 프로세스 간소화

**입력**:
```json
{
  "task_type": "emergency_patch",
  "patch_info": {
    "name": "Security Patch CVE-2024-1234",
    "urgency": "critical",
    "target_systems": ["sys-001", "sys-002", "sys-003"]
  }
}
```

**처리 프로세스**:
- 일부 단계 생략 (긴급)
- 승인 프로세스 간소화
- 배포 후 모니터링 강화

**검증 기준**:
- 배포 완료 시간 < 30분
- 롤백 가능 여부 확인

---

### UC-C-03: 정기 변경 프로세스

**목적**: 계획된 정기 변경 (월간 패치 등)

**입력**:
```json
{
  "task_type": "scheduled_change",
  "schedule": "2025-11-15 02:00:00",
  "changes": [...]
}
```

**처리 프로세스**:
- 전체 프로세스 준수
- 사전 알림 발송
- 예정 시간에 자동 실행

**검증 기준**:
- 예정 시간 정확도 (±5분)
- 사전 알림 발송 100%

---

## 6. Biz Support Agent 유즈케이스

### UC-B-01: 사용법 문의 응대

**목적**: 시스템 사용법에 대한 질문에 답변

**입력**:
```json
{
  "question": "주문 시스템에서 배송지 변경은 어떻게 해?"
}
```

**처리 프로세스**:
1. RAG에서 관련 매뉴얼 검색
2. 컨텍스트 기반 답변 생성
3. 스크린샷 또는 링크 포함 (가능한 경우)
4. 답변 제공
5. 추가 질문 대기

**출력**:
```json
{
  "answer": "주문 시스템에서 배송지 변경 방법:\n\n1. 주문 내역 메뉴 진입\n2. 변경할 주문 선택\n3. '배송지 변경' 버튼 클릭\n4. 새 배송지 입력 후 저장\n\n※ 주의: 배송 준비 단계 이후에는 변경 불가합니다.",
  "confidence": 0.95,
  "source_documents": [
    "주문시스템_사용자매뉴얼_v2.1.pdf (페이지 15-16)"
  ],
  "related_links": [
    "http://manual.example.com/order/change-address"
  ]
}
```

**검증 기준**:
| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| 답변 정확도 | > 90% | 사용자 피드백 (정확함/부정확함) |
| 응답 시간 | < 3초 | 시간 측정 |
| RAG 검색 관련도 | Confidence > 0.8 | Relevance Score |

---

### UC-B-02: 담당자 정보 조회

**목적**: 시스템 담당자 정보 제공

**입력**:
```json
{
  "question": "A 시스템 담당자는 누구야?"
}
```

**처리 프로세스**:
1. 시스템 이름 추출 ("A 시스템")
2. RAG에서 담당자 정보 검색
3. 답변 생성

**출력**:
```json
{
  "answer": "A 시스템 담당자:\n\n- **주 담당**: 김철수 (chulsoo.kim@example.com, 내선 1234)\n- **부 담당**: 이영희 (younghee.lee@example.com, 내선 1235)\n\n업무 시간: 평일 09:00-18:00",
  "confidence": 0.98
}
```

**검증 기준**:
- 정보 정확도 100% (최신 정보 유지 필요)
- 응답 시간 < 2초

---

### UC-B-03: 계정 발급 요청 연계

**목적**: 계정 발급 요청을 ITS로 연계

**입력**:
```json
{
  "question": "B 시스템 계정 발급 신청하고 싶어"
}
```

**처리 프로세스**:
1. 의도 파악 (계정 발급 요청)
2. 필요한 정보 수집 (사용자 정보, 권한 레벨 등)
3. ITS Agent 호출하여 티켓 생성
4. 티켓 번호 안내

**출력**:
```json
{
  "answer": "B 시스템 계정 발급 요청이 접수되었습니다.\n\n- **티켓 번호**: RITM0001235\n- **예상 처리 시간**: 1영업일\n- **처리 담당자**: 홍길동\n\n진행 상황은 ServiceNow에서 확인하실 수 있습니다.",
  "ticket_id": "RITM0001235"
}
```

**검증 기준**:
- ITS 티켓 생성 성공률 100%
- 필요 정보 수집 완전성 > 95%

---

## 7. SOP Agent 유즈케이스

### UC-S-01: 장애 자동 감지 및 조치

**목적**: Monitoring Agent 결과를 분석하여 장애 조치 가이드 제공

**입력** (Monitoring Agent로부터):
```json
{
  "source": "monitoring_agent",
  "alert": {
    "system_id": "sys-012",
    "system_name": "결제 시스템",
    "issue": "Health Check 실패",
    "severity": "critical",
    "details": {
      "response_code": 503,
      "error_message": "Service Unavailable"
    }
  }
}
```

**처리 프로세스**:
1. 장애 증상 분석
2. RAG에서 유사 장애 사례 검색
3. SOP 문서 참조
4. 조치 가이드 생성
5. 자동 조치 가능 여부 판단
6. 승인 후 자동 조치 실행 또는 가이드 제공
7. 장애 전파

**출력**:
```json
{
  "incident_id": "INC0001234",
  "analysis": {
    "issue_type": "서비스 중단",
    "probable_cause": "Database 연결 실패",
    "confidence": 0.85
  },
  "remediation_guide": {
    "steps": [
      {
        "step": 1,
        "action": "Database 접속 상태 확인",
        "command": "telnet db-server 5432",
        "auto_executable": true
      },
      {
        "step": 2,
        "action": "Database 프로세스 재시작",
        "command": "sudo systemctl restart postgresql",
        "auto_executable": true,
        "requires_approval": true
      },
      {
        "step": 3,
        "action": "서비스 재시작",
        "command": "kubectl rollout restart deployment payment-service",
        "auto_executable": true,
        "requires_approval": true
      }
    ],
    "estimated_recovery_time": "10분"
  },
  "similar_incidents": [
    {
      "incident_id": "INC0000987",
      "date": "2025-10-15",
      "resolution": "Database connection pool 설정 조정으로 해결"
    }
  ],
  "actions_taken": [
    "Step 1 자동 실행 완료 - DB 접속 불가 확인",
    "Step 2 승인 대기 중",
    "장애 알림 발송 (SMS/Email)"
  ],
  "notifications_sent": [
    {"channel": "sms", "recipient": "010-1234-5678", "status": "sent"},
    {"channel": "email", "recipient": "oncall@example.com", "status": "sent"},
    {"channel": "slack", "channel": "#ops-alerts", "status": "sent"}
  ]
}
```

**검증 기준**:
| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| 장애 원인 분석 정확도 | > 80% | 사후 검토 |
| 조치 가이드 적절성 | > 90% | 운영자 평가 |
| 알림 발송 시간 | < 1분 | 시간 측정 |
| 자동 조치 성공률 | > 85% | 자동 테스트 |

**테스트 시나리오**:

```python
async def test_incident_auto_remediation():
    """장애 자동 조치 테스트"""
    # Given
    agent = SOPAgent()
    mock_alert = {
        "system_id": "test-sys-012",
        "issue": "Health Check 실패",
        "severity": "critical"
    }

    # Mock 자동 조치 함수
    mock_execute_command = AsyncMock(return_value={"success": True})

    # When
    result = await agent.execute_task({
        "source": "monitoring_agent",
        "alert": mock_alert
    })

    # Then
    assert result.incident_id is not None
    assert result.analysis.confidence > 0.7
    assert len(result.remediation_guide.steps) > 0
    assert len(result.notifications_sent) > 0

    # 알림 발송 확인
    for notification in result.notifications_sent:
        assert notification.status == "sent"
```

---

### UC-S-02: 유사 장애 사례 검색

**목적**: 현재 장애와 유사한 과거 사례 및 해결 방법 검색

**입력**:
```json
{
  "task_type": "search_similar_incidents",
  "current_incident": {
    "symptoms": "CPU 사용률 100%, 응답 시간 지연",
    "system": "웹 서버"
  }
}
```

**처리 프로세스**:
1. 장애 증상을 임베딩으로 변환
2. Vector DB에서 유사도 검색
3. 상위 5개 유사 사례 반환
4. 각 사례의 해결 방법 요약

**출력**:
```json
{
  "similar_incidents": [
    {
      "incident_id": "INC0000876",
      "similarity_score": 0.92,
      "date": "2025-09-20",
      "symptoms": "CPU 100%, 메모리 누수",
      "root_cause": "무한 루프 버그",
      "resolution": "애플리케이션 재시작 및 패치 적용",
      "resolution_time": "30분"
    },
    {
      "incident_id": "INC0000654",
      "similarity_score": 0.88,
      "date": "2025-08-10",
      "symptoms": "CPU 과부하, 슬로우 쿼리",
      "root_cause": "DB 쿼리 최적화 부족",
      "resolution": "인덱스 추가 및 쿼리 튜닝",
      "resolution_time": "2시간"
    }
  ]
}
```

**검증 기준**:
- 유사도 점수 정확도 (수동 검증)
- 검색 시간 < 5초
- Relevance > 0.8인 사례 반환

---

### UC-S-03: 장애 전파 및 보고

**목적**: 장애 발생 시 관련자에게 즉시 알림 및 보고서 작성

**입력**:
```json
{
  "task_type": "incident_notification",
  "incident_id": "INC0001234",
  "notification_targets": "auto"  // 자동으로 대상자 선정
}
```

**처리 프로세스**:
1. RAG에서 장애 대상 시스템의 알림 대상자 조회
2. 알림 템플릿 생성
3. 채널별 알림 발송 (SMS/Email/Slack 등)
4. 발송 결과 기록

**출력**:
```json
{
  "notifications_sent": [
    {
      "channel": "sms",
      "recipient": "010-1234-5678 (당직자)",
      "status": "sent",
      "timestamp": "2025-11-10T10:00:15Z"
    },
    {
      "channel": "email",
      "recipient": "team-ops@example.com",
      "status": "sent",
      "timestamp": "2025-11-10T10:00:16Z"
    },
    {
      "channel": "slack",
      "channel": "#critical-alerts",
      "status": "sent",
      "timestamp": "2025-11-10T10:00:17Z"
    }
  ],
  "report_generated": "/reports/incident_INC0001234.md"
}
```

**검증 기준**:
- 알림 발송 성공률 > 98%
- 발송 지연 시간 < 30초
- 대상자 선정 정확도 > 95%

---

## 8. Infra Agent 유즈케이스

### UC-F-01: 성능 분석 및 진단

**목적**: 시스템 성능 메트릭 수집 및 분석, 개선 방안 제시

**입력**:
```json
{
  "task_type": "performance_analysis",
  "target_system": "sys-001",
  "time_range": "last_7_days"
}
```

**처리 프로세스**:
1. Monitoring Agent를 통해 성능 메트릭 수집
   - CPU, Memory, Disk I/O, Network
2. 클라우드 프로바이더 API로 상세 메트릭 조회
3. LLM을 통한 성능 분석
4. 병목 구간 식별
5. 개선 방안 제시

**출력**:
```json
{
  "system_id": "sys-001",
  "analysis_period": "2025-11-03 ~ 2025-11-10",
  "current_metrics": {
    "cpu_avg": 85,
    "cpu_peak": 98,
    "memory_avg": 78,
    "memory_peak": 92,
    "disk_io_avg": 450,
    "network_latency_avg": 120
  },
  "bottlenecks": [
    {
      "resource": "CPU",
      "severity": "high",
      "description": "피크 시간대(14:00-16:00) CPU 사용률 95% 이상 지속",
      "impact": "응답 시간 2배 증가"
    },
    {
      "resource": "Memory",
      "severity": "medium",
      "description": "메모리 사용률 지속적 증가 추세",
      "impact": "OOM 위험 잠재"
    }
  ],
  "recommendations": [
    {
      "priority": 1,
      "action": "CPU 리소스 증설",
      "details": "16 vCPU → 24 vCPU",
      "expected_improvement": "피크 시간대 응답 시간 40% 개선 예상"
    },
    {
      "priority": 2,
      "action": "메모리 누수 점검",
      "details": "애플리케이션 프로파일링 필요"
    },
    {
      "priority": 3,
      "action": "Auto Scaling 설정",
      "details": "CPU 80% 이상 시 자동 스케일 아웃"
    }
  ],
  "estimated_cost": {
    "current_monthly": "$1,200",
    "after_optimization": "$1,650",
    "increase": "$450"
  }
}
```

**검증 기준**:
| 항목 | 기준 | 측정 방법 |
|------|------|-----------|
| 병목 구간 식별 정확도 | > 90% | 실제 성능 개선 결과로 검증 |
| 개선 방안 적절성 | > 85% | 운영자 평가 |
| 분석 완료 시간 | < 10분 | 시간 측정 |

---

### UC-F-02: Auto Scaling 실행

**목적**: 리소스 사용률에 따른 자동 스케일링

**입력**:
```json
{
  "task_type": "auto_scaling",
  "target_system": "sys-001",
  "action": "scale_out",
  "target_replicas": 5
}
```

**처리 프로세스**:
1. 현재 리소스 상태 확인
2. 스케일링 가능 여부 확인 (할당량, 비용 등)
3. 스케일링 계획 생성
4. 승인 후 실행 (Cloud API 호출)
5. 스케일링 결과 확인
6. Monitoring Agent를 통해 사후 점검

**출력**:
```json
{
  "success": true,
  "action": "scale_out",
  "before": {
    "replicas": 3,
    "cpu_usage": 92
  },
  "after": {
    "replicas": 5,
    "cpu_usage": 65
  },
  "execution_time_seconds": 180,
  "cost_impact": {
    "hourly_increase": "$2.5"
  }
}
```

**검증 기준**:
- 스케일링 성공률 > 98%
- 목표 리소스 사용률 달성 (±10%)
- 스케일링 완료 시간 < 5분

---

### UC-F-03: 패치 작업 자동화

**목적**: OS/미들웨어 패치 자동 적용

**입력**:
```json
{
  "task_type": "patch_application",
  "target_servers": ["web-01", "web-02", "api-01"],
  "patch_type": "security",
  "patch_id": "CVE-2024-1234"
}
```

**처리 프로세스**:
1. 패치 정보 확인
2. 대상 서버 백업 (스냅샷)
3. 패치 적용 순서 계획 (순차적, 최소 다운타임)
4. 각 서버에 패치 적용
5. 재시작 (필요 시)
6. Health Check
7. 패치 결과 보고

**출력**:
```json
{
  "success": true,
  "total_servers": 3,
  "patched": 3,
  "failed": 0,
  "details": [
    {
      "server": "web-01",
      "status": "success",
      "patch_time": "5분",
      "reboot_required": true,
      "reboot_completed": true
    },
    {
      "server": "web-02",
      "status": "success",
      "patch_time": "5분",
      "reboot_required": true,
      "reboot_completed": true
    },
    {
      "server": "api-01",
      "status": "success",
      "patch_time": "4분",
      "reboot_required": false
    }
  ],
  "total_downtime": "0분 (순차 패치)",
  "backup_snapshots": ["snap-001", "snap-002", "snap-003"]
}
```

**검증 기준**:
- 패치 성공률 > 95%
- 서비스 다운타임 최소화
- 롤백 가능 여부 확인

---

## 9. 통합 E2E 시나리오

### E2E-01: 성능 이슈 → 분석 → 배포 → 모니터링 (전체 흐름)

**시나리오 설명**: 성능 문제 감지부터 해결까지 모든 Agent 협업

**참여 Agent**: Monitoring → SOP → Infra → Change Management → Report

**단계별 흐름**:

```
[10:00] Monitoring Agent: CPU 90% 이상 감지
  ↓
[10:01] SOP Agent: 장애 상황 판단, 과거 사례 검색
  → 판단: "성능 리소스 부족"
  → 액션: Infra Agent 호출
  ↓
[10:05] Infra Agent: 성능 분석 실행
  → 결과: CPU 증설 필요 (16 → 24 vCPU)
  → 액션: Change Management Agent 호출
  ↓
[10:10] Change Management Agent: 변경 프로세스 시작
  ├─ [10:11] Report Agent: 변경계획서 작성
  ├─ [10:15] ITS Agent: 변경 승인 요청
  ├─ [10:25] 승인 완료 (10분 대기)
  ├─ [10:26] Infra Agent: DevOps 배포 실행
  ├─ [10:40] 배포 완료
  ├─ [10:41] Monitoring Agent: 배포 후 점검
  │   └─ CPU: 92% → 68%
  │   └─ 응답시간: 1200ms → 450ms
  └─ [10:45] Report Agent: 최종 보고서 작성
  ↓
[10:46] Notification: 관련자에게 완료 알림
```

**검증 시나리오**:

```python
async def test_e2e_performance_issue_to_resolution():
    """E2E: 성능 이슈 감지부터 해결까지"""

    # 초기 상태 설정
    mock_system = setup_mock_system(cpu_usage=92)

    # Step 1: Monitoring Agent가 이슈 감지
    monitoring_result = await trigger_monitoring_agent()
    assert monitoring_result.alerts[0].severity == "high"

    # Step 2: SOP Agent 자동 호출 확인
    await wait_for_agent_execution("sop")
    sop_result = get_agent_result("sop")
    assert "Infra Agent" in sop_result.actions_taken

    # Step 3: Infra Agent 성능 분석 확인
    await wait_for_agent_execution("infra")
    infra_result = get_agent_result("infra")
    assert infra_result.recommendations[0].action == "CPU 리소스 증설"

    # Step 4: Change Management Agent 실행 확인
    await wait_for_agent_execution("change_mgmt")
    change_result = get_agent_result("change_mgmt")
    assert change_result.success == True

    # Step 5: 각 하위 Agent 호출 확인
    assert "report" in change_result.agents_used
    assert "its" in change_result.agents_used
    assert "monitoring" in change_result.agents_used

    # Step 6: 최종 성능 개선 확인
    final_metrics = get_system_metrics(mock_system)
    assert final_metrics.cpu_usage < 75
    assert final_metrics.response_time < 600

    # Step 7: 보고서 생성 확인
    assert os.path.exists(change_result.final_report_path)

    # Step 8: 알림 발송 확인
    notifications = get_sent_notifications()
    assert len(notifications) > 0
```

**성공 기준**:
- 전체 프로세스 완료 시간: < 60분
- 모든 Agent 협업 성공
- 성능 개선 목표 달성: CPU < 75%, 응답시간 > 30% 개선
- 보고서 자동 생성 완료
- 알림 발송 100%

---

### E2E-02: 사용자 문의 → 티켓 생성 → 처리 → 완료

**시나리오 설명**: 사용자 문의부터 ITS 티켓 처리까지

**참여 Agent**: Biz Support → ITS

**단계별 흐름**:

```
[14:00] 사용자: "방화벽 오픈 어떻게 신청해?"
  ↓
[14:00] Biz Support Agent: RAG 검색
  → 답변 생성 및 제공
  ↓
[14:01] 사용자: "그럼 신청 진행해줘"
  ↓
[14:01] Biz Support Agent: ITS Agent 호출
  ↓
[14:02] ITS Agent: ServiceNow 티켓 생성
  → 티켓 번호: RITM0001234
  ↓
[14:02] Notification: 사용자에게 티켓 번호 안내
```

**검증 시나리오**:

```python
async def test_e2e_user_inquiry_to_ticket():
    """E2E: 사용자 문의부터 티켓 생성까지"""

    # Step 1: 사용자 질문
    response1 = await biz_support_agent.ask("방화벽 오픈 어떻게 신청해?")
    assert response1.confidence > 0.8
    assert "방화벽" in response1.answer

    # Step 2: 신청 요청
    response2 = await biz_support_agent.ask("그럼 신청 진행해줘")
    assert response2.ticket_id is not None
    assert response2.ticket_id.startswith("RITM")

    # Step 3: ITS Agent 호출 확인
    its_result = get_agent_result("its")
    assert its_result.ticket_created == True

    # Step 4: ServiceNow 티켓 확인 (Mock)
    ticket = get_servicenow_ticket(response2.ticket_id)
    assert ticket.status == "submitted"
```

**성공 기준**:
- 답변 제공 시간: < 3초
- 티켓 생성 시간: < 30초
- 티켓 정보 정확도: 100%

---

### E2E-03: 장애 감지 → 자동 조치 → 사후 보고

**시나리오 설명**: 장애 자동 복구 전체 흐름

**참여 Agent**: Monitoring → SOP → Infra → Report

**단계별 흐름**:

```
[03:00] Monitoring Agent: 서비스 Down 감지
  ↓
[03:00] SOP Agent: 자동 호출
  → 유사 장애 사례 검색
  → 자동 조치 계획 수립
  ↓
[03:02] SOP Agent: 자동 조치 실행 (승인 불요 - 긴급)
  1. DB 연결 확인
  2. 애플리케이션 재시작
  ↓
[03:05] Infra Agent: 재시작 실행
  ↓
[03:08] Monitoring Agent: Health Check
  → 정상 복구 확인
  ↓
[03:10] Report Agent: 장애 보고서 자동 작성
  ↓
[03:11] Notification: 담당자에게 장애 복구 알림
```

**검증 시나리오**:

```python
async def test_e2e_auto_incident_recovery():
    """E2E: 장애 자동 복구"""

    # 장애 주입
    inject_failure(system="payment-service", type="service_down")

    # Step 1: Monitoring Agent 감지
    await wait_for_alert(timeout=60)
    alert = get_latest_alert()
    assert alert.system == "payment-service"

    # Step 2: SOP Agent 자동 조치
    await wait_for_agent_execution("sop", timeout=120)
    sop_result = get_agent_result("sop")
    assert sop_result.auto_remediation_executed == True

    # Step 3: 복구 확인
    await wait_for_service_recovery(timeout=300)
    health = check_service_health("payment-service")
    assert health.status == "healthy"

    # Step 4: 보고서 생성 확인
    report = get_incident_report(sop_result.incident_id)
    assert report is not None
    assert report.resolution_time < 600  # 10분 이내

    # Step 5: 알림 확인
    notifications = get_sent_notifications()
    assert any(n.type == "incident_resolved" for n in notifications)
```

**성공 기준**:
- 장애 감지 시간: < 1분
- 자동 조치 완료 시간: < 10분
- 복구 성공률: > 80%
- 보고서 자동 생성 완료

---

## 10. 테스트 자동화 전략

### 10.1 단위 테스트

각 Agent별 핵심 기능 단위 테스트

```python
# tests/unit/agents/test_report_agent.py
class TestReportAgent:
    def test_parse_template(self):
        """템플릿 파싱 테스트"""
        pass

    def test_extract_work_logs(self):
        """작업일지 추출 테스트"""
        pass

    def test_generate_report(self):
        """보고서 생성 테스트"""
        pass
```

### 10.2 통합 테스트

Agent 간 협업 테스트

```python
# tests/integration/test_agent_collaboration.py
class TestAgentCollaboration:
    async def test_change_mgmt_calls_report_agent(self):
        """Change Mgmt Agent가 Report Agent 호출"""
        pass

    async def test_sop_calls_monitoring_agent(self):
        """SOP Agent가 Monitoring Agent 호출"""
        pass
```

### 10.3 E2E 테스트

전체 시나리오 테스트 (위 E2E 시나리오들)

### 10.4 성능 테스트

```python
# tests/performance/test_load.py
class TestPerformance:
    async def test_concurrent_agent_execution(self):
        """동시 Agent 실행 성능 테스트"""
        tasks = [
            execute_agent("monitoring"),
            execute_agent("biz_support"),
            execute_agent("report")
        ]
        results = await asyncio.gather(*tasks)
        # 성능 메트릭 검증
        pass
```

### 10.5 테스트 커버리지 목표

| 계층 | 목표 커버리지 |
|------|--------------|
| 공통 모듈 (Core) | > 90% |
| Agent 로직 | > 80% |
| API | > 85% |
| 전체 | > 80% |

---

## 11. 결론

본 문서는 8개 AI Agent의 26개 유즈케이스와 3개 E2E 시나리오를 상세히 정의했습니다.

**활용 방안**:
1. **개발 가이드**: 각 Agent 개발 시 참조
2. **테스트 시나리오**: QA 테스트 케이스로 직접 활용
3. **검증 기준**: 완료 조건 명확화
4. **사용자 매뉴얼**: 각 유즈케이스를 사용자 가이드로 전환

**다음 단계**:
- 각 유즈케이스별 테스트 코드 작성
- Mock 시스템 구축
- 점진적 유즈케이스 검증
