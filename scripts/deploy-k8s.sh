#!/bin/bash
#
# Kubernetes 배포 스크립트
#
# 사용법:
#   ./scripts/deploy-k8s.sh [deploy|delete|status|logs]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$PROJECT_ROOT/k8s"
NAMESPACE="agentic-ai"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi

    # Check if connected to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Not connected to any Kubernetes cluster."
        exit 1
    fi
}

create_secrets() {
    log_info "Creating secrets..."

    # Check if .env exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_error ".env file not found. Please create it first."
        exit 1
    fi

    # Source .env file
    source "$PROJECT_ROOT/.env"

    # Create backend secret
    kubectl create secret generic backend-secret \
        --from-literal=AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}" \
        --from-literal=AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT}" \
        --from-literal=AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-gpt-4}" \
        --from-literal=AZURE_OPENAI_EMBEDDING_DEPLOYMENT="${AZURE_OPENAI_EMBEDDING_DEPLOYMENT:-text-embedding-ada-002}" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -

    # Create postgres secret
    kubectl create secret generic postgres-secret \
        --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-secure_password}" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -

    log_info "Secrets created successfully!"
}

deploy_all() {
    log_info "Deploying Agentic AI to Kubernetes..."

    # Create namespace
    log_info "Creating namespace..."
    kubectl apply -f "$K8S_DIR/namespace.yaml"

    # Create secrets
    create_secrets

    # Deploy database
    log_info "Deploying PostgreSQL..."
    kubectl apply -f "$K8S_DIR/database/postgres-statefulset.yaml"

    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s || true

    # Deploy backend
    log_info "Deploying backend..."
    kubectl apply -f "$K8S_DIR/backend/deployment.yaml"

    # Deploy frontend
    log_info "Deploying frontend..."
    kubectl apply -f "$K8S_DIR/frontend/deployment.yaml"

    # Deploy monitoring
    log_info "Deploying monitoring stack..."
    kubectl apply -f "$K8S_DIR/monitoring/prometheus.yaml"
    kubectl apply -f "$K8S_DIR/monitoring/grafana.yaml"

    log_info "Deployment completed!"
    log_info ""
    log_info "Waiting for deployments to be ready..."
    kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=600s || true
    kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=600s || true

    show_status
}

delete_all() {
    log_warn "Deleting Agentic AI from Kubernetes..."

    read -p "Are you sure you want to delete all resources? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Deletion cancelled."
        exit 0
    fi

    # Delete monitoring
    kubectl delete -f "$K8S_DIR/monitoring/grafana.yaml" || true
    kubectl delete -f "$K8S_DIR/monitoring/prometheus.yaml" || true

    # Delete frontend
    kubectl delete -f "$K8S_DIR/frontend/deployment.yaml" || true

    # Delete backend
    kubectl delete -f "$K8S_DIR/backend/deployment.yaml" || true

    # Delete database
    kubectl delete -f "$K8S_DIR/database/postgres-statefulset.yaml" || true

    # Delete secrets
    kubectl delete secret backend-secret postgres-secret -n "$NAMESPACE" || true

    # Delete namespace (optional)
    read -p "Delete namespace '$NAMESPACE'? (yes/no): " confirm_ns
    if [ "$confirm_ns" == "yes" ]; then
        kubectl delete namespace "$NAMESPACE" || true
    fi

    log_info "Deletion completed!"
}

show_status() {
    log_info "Kubernetes Resources Status:"
    echo ""

    log_info "Pods:"
    kubectl get pods -n "$NAMESPACE" -o wide

    echo ""
    log_info "Services:"
    kubectl get svc -n "$NAMESPACE"

    echo ""
    log_info "Deployments:"
    kubectl get deployments -n "$NAMESPACE"

    echo ""
    log_info "StatefulSets:"
    kubectl get statefulsets -n "$NAMESPACE"

    echo ""
    log_info "HPA (Horizontal Pod Autoscaler):"
    kubectl get hpa -n "$NAMESPACE" || true

    echo ""
    log_info "Access URLs:"

    # Get LoadBalancer IPs
    FRONTEND_IP=$(kubectl get svc frontend -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    GRAFANA_IP=$(kubectl get svc grafana -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

    log_info "  - Frontend: http://$FRONTEND_IP"
    log_info "  - Backend API: http://$FRONTEND_IP/api"
    log_info "  - Grafana: http://$GRAFANA_IP:3000"

    if [ "$FRONTEND_IP" == "pending" ] || [ "$GRAFANA_IP" == "pending" ]; then
        log_warn ""
        log_warn "LoadBalancer IPs are still pending. Run this command again later."
        log_warn "Or use port-forward to access services:"
        log_warn "  kubectl port-forward -n $NAMESPACE svc/frontend 3000:80"
        log_warn "  kubectl port-forward -n $NAMESPACE svc/backend 8000:8000"
        log_warn "  kubectl port-forward -n $NAMESPACE svc/grafana 3001:3000"
    fi
}

show_logs() {
    SERVICE="${2:-backend}"

    log_info "Showing logs for $SERVICE..."

    case "$SERVICE" in
        backend)
            kubectl logs -f -l app=backend -n "$NAMESPACE" --tail=100
            ;;
        frontend)
            kubectl logs -f -l app=frontend -n "$NAMESPACE" --tail=100
            ;;
        postgres)
            kubectl logs -f -l app=postgres -n "$NAMESPACE" --tail=100
            ;;
        prometheus)
            kubectl logs -f -l app=prometheus -n "$NAMESPACE" --tail=100
            ;;
        grafana)
            kubectl logs -f -l app=grafana -n "$NAMESPACE" --tail=100
            ;;
        *)
            log_error "Unknown service: $SERVICE"
            log_info "Available services: backend, frontend, postgres, prometheus, grafana"
            exit 1
            ;;
    esac
}

scale_deployment() {
    DEPLOYMENT="$2"
    REPLICAS="$3"

    if [ -z "$DEPLOYMENT" ] || [ -z "$REPLICAS" ]; then
        log_error "Usage: $0 scale <deployment> <replicas>"
        exit 1
    fi

    log_info "Scaling $DEPLOYMENT to $REPLICAS replicas..."
    kubectl scale deployment "$DEPLOYMENT" --replicas="$REPLICAS" -n "$NAMESPACE"
    log_info "Scaled successfully!"
}

# Main
check_kubectl

case "${1:-deploy}" in
    deploy)
        deploy_all
        ;;
    delete)
        delete_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$@"
        ;;
    scale)
        scale_deployment "$@"
        ;;
    secrets)
        create_secrets
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Usage: $0 [deploy|delete|status|logs|scale|secrets]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy all resources to Kubernetes"
        echo "  delete  - Delete all resources from Kubernetes"
        echo "  status  - Show status of all resources"
        echo "  logs    - Show logs (usage: $0 logs [backend|frontend|postgres])"
        echo "  scale   - Scale deployment (usage: $0 scale <deployment> <replicas>)"
        echo "  secrets - Create/update secrets"
        exit 1
        ;;
esac
