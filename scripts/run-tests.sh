#!/bin/bash
#
# 통합 테스트 실행 스크립트
#
# 사용법:
#   ./scripts/run-tests.sh [all|unit|integration|e2e|load]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Check if services are running
check_services() {
    log_info "Checking if services are running..."

    if ! curl -s -f http://localhost:8000/api/monitoring/health > /dev/null 2>&1; then
        log_warn "Backend is not running. Starting Docker Compose..."
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.full.yml up -d

        log_info "Waiting for services to be ready..."
        for i in {1..30}; do
            if curl -s -f http://localhost:8000/api/monitoring/health > /dev/null 2>&1; then
                log_info "Backend is ready!"
                break
            fi
            echo -n "."
            sleep 2
        done
        echo ""
    else
        log_info "Services are running!"
    fi
}

# Run unit tests
run_unit_tests() {
    log_section "Running Unit Tests"

    cd "$PROJECT_ROOT"

    # Install test dependencies
    pip install -q pytest pytest-asyncio pytest-cov httpx

    # Run unit tests with coverage
    pytest tests/unit -v --cov=src --cov-report=html --cov-report=term

    log_info "Unit tests completed!"
    log_info "Coverage report: $PROJECT_ROOT/htmlcov/index.html"
}

# Run integration tests
run_integration_tests() {
    log_section "Running Integration Tests"

    check_services

    cd "$PROJECT_ROOT"

    # Run integration tests
    pytest tests/integration -v

    log_info "Integration tests completed!"
}

# Run E2E tests
run_e2e_tests() {
    log_section "Running E2E Scenario Tests"

    check_services

    cd "$PROJECT_ROOT"

    # Run E2E tests
    pytest tests/integration/test_e2e_scenarios.py -v

    log_info "E2E tests completed!"
}

# Run load tests
run_load_tests() {
    log_section "Running Load Tests with Locust"

    check_services

    cd "$PROJECT_ROOT"

    # Install locust
    pip install -q locust

    log_info "Starting Locust load test..."
    log_info "Test parameters:"
    log_info "  - Users: 50"
    log_info "  - Spawn rate: 5 users/sec"
    log_info "  - Duration: 2 minutes"

    # Run locust in headless mode
    locust -f tests/load/locustfile.py \
        --host=http://localhost:8000 \
        --users=50 \
        --spawn-rate=5 \
        --run-time=2m \
        --headless \
        --html=load-test-report.html \
        --csv=load-test-results

    log_info "Load test completed!"
    log_info "Report: $PROJECT_ROOT/load-test-report.html"
}

# Generate test data
generate_test_data() {
    log_section "Generating Test Data"

    cd "$PROJECT_ROOT"
    python scripts/generate_test_data.py

    log_info "Test data generated successfully!"
}

# Run all tests
run_all_tests() {
    log_section "Running All Tests"

    generate_test_data
    run_unit_tests
    run_integration_tests
    run_e2e_tests

    log_section "Test Summary"
    log_info "✓ Unit tests completed"
    log_info "✓ Integration tests completed"
    log_info "✓ E2E tests completed"
    log_info ""
    log_info "To run load tests, execute: $0 load"
}

# Show test status
show_test_status() {
    log_section "Test Status"

    # Check test coverage
    if [ -f "$PROJECT_ROOT/.coverage" ]; then
        log_info "Latest test coverage:"
        coverage report
    else
        log_warn "No coverage data found. Run unit tests first."
    fi

    # Check test results
    if [ -f "$PROJECT_ROOT/load-test-results_stats.csv" ]; then
        log_info ""
        log_info "Latest load test results:"
        cat "$PROJECT_ROOT/load-test-results_stats.csv"
    fi
}

# Main
cd "$PROJECT_ROOT"

case "${1:-all}" in
    all)
        run_all_tests
        ;;
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    load)
        run_load_tests
        ;;
    data)
        generate_test_data
        ;;
    status)
        show_test_status
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Usage: $0 [all|unit|integration|e2e|load|data|status]"
        echo ""
        echo "Commands:"
        echo "  all         - Run all tests (except load tests)"
        echo "  unit        - Run unit tests with coverage"
        echo "  integration - Run integration tests"
        echo "  e2e         - Run E2E scenario tests"
        echo "  load        - Run load tests with Locust"
        echo "  data        - Generate test data"
        echo "  status      - Show test status and coverage"
        exit 1
        ;;
esac
