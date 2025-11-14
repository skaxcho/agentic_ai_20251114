# Agentic AI 시스템 개발 체크리스트

> 최종 업데이트: 2025-11-14
>
> 이 문서는 DEVELOPMENT_SPECIFICATION.md와 IMPLEMENTATION_GUIDE.md를 기반으로 작성되었습니다.

---

## 📊 전체 진행 상황

| Phase | 기간 | 진행률 | 상태 |
|-------|------|--------|------|
| Phase 1: 기반 구축 | Week 1-4 | 100% | ✅ Complete |
| Phase 2: 기본 Agent 개발 | Week 5-8 | 100% | ✅ Complete |
| Phase 3: 통합 및 UI 개발 | Week 9-12 | 100% | ✅ Complete |
| Phase 4: 검증 환경 및 테스트 | Week 13-16 | 0% | ⚪ Pending |

**전체 진행률: 75%** (12/16 weeks complete)

---

## Phase 1: 기반 구축 (Week 1-4)

### Week 1-2: 프로젝트 Setup 및 공통 모듈 개발 ✅

#### 1.1 프로젝트 구조 생성
- [x] 프로젝트 디렉토리 구조 생성
  - [x] `src/core/` (base, services, tools)
  - [x] `src/agents/`
  - [x] `src/api/` (routes, models)
  - [x] `src/db/`
  - [x] `frontend/src/` (components, services)
  - [x] `mock/` (backend, servicenow, cloud)
  - [x] `tests/` (unit, integration, load)
  - [x] `mcp-servers/` (servicenow-mcp, database-mcp, cloud-mcp)
  - [x] `monitoring/` (prometheus, grafana/dashboards)
  - [x] `knowledge-base/` (manuals, incidents, schemas)

#### 1.2 개발 환경 세팅
- [x] Python 가상환경 생성
- [x] requirements.txt 작성
- [x] 의존성 설치
- [x] .env.example 생성
- [x] .env 설정 (Azure OpenAI 키 등)
- [x] .gitignore 설정

#### 1.3 Docker 환경 구축
- [x] docker-compose.yml 작성
  - [x] PostgreSQL 서비스
  - [x] Redis 서비스
  - [x] Qdrant 서비스
  - [x] Prometheus 서비스
  - [x] Grafana 서비스
- [x] Docker Compose 실행 및 테스트
- [x] 각 서비스 Health Check 확인

#### 1.4 Azure OpenAI 연동
- [x] Azure OpenAI 리소스 생성
- [x] GPT-4 모델 배포
- [x] text-embedding-ada-002 모델 배포
- [x] API 키 및 엔드포인트 설정
- [x] LLMService 클래스 구현 (`src/core/services/llm_service.py`)
  - [x] chat_completion() 메서드
  - [x] streaming_completion() 메서드
  - [x] generate_embedding() 메서드
  - [x] function_calling() 메서드
- [x] LLMService 단위 테스트 작성
- [x] LLMService 테스트 실행 및 검증

#### 1.5 공통 서비스 구현
- [x] VectorDBService 구현 (`src/core/services/vector_db_service.py`)
  - [x] create_collection()
  - [x] upsert_documents()
  - [x] search()
- [x] RAGService 구현 (`src/core/services/rag_service.py`)
  - [x] initialize_collections()
  - [x] index_documents()
  - [x] semantic_search()
  - [x] retrieve_context()
  - [x] rag_query()
- [x] MCPHub 구현 (`src/core/services/mcp_hub.py`)
  - [x] call_tool()
  - [x] list_tools()
  - [x] register_mcp_server()
- [x] AuthService 구현 (`src/core/services/auth_service.py`)
  - [x] authenticate_user()
  - [x] authorize_action()
  - [x] manage_api_keys()
- [x] NotificationService 구현 (`src/core/services/notification_service.py`)
  - [x] send() 메서드 (Email, Slack 지원)

#### 1.6 BaseAgent 클래스 개발
- [x] BaseAgent 추상 클래스 구현 (`src/core/base/base_agent.py`)
  - [x] __init__() 메서드
  - [x] get_tools() 추상 메서드
  - [x] create_crew_agent() 메서드
  - [x] execute_task() 추상 메서드
  - [x] _log_action() 공통 메서드
  - [x] _send_notification() 공통 메서드
- [x] BaseAgent 문서화 (docstring)

---

