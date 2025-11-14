# Agentic AI 시스템 사용자 매뉴얼

> 버전: 1.0.0
> 최종 업데이트: 2025-11-14

## 목차

1. [시스템 개요](#시스템-개요)
2. [시작하기](#시작하기)
3. [Agent별 사용 가이드](#agent별-사용-가이드)
4. [웹 인터페이스 사용법](#웹-인터페이스-사용법)
5. [API 사용법](#api-사용법)
6. [트러블슈팅](#트러블슈팅)
7. [FAQ](#faq)

---

## 시스템 개요

Agentic AI는 IT 운영 업무를 자동화하기 위한 Multi-Agent 시스템입니다.

### 주요 기능

- **8개의 전문 AI Agent**: 각 업무 영역에 특화된 Agent
- **자연어 처리**: 자연어로 작업 요청 가능
- **실시간 모니터링**: 시스템 및 작업 상태 실시간 확인
- **Multi-agent 협업**: 복잡한 작업을 여러 Agent가 협력하여 처리

### 8개 Agent 소개

| Agent | 역할 | 주요 기능 |
|-------|------|-----------|
| Report Agent | 보고서 자동화 | 주간보고서, 회의록, 현황 조사 |
| Monitoring Agent | 시스템 모니터링 | Health Check, DB 점검, 로그 분석 |
| ITS Agent | 티켓 관리 | 인시던트 접수, 구성정보 관리 |
| DB Extract Agent | 데이터 추출 | 자연어 쿼리, 데이터 검증 |
| Change Management Agent | 변경 관리 | 배포 자동화, 패치 관리 |
| Business Support Agent | 사용자 지원 | 문의 응대, 담당자 조회 |
| SOP Agent | 장애 대응 | 장애 감지, 자동 조치 |
| Infrastructure Agent | 인프라 관리 | 성능 분석, Auto Scaling |

---

## 시작하기

### 1. 시스템 접속

웹 브라우저에서 다음 URL로 접속:
```
http://your-domain.com
```

기본 포트: `3000`

### 2. 대시보드 확인

로그인 후 메인 대시보드에서 다음 정보를 확인할 수 있습니다:

- **전체 작업 수**: 처리된 총 작업 건수
- **성공률**: 성공한 작업의 비율
- **활성 Agent 수**: 현재 사용 가능한 Agent 수
- **시스템 상태**: 전반적인 시스템 건강도

### 3. 첫 작업 실행

1. 좌측 메뉴에서 **"Agents"** 선택
2. 사용할 Agent 선택
3. 작업 유형 선택
4. 작업 데이터 입력 (JSON 형식)
5. **"Execute"** 버튼 클릭

---

## Agent별 사용 가이드

### Report Agent

**주간보고서 생성**

```json
{
  "report_type": "generate_weekly_report",
  "period": "2025-W46",
  "include_charts": true
}
```

**회의록 생성**

```json
{
  "report_type": "generate_meeting_minutes",
  "meeting_date": "2025-11-14",
  "attendees": ["김철수", "이영희"],
  "topics": ["프로젝트 진행 상황", "이슈 논의"]
}
```

### Monitoring Agent

**시스템 Health Check**

```json
{
  "check_type": "health_check",
  "target": "OrderManagement",
  "components": ["api", "database", "cache"]
}
```

**데이터베이스 점검**

```json
{
  "check_type": "database_check",
  "database": "production",
  "checks": ["connection", "slow_queries", "locks"]
}
```

### ITS Agent

**인시던트 생성**

```json
{
  "task_type": "create_incident",
  "title": "주문 시스템 응답 지연",
  "description": "평균 응답 시간이 5초를 초과합니다",
  "priority": "high",
  "category": "performance"
}
```

### DB Extract Agent

**자연어 쿼리**

```json
{
  "query": "지난 달 총 매출액과 주문 건수를 조회해주세요",
  "database": "analytics"
}
```

**데이터 검증**

```json
{
  "task_type": "data_validation",
  "table": "orders",
  "rules": {
    "total_amount": {"min": 0, "required": true},
    "order_date": {"type": "date", "required": true}
  }
}
```

### Change Management Agent

**배포 실행**

```json
{
  "deployment_type": "performance_deployment",
  "target_env": "production",
  "version": "v2.1.0",
  "rollback_enabled": true
}
```

### Business Support Agent

**사용법 문의**

```json
{
  "question": "비밀번호를 재설정하려면 어떻게 해야 하나요?",
  "user_email": "user@example.com"
}
```

**담당자 조회**

```json
{
  "task_type": "find_contact",
  "system": "OrderManagement",
  "role": "system_admin"
}
```

### SOP Agent

**장애 감지 및 조치**

```json
{
  "incident_type": "high_cpu_usage",
  "severity": "high",
  "target": "web-server-01",
  "auto_remediation": true
}
```

### Infrastructure Agent

**성능 분석**

```json
{
  "operation": "performance_analysis",
  "target": "api-server",
  "metrics": ["cpu", "memory", "response_time"],
  "period": "24h"
}
```

**Auto Scaling**

```json
{
  "operation": "auto_scaling",
  "resource": "web-server",
  "min_instances": 3,
  "max_instances": 10,
  "target_cpu": 70
}
```

---

## 웹 인터페이스 사용법

### 대시보드

실시간으로 시스템 상태를 모니터링할 수 있습니다.

- **Overview 카드**: 주요 메트릭 요약
- **작업 통계**: 상태별 작업 분포
- **시스템 리소스**: CPU, 메모리 사용률
- **Agent 통계**: Agent별 실행 현황

### Agent Selector

1. **Agent 선택**: 드롭다운에서 Agent 선택
2. **작업 유형**: 해당 Agent의 작업 유형 선택
3. **작업 데이터**: JSON 형식으로 데이터 입력
4. **실행**: Execute 버튼 클릭
5. **결과 확인**: 하단에 실행 결과 표시

### Task Monitor

실시간으로 작업 상태를 모니터링:

- **필터링**: 상태 또는 Agent별로 필터링
- **WebSocket**: 실시간 업데이트 자동 반영
- **상세 정보**: 작업 클릭 시 상세 결과 표시
- **삭제**: 완료된 작업 삭제 가능

---

## API 사용법

### 인증

모든 API 요청에는 API 키가 필요합니다:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://api.your-domain.com/api/agents/list
```

### Agent 목록 조회

```bash
GET /api/agents/list
```

### Agent 작업 실행

```bash
POST /api/agents/execute
Content-Type: application/json

{
  "agent_type": "monitoring",
  "task_type": "health_check",
  "task_data": {
    "target": "OrderManagement"
  },
  "user_id": "your_user_id"
}
```

### 작업 조회

```bash
GET /api/tasks/{task_id}
```

### 워크플로우 실행

여러 Agent를 순차적으로 실행:

```bash
POST /api/workflows/execute
Content-Type: application/json

{
  "workflow": [
    {
      "agent_type": "monitoring",
      "task": {
        "type": "health_check",
        "data": {"target": "OrderManagement"}
      }
    },
    {
      "agent_type": "report",
      "task": {
        "type": "system_status_report",
        "data": {"system": "OrderManagement"}
      }
    }
  ],
  "mode": "sequential"
}
```

---

## 트러블슈팅

### 작업이 실패합니다

**증상**: 작업 상태가 "failed"

**해결 방법**:
1. 작업 데이터 형식 확인
2. 에러 메시지 확인
3. Agent 로그 확인
4. 시스템 리소스 확인

### Agent가 응답하지 않습니다

**증상**: 작업이 "running" 상태에서 멈춤

**해결 방법**:
1. Agent 상태 확인: `/api/agents/{agent_name}/status`
2. 시스템 로그 확인
3. 타임아웃 설정 확인
4. Agent 재시작

### 대시보드가 업데이트되지 않습니다

**증상**: 실시간 데이터가 반영되지 않음

**해결 방법**:
1. WebSocket 연결 상태 확인
2. 브라우저 새로고침
3. 네트워크 연결 확인
4. 브라우저 콘솔 에러 확인

---

## FAQ

### Q1: 여러 Agent를 동시에 실행할 수 있나요?

**A**: 예, Workflow API를 사용하여 여러 Agent를 순차적 또는 병렬로 실행할 수 있습니다.

### Q2: 작업 결과를 어떻게 저장하나요?

**A**: 모든 작업 결과는 자동으로 데이터베이스에 저장됩니다. API를 통해 조회 가능합니다.

### Q3: 사용자별 작업 이력을 볼 수 있나요?

**A**: 예, `user_id` 필터를 사용하여 특정 사용자의 작업만 조회할 수 있습니다.

### Q4: Agent를 커스터마이징할 수 있나요?

**A**: BaseAgent를 상속하여 새로운 Agent를 개발할 수 있습니다. 개발 가이드를 참조하세요.

### Q5: 시스템 확장성은 어떻게 되나요?

**A**: Kubernetes Auto Scaling을 통해 자동으로 확장됩니다. 최대 10개 Pod까지 확장 가능합니다.

---

## 추가 도움말

- **운영 가이드**: [OPERATIONS_GUIDE.md](./OPERATIONS_GUIDE.md)
- **개발 문서**: [DEVELOPMENT_SPECIFICATION.md](../DEVELOPMENT_SPECIFICATION.md)
- **API 문서**: http://api.your-domain.com/docs
- **지원 문의**: support@your-domain.com
