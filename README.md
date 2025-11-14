# Agentic AI Platform - Multi-Agent 운영 자동화 시스템

[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)](https://github.com/features/actions)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **프로젝트 상태**: ✅ 개발 완료 (100%) | **버전**: 1.0.0 | **최종 업데이트**: 2025-11-14

8개의 전문화된 AI Agent가 협력하여 IT 운영 업무를 자동화하는 Multi-Agent 시스템입니다.

---

## 📖 목차

- [주요 특징](#주요-특징)
- [시스템 아키텍처](#시스템-아키텍처)
- [8개 AI Agent](#8개-ai-agent-소개)
- [빠른 시작](#빠른-시작)
- [배포](#배포)
- [테스트](#테스트)
- [문서](#문서)
- [기술 스택](#기술-스택)

---

## 🌟 주요 특징

### ✅ 완성된 시스템

- **8개 전문 AI Agent**: Report, Monitoring, ITS, DB Extract, Change Mgmt, Biz Support, SOP, Infra
- **Multi-Agent 협업**: Crew AI 기반 Sequential/Parallel/Conditional/Delegated 실행 모드
- **FastAPI Backend**: RESTful API, WebSocket 실시간 업데이트
- **React Frontend**: Material-UI 기반 대시보드, Agent Selector, Task Monitor
- **RAG 시스템**: Qdrant Vector DB + 33개 지식 베이스 문서
- **완전한 모니터링**: Prometheus + Grafana (2개 대시보드)
- **CI/CD 파이프라인**: GitHub Actions 자동 테스트 및 배포
- **컨테이너화**: Docker Compose + Kubernetes 지원

### 🎯 주요 기능

- ✅ 자연어로 Agent 작업 실행
- ✅ 실시간 작업 모니터링 (WebSocket)
- ✅ 복잡한 워크플로우 자동화 (Multi-agent orchestration)
- ✅ RAG 기반 지능형 응답
- ✅ 자동 스케일링 (Kubernetes HPA)
- ✅ 부하 테스트 및 성능 검증

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│              Frontend (React + TypeScript)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐          │
│  │Dashboard │  │ Agent    │  │  Task Monitor    │          │
│  │          │  │ Selector │  │  (WebSocket)     │          │
│  └──────────┘  └──────────┘  └──────────────────┘          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                  Backend API (FastAPI)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Routes                                            │ │
│  │  - /api/agents/*  - /api/tasks/*                       │ │
│  │  - /api/workflows/*  - /api/monitoring/*               │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Orchestration Manager                                 │ │
│  │  - Sequential/Parallel/Conditional/Delegated           │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Common Services                                       │ │
│  │  - LLMService (Azure OpenAI GPT-4)                     │ │
│  │  - RAGService (Qdrant Vector DB)                       │ │
│  │  - MCPHub (External System Integration)               │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  8 AI Agents (Crew AI)                                 │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐    │ │
│  │  │ Report  │ │Monitor  │ │   ITS   │ │DB Extract│    │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘    │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │ │
│  │  │ Change  │ │BizSupport│ │   SOP   │ │  Infra  │    │ │
│  │  │  Mgmt   │ │         │ │         │ │         │    │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Data Layer                                                  │
│  - PostgreSQL (메타데이터)                                   │
│  - Qdrant (Vector 검색)                                      │
│  - Redis (캐싱)                                              │
└──────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────┐
│  Monitoring: Prometheus + Grafana                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 🤖 8개 AI Agent 소개

| Agent | 역할 | 주요 기능 | 구현 상태 |
|-------|------|----------|----------|
| **Report Agent** | 보고서 자동화 | 주간보고서, 회의록, 현황조사 | ✅ 완료 |
| **Monitoring Agent** | 시스템 모니터링 | Health Check, DB 점검, 로그 분석 | ✅ 완료 |
| **ITS Agent** | 티켓 관리 | ServiceNow 인시던트 자동 처리 | ✅ 완료 |
| **DB Extract Agent** | DB 분석 | 자연어→SQL, 데이터 검증 | ✅ 완료 |
| **Change Management Agent** | 변경 관리 | 배포 자동화, Agent 조율 | ✅ 완료 |
| **Business Support Agent** | 사용자 지원 | RAG 기반 문의 응대 | ✅ 완료 |
| **SOP Agent** | 장애 대응 | 장애 감지, 자동 조치 | ✅ 완료 |
| **Infrastructure Agent** | 인프라 관리 | 성능 분석, Auto Scaling | ✅ 완료 |

---

## 🚀 빠른 시작

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Azure OpenAI API Key

### 1. 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd agentic_ai_20251114

# 환경 변수 설정
cp .env.example .env
# .env 파일에 Azure OpenAI 키 등 설정
```

### 2. Docker Compose로 전체 스택 실행

```bash
# 전체 스택 시작 (Backend + Frontend + DB + Monitoring)
./scripts/deploy-docker.sh start

# 또는
docker-compose -f docker-compose.full.yml up -d
```

### 3. 서비스 접속

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

### 4. 지식 베이스 구축 (선택사항)

```bash
# RAG를 위한 지식 베이스 인덱싱
python scripts/build_knowledge_base.py
```

---

## 📦 배포

### Docker Compose 배포

```bash
# 시작
./scripts/deploy-docker.sh start

# 중지
./scripts/deploy-docker.sh stop

# 재시작
./scripts/deploy-docker.sh restart

# 로그 확인
./scripts/deploy-docker.sh logs

# 상태 확인
./scripts/deploy-docker.sh status
```

### Kubernetes 배포

```bash
# 배포
./scripts/deploy-k8s.sh deploy

# 상태 확인
./scripts/deploy-k8s.sh status

# 로그 확인
./scripts/deploy-k8s.sh logs backend

# 스케일 조정
./scripts/deploy-k8s.sh scale backend 5

# 삭제
./scripts/deploy-k8s.sh delete
```

### Azure AKS 배포

```bash
# Azure 로그인
az login

# Secrets 설정 (.env 파일 필요)
./scripts/deploy-k8s.sh secrets

# 전체 배포
./scripts/deploy-k8s.sh deploy
```

---

## 🧪 테스트

### 통합 테스트 실행

```bash
# 모든 테스트 실행
./scripts/run-tests.sh all

# 단위 테스트만
./scripts/run-tests.sh unit

# 통합 테스트만
./scripts/run-tests.sh integration

# E2E 테스트만
./scripts/run-tests.sh e2e

# 부하 테스트 (Locust)
./scripts/run-tests.sh load

# 테스트 데이터 생성
./scripts/run-tests.sh data
```

### CI/CD 파이프라인

GitHub Actions 자동 실행:

- **Push/PR**: 자동 테스트, 린팅, 보안 스캔
- **Main 브랜치**: Docker 이미지 빌드 및 푸시
- **Release**: 프로덕션 배포

워크플로우:
- `.github/workflows/ci-cd.yml`: CI/CD 파이프라인
- `.github/workflows/deploy.yml`: 프로덕션 배포

---

## 📚 문서

### 핵심 문서

| 문서 | 설명 | 링크 |
|------|------|------|
| **개발 명세서** | 전체 시스템 설계 및 아키텍처 | [DEVELOPMENT_SPECIFICATION.md](./DEVELOPMENT_SPECIFICATION.md) |
| **구현 가이드** | 단계별 개발 가이드 | [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) |
| **유즈케이스** | 26개 유즈케이스 및 테스트 시나리오 | [USE_CASES_AND_TEST_SCENARIOS.md](./USE_CASES_AND_TEST_SCENARIOS.md) |
| **개발 체크리스트** | 16주 개발 진행 상황 | [DEVELOPMENT_CHECKLIST.md](./DEVELOPMENT_CHECKLIST.md) |
| **사용자 매뉴얼** | 시스템 사용 가이드 | [docs/USER_MANUAL.md](./docs/USER_MANUAL.md) |
| **운영 가이드** | 배포 및 운영 가이드 | [docs/OPERATIONS_GUIDE.md](./docs/OPERATIONS_GUIDE.md) |

### API 문서

- **OpenAPI 문서**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

---

## 🛠️ 기술 스택

### Core AI

| 컴포넌트 | 기술 | 버전 |
|----------|------|------|
| Orchestration | Crew AI | Latest |
| LLM | Azure OpenAI GPT-4 | - |
| Embedding | text-embedding-ada-002 | - |
| Framework | LangChain | 0.1.0 |
| Vector DB | Qdrant | Latest |

### Backend

| 컴포넌트 | 기술 | 버전 |
|----------|------|------|
| API Framework | FastAPI | 0.104+ |
| Language | Python | 3.11 |
| Database | PostgreSQL | 15 |
| Cache | Redis | 7 |
| ORM | SQLAlchemy | 2.0 |

### Frontend

| 컴포넌트 | 기술 | 버전 |
|----------|------|------|
| Framework | React | 18.2 |
| Language | TypeScript | 5.3 |
| UI Library | Material-UI | 5.14 |
| State Management | React Query | 5.0 |
| Build Tool | Vite | 5.0 |

### DevOps & Monitoring

| 컴포넌트 | 기술 | 버전 |
|----------|------|------|
| Containerization | Docker | Latest |
| Orchestration | Kubernetes | 1.28 |
| CI/CD | GitHub Actions | - |
| Monitoring | Prometheus | Latest |
| Dashboards | Grafana | Latest |
| Load Testing | Locust | Latest |

---

## 📊 프로젝트 상태

### 개발 진행률: 100% ✅

| Phase | 기간 | 상태 |
|-------|------|------|
| Phase 1: 기반 구축 | Week 1-4 | ✅ 완료 |
| Phase 2: Agent 개발 | Week 5-8 | ✅ 완료 |
| Phase 3: 통합 및 UI | Week 9-12 | ✅ 완료 |
| Phase 4: 검증 및 테스트 | Week 13-16 | ✅ 완료 |

### 주요 마일스톤

- ✅ M1: 공통 모듈 완성 (Week 4)
- ✅ M2: 8개 Agent 완성 (Week 8)
- ✅ M3: 통합 및 UI 완성 (Week 12)
- ✅ M4: 검증 완료 (Week 16)

### 구현 완료 항목

#### Backend (100%)
- ✅ 8개 AI Agent 구현
- ✅ Orchestration Manager (4가지 모드)
- ✅ FastAPI REST API (4개 route 모듈)
- ✅ WebSocket 실시간 업데이트
- ✅ Database Layer (Repository 패턴)
- ✅ LLM/RAG/MCP 통합 서비스

#### Frontend (100%)
- ✅ React + TypeScript 구조
- ✅ Dashboard (실시간 메트릭)
- ✅ Agent Selector (작업 실행)
- ✅ Task Monitor (WebSocket 연동)
- ✅ Material-UI 디자인

#### DevOps (100%)
- ✅ Docker Compose 전체 스택
- ✅ Kubernetes 매니페스트
- ✅ GitHub Actions CI/CD
- ✅ Prometheus + Grafana
- ✅ 배포 스크립트

#### 테스트 (100%)
- ✅ E2E 시나리오 테스트
- ✅ API 통합 테스트
- ✅ Locust 부하 테스트
- ✅ 테스트 데이터 생성기

#### 문서 (100%)
- ✅ 사용자 매뉴얼
- ✅ 운영 가이드
- ✅ 개발 스펙 문서
- ✅ 구현 가이드

---

## 🎯 E2E 시나리오 예시

### 시나리오 1: 성능 이슈 자동 처리

```
1. Monitoring Agent: CPU 90% 감지
   ↓
2. SOP Agent: 장애 상황 판단, 유사 사례 검색
   ↓
3. Infra Agent: 성능 분석, 리소스 증설 계획
   ↓
4. Change Management Agent: 변경 프로세스 시작
   ├─ Report Agent: 변경 계획서 작성
   ├─ ITS Agent: 변경 승인 요청
   ├─ DevOps Tool: 배포 실행
   ├─ Monitoring Agent: 배포 후 점검
   └─ Report Agent: 최종 보고서 작성
   ↓
5. Notification: 완료 알림
```

**결과**: 60분 이내 전체 프로세스 자동 완료

---

## 📈 기대 효과

- ✅ **운영 업무 자동화율**: 70% 이상
- ✅ **반복 작업 처리 시간**: 80% 단축
- ✅ **장애 대응 시간**: 50% 단축
- ✅ **보고서 작성 시간**: 90% 단축

---

## 🤝 기여 가이드

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 개발 규칙

- Agent 개발 시 BaseAgent 상속
- 테스트 커버리지 80% 이상 유지
- Black, flake8 린팅 통과
- 모든 API는 OpenAPI 스키마 정의

---

## 🐛 트러블슈팅

### 서비스가 시작되지 않을 때

```bash
# Docker 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs backend
```

### 데이터베이스 연결 실패

```bash
# PostgreSQL 상태 확인
docker-compose ps postgres

# 연결 테스트
docker-compose exec postgres psql -U admin -d agentic_ai
```

### Azure OpenAI API 에러

- .env 파일의 API 키 확인
- Azure OpenAI 리소스 할당량 확인
- 네트워크 연결 확인

더 많은 트러블슈팅: [docs/OPERATIONS_GUIDE.md](./docs/OPERATIONS_GUIDE.md#트러블슈팅)

---

## 📞 지원

- **이슈 등록**: GitHub Issues
- **문서**: [docs/](./docs/)
- **API 문서**: http://localhost:8000/docs

---

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들을 사용합니다:

- [Crew AI](https://github.com/joaomdmoura/crewAI) - Multi-agent orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [Qdrant](https://qdrant.tech/) - Vector database
- [React](https://react.dev/) - UI framework

---

**Built with ❤️ using AI** | **Last Updated**: 2025-11-14 | **Status**: Production Ready ✅