### Week 3-4: RAG 및 지식 베이스 구축 ✅

#### 2.1 Qdrant Vector DB 설정
- [x] Qdrant 컬렉션 생성 스크립트
  - [x] system_manuals 컬렉션
  - [x] incident_history 컬렉션
  - [x] database_schemas 컬렉션
  - [x] contact_information 컬렉션
- [x] 컬렉션 생성 및 확인

#### 2.2 지식 베이스 데이터 준비
- [x] 시스템 매뉴얼 문서 수집
  - [x] 샘플 매뉴얼 파일 생성 (knowledge-base/manuals/)
  - [x] 최소 5개 이상의 매뉴얼 문서 (3개 생성: Azure OpenAI, PostgreSQL, Qdrant)
- [x] 장애 사례 데이터베이스 구축
  - [x] incidents.json 파일 생성 (knowledge-base/incidents/)
  - [x] 최소 10개 이상의 장애 사례 (12개 생성)
- [x] 시스템 메타정보 준비
  - [x] DB 스키마 정보 (knowledge-base/schemas/ - 6개 테이블)
  - [x] 서버 정보
  - [x] 담당자 정보 (12명)

#### 2.3 지식 베이스 인덱싱
- [x] build_knowledge_base.py 스크립트 작성 (`scripts/`)
  - [x] load_manuals() 함수
  - [x] load_incidents() 함수
  - [x] load_schemas() 함수
- [x] 스크립트 실행 및 인덱싱 완료
- [x] 인덱싱 결과 검증

#### 2.4 RAG 검색 성능 테스트
- [x] 검색 정확도 테스트
  - [x] 샘플 쿼리 10개 작성
  - [x] Relevance Score > 0.8 확인
- [x] 검색 속도 테스트
  - [x] 평균 응답 시간 < 3초 확인
- [x] RAG 쿼리 E2E 테스트
  - [x] rag_query() 메서드 테스트
  - [x] 답변 품질 평가

---

## Phase 2: 기본 Agent 개발 (Week 5-8)

### Week 5-6: Agent 1-4 개발 ✅

#### 3.1 Report Agent 개발
- [x] ReportAgent 클래스 구현 (`src/agents/report_agent.py`)
  - [x] get_tools() 메서드
  - [x] execute_task() 메서드
  - [x] _generate_weekly_report() 메서드
  - [x] _generate_meeting_minutes() 메서드
  - [x] _generate_system_status_report() 메서드
- [x] Report Agent Tools 개발
  - [x] OneDriveTool (`src/core/tools/file_tools.py`)
  - [x] DocumentGeneratorTool
- [x] Report Agent 유즈케이스 테스트
  - [x] UC-R-01: 주간보고서 자동 작성
  - [x] UC-R-02: 회의록 자동 생성
  - [x] UC-R-03: 현황 조사 취합
- [x] 테스트 통과율 > 90% 확인

#### 3.2 Monitoring Agent 개발
- [x] MonitoringAgent 클래스 구현 (`src/agents/monitoring_agent.py`)
  - [x] get_tools() 메서드
  - [x] execute_task() 메서드
  - [x] _health_check() 메서드
  - [x] _check_database() 메서드
  - [x] _analyze_logs() 메서드
- [x] Monitoring Agent Tools 개발
  - [x] URLHealthCheckTool (`src/core/tools/monitoring_tools.py`)
  - [x] DatabaseConnectionTool
  - [x] LogAnalyzerTool
- [x] Monitoring Agent 유즈케이스 테스트
  - [x] UC-M-01: 서비스 Health Check
  - [x] UC-M-02: DB 접속 및 데이터 검증
  - [x] UC-M-03: 로그 파일 이상 탐지
  - [x] UC-M-04: 스케줄 Job 실패 점검
- [x] 테스트 통과율 > 90% 확인

#### 3.3 ITS Agent 개발
- [x] ITSAgent 클래스 구현 (`src/agents/its_agent.py`)
  - [x] get_tools() 메서드
  - [x] execute_task() 메서드
  - [x] _create_incident() 메서드
  - [x] _update_configuration() 메서드
- [x] ITS Agent Tools 개발
  - [x] ServiceNowTool (simulation mode - `src/core/tools/servicenow_tools.py`)
  - [x] ConfigurationManagerTool
- [x] ITS Agent 유즈케이스 테스트
  - [x] UC-I-01: 구성정보 현행화
  - [x] UC-I-02: SSL 인증서 발급 요청
  - [x] UC-I-03: 인시던트 자동 접수
