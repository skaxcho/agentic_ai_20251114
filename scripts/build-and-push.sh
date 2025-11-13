#!/bin/bash
# Docker 이미지 빌드 및 ACR 푸시 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ACR 정보 (환경 변수 또는 기본값)
ACR_NAME=${ACR_NAME:-"agenticairegistry"}
IMAGE_NAME="agentic-ai-platform"
VERSION=${VERSION:-$(date +%Y%m%d-%H%M%S)}

echo -e "${GREEN}=== Docker 이미지 빌드 및 푸시 ===${NC}"
echo "ACR: ${ACR_NAME}.azurecr.io"
echo "이미지: ${IMAGE_NAME}"
echo "버전: ${VERSION}"
echo ""

# 1. ACR 로그인
echo -e "${YELLOW}[1/4] ACR 로그인...${NC}"
az acr login --name ${ACR_NAME}

# 2. 이미지 빌드
echo -e "${YELLOW}[2/4] Docker 이미지 빌드...${NC}"
docker build -t ${IMAGE_NAME}:${VERSION} .
docker tag ${IMAGE_NAME}:${VERSION} ${IMAGE_NAME}:latest

# 3. ACR 태그
echo -e "${YELLOW}[3/4] ACR 태그 추가...${NC}"
docker tag ${IMAGE_NAME}:${VERSION} ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${VERSION}
docker tag ${IMAGE_NAME}:latest ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest

# 4. ACR 푸시
echo -e "${YELLOW}[4/4] ACR 푸시...${NC}"
docker push ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${VERSION}
docker push ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest

echo ""
echo -e "${GREEN}=== 빌드 및 푸시 완료! ===${NC}"
echo ""
echo "이미지 정보:"
echo "  ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${VERSION}"
echo "  ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest"
echo ""
echo "다음 단계:"
echo "  1. deployment/aks/api-deployment.yaml 에서 이미지 버전 업데이트"
echo "  2. kubectl apply -f deployment/aks/"
echo ""
