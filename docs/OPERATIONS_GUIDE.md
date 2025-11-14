# Agentic AI 시스템 운영 가이드

> 버전: 1.0.0
> 최종 업데이트: 2025-11-14

## 목차

1. [시스템 아키텍처](#시스템-아키텍처)
2. [배포 절차](#배포-절차)
3. [모니터링](#모니터링)
4. [백업 및 복구](#백업-및-복구)
5. [스케일링](#스케일링)
6. [보안](#보안)
7. [트러블슈팅](#트러블슈팅)

---

## 시스템 아키텍처

### 전체 구조

```
┌─────────────┐
│  Frontend   │ (React + TypeScript)
│   (Nginx)   │
└──────┬──────┘
       │ HTTP/WebSocket
┌──────▼──────────────────────────┐
│      Backend API (FastAPI)      │
│  ┌────────────────────────────┐ │
│  │  Orchestration Manager     │ │
│  │  ┌──────────────────────┐  │ │
│  │  │  8 AI Agents        │  │ │
│  │  └──────────────────────┘  │ │
│  └────────────────────────────┘ │
└──────┬──────────────────────────┘
       │
   ┌───┴────┬──────────┬──────────┐
   │        │          │          │
┌──▼──┐ ┌──▼───┐ ┌────▼───┐ ┌───▼────┐
│Postgres│Redis│ │Qdrant │ │Azure   │
│       │     │ │Vector │ │OpenAI  │
└───────┘ └─────┘ └────────┘ └────────┘
       │
   ┌───┴────┬────────┐
   │        │        │
┌──▼────┐ ┌▼──────┐ │
│Prometheus│Grafana│ │
└─────────┘ └───────┘ │
```

### 컴포넌트

| 컴포넌트 | 역할 | 기술 스택 |
|----------|------|-----------|
| Frontend | 사용자 인터페이스 | React 18, TypeScript, MUI |
| Backend API | REST API 서버 | FastAPI, Python 3.11 |
| PostgreSQL | 메타데이터 저장 | PostgreSQL 15 |
| Redis | 캐싱 | Redis 7 |
| Qdrant | Vector 검색 | Qdrant Latest |
| Prometheus | 메트릭 수집 | Prometheus Latest |
| Grafana | 대시보드 | Grafana Latest |
| Azure OpenAI | LLM 서비스 | GPT-4, text-embedding-ada-002 |

---

## 배포 절차

### 로컬 개발 환경

#### 1. Prerequisites

```bash
# Python 3.11+
python --version

# Docker & Docker Compose
docker --version
docker-compose --version

# Node.js 18+
node --version
```

#### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일 편집하여 Azure OpenAI 키 등 설정
```

#### 3. Docker Compose로 실행

```bash
# 전체 스택 실행
docker-compose -f docker-compose.full.yml up -d

# 로그 확인
docker-compose -f docker-compose.full.yml logs -f

# 중지
docker-compose -f docker-compose.full.yml down
```

#### 4. 서비스 확인

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090

### Kubernetes 배포

#### 1. 네임스페이스 생성

```bash
kubectl apply -f k8s/namespace.yaml
```

#### 2. Secrets 설정

```bash
# Azure OpenAI Secrets
kubectl create secret generic backend-secret \
  --from-literal=AZURE_OPENAI_API_KEY='your-key' \
  --from-literal=AZURE_OPENAI_ENDPOINT='your-endpoint' \
  --from-literal=AZURE_OPENAI_DEPLOYMENT='gpt-4' \
  --from-literal=AZURE_OPENAI_EMBEDDING_DEPLOYMENT='text-embedding-ada-002' \
  -n agentic-ai

# Database Password
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_PASSWORD='secure-password' \
  -n agentic-ai
```

#### 3. 데이터베이스 배포

```bash
kubectl apply -f k8s/database/postgres-statefulset.yaml
```

#### 4. Backend 배포

```bash
# Docker 이미지 빌드 및 푸시
docker build -f Dockerfile.backend -t your-registry/agentic-ai-backend:latest .
docker push your-registry/agentic-ai-backend:latest

# 배포
kubectl apply -f k8s/backend/deployment.yaml
```

#### 5. Frontend 배포

```bash
# Docker 이미지 빌드 및 푸시
docker build -f Dockerfile.frontend -t your-registry/agentic-ai-frontend:latest .
docker push your-registry/agentic-ai-frontend:latest

# 배포
kubectl apply -f k8s/frontend/deployment.yaml
```

#### 6. 모니터링 스택 배포

```bash
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl apply -f k8s/monitoring/grafana.yaml
```

#### 7. 배포 확인

```bash
# Pod 상태 확인
kubectl get pods -n agentic-ai

# Service 확인
kubectl get svc -n agentic-ai

# Logs 확인
kubectl logs -f deployment/backend -n agentic-ai
```

### Azure AKS 배포

#### 1. AKS 클러스터 생성

```bash
# Resource Group 생성
az group create --name agentic-ai-rg --location koreacentral

# AKS 클러스터 생성
az aks create \
  --resource-group agentic-ai-rg \
  --name agentic-ai-aks \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# kubectl 인증 설정
az aks get-credentials --resource-group agentic-ai-rg --name agentic-ai-aks
```

#### 2. Container Registry 연결

```bash
# ACR 생성
az acr create --resource-group agentic-ai-rg --name agenticairegistry --sku Standard

# AKS와 ACR 연결
az aks update -n agentic-ai-aks -g agentic-ai-rg --attach-acr agenticairegistry
```

#### 3. 이미지 푸시 및 배포

위 Kubernetes 배포 절차 동일하게 진행

---

## 모니터링

### Grafana 대시보드

#### 접속

- URL: http://your-grafana-url:3000
- Username: admin
- Password: admin (변경 권장)

#### 대시보드

1. **Agent Performance Dashboard**
   - Agent별 작업 통계
   - 성공률
   - 평균 실행 시간
   - LLM API 호출 횟수

2. **System Health Dashboard**
   - CPU/Memory 사용률
   - API 응답 시간
   - 에러율
   - 활성 사용자 수

### Prometheus 메트릭

주요 메트릭:

```
# 작업 관련
agent_tasks_total{agent_type="monitoring"}
agent_tasks_successful_total{agent_type="monitoring"}
agent_task_duration_seconds{agent_type="monitoring"}

# 시스템 관련
system_cpu_usage_percent
system_memory_usage_percent
database_connections_active

# API 관련
http_requests_total{method="POST", path="/api/agents/execute"}
http_request_duration_seconds
```

### 로그 확인

#### Docker Compose

```bash
# 특정 서비스 로그
docker-compose logs -f backend

# 전체 로그
docker-compose logs -f

# 최근 100라인
docker-compose logs --tail=100 backend
```

#### Kubernetes

```bash
# Pod 로그
kubectl logs -f deployment/backend -n agentic-ai

# 이전 컨테이너 로그
kubectl logs deployment/backend --previous -n agentic-ai

# 전체 로그 스트림
kubectl logs -f -l app=backend -n agentic-ai
```

### Alert 설정

Prometheus AlertManager 설정 예:

```yaml
groups:
  - name: agentic_ai_alerts
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"

      - alert: HighCPUUsage
        expr: system_cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"
```

---

## 백업 및 복구

### 데이터베이스 백업

#### PostgreSQL 백업

```bash
# 전체 백업
kubectl exec -it postgres-0 -n agentic-ai -- \
  pg_dump -U admin agentic_ai > backup_$(date +%Y%m%d).sql

# 자동 백업 (cron)
0 2 * * * kubectl exec -it postgres-0 -n agentic-ai -- \
  pg_dump -U admin agentic_ai | gzip > /backup/agentic_ai_$(date +\%Y\%m\%d).sql.gz
```

#### 복구

```bash
# 복구
kubectl exec -i postgres-0 -n agentic-ai -- \
  psql -U admin agentic_ai < backup_20251114.sql
```

### Qdrant Vector DB 백업

```bash
# Snapshot 생성
curl -X POST "http://qdrant:6333/collections/system_manuals/snapshots"

# Snapshot 다운로드
curl "http://qdrant:6333/collections/system_manuals/snapshots/{snapshot_name}" \
  -o snapshot.tar
```

### 설정 파일 백업

```bash
# ConfigMaps & Secrets 백업
kubectl get configmaps -n agentic-ai -o yaml > configmaps-backup.yaml
kubectl get secrets -n agentic-ai -o yaml > secrets-backup.yaml
```

---

## 스케일링

### Horizontal Pod Autoscaler (HPA)

Backend Pod는 CPU/Memory 사용률에 따라 자동 스케일링됩니다:

```yaml
minReplicas: 3
maxReplicas: 10
metrics:
  - CPU: 70%
  - Memory: 80%
```

### 수동 스케일링

```bash
# Backend 스케일 아웃
kubectl scale deployment backend --replicas=5 -n agentic-ai

# Frontend 스케일 아웃
kubectl scale deployment frontend --replicas=3 -n agentic-ai
```

### 데이터베이스 스케일링

PostgreSQL은 StatefulSet으로 관리되며, 수직 스케일링 권장:

```bash
# 리소스 증가
kubectl edit statefulset postgres -n agentic-ai
# resources.limits.memory: 1Gi -> 2Gi
```

---

## 보안

### 인증 및 권한

1. **API 키 관리**
   - 환경 변수로 관리
   - Kubernetes Secrets 사용
   - 정기적 로테이션

2. **네트워크 정책**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: backend-policy
   spec:
     podSelector:
       matchLabels:
         app: backend
     ingress:
       - from:
           - podSelector:
               matchLabels:
                 app: frontend
   ```

3. **TLS/SSL**
   - Let's Encrypt 인증서
   - Cert-Manager 자동 갱신

### 취약점 점검

```bash
# 컨테이너 이미지 스캔
docker scan agentic-ai-backend:latest

# Kubernetes 보안 점검
kubectl auth can-i --list -n agentic-ai
```

---

## 트러블슈팅

### Pod가 시작되지 않음

```bash
# Pod 상태 확인
kubectl describe pod <pod-name> -n agentic-ai

# 이벤트 확인
kubectl get events -n agentic-ai --sort-by='.lastTimestamp'

# 로그 확인
kubectl logs <pod-name> -n agentic-ai
```

### 데이터베이스 연결 실패

1. PostgreSQL Pod 상태 확인
2. Service 확인
3. 네트워크 정책 확인
4. Secret 확인

### 높은 응답 시간

1. Grafana에서 메트릭 확인
2. Pod 리소스 사용률 확인
3. Database 슬로우 쿼리 확인
4. HPA 스케일링 확인

### Azure OpenAI Rate Limit

```python
# Exponential backoff 적용
# LLMService에서 자동 처리
```

---

## 참고 자료

- [Kubernetes 공식 문서](https://kubernetes.io/docs/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Prometheus 문서](https://prometheus.io/docs/)
- [Grafana 문서](https://grafana.com/docs/)