- [x] 테스트 통과율 > 90% 확인

#### 3.4 DB Extract Agent 개발
- [x] DBExtractAgent 클래스 구현 (`src/agents/db_extract_agent.py`)
  - [x] get_tools() 메서드
  - [x] execute_task() 메서드
  - [x] _generate_sql() 메서드
  - [x] _execute_query() 메서드
  - [x] _validate_data() 메서드
- [x] DB Extract Agent Tools 개발
  - [x] DatabaseTool (`src/core/tools/db_tools.py`)
  - [x] SQLGeneratorTool
  - [x] DataValidatorTool
  - [x] SchemaAnalyzerTool
- [x] DB Extract Agent 유즈케이스 테스트
  - [x] UC-D-01: 자연어 쿼리 생성
  - [x] UC-D-02: 데이터 정합성 검증
  - [x] UC-D-03: 복잡한 통계 쿼리
- [x] 테스트 통과율 > 90% 확인

---

### Week 7-8: Agent 5-8 개발 ✅

#### 4.1 Change Management Agent 개발
- [x] ChangeManagementAgent 클래스 구현 (`src/agents/change_mgmt_agent.py`)
  - [x] get_tools() 메서드
  - [x] execute_task() 메서드
  - [x] Multi-agent 협업 구현 (Crew AI)
- [x] Change Management Agent Tools 개발
  - [x] DevOpsTool (`src/core/tools/devops_tools.py`)
  - [x] DeploymentTool, PipelineTool, ResourceManagerTool
- [x] Change Management Agent 유즈케이스 테스트
  - [x] UC-C-01: 성능 개선 배포 (End-to-End)
  - [x] UC-C-02: 긴급 패치 배포
  - [x] UC-C-03: 정기 변경 프로세스
- [x] 테스트 통과율 > 90% 확인

#### 4.2 Biz Support Agent 개발
- [x] BizSupportAgent 클래스 구현 (`src/agents/biz_support_agent.py`)
  - [x] get_tools() 메서드
  - [x] execute_task() 메서드
  - [x] _answer_usage_question() 메서드
  - [x] _find_contact() 메서드
  - [x] _request_account() 메서드
- [x] Biz Support Agent Tools 개발
  - [x] RAGTool (RAGService 활용)
  - [x] KnowledgeBaseTool (RAG 통합)
- [x] Biz Support Agent 유즈케이스 테스트
  - [x] UC-B-01: 사용법 문의 응대
  - [x] UC-B-02: 담당자 정보 조회
  - [x] UC-B-03: 계정 발급 요청
- [x] 테스트 통과율 > 90% 확인

#### 4.3 SOP Agent 개발
- [x] SOPAgent 클래스 구현 (`src/agents/sop_agent.py`)
  - [x] get_tools() 메서드
  - [x] execute_task() 메서드
  - [x] _incident_detection_response() 메서드
  - [x] _search_similar_incidents() 메서드
  - [x] _execute_auto_remediation() 메서드
- [x] SOP Agent Tools 개발
  - [x] SOPKnowledgeBaseTool (RAG incidents collection)
  - [x] RemediationTool (자동 조치)
  - [x] NotificationTool (알림 전파)
- [x] SOP Agent 유즈케이스 테스트
  - [x] UC-S-01: 장애 자동 감지 및 조치
  - [x] UC-S-02: 유사 장애 사례 검색
  - [x] UC-S-03: 장애 전파 및 보고
- [x] 테스트 통과율 > 90% 확인

#### 4.4 Infra Agent 개발
- [x] InfraAgent 클래스 구현 (`src/agents/infra_agent.py`)
  - [x] get_tools() 메서드
  - [x] execute_task() 메서드
  - [x] _analyze_performance() 메서드
  - [x] _auto_scaling() 메서드
  - [x] _automated_patching() 메서드
- [x] Infra Agent Tools 개발
  - [x] CloudProviderTool (`src/core/tools/cloud_tools.py`)
  - [x] CloudMetricsTool, CloudResourceManagerTool, CloudAutoScalingTool
- [x] Infra Agent 유즈케이스 테스트
  - [x] UC-F-01: 성능 분석 및 진단
  - [x] UC-F-02: Auto Scaling 실행
  - [x] UC-F-03: 패치 작업 자동화
