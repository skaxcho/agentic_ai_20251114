# CLAUDE.md - AI Assistant Guide for Agentic AI Platform

This document provides comprehensive guidance for AI assistants (like Claude) working on this codebase. It explains the project structure, development workflows, conventions, and best practices.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Technology Stack](#technology-stack)
4. [Development Workflows](#development-workflows)
5. [Key Conventions](#key-conventions)
6. [Agent Development Guidelines](#agent-development-guidelines)
7. [Testing Guidelines](#testing-guidelines)
8. [Deployment Workflows](#deployment-workflows)
9. [Common Tasks](#common-tasks)
10. [Important Files Reference](#important-files-reference)

---

## Project Overview

**Agentic AI Platform** is a production-ready, multi-agent AI system designed for IT operations automation. The platform features 8 specialized AI agents that collaborate to automate complex IT workflows.

### Key Statistics
- **Status**: Phase 4 Complete (100% implementation)
- **Total Codebase**: ~6,200 lines of Python code
- **Agents**: 8 specialized agents (~175KB of agent code)
- **Documentation**: 19 markdown files (~150KB)
- **Development Period**: 16 weeks (4 phases)

### Architecture Overview
```
User Interface (React)
    ↓
FastAPI REST API Gateway
    ↓
Orchestration Manager (Crew AI)
    ↓
8 AI Agents + Common Services (LLM, RAG, MCP Hub)
    ↓
Data Layer (PostgreSQL, Redis, Qdrant)
    ↓
External Systems (ServiceNow, Cloud, DevOps)
```

---

## Repository Structure

### Root Directory Layout
```
/home/user/agentic_ai_20251114/
├── src/                      # Backend Python source code
│   ├── core/                 # Core modules and services
│   ├── agents/               # 8 AI agent implementations
│   ├── api/                  # FastAPI routes and models
│   └── db/                   # Database models and repositories
├── frontend/                 # React TypeScript frontend
│   ├── src/components/       # React components
│   └── src/services/         # API client services
├── tests/                    # Test suites
│   ├── integration/          # Integration tests
│   └── load/                 # Load tests (Locust)
├── scripts/                  # Utility and deployment scripts
├── knowledge-base/           # RAG knowledge base documents
├── monitoring/               # Prometheus & Grafana configs
├── deployment/               # Azure AKS deployment configs
├── k8s/                      # Kubernetes manifests
├── docs/                     # User documentation
└── docker-compose.yml        # Local development environment
```

### Backend Structure (src/)
```
src/
├── core/
│   ├── base/                 # BaseAgent abstract class
│   ├── services/             # LLMService, RAGService, VectorDBService, MCPHub
│   ├── tools/                # Reusable tools (DB, Cloud, DevOps, ServiceNow)
│   └── orchestration/        # Multi-agent orchestration manager
├── agents/                   # 8 agent implementations
│   ├── report_agent.py       # Report automation (16KB)
│   ├── monitoring_agent.py   # System monitoring (20KB)
│   ├── its_agent.py          # ServiceNow ticket management (18KB)
│   ├── db_extract_agent.py   # Natural language to SQL (18KB)
│   ├── change_mgmt_agent.py  # Change orchestrator (28KB) - MASTER
│   ├── biz_support_agent.py  # RAG-based user support (18KB)
│   ├── sop_agent.py          # Incident response (25KB)
│   └── infra_agent.py        # Infrastructure management (27KB)
├── api/
│   ├── main.py               # FastAPI application entry point
│   ├── routes/               # API route handlers
│   │   ├── agents.py         # Agent execution endpoints
│   │   ├── tasks.py          # Task management endpoints
│   │   ├── workflows.py      # Workflow orchestration endpoints
│   │   └── monitoring.py     # Monitoring endpoints
│   └── websocket.py          # WebSocket support for real-time updates
└── db/
    ├── models.py             # SQLAlchemy models (User, Task, AgentExecution, etc.)
    ├── database.py           # Database connection management
    └── repositories.py       # Data access layer
```

### Frontend Structure (frontend/)
```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx     # Main dashboard
│   │   ├── AgentSelector.tsx # Agent selection UI
│   │   └── TaskMonitor.tsx   # Task monitoring UI
│   ├── services/
│   │   └── api.ts            # API client
│   ├── App.tsx               # Root component
│   └── main.tsx              # Entry point
├── package.json              # NPM dependencies
├── vite.config.ts            # Vite configuration
└── tsconfig.json             # TypeScript configuration
```

---

## Technology Stack

### Core AI & Orchestration
- **Multi-Agent Framework**: Crew AI 0.1.0 (Role-based agents, task delegation)
- **LLM**: Azure OpenAI GPT-4 (gpt-4-0613)
- **Embedding**: Azure OpenAI text-embedding-ada-002
- **AI Framework**: LangChain 0.1.0, LangGraph 0.0.20
- **Vector Database**: Qdrant 1.7.0 (for RAG system)

### Backend Technologies
- **API Framework**: FastAPI 0.109.0
- **ASGI Server**: Uvicorn 0.27.0
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0.25
- **Cache/Queue**: Redis 5.0.1
- **Validation**: Pydantic 2.5.0

### Frontend Technologies
- **Framework**: React 18.2 + TypeScript
- **UI Library**: Material-UI (MUI) 5.14
- **State Management**: React Query (@tanstack/react-query)
- **Build Tool**: Vite 5.0
- **HTTP Client**: Axios
- **Real-time**: Socket.IO Client

### DevOps & Infrastructure
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (Azure AKS)
- **Monitoring**: Prometheus + Grafana
- **Reverse Proxy**: Nginx

### Python Dependencies (Key Libraries)
```python
# Core AI
crewai==0.1.0
langchain==0.1.0
langgraph==0.0.20
openai==1.0.0
qdrant-client==1.7.0

# Backend
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.0
sqlalchemy==2.0.25
redis==5.0.1
psycopg2-binary==2.9.9

# Utilities
python-dotenv==1.0.0
tenacity==8.2.3  # Retry logic
aiofiles==23.2.1  # Async file operations
httpx==0.25.2     # Async HTTP client

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Code Quality
black==23.12.0
flake8==6.1.0
mypy==1.7.1
pre-commit==3.5.0

# Monitoring
prometheus-client==0.19.0
```

---

## Development Workflows

### Local Development Setup

#### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd agentic_ai_20251114

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with Azure OpenAI credentials and other settings
```

#### 2. Start Infrastructure Services
```bash
# Start PostgreSQL, Redis, Qdrant, Prometheus, Grafana
docker-compose up -d

# Verify services are running
docker-compose ps
```

#### 3. Initialize Knowledge Base
```bash
# Build RAG knowledge base (indexes documents into Qdrant)
python scripts/build_knowledge_base.py
```

#### 4. Run Backend API
```bash
# Development mode with auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080

# API will be available at http://localhost:8080
# API docs at http://localhost:8080/docs
```

#### 5. Run Frontend (separate terminal)
```bash
cd frontend
npm install
npm run dev

# Frontend will be available at http://localhost:5173
```

### Git Workflow

#### Branch Naming Convention
- All Claude-created branches MUST start with `claude/`
- Current branch: `claude/claude-md-mhypx786wy57fedw-0193GobCeNk4KEFv46zt6o9R`
- Main branch: (to be specified)

#### Commit Guidelines
```bash
# Commit message format
git commit -m "$(cat <<'EOF'
feat: Add monitoring dashboard component

- Implement real-time metrics display
- Add chart visualizations
- Integrate with Prometheus API
EOF
)"
```

**Commit Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `docs:` - Documentation updates
- `test:` - Test additions/modifications
- `chore:` - Maintenance tasks

#### Push Workflow
```bash
# Always push to Claude branches with -u flag
git push -u origin claude/branch-name

# If push fails due to network errors, retry up to 4 times
# with exponential backoff (2s, 4s, 8s, 16s)
```

---

## Key Conventions

### Code Style and Standards

#### Python Conventions
- **PEP 8 Compliance**: Enforced by black and flake8
- **Type Hints**: Full mypy type checking required
- **Docstrings**: Google-style docstrings for all functions
- **Line Length**: 120 characters (configured in black)

**Example:**
```python
from typing import List, Dict, Any, Optional

def execute_task(
    self,
    task: Dict[str, Any],
    timeout: Optional[int] = 300
) -> Dict[str, Any]:
    """
    Execute a task with the specified parameters.

    Args:
        task: Dictionary containing task parameters
        timeout: Optional timeout in seconds (default: 300)

    Returns:
        Dictionary containing task execution results

    Raises:
        ValueError: If task parameters are invalid
        TimeoutError: If execution exceeds timeout
    """
    pass
```

#### TypeScript/React Conventions
- **Functional Components**: Use functional components with hooks
- **Type Safety**: Explicit TypeScript interfaces for all props
- **File Naming**: PascalCase for components (e.g., `AgentSelector.tsx`)

**Example:**
```typescript
interface AgentSelectorProps {
  onSelect: (agentName: string) => void;
  selectedAgent?: string;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  onSelect,
  selectedAgent
}) => {
  // Component implementation
};
```

### Naming Conventions

#### Python
- **Classes**: PascalCase (e.g., `MonitoringAgent`, `RAGService`)
- **Functions/Methods**: snake_case (e.g., `execute_task`, `rag_query`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private Methods**: Prefix with `_` (e.g., `_log_action`, `_validate_input`)

#### TypeScript/React
- **Components**: PascalCase (e.g., `TaskMonitor`, `AgentCard`)
- **Functions**: camelCase (e.g., `fetchAgents`, `handleSubmit`)
- **Interfaces**: PascalCase with descriptive names (e.g., `AgentExecutionResult`)
- **Constants**: UPPER_SNAKE_CASE

### Logging Convention
```python
import logging

# Logger naming: "Agent.{AgentName}" or "Service.{ServiceName}"
logger = logging.getLogger(f"Agent.{self.name}")

# Log levels
logger.debug("Detailed debugging information")
logger.info("General informational messages")
logger.warning("Warning messages for potential issues")
logger.error("Error messages for failures")
logger.critical("Critical failures requiring immediate attention")
```

### Error Handling Pattern
```python
try:
    result = await self.execute_task(task)
except ValueError as e:
    logger.error(f"Invalid task parameters: {e}")
    raise
except TimeoutError as e:
    logger.error(f"Task execution timeout: {e}")
    # Implement retry logic or graceful degradation
except Exception as e:
    logger.critical(f"Unexpected error during task execution: {e}")
    # Send notification, update metrics
    raise
```

---

## Agent Development Guidelines

### Agent Architecture

All agents extend the `BaseAgent` class located at `src/core/base/base_agent.py`.

#### BaseAgent Class Structure
```python
from abc import ABC, abstractmethod
from crewai import Agent, Task, Crew

class BaseAgent(ABC):
    """Base class for all AI agents"""

    def __init__(self, name: str, role: str, goal: str):
        self.name = name
        self.role = role
        self.goal = goal

        # Common services available to all agents
        self.llm_service = AzureOpenAIService()
        self.rag_service = RAGService()
        self.mcp_hub = MCPHub()
        self.auth_service = AuthService()

    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Define agent-specific tools"""
        pass

    @abstractmethod
    def execute_task(self, task: Dict) -> Dict:
        """Execute agent-specific task logic"""
        pass
```

### The 8 Specialized Agents

#### 1. Report Agent (`report_agent.py`)
- **Role**: Report Automation Specialist
- **Purpose**: Generate weekly reports, meeting minutes, status reports
- **Tools**: OneDriveTool, FileReaderTool, DocumentGeneratorTool
- **Use Cases**:
  - UC-R-01: Weekly report generation
  - UC-R-02: Meeting minutes from audio
  - UC-R-03: System status aggregation

#### 2. Monitoring Agent (`monitoring_agent.py`)
- **Role**: System Monitoring Specialist
- **Purpose**: Health checks, DB monitoring, log analysis, job monitoring
- **Tools**: URLHealthCheckTool, ServerAccessTool, DatabaseConnectionTool, LogAnalyzerTool
- **Use Cases**:
  - UC-M-01: Service health checks
  - UC-M-02: Database connectivity validation
  - UC-M-03: Log anomaly detection
  - UC-M-04: Scheduled job failure detection

#### 3. ITS Agent (`its_agent.py`)
- **Role**: IT Service Management Specialist
- **Purpose**: ServiceNow ticket management (incidents, requests, changes)
- **Tools**: ServiceNowTool, CertificateManagerTool, ConfigurationManagerTool
- **Use Cases**:
  - UC-I-01: Configuration item updates
  - UC-I-02: SSL certificate requests
  - UC-I-03: Incident auto-creation

#### 4. DB Extract Agent (`db_extract_agent.py`)
- **Role**: Database Analysis Specialist
- **Purpose**: Natural language to SQL conversion, data validation
- **Tools**: DatabaseTool, SQLGeneratorTool, DataValidatorTool
- **Use Cases**:
  - UC-D-01: Natural language query generation
  - UC-D-02: Data integrity validation
  - UC-D-03: Complex statistical queries

#### 5. Change Management Agent (`change_mgmt_agent.py`) **[MASTER ORCHESTRATOR]**
- **Role**: Change Management Orchestrator
- **Purpose**: Orchestrate entire change management workflows
- **Sub-Agents**: Can delegate to Report, ITS, Monitoring, Infra agents
- **Workflow Steps**:
  1. Create change plan (Report Agent)
  2. Request approval (ITS Agent)
  3. Execute deployment (DevOps tools)
  4. Post-deployment validation (Monitoring Agent)
  5. Generate final report (Report Agent)
- **Use Cases**:
  - UC-C-01: End-to-end performance improvement deployment
  - UC-C-02: Emergency patch deployment
  - UC-C-03: Regular change process automation

#### 6. Biz Support Agent (`biz_support_agent.py`)
- **Role**: Business Support Specialist
- **Purpose**: RAG-based user support, contact lookup
- **Tools**: RAGTool, ITSAgent (for ticket escalation), KnowledgeBaseTool
- **Use Cases**:
  - UC-B-01: User inquiry responses
  - UC-B-02: Contact information lookup
  - UC-B-03: Account provisioning requests

#### 7. SOP Agent (`sop_agent.py`)
- **Role**: Standard Operating Procedure Specialist
- **Purpose**: Incident detection, response procedures, case search
- **Tools**: MonitoringAgent, SOPKnowledgeBaseTool, RemediationTool, NotificationTool
- **Use Cases**:
  - UC-S-01: Automated incident detection and response
  - UC-S-02: Similar incident case search
  - UC-S-03: Incident notification and reporting

#### 8. Infra Agent (`infra_agent.py`)
- **Role**: Infrastructure Management Specialist
- **Purpose**: Performance analysis, auto-scaling, patching
- **Tools**: CloudProviderTool, DevOpsTool, GitTool, MonitoringAgent
- **Use Cases**:
  - UC-F-01: Performance analysis and diagnostics
  - UC-F-02: Auto-scaling execution
  - UC-F-03: Automated patching workflows

### Creating a New Agent

#### Step-by-Step Checklist
- [ ] Create agent file in `src/agents/{agent_name}_agent.py`
- [ ] Extend `BaseAgent` class
- [ ] Implement `get_tools()` method with agent-specific tools
- [ ] Implement `execute_task()` method with task logic
- [ ] Add Crew AI agent creation in `create_crew_agent()` if needed
- [ ] Define use cases in documentation
- [ ] Write unit tests in `tests/unit/test_{agent_name}_agent.py`
- [ ] Write integration tests in `tests/integration/`
- [ ] Add agent to `AGENTS` dictionary in `src/api/routes/agents.py`
- [ ] Update documentation

#### Agent Template
```python
# src/agents/new_agent.py
from src.core.base.base_agent import BaseAgent
from typing import List, Dict, Any

class NewAgent(BaseAgent):
    """New Agent - Brief description"""

    def __init__(self):
        super().__init__(
            name="NewAgent",
            role="Specialist Role",
            goal="What this agent aims to accomplish",
            backstory="Agent's expertise and background"
        )

    def get_tools(self) -> List:
        """Define agent-specific tools"""
        return [
            # List of tools this agent can use
        ]

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task"""
        task_type = task.get("task_type")

        if task_type == "example_task":
            return await self._handle_example_task(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _handle_example_task(self, task: Dict) -> Dict:
        """Handle specific task implementation"""
        # Task logic here
        return {
            "success": True,
            "result": "Task completed"
        }
```

---

## Testing Guidelines

### Test Structure
```
tests/
├── unit/                     # Unit tests for individual components
├── integration/              # Integration tests for agent workflows
│   ├── test_api_endpoints.py
│   └── test_e2e_scenarios.py
└── load/                     # Load tests
    └── locustfile.py
```

### Unit Testing
```python
# tests/unit/test_report_agent.py
import pytest
from src.agents.report_agent import ReportAgent

@pytest.fixture
def report_agent():
    return ReportAgent()

@pytest.mark.asyncio
async def test_weekly_report_generation(report_agent):
    """Test weekly report generation"""
    task = {
        "task_type": "weekly_report",
        "source_files": ["test_data/work_log_1.md"],
        "output_path": "/tmp/weekly_report.md"
    }

    result = await report_agent.execute_task(task)

    assert result["success"] is True
    assert "content" in result
    assert "주요 수행 업무" in result["content"]
```

### Integration Testing (E2E Scenarios)
```python
# tests/integration/test_e2e_scenarios.py
import pytest

@pytest.mark.e2e
async def test_performance_issue_to_deployment():
    """
    E2E Scenario 1: Performance Issue → Analysis → Deployment → Monitoring

    Tests the full workflow of:
    1. Monitoring Agent detects CPU > 90%
    2. SOP Agent analyzes and recommends action
    3. Infra Agent performs performance analysis
    4. Change Management Agent orchestrates deployment
    5. Report Agent generates final report
    """
    # Test implementation
    pass
```

### Testing Best Practices
- **Coverage Target**: >80% code coverage
- **Test Naming**: Use descriptive names starting with `test_`
- **Fixtures**: Use pytest fixtures for common setup
- **Markers**: Use `@pytest.mark.e2e` for end-to-end tests
- **Async Tests**: Use `@pytest.mark.asyncio` for async functions
- **Mocking**: Mock external services (Azure OpenAI, ServiceNow, etc.)

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_report_agent.py

# Run E2E tests only
pytest tests/integration/ -m e2e

# Run with verbose output
pytest tests/ -v

# Run load tests
cd tests/load
locust -f locustfile.py --host=http://localhost:8080
```

---

## Deployment Workflows

### Local Development (Docker Compose)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild services
docker-compose up -d --build
```

### Azure AKS Deployment

#### 1. Infrastructure Setup
```bash
# Login to Azure
az login

# Create AKS cluster and resources
./scripts/azure-aks-setup.sh

# This creates:
# - Azure Resource Group
# - Azure Container Registry (ACR)
# - AKS Cluster (3 nodes)
# - Azure OpenAI resource
# - Kubernetes namespaces and secrets
```

#### 2. Build and Push Images
```bash
# Build Docker images and push to ACR
./scripts/build-and-push.sh
```

#### 3. Deploy to Kubernetes
```bash
# Deploy all services
kubectl apply -f deployment/aks/

# Check deployment status
kubectl get pods -n agentic-ai
kubectl get svc -n agentic-ai

# View logs
kubectl logs -f deployment/backend-api -n agentic-ai
```

#### 4. Create Simulation Environment
```bash
# Create test environment with sample data
./scripts/simulation-env-create.sh

# View environment info
cat simulation-env-info.txt

# Destroy simulation environment when done
./scripts/simulation-env-destroy.sh
```

### Monitoring Access
```bash
# Get Grafana URL
kubectl get svc grafana -n agentic-ai

# Default credentials: admin/admin
# Access dashboards:
# - Agent Performance Dashboard
# - System Health Dashboard
# - Use Case Validation Dashboard
```

---

## Common Tasks

### 1. Adding a New API Endpoint
```python
# src/api/routes/custom.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/custom-endpoint")
async def custom_endpoint(data: dict):
    """Custom endpoint description"""
    return {"result": "success"}

# src/api/main.py
from src.api.routes import custom
app.include_router(custom.router, prefix="/api/custom", tags=["custom"])
```

### 2. Adding Documents to Knowledge Base
```python
# 1. Add documents to knowledge-base/ directory
# knowledge-base/manuals/new_manual.md

# 2. Run indexing script
python scripts/build_knowledge_base.py

# 3. Verify in Qdrant
# Access http://localhost:6333/dashboard
```

### 3. Creating a Custom Tool
```python
# src/core/tools/custom_tool.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class CustomToolInput(BaseModel):
    param: str = Field(description="Parameter description")

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "Tool description for LLM to understand when to use"
    args_schema: Type[BaseModel] = CustomToolInput

    def _run(self, param: str) -> str:
        """Synchronous implementation"""
        return f"Result: {param}"

    async def _arun(self, param: str) -> str:
        """Async implementation"""
        return self._run(param)
```

### 4. Adding Prometheus Metrics
```python
# src/api/monitoring/metrics.py
from prometheus_client import Counter, Histogram

# Define metric
custom_metric = Counter(
    'custom_metric_total',
    'Description of custom metric',
    ['label1', 'label2']
)

# Use in code
custom_metric.labels(label1='value1', label2='value2').inc()
```

### 5. Updating Environment Variables
```bash
# 1. Edit .env file
nano .env

# 2. Restart services
docker-compose down
docker-compose up -d

# 3. For Kubernetes, update secrets
kubectl create secret generic app-secrets \
  --from-env-file=.env \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

## Important Files Reference

### Core Configuration Files

#### `.env.example` - Environment Variables Template
Contains all required environment variables:
- Azure OpenAI configuration (endpoint, API key, deployments)
- Database connections (PostgreSQL, Redis, Qdrant)
- External systems (ServiceNow, OneDrive, Cloud providers)
- Monitoring (Prometheus, Grafana)
- Application settings (environment, logging, API keys)
- Agent parameters (temperature, max tokens, RAG settings)

#### `docker-compose.yml` - Local Development Environment
Defines services:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Qdrant (port 6333)
- Prometheus (port 9090)
- Grafana (port 3001)

All services include health checks and volume persistence.

#### `requirements.txt` - Python Dependencies
Complete list of Python packages with pinned versions for reproducibility.

### Documentation Files

#### Core Documentation
1. **README.md** - Project overview and quick start guide
2. **DEVELOPMENT_SPECIFICATION.md** (30KB) - Comprehensive technical design
   - Technology stack selection rationale (Crew AI vs Dify)
   - System architecture
   - 8 agent detailed designs
   - 16-week development plan
3. **IMPLEMENTATION_GUIDE.md** (56KB) - Step-by-step development guide
   - Environment setup
   - Azure OpenAI integration
   - Crew AI implementation
   - RAG system construction
   - MCP server development
   - API and frontend implementation
4. **USE_CASES_AND_TEST_SCENARIOS.md** (45KB)
   - 26 detailed use cases (3-4 per agent)
   - 3 end-to-end integration scenarios
   - Validation criteria and test strategies
5. **DEVELOPMENT_CHECKLIST.md** (20KB) - Progress tracking (100% complete)

#### Agent Opinion Documents
8 files analyzing each agent's design decisions:
- `ai-agent-report-opinion.md`
- `ai-agent-monitoring-opinion.md`
- `ai-agent-its-opinion.md`
- `ai-agent-dbExtract-opinion.md`
- `ai-agent-change-history-opinion.md`
- `ai-agent-biz-support-opinion.md`
- `ai-agent-SOP-opinion.md`
- `ai-agent-Infra-opinion.md`

### Key Source Files

#### Services (`src/core/services/`)
- `llm_service.py` - Azure OpenAI integration with retry logic
- `rag_service.py` - RAG system (retrieval, indexing, querying)
- `vector_db_service.py` - Qdrant vector database abstraction
- `mcp_hub.py` - MCP protocol integration hub
- `auth_service.py` - Authentication and authorization
- `notification_service.py` - Multi-channel notifications (Email, Slack)

#### Database (`src/db/`)
- `models.py` - SQLAlchemy models (User, Task, AgentExecution, WorkflowExecution, SystemMetrics)
- `database.py` - Database connection and session management
- `repositories.py` - Data access layer (TaskRepository, AgentExecutionRepository)

#### API Routes (`src/api/routes/`)
- `agents.py` - Agent management and execution endpoints
- `tasks.py` - Task CRUD and status tracking
- `workflows.py` - Multi-agent workflow orchestration
- `monitoring.py` - System health and metrics endpoints

### Deployment Files

#### Kubernetes (`k8s/` and `deployment/aks/`)
- Backend deployments and services
- Frontend deployments
- PostgreSQL StatefulSets
- Prometheus and Grafana configs
- Ingress rules
- ConfigMaps and Secrets

#### Scripts (`scripts/`)
- `build_knowledge_base.py` - Index documents into Qdrant
- `generate_test_data.py` - Create test data for validation
- `test_rag_performance.py` - Benchmark RAG system performance
- `azure-aks-setup.sh` - Provision Azure infrastructure
- `build-and-push.sh` - Build and push Docker images to ACR
- `simulation-env-create.sh` - Create test environment
- `simulation-env-destroy.sh` - Tear down test environment

---

## Best Practices for AI Assistants

### When Making Code Changes

1. **Always Read Before Edit**
   - Use Read tool to view current file content
   - Understand existing patterns and conventions
   - Never write files without reading them first

2. **Preserve Code Style**
   - Match existing indentation (spaces vs tabs)
   - Follow naming conventions
   - Maintain consistency with surrounding code

3. **Add Comprehensive Logging**
   ```python
   self.logger.info(f"Starting task execution: {task['task_type']}")
   self.logger.debug(f"Task parameters: {task}")
   # ... execute task
   self.logger.info(f"Task completed successfully")
   ```

4. **Handle Errors Gracefully**
   - Always use try-except blocks for external calls
   - Log errors with context
   - Return meaningful error messages
   - Update metrics on failures

5. **Update Documentation**
   - Add docstrings to new functions
   - Update relevant .md files
   - Include usage examples

### When Testing

1. **Write Tests First** (TDD approach when feasible)
2. **Test Edge Cases** - Don't just test happy paths
3. **Mock External Services** - Don't hit real Azure OpenAI in unit tests
4. **Use Fixtures** - Reuse common test setup
5. **Verify Metrics** - Check that Prometheus metrics are updated

### When Deploying

1. **Review Checklist**
   - All tests passing
   - Environment variables configured
   - Database migrations prepared
   - Backup created
   - Rollback plan documented

2. **Gradual Rollout**
   - Deploy to simulation environment first
   - Run E2E tests
   - Monitor metrics
   - Then deploy to production

3. **Monitor After Deployment**
   - Check Grafana dashboards
   - Review error logs
   - Validate key use cases
   - Monitor performance metrics

---

## Troubleshooting Guide

### Common Issues

#### Azure OpenAI Rate Limits
**Symptom**: HTTP 429 errors from Azure OpenAI
**Solution**:
- Check `tenacity` retry configuration in `llm_service.py`
- Implement request throttling
- Consider increasing quota in Azure portal

#### Qdrant Connection Failures
**Symptom**: Cannot connect to Qdrant on port 6333
**Solution**:
```bash
# Check if Qdrant is running
docker-compose ps qdrant

# Restart Qdrant
docker-compose restart qdrant

# Check logs
docker-compose logs qdrant
```

#### Agent Execution Timeouts
**Symptom**: Tasks exceeding timeout limits
**Solution**:
- Break tasks into smaller subtasks
- Increase timeout in task configuration
- Use async execution for long-running tasks
- Implement progress checkpoints

#### RAG Search Performance Issues
**Symptom**: Slow semantic search queries
**Solution**:
- Check Qdrant index configuration
- Reduce result limit
- Implement embedding caching
- Use batch queries

#### Database Connection Pool Exhausted
**Symptom**: "Too many connections" errors
**Solution**:
```python
# Adjust pool size in database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Increase from default
    max_overflow=40,     # Increase overflow
    pool_pre_ping=True   # Enable connection health checks
)
```

---

## Quick Reference Commands

### Development
```bash
# Start backend
uvicorn src.api.main:app --reload

# Start frontend
cd frontend && npm run dev

# Run tests
pytest tests/ --cov=src

# Format code
black src/
flake8 src/

# Type check
mypy src/
```

### Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Rebuild service
docker-compose up -d --build [service_name]

# Stop all services
docker-compose down
```

### Kubernetes
```bash
# Deploy all
kubectl apply -f deployment/aks/

# Get pods
kubectl get pods -n agentic-ai

# Get logs
kubectl logs -f deployment/backend-api -n agentic-ai

# Port forward
kubectl port-forward svc/backend-api 8080:8080 -n agentic-ai
```

### Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U admin -d agentic_ai

# Run migrations (if using Alembic)
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "Description"
```

---

## Additional Resources

### Internal Documentation
- `/docs/OPERATIONS_GUIDE.md` - System operations manual
- `/docs/USER_MANUAL.md` - End-user guide
- `/knowledge-base/README.md` - Knowledge base structure

### External References
- [Crew AI Documentation](https://docs.crewai.com/)
- [Azure OpenAI Guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [LangChain Documentation](https://python.langchain.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

---

## Conclusion

This platform is a production-ready multi-agent AI system with:
- ✅ Complete implementation of 8 specialized agents
- ✅ Robust orchestration with Crew AI
- ✅ Full RAG system with vector database
- ✅ Azure OpenAI integration with retry logic
- ✅ RESTful API with comprehensive routes
- ✅ Modern React frontend
- ✅ Complete containerization and Kubernetes deployments
- ✅ Monitoring and observability stack
- ✅ Comprehensive documentation

When working on this codebase:
1. Follow the established conventions
2. Write tests for new features
3. Update documentation
4. Use logging extensively
5. Handle errors gracefully
6. Monitor metrics after changes

**Status**: Phase 4 Complete - Production Ready 🚀

---

**Last Updated**: 2025-11-14
**Version**: 1.0.0
**Maintainer**: Development Team
