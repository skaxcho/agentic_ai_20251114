#!/bin/bash
# 시뮬레이션 환경 삭제 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

NAMESPACE="agentic-ai-simulation"

echo -e "${YELLOW}=== 시뮬레이션 환경 삭제 ===${NC}"
echo ""
echo "다음 리소스가 삭제됩니다:"
echo "  - Namespace: ${NAMESPACE}"
echo "  - 모든 Deployments, Services, PVCs"
echo ""
read -p "계속하시겠습니까? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "삭제가 취소되었습니다."
    exit 0
fi

echo ""
echo -e "${YELLOW}삭제 시작...${NC}"

# 1. 현재 리소스 확인
echo -e "${YELLOW}[1/3] 현재 리소스 확인...${NC}"
kubectl get all -n ${NAMESPACE}

# 2. Namespace 삭제 (모든 리소스 포함)
echo ""
echo -e "${YELLOW}[2/3] Namespace 삭제 중...${NC}"
kubectl delete namespace ${NAMESPACE} --timeout=120s

# 3. PV 정리 (필요시)
echo ""
echo -e "${YELLOW}[3/3] PersistentVolume 정리...${NC}"
kubectl get pv | grep ${NAMESPACE} | awk '{print $1}' | xargs -r kubectl delete pv

echo ""
echo -e "${GREEN}=== 시뮬레이션 환경 삭제 완료! ===${NC}"
echo ""
echo "확인:"
echo "  kubectl get namespace ${NAMESPACE}"
echo ""