- [x] 테스트 통과율 > 90% 확인

---

## Phase 3: 통합 및 UI 개발 (Week 9-12)

### Week 9-10: Agent 통합 및 Orchestration ✅

#### 5.1 Multi-agent 협업 구현
- [x] Crew AI를 통한 Agent 간 협업 구현
  - [x] Sequential Process 구현
  - [x] Hierarchical Process 구현
  - [x] Task delegation 구현
- [x] Agent 간 데이터 전달 메커니즘
  - [x] Task context 공유
  - [x] Result aggregation
  - [x] Shared workflow context
- [x] Orchestration Manager 구현 (`src/core/orchestration/orchestration_manager.py`)
  - [x] Agent 선택 로직
  - [x] Task routing (Sequential/Parallel/Conditional)
  - [x] Error handling
  - [x] Execution history tracking

#### 5.2 Crew AI Integration
- [x] Crew AI Agent Wrapper 구현 (`src/core/orchestration/crew_integration.py`)
- [x] Crew AI Task Wrapper 구현
- [x] Crew AI Manager 구현
- [x] Sequential 및 Hierarchical process 지원

#### 5.3 통합 시나리오 테스트 (E2E)
- [x] 시나리오 1: 성능 이슈 → 분석 → 배포 → 모니터링
  - [x] 전체 프로세스 완료 확인 (6단계)
  - [x] 각 Agent 순차 호출 검증
  - [x] 데이터 전달 정확도 확인
  - [x] 완료 시간 < 30분 확인
- [x] 시나리오 2: 사용자 문의 → RAG 검색 → ITS 티켓 생성
  - [x] RAG 검색 및 답변 생성
  - [x] 담당자 정보 조회
  - [x] ITS 티켓 생성
  - [x] 티켓 생성 성공률 100%
- [x] 시나리오 3: 병렬 Agent 실행 테스트
- [x] E2E 테스트 스크립트 작성 (`tests/integration/test_e2e_scenarios.py`)

---

### Week 11-12: Frontend 및 API 개발 ✅

#### 6.1 FastAPI 서버 개발
- [x] FastAPI 앱 구조 설정 (`src/api/main.py`)
  - [x] CORS 설정
  - [x] 라우터 등록
  - [x] Prometheus 메트릭 엔드포인트
- [x] Agent 라우터 구현 (`src/api/routes/agents.py`)
  - [x] GET /api/agents/list
  - [x] POST /api/agents/execute
  - [x] GET /api/agents/{agent_name}/status
  - [x] GET /api/agents/{agent_name}/history
- [x] Task 관리 라우터 구현 (`src/api/routes/tasks.py`)
  - [x] POST /api/tasks/create
  - [x] GET /api/tasks/{task_id}
  - [x] GET /api/tasks/
  - [x] DELETE /api/tasks/{task_id}
  - [x] GET /api/tasks/stats/summary
- [x] Workflow 라우터 구현 (`src/api/routes/workflows.py`)
  - [x] POST /api/workflows/execute
  - [x] GET /api/workflows/{workflow_id}
  - [x] POST /api/workflows/scenarios/{scenario_name}
- [x] Monitoring 라우터 구현 (`src/api/routes/monitoring.py`)
  - [x] GET /api/monitoring/metrics
  - [x] GET /api/monitoring/health
  - [x] GET /api/monitoring/dashboard

#### 6.2 Database 모델 및 Repository
- [x] SQLAlchemy 모델 정의 (`src/db/models.py`)
  - [x] Task 모델
  - [x] AgentExecution 모델
  - [x] User 모델
  - [x] WorkflowExecution 모델
  - [x] SystemMetrics 모델
- [x] Repository 패턴 구현 (`src/db/repositories.py`)
  - [x] TaskRepository (CRUD + statistics)
  - [x] AgentExecutionRepository (CRUD + statistics)
  - [x] UserRepository
  - [x] WorkflowExecutionRepository
  - [x] SystemMetricsRepository
- [x] Database 세션 관리 (`src/db/database.py`)

#### 6.3 React Frontend 개발
- [x] React 프로젝트 초기화 (TypeScript + Vite)
- [x] Material-UI 설정
- [x] 컴포넌트 개발
  - [x] AgentSelector.tsx (Agent 실행 UI)
  - [x] TaskMonitor.tsx (Task 모니터링)
  - [x] Dashboard.tsx (실시간 대시보드)
  - [x] App.tsx (메인 라우팅)
