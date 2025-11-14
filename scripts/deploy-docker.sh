#!/bin/bash
#
# Docker Compose 배포 스크립트
#
# 사용법:
#   ./scripts/deploy-docker.sh [start|stop|restart|logs|status]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.full.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

check_env() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warn ".env file not found. Copying from .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        log_warn "Please update .env file with your configuration."
        exit 1
    fi
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

start_services() {
    log_info "Starting Agentic AI services..."
    check_env

    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" up -d

    log_info "Services started successfully!"
    log_info ""
    log_info "Access URLs:"
    log_info "  - Frontend: http://localhost:3000"
    log_info "  - Backend API: http://localhost:8000"
    log_info "  - API Docs: http://localhost:8000/docs"
    log_info "  - Grafana: http://localhost:3001 (admin/admin)"
    log_info "  - Prometheus: http://localhost:9090"
    log_info ""
    log_info "Run 'docker-compose -f $COMPOSE_FILE logs -f' to view logs"
}

stop_services() {
    log_info "Stopping Agentic AI services..."
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" down
    log_info "Services stopped successfully!"
}

restart_services() {
    log_info "Restarting Agentic AI services..."
    stop_services
    sleep 2
    start_services
}

show_logs() {
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" logs -f
}

show_status() {
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps

    log_info ""
    log_info "Service Health:"

    # Check backend health
    if curl -s -f http://localhost:8000/api/monitoring/health > /dev/null 2>&1; then
        log_info "  ✓ Backend API: Healthy"
    else
        log_warn "  ✗ Backend API: Unhealthy or not responding"
    fi

    # Check frontend
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        log_info "  ✓ Frontend: Healthy"
    else
        log_warn "  ✗ Frontend: Unhealthy or not responding"
    fi

    # Check Grafana
    if curl -s -f http://localhost:3001/api/health > /dev/null 2>&1; then
        log_info "  ✓ Grafana: Healthy"
    else
        log_warn "  ✗ Grafana: Unhealthy or not responding"
    fi
}

build_images() {
    log_info "Building Docker images..."
    cd "$PROJECT_ROOT"

    docker build -f Dockerfile.backend -t agentic-ai-backend:latest .
    docker build -f Dockerfile.frontend -t agentic-ai-frontend:latest .

    log_info "Images built successfully!"
}

# Main
check_docker

case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    build)
        build_images
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Usage: $0 [start|stop|restart|logs|status|build]"
        exit 1
        ;;
esac
