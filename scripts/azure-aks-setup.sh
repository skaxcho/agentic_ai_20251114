#!/bin/bash
# Azure AKS 환경 구축 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정 변수
RESOURCE_GROUP=${RESOURCE_GROUP:-"agentic-ai-rg"}
LOCATION=${LOCATION:-"koreacentral"}
AKS_CLUSTER_NAME=${AKS_CLUSTER_NAME:-"agentic-ai-aks"}
ACR_NAME=${ACR_NAME:-"agenticairegistry"}
NODE_COUNT=${NODE_COUNT:-3}
NODE_VM_SIZE=${NODE_VM_SIZE:-"Standard_D4s_v3"}

echo -e "${GREEN}=== Azure AKS 환경 구축 시작 ===${NC}"

# 1. Azure 로그인 확인
echo -e "${YELLOW}[1/8] Azure 로그인 확인...${NC}"
az account show > /dev/null 2>&1 || {
    echo -e "${RED}Azure 로그인이 필요합니다${NC}"
    az login
}

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}✓ 구독 ID: ${SUBSCRIPTION_ID}${NC}"

# 2. 리소스 그룹 생성
echo -e "${YELLOW}[2/8] 리소스 그룹 생성...${NC}"
az group create \
    --name ${RESOURCE_GROUP} \
    --location ${LOCATION} \
    --output table

# 3. Azure Container Registry (ACR) 생성
echo -e "${YELLOW}[3/8] Azure Container Registry 생성...${NC}"
az acr create \
    --resource-group ${RESOURCE_GROUP} \
    --name ${ACR_NAME} \
    --sku Standard \
    --location ${LOCATION} \
    --output table

# ACR 관리자 계정 활성화
az acr update \
    --name ${ACR_NAME} \
    --admin-enabled true

# ACR 로그인
az acr login --name ${ACR_NAME}

echo -e "${GREEN}✓ ACR 생성 완료: ${ACR_NAME}.azurecr.io${NC}"

# 4. AKS 클러스터 생성
echo -e "${YELLOW}[4/8] AKS 클러스터 생성 (10-15분 소요)...${NC}"
az aks create \
    --resource-group ${RESOURCE_GROUP} \
    --name ${AKS_CLUSTER_NAME} \
    --node-count ${NODE_COUNT} \
    --node-vm-size ${NODE_VM_SIZE} \
    --enable-managed-identity \
    --attach-acr ${ACR_NAME} \
    --generate-ssh-keys \
    --network-plugin azure \
    --enable-addons monitoring \
    --location ${LOCATION} \
    --output table

echo -e "${GREEN}✓ AKS 클러스터 생성 완료${NC}"

# 5. kubectl 자격 증명 가져오기
echo -e "${YELLOW}[5/8] kubectl 자격 증명 구성...${NC}"
az aks get-credentials \
    --resource-group ${RESOURCE_GROUP} \
    --name ${AKS_CLUSTER_NAME} \
    --overwrite-existing

# kubectl 확인
kubectl get nodes

# 6. Namespace 생성
echo -e "${YELLOW}[6/8] Kubernetes Namespace 생성...${NC}"
kubectl create namespace agentic-ai --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace agentic-ai-simulation --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Namespaces 생성 완료${NC}"

# 7. Azure OpenAI 리소스 생성
echo -e "${YELLOW}[7/8] Azure OpenAI 리소스 생성...${NC}"
OPENAI_RESOURCE_NAME="agentic-ai-openai-${RANDOM}"

az cognitiveservices account create \
    --name ${OPENAI_RESOURCE_NAME} \
    --resource-group ${RESOURCE_GROUP} \
    --kind OpenAI \
    --sku S0 \
    --location eastus \
    --yes \
    --output table

# GPT-4 모델 배포
az cognitiveservices account deployment create \
    --name ${OPENAI_RESOURCE_NAME} \
    --resource-group ${RESOURCE_GROUP} \
    --deployment-name gpt-4 \
    --model-name gpt-4 \
    --model-version "0613" \
    --model-format OpenAI \
    --sku-name "Standard" \
    --sku-capacity 10

# Embedding 모델 배포
az cognitiveservices account deployment create \
    --name ${OPENAI_RESOURCE_NAME} \
    --resource-group ${RESOURCE_GROUP} \
    --deployment-name text-embedding-ada-002 \
    --model-name text-embedding-ada-002 \
    --model-version "2" \
    --model-format OpenAI \
    --sku-name "Standard" \
    --sku-capacity 10

# OpenAI 키 가져오기
OPENAI_KEY=$(az cognitiveservices account keys list \
    --name ${OPENAI_RESOURCE_NAME} \
    --resource-group ${RESOURCE_GROUP} \
    --query key1 -o tsv)

OPENAI_ENDPOINT=$(az cognitiveservices account show \
    --name ${OPENAI_RESOURCE_NAME} \
    --resource-group ${RESOURCE_GROUP} \
    --query properties.endpoint -o tsv)

echo -e "${GREEN}✓ Azure OpenAI 리소스 생성 완료${NC}"

# 8. Kubernetes Secrets 생성
echo -e "${YELLOW}[8/8] Kubernetes Secrets 생성...${NC}"

# Azure OpenAI Secret
kubectl create secret generic azure-openai-secret \
    --from-literal=endpoint=${OPENAI_ENDPOINT} \
    --from-literal=api-key=${OPENAI_KEY} \
    --from-literal=deployment-name=gpt-4 \
    --from-literal=embedding-deployment=text-embedding-ada-002 \
    --namespace=agentic-ai \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓ Secrets 생성 완료${NC}"

# 환경 정보 저장
cat > azure-env-info.txt << EOF
=== Azure AKS 환경 정보 ===
리소스 그룹: ${RESOURCE_GROUP}
위치: ${LOCATION}
AKS 클러스터: ${AKS_CLUSTER_NAME}
ACR 이름: ${ACR_NAME}
ACR 주소: ${ACR_NAME}.azurecr.io
Azure OpenAI 리소스: ${OPENAI_RESOURCE_NAME}
Azure OpenAI Endpoint: ${OPENAI_ENDPOINT}

=== kubectl 명령어 ===
클러스터 노드 확인:
  kubectl get nodes

Pod 확인:
  kubectl get pods -n agentic-ai

서비스 확인:
  kubectl get svc -n agentic-ai

로그 확인:
  kubectl logs -n agentic-ai <pod-name>

=== ACR 이미지 푸시 ===
로컬 이미지 빌드:
  docker build -t agentic-ai-platform:latest .

ACR 태그:
  docker tag agentic-ai-platform:latest ${ACR_NAME}.azurecr.io/agentic-ai-platform:latest

ACR 푸시:
  docker push ${ACR_NAME}.azurecr.io/agentic-ai-platform:latest

=== 리소스 정리 ===
전체 삭제:
  az group delete --name ${RESOURCE_GROUP} --yes --no-wait
EOF

echo -e "${GREEN}✓ 환경 정보가 azure-env-info.txt에 저장되었습니다${NC}"

echo ""
echo -e "${GREEN}=== Azure AKS 환경 구축 완료! ===${NC}"
echo ""
echo "다음 단계:"
echo "1. 이미지 빌드 및 ACR 푸시:"
echo "   ./scripts/build-and-push.sh"
echo ""
echo "2. 애플리케이션 배포:"
echo "   kubectl apply -f deployment/aks/"
echo ""
echo "3. 시뮬레이션 환경 생성:"
echo "   ./scripts/simulation-env-create.sh"
echo ""