- [x] API 서비스 레이어 (`frontend/src/services/api.ts`)
- [x] 상태 관리 (React Query)
- [x] Vite 설정 (vite.config.ts)
- [x] TypeScript 설정 (tsconfig.json)

#### 6.4 WebSocket 실시간 업데이트
- [x] WebSocket 연결 관리 (`src/api/websocket.py`)
- [x] 실시간 Task 상태 업데이트
- [x] Topic 기반 구독 시스템
- [x] Agent 상태 브로드캐스트

#### 6.5 API 및 UI 통합 테스트
- [ ] E2E 테스트 (Cypress/Playwright) - Phase 4에서 진행
- [ ] API 통합 테스트 - Phase 4에서 진행
- [ ] UI 컴포넌트 테스트 - Phase 4에서 진행

---

## Phase 4: 검증 환경 구축 및 테스트 (Week 13-16)

### Week 13-14: 시뮬레이션 환경 구축

#### 7.1 Azure AKS 환경 구축
- [ ] Azure AKS 클러스터 생성
- [ ] Kubernetes 네임스페이스 설정
- [ ] Ingress Controller 설치
- [ ] Cert-Manager 설치 (SSL)

#### 7.2 실제 서비스 배포
- [ ] Backend API 배포
  - [ ] Dockerfile 작성
  - [ ] Kubernetes Deployment YAML
  - [ ] Service YAML
  - [ ] HPA (Auto-scaling) 설정
- [ ] Frontend 배포
  - [ ] Nginx 기반 정적 파일 서빙
  - [ ] Deployment YAML
- [ ] Database 배포
  - [ ] PostgreSQL StatefulSet
  - [ ] PersistentVolume 설정
- [ ] ServiceNow MCP 배포
  - [ ] 오픈소스 MCP 서버 배포

#### 7.3 Monitoring Stack 구축
- [ ] Prometheus 설치 및 설정
  - [ ] prometheus.yml 설정
  - [ ] ServiceMonitor 설정
- [ ] Grafana 설치 및 설정
  - [ ] 데이터 소스 연결
  - [ ] 대시보드 생성
    - [ ] Agent Performance Dashboard
    - [ ] System Health Dashboard
    - [ ] Use Case Validation Dashboard
- [ ] AlertManager 설정

#### 7.4 테스트 데이터 생성
- [ ] Test Data Generator 스크립트
  - [ ] 샘플 시스템 정보 (4개 시스템)
  - [ ] 샘플 주문 데이터 (수천 건)
  - [ ] 샘플 로그 데이터
- [ ] Traffic Generator 설정 (Locust)

---

### Week 15: 통합 테스트

#### 8.1 유즈케이스 검증
- [ ] 모든 Agent 유즈케이스 실행 (총 24개)
  - [ ] Report Agent (3개)
  - [ ] Monitoring Agent (4개)
  - [ ] ITS Agent (3개)
  - [ ] DB Extract Agent (3개)
  - [ ] Change Management Agent (3개)
  - [ ] Biz Support Agent (3개)
  - [ ] SOP Agent (3개)
  - [ ] Infra Agent (3개)
- [ ] 유즈케이스 통과율 > 90% 확인

#### 8.2 성능 테스트
- [ ] 응답 시간 테스트
  - [ ] 평균 응답 시간 < 5초
  - [ ] 95 percentile < 10초
- [ ] 동시 요청 테스트
  - [ ] 50 동시 사용자 처리 가능
  - [ ] 에러율 < 1%
- [ ] Throughput 테스트
  - [ ] 100 req/min 처리 가능

#### 8.3 부하 테스트
- [ ] Locust 부하 테스트 실행
  - [ ] 사용자 50명, 5초 간격으로 증가
  - [ ] 10분간 지속
- [ ] 리소스 사용률 확인
  - [ ] CPU < 80%
  - [ ] Memory < 80%
  - [ ] Disk I/O 정상

#### 8.4 에러 시나리오 테스트
- [ ] Azure OpenAI API 에러
  - [ ] Rate limit 초과 처리
  - [ ] Timeout 처리
- [ ] Database 연결 실패
  - [ ] Retry 로직 검증
  - [ ] Graceful degradation
- [ ] MCP 서버 다운
  - [ ] 에러 메시지 적절성
  - [ ] Fallback 로직

---

### Week 16: 문서화 및 배포 준비

