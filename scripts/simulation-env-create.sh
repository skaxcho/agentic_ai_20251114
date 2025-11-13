#!/bin/bash
# 시뮬레이션 환경 생성 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="agentic-ai-simulation"

echo -e "${GREEN}=== 시뮬레이션 환경 생성 시작 ===${NC}"

# 1. Namespace 확인/생성
echo -e "${YELLOW}[1/6] Namespace 확인...${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# 2. PostgreSQL 배포 (테스트 데이터베이스)
echo -e "${YELLOW}[2/6] PostgreSQL 배포...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-init
  namespace: ${NAMESPACE}
data:
  init.sql: |
    -- 테스트 데이터 초기화
    CREATE TABLE IF NOT EXISTS systems (
      id SERIAL PRIMARY KEY,
      name VARCHAR(100),
      status VARCHAR(20),
      cpu_usage INTEGER,
      memory_usage INTEGER,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 샘플 시스템 데이터
    INSERT INTO systems (name, status, cpu_usage, memory_usage) VALUES
    ('주문관리 시스템', 'active', 65, 72),
    ('결제 시스템', 'active', 58, 68),
    ('재고관리 시스템', 'active', 45, 55),
    ('배송 시스템', 'active', 52, 61);

    CREATE TABLE IF NOT EXISTS orders (
      id SERIAL PRIMARY KEY,
      customer_id INTEGER,
      customer_name VARCHAR(100),
      amount DECIMAL(10, 2),
      status VARCHAR(20),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 샘플 주문 데이터
    INSERT INTO orders (customer_id, customer_name, amount, status) VALUES
    (1001, '홍길동', 2500000, 'completed'),
    (1002, '김철수', 1800000, 'completed'),
    (1003, '이영희', 3200000, 'processing'),
    (1004, '박민수', 950000, 'pending');
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  POSTGRES_USER: testuser
  POSTGRES_PASSWORD: testpassword
  POSTGRES_DB: simulation_db
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: ${NAMESPACE}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: ${NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        envFrom:
        - secretRef:
            name: postgres-secret
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: init-script
          mountPath: /docker-entrypoint-initdb.d
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
      - name: init-script
        configMap:
          name: postgres-init
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: ${NAMESPACE}
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
EOF

echo -e "${GREEN}✓ PostgreSQL 배포 완료${NC}"

# 3. 테스트용 Backend API 배포
echo -e "${YELLOW}[3/6] 테스트 Backend API 배포...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-backend
  namespace: ${NAMESPACE}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test-backend
  template:
    metadata:
      labels:
        app: test-backend
    spec:
      containers:
      - name: backend
        image: kennethreitz/httpbin
        ports:
        - containerPort: 80
        env:
        - name: GUNICORN_CMD_ARGS
          value: "--bind=0.0.0.0:80 --workers=2"
        livenessProbe:
          httpGet:
            path: /status/200
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
        readinessProbe:
          httpGet:
            path: /status/200
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
---
apiVersion: v1
kind: Service
metadata:
  name: test-backend
  namespace: ${NAMESPACE}
spec:
  selector:
    app: test-backend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
EOF

echo -e "${GREEN}✓ Backend API 배포 완료${NC}"

# 4. 테스트용 Frontend 배포
echo -e "${YELLOW}[4/6] 테스트 Frontend 배포...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-frontend
  namespace: ${NAMESPACE}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test-frontend
  template:
    metadata:
      labels:
        app: test-frontend
    spec:
      containers:
      - name: frontend
        image: nginx:alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: nginx-config
        configMap:
          name: nginx-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: ${NAMESPACE}
data:
  default.conf: |
    server {
        listen 80;
        server_name _;

        location / {
            root /usr/share/nginx/html;
            index index.html;
        }

        location /api/ {
            proxy_pass http://test-backend/;
        }

        location /health {
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
---
apiVersion: v1
kind: Service
metadata:
  name: test-frontend
  namespace: ${NAMESPACE}
spec:
  selector:
    app: test-frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
EOF

echo -e "${GREEN}✓ Frontend 배포 완료${NC}"

# 5. Prometheus & Grafana 배포
echo -e "${YELLOW}[5/6] Prometheus & Grafana 배포...${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: ${NAMESPACE}
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
        - role: pod
          namespaces:
            names:
            - ${NAMESPACE}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: ${NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: ${NAMESPACE}
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: LoadBalancer
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: ${NAMESPACE}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: ${NAMESPACE}
spec:
  selector:
    app: grafana
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
EOF

echo -e "${GREEN}✓ Prometheus & Grafana 배포 완료${NC}"

# 6. 배포 상태 확인
echo -e "${YELLOW}[6/6] 배포 상태 확인...${NC}"
sleep 10

kubectl get pods -n ${NAMESPACE}
echo ""
kubectl get svc -n ${NAMESPACE}

# External IP 대기
echo ""
echo -e "${YELLOW}External IP 할당 대기 중... (2-3분 소요)${NC}"
sleep 30

kubectl get svc -n ${NAMESPACE}

# 환경 정보 저장
BACKEND_IP=$(kubectl get svc test-backend -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
FRONTEND_IP=$(kubectl get svc test-frontend -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
PROMETHEUS_IP=$(kubectl get svc prometheus -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
GRAFANA_IP=$(kubectl get svc grafana -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

cat > simulation-env-info.txt << EOF
=== 시뮬레이션 환경 정보 ===
생성 시간: $(date)
Namespace: ${NAMESPACE}

=== 서비스 엔드포인트 ===
Backend API: http://${BACKEND_IP}
  - Health Check: http://${BACKEND_IP}/status/200
  - Test Echo: http://${BACKEND_IP}/anything

Frontend: http://${FRONTEND_IP}
  - Health Check: http://${FRONTEND_IP}/health

PostgreSQL (내부):
  - Host: postgres.${NAMESPACE}.svc.cluster.local
  - Port: 5432
  - Database: simulation_db
  - Username: testuser
  - Password: testpassword

Prometheus: http://${PROMETHEUS_IP}:9090
Grafana: http://${GRAFANA_IP}:3000
  - Username: admin
  - Password: admin

=== 데이터베이스 접속 (kubectl port-forward) ===
kubectl port-forward -n ${NAMESPACE} svc/postgres 5432:5432

그 후:
psql -h localhost -U testuser -d simulation_db

=== 유용한 명령어 ===
Pod 목록:
  kubectl get pods -n ${NAMESPACE}

로그 확인:
  kubectl logs -n ${NAMESPACE} <pod-name>

Shell 접속:
  kubectl exec -it -n ${NAMESPACE} <pod-name> -- /bin/sh

서비스 확인:
  kubectl get svc -n ${NAMESPACE}

전체 리소스 확인:
  kubectl get all -n ${NAMESPACE}

=== 환경 삭제 ===
  ./scripts/simulation-env-destroy.sh
EOF

echo ""
echo -e "${GREEN}=== 시뮬레이션 환경 생성 완료! ===${NC}"
echo ""
echo "환경 정보가 simulation-env-info.txt에 저장되었습니다."
echo ""
echo "접속 정보:"
echo "  Backend: http://${BACKEND_IP}"
echo "  Frontend: http://${FRONTEND_IP}"
echo "  Grafana: http://${GRAFANA_IP}:3000 (admin/admin)"
echo "  Prometheus: http://${PROMETHEUS_IP}:9090"
echo ""

if [ "$BACKEND_IP" == "pending" ]; then
    echo -e "${YELLOW}주의: External IP가 아직 할당되지 않았습니다.${NC}"
    echo "다음 명령어로 상태를 확인하세요:"
    echo "  kubectl get svc -n ${NAMESPACE}"
fi