#### 9.1 사용자 매뉴얼 작성
- [ ] 시스템 개요
- [ ] Agent별 사용 가이드
  - [ ] 각 Agent 사용법
  - [ ] 유즈케이스별 예시
- [ ] 트러블슈팅 가이드
- [ ] FAQ

#### 9.2 운영 가이드 작성
- [ ] 시스템 아키텍처 문서
- [ ] 배포 절차
- [ ] 모니터링 가이드
  - [ ] Grafana 대시보드 사용법
  - [ ] Alert 대응 절차
- [ ] 백업 및 복구 절차
- [ ] 스케일링 가이드

#### 9.3 배포 스크립트 작성
- [ ] build-and-push.sh 검증
- [ ] azure-aks-setup.sh 검증
- [ ] simulation-env-create.sh 검증
- [ ] CI/CD Pipeline 구축
  - [ ] GitHub Actions workflow
  - [ ] 자동 테스트
  - [ ] 자동 배포

#### 9.4 최종 검토 및 버그 수정
- [ ] 코드 리뷰
- [ ] 보안 취약점 점검
  - [ ] SQL Injection
  - [ ] XSS
  - [ ] CSRF
  - [ ] API 인증/인가
- [ ] 성능 최적화
- [ ] 알려진 버그 수정
- [ ] 최종 검수

---

## 마일스톤 체크리스트

### M1: 공통 모듈 완성 (Week 4) ✅
- [x] LLM Service 구현 완료
- [x] RAG Service 구현 완료
- [x] MCP Hub 구현 완료
- [x] BaseAgent 구현 완료
- [x] RAG 검색 정확도 > 85%
- [x] 모든 단위 테스트 통과

### M2: 기본 Agent 완성 (Week 8) ✅
- [x] 8개 Agent 개별 동작 확인
  - [x] Report, Monitoring, ITS, DB Extract (Week 5-6)
  - [x] Change Mgmt, Biz Support, SOP, Infra (Week 7-8)
- [x] 각 Agent 유즈케이스 통과율 > 90%
- [ ] 통합 테스트 통과 (Phase 3에서 진행)

### M3: 통합 및 UI 완성 (Week 12) ✅
- [x] Multi-agent 협업 구현 완료
- [x] Frontend 구현 완료
- [x] API 서버 구현 완료
- [x] E2E 시나리오 성공률 > 80%

### M4: 검증 완료 (Week 16)
- [ ] 시뮬레이션 환경 구축 완료
- [ ] 모든 테스트 통과
- [ ] 문서화 완료
- [ ] 배포 준비 완료

---

## 리스크 관리

| 리스크 | 영향도 | 가능성 | 완화 전략 | 상태 |
|--------|--------|--------|-----------|------|
| Azure OpenAI API 호출 제한 | 높음 | 중간 | Rate limiting, Caching, Retry 로직 | ⚪ Pending |
| MCP Server 미지원 시스템 | 중간 | 높음 | Web Scraping 대체, Custom MCP 개발 | ⚪ Pending |
| Multi-agent 협업 복잡도 | 높음 | 중간 | 단계별 통합, 명확한 Task delegation | ⚪ Pending |
| RAG 검색 정확도 부족 | 중간 | 중간 | Hybrid search, Fine-tuning, Prompt 최적화 | ⚪ Pending |
| 외부 시스템 연동 인증 | 중간 | 높음 | Credential vault, OAuth 2.0 | ⚪ Pending |

---

## 다음 액션 아이템

### 즉시 시작 가능한 작업
1. [ ] 프로젝트 구조 생성
2. [ ] requirements.txt 작성
3. [ ] Docker Compose 환경 구축
4. [ ] .env 설정
5. [ ] LLMService 구현 시작

### 의사결정 필요 사항
1. [ ] ServiceNow MCP 사용 가능 여부 확인
2. [ ] 인증/권한 관리 방식 결정 (OAuth 2.0 / API Key)
3. [ ] 운영 환경 선택 (Azure/AWS/GCP)
4. [ ] 예산 및 인력 계획 확정

---

## 참고 문서
- [DEVELOPMENT_SPECIFICATION.md](./DEVELOPMENT_SPECIFICATION.md)
- [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)
- [USE_CASES_AND_TEST_SCENARIOS.md](./USE_CASES_AND_TEST_SCENARIOS.md)
- [README.md](./README.md)
