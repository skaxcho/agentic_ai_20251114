# Agentic AI 시스템 구현 가이드

## 목차
1. [개발 환경 세팅](#1-개발-환경-세팅)
2. [Azure OpenAI 연동](#2-azure-openai-연동)
3. [Crew AI 구현](#3-crew-ai-구현)
4. [RAG 시스템 구축](#4-rag-시스템-구축)
5. [MCP 서버 개발](#5-mcp-서버-개발)
6. [Agent 개발 가이드](#6-agent-개발-가이드)
7. [API 서버 구현](#7-api-서버-구현)
8. [Frontend 구현](#8-frontend-구현)
9. [모니터링 구축](#9-모니터링-구축)
10. [배포 가이드](#10-배포-가이드)

---

## 1. 개발 환경 세팅

### 1.1 필수 소프트웨어

```bash
# Python 3.11 설치
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Node.js 18+ 설치 (Frontend용)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Docker & Docker Compose 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 설치
sudo apt install git
```

### 1.2 프로젝트 초기화

```bash
# 프로젝트 클론
git clone <repository-url>
cd agentic-ai-platform

# Python 가상환경 생성
python3.11 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 프로젝트 구조 생성
mkdir -p src/{core/{base,services,tools},agents,api/{routes,models},db}
mkdir -p frontend/src/{components,services}
mkdir -p mock/{backend,servicenow,cloud}
mkdir -p tests/{unit,integration,load}
mkdir -p mcp-servers/{servicenow-mcp,database-mcp,cloud-mcp}
mkdir -p monitoring/{prometheus,grafana/dashboards}
mkdir -p knowledge-base/{manuals,incidents,schemas}
```

### 1.3 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agentic_ai
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Qdrant (Vector DB)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

# ServiceNow (ITS)
SERVICENOW_INSTANCE=your-instance.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=password

# OneDrive
ONEDRIVE_CLIENT_ID=your-client-id
ONEDRIVE_CLIENT_SECRET=your-client-secret
ONEDRIVE_TENANT_ID=your-tenant-id

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_ADMIN_PASSWORD=admin

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
EOF
```

### 1.4 Docker Compose 실행

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT}:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD}

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "${QDRANT_PORT}:6333"
    volumes:
      - qdrant-data:/qdrant/storage

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "${PROMETHEUS_PORT}:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "${GRAFANA_PORT}:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards

volumes:
  postgres-data:
  qdrant-data:
  prometheus-data:
  grafana-data:
```

```bash
# 실행
docker-compose up -d

# 확인
docker-compose ps
```

---

## 2. Azure OpenAI 연동

### 2.1 Azure OpenAI Service 생성

```bash
# Azure CLI 설치 및 로그인
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az login

# OpenAI 리소스 생성
az cognitiveservices account create \
  --name agentic-ai-openai \
  --resource-group agentic-ai-rg \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# 모델 배포
az cognitiveservices account deployment create \
  --name agentic-ai-openai \
  --resource-group agentic-ai-rg \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-name "Standard" \
  --sku-capacity 10

# Embedding 모델 배포
az cognitiveservices account deployment create \
  --name agentic-ai-openai \
  --resource-group agentic-ai-rg \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-name "Standard" \
  --sku-capacity 10
```

### 2.2 LLM Service 구현

```python
# src/core/services/llm_service.py
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional, AsyncIterator
import os
from dotenv import load_load_dotenv()

class AzureOpenAIService:
    """Azure OpenAI 통합 서비스"""

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        functions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """채팅 완성 API 호출"""
        try:
            kwargs = {
                "model": self.deployment_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            if functions:
                kwargs["functions"] = functions
                kwargs["function_call"] = "auto"

            response = self.client.chat.completions.create(**kwargs)

            return {
                "content": response.choices[0].message.content,
                "function_call": response.choices[0].message.function_call if functions else None,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

        except Exception as e:
            raise Exception(f"Azure OpenAI API 호출 실패: {str(e)}")

    async def streaming_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncIterator[str]:
        """스트리밍 채팅 완성"""
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise Exception(f"Streaming API 호출 실패: {str(e)}")

    def generate_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_deployment,
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            raise Exception(f"Embedding 생성 실패: {str(e)}")

    def function_calling(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Function Calling"""
        response = self.chat_completion(
            messages=messages,
            functions=functions
        )

        if response["function_call"]:
            return {
                "function_name": response["function_call"].name,
                "arguments": response["function_call"].arguments
            }
        else:
            return {"content": response["content"]}
```

### 2.3 사용 예시

```python
# 사용 예시
llm_service = AzureOpenAIService()

# 일반 채팅
response = llm_service.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Azure OpenAI에 대해 설명해줘"}
    ]
)
print(response["content"])

# Function Calling
functions = [
    {
        "name": "create_incident",
        "description": "Create an incident ticket in ServiceNow",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
            },
            "required": ["title", "description"]
        }
    }
]

response = llm_service.function_calling(
    messages=[
        {"role": "user", "content": "결제 시스템이 다운되었어, 긴급 티켓 생성해줘"}
    ],
    functions=functions
)

if "function_name" in response:
    print(f"Function: {response['function_name']}")
    print(f"Arguments: {response['arguments']}")
```

---

## 3. Crew AI 구현

### 3.1 Crew AI 설치

```bash
pip install crewai==0.1.0 crewai-tools==0.1.0
```

### 3.2 Base Agent 구현

```python
# src/core/base/base_agent.py
from abc import ABC, abstractmethod
from crewai import Agent, Task, Crew
from typing import List, Dict, Any
from src.core.services.llm_service import AzureOpenAIService
from src.core.services.rag_service import RAGService
from src.core.services.mcp_hub import MCPHub
import logging

class BaseAgent(ABC):
    """모든 Agent의 Base Class"""

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str = ""
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory

        # 공통 서비스
        self.llm_service = AzureOpenAIService()
        self.rag_service = RAGService()
        self.mcp_hub = MCPHub()

        # Logger
        self.logger = logging.getLogger(f"Agent.{name}")

        # Crew AI Agent 초기화
        self._agent = None

    @abstractmethod
    def get_tools(self) -> List:
        """Agent별 Tool 정의 (하위 클래스에서 구현)"""
        pass

    def create_crew_agent(self) -> Agent:
        """Crew AI Agent 생성"""
        if not self._agent:
            self._agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=self.get_tools(),
                verbose=True,
                allow_delegation=False,  # Agent별로 설정
                llm=self._get_llm_config()
            )
        return self._agent

    def _get_llm_config(self):
        """LLM 설정 (Crew AI용)"""
        from langchain_openai import AzureChatOpenAI
        import os

        return AzureChatOpenAI(
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.7
        )

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Task 실행 (하위 클래스에서 구현)"""
        pass

    def _log_action(self, action: str, result: Any):
        """공통 로깅"""
        self.logger.info(f"[{self.name}] {action}: {result}")

    async def _send_notification(self, channel: str, message: str):
        """공통 알림"""
        from src.core.services.notification_service import NotificationService
        notification_service = NotificationService()
        await notification_service.send(channel, message)
```

### 3.3 Agent 구현 예시 (Report Agent)

```python
# src/agents/report_agent.py
from src.core.base.base_agent import BaseAgent
from crewai_tools import FileReadTool, DirectoryReadTool
from typing import List, Dict, Any

class ReportAgent(BaseAgent):
    """Report Agent - 보고서 자동 작성"""

    def __init__(self):
        super().__init__(
            name="ReportAgent",
            role="Report Automation Specialist",
            goal="자동으로 회의록, 보고서, 현황 조사를 작성합니다",
            backstory="""당신은 10년 경력의 문서 작성 전문가입니다.
            다양한 소스에서 정보를 수집하고 명확하고 간결한 보고서를 작성하는 데 능숙합니다."""
        )

    def get_tools(self) -> List:
        """Report Agent 전용 Tool"""
        from src.core.tools.file_tools import OneDriveTool, DocumentGeneratorTool

        return [
            FileReadTool(),
            DirectoryReadTool(),
            OneDriveTool(),
            DocumentGeneratorTool()
        ]

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Task 실행"""
        task_type = task.get("task_type")

        if task_type == "weekly_report":
            return await self._generate_weekly_report(task)
        elif task_type == "meeting_minutes":
            return await self._generate_meeting_minutes(task)
        elif task_type == "system_status_report":
            return await self._generate_system_status_report(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _generate_weekly_report(self, task: Dict) -> Dict:
        """주간보고서 생성"""
        from crewai import Task as CrewTask, Crew

        # Step 1: 작업일지 파일 읽기
        source_files = task.get("source_files", [])
        work_logs = []
        for file_path in source_files:
            content = self._read_file(file_path)
            work_logs.append(content)

        # Step 2: Crew AI Task 정의
        crew_task = CrewTask(
            description=f"""
            다음 작업일지들을 분석하여 주간보고서를 작성하세요:

            {chr(10).join(work_logs)}

            보고서는 다음 구조를 따라야 합니다:
            1. 주요 수행 업무
            2. 주요 이슈 및 해결
            3. 다음 주 계획
            """,
            agent=self.create_crew_agent(),
            expected_output="마크다운 형식의 주간 보고서"
        )

        # Step 3: Crew 실행
        crew = Crew(
            agents=[self.create_crew_agent()],
            tasks=[crew_task],
            verbose=True
        )

        result = crew.kickoff()

        # Step 4: 결과 저장
        output_path = task.get("output_path")
        if output_path:
            self._write_file(output_path, result)

        return {
            "success": True,
            "output_path": output_path,
            "content": result
        }

    def _read_file(self, file_path: str) -> str:
        """파일 읽기"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _write_file(self, file_path: str, content: str):
        """파일 쓰기"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
```

### 3.4 Multi-Agent 협업 (Change Management Agent)

```python
# src/agents/change_mgmt_agent.py
from src.core.base.base_agent import BaseAgent
from src.agents.report_agent import ReportAgent
from src.agents.its_agent import ITSAgent
from src.agents.monitoring_agent import MonitoringAgent
from src.agents.infra_agent import InfraAgent
from crewai import Crew, Process
from typing import List, Dict, Any

class ChangeManagementAgent(BaseAgent):
    """Change Management Agent - 변경관리 orchestrator"""

    def __init__(self):
        super().__init__(
            name="ChangeManagementAgent",
            role="Change Management Orchestrator",
            goal="변경관리 프로세스를 자동화하고 다른 Agent들을 조율합니다",
            backstory="""당신은 ITIL 변경관리 전문가로, 안전하고 효율적인 변경 프로세스를 보장합니다."""
        )

        # Sub-agents
        self.report_agent = ReportAgent()
        self.its_agent = ITSAgent()
        self.monitoring_agent = MonitoringAgent()
        self.infra_agent = InfraAgent()

    def get_tools(self) -> List:
        """Change Management Agent Tool"""
        from src.core.tools.devops_tools import DevOpsTool
        return [DevOpsTool()]

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """변경관리 프로세스 실행"""
        from crewai import Task as CrewTask

        # Step 1: 변경계획서 작성 (Report Agent)
        self.logger.info("Step 1: 변경계획서 작성 중...")
        plan_task = CrewTask(
            description=f"다음 변경 요청에 대한 변경계획서를 작성하세요: {task.get('request')}",
            agent=self.report_agent.create_crew_agent(),
            expected_output="변경계획서 (마크다운)"
        )

        # Step 2: 승인 요청 (ITS Agent)
        approval_task = CrewTask(
            description="변경계획서를 기반으로 ServiceNow에 변경 승인 요청 티켓을 생성하세요",
            agent=self.its_agent.create_crew_agent(),
            expected_output="티켓 번호 및 상태"
        )

        # Step 3: 배포 실행 (Infra Agent)
        deployment_task = CrewTask(
            description=f"다음 변경을 배포하세요: {task.get('changes')}",
            agent=self.infra_agent.create_crew_agent(),
            expected_output="배포 결과"
        )

        # Step 4: 배포 후 점검 (Monitoring Agent)
        monitoring_task = CrewTask(
            description="배포 후 시스템 상태를 점검하고 보고하세요",
            agent=self.monitoring_agent.create_crew_agent(),
            expected_output="점검 결과"
        )

        # Step 5: 최종 보고서 (Report Agent)
        final_report_task = CrewTask(
            description="변경 프로세스 전체를 요약한 최종 보고서를 작성하세요",
            agent=self.report_agent.create_crew_agent(),
            expected_output="최종 보고서"
        )

        # Crew 생성 (순차 실행)
        crew = Crew(
            agents=[
                self.report_agent.create_crew_agent(),
                self.its_agent.create_crew_agent(),
                self.infra_agent.create_crew_agent(),
                self.monitoring_agent.create_crew_agent()
            ],
            tasks=[
                plan_task,
                approval_task,
                deployment_task,
                monitoring_task,
                final_report_task
            ],
            process=Process.sequential,  # 순차 실행
            verbose=True
        )

        # 실행
        result = crew.kickoff()

        return {
            "success": True,
            "final_report": result,
            "steps_completed": 5
        }
```

---

## 4. RAG 시스템 구축

### 4.1 Qdrant (Vector DB) 설정

```python
# src/core/services/vector_db_service.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import os

class VectorDBService:
    """Qdrant Vector DB 서비스"""

    def __init__(self):
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 1536,  # text-embedding-ada-002 dimension
        distance: Distance = Distance.COSINE
    ):
        """컬렉션 생성"""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            print(f"Collection '{collection_name}' created successfully")
        except Exception as e:
            print(f"Collection creation failed: {e}")

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        """문서 삽입/업데이트"""
        points = [
            PointStruct(
                id=i,
                vector=embeddings[i],
                payload=documents[i]
            )
            for i in range(len(documents))
        ]

        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """유사도 검색"""
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]
```

### 4.2 RAG Service 구현

```python
# src/core/services/rag_service.py
from src.core.services.vector_db_service import VectorDBService
from src.core.services.llm_service import AzureOpenAIService
from typing import List, Dict, Any
import os

class RAGService:
    """RAG (Retrieval-Augmented Generation) 서비스"""

    def __init__(self):
        self.vector_db = VectorDBService()
        self.llm_service = AzureOpenAIService()
        self.collection_names = {
            "manuals": "system_manuals",
            "incidents": "incident_history",
            "schemas": "database_schemas",
            "contacts": "contact_information"
        }

    def initialize_collections(self):
        """컬렉션 초기화"""
        for collection_name in self.collection_names.values():
            self.vector_db.create_collection(collection_name)

    def index_documents(
        self,
        collection_type: str,
        documents: List[Dict[str, Any]]
    ):
        """문서 인덱싱"""
        collection_name = self.collection_names.get(collection_type)
        if not collection_name:
            raise ValueError(f"Unknown collection type: {collection_type}")

        # 문서 임베딩 생성
        embeddings = []
        for doc in documents:
            text = doc.get("content", "")
            embedding = self.llm_service.generate_embedding(text)
            embeddings.append(embedding)

        # Vector DB에 저장
        self.vector_db.upsert_documents(
            collection_name=collection_name,
            documents=documents,
            embeddings=embeddings
        )

    def semantic_search(
        self,
        collection_type: str,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """의미 기반 검색"""
        collection_name = self.collection_names.get(collection_type)
        if not collection_name:
            raise ValueError(f"Unknown collection type: {collection_type}")

        # 쿼리 임베딩 생성
        query_embedding = self.llm_service.generate_embedding(query)

        # 검색
        results = self.vector_db.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit
        )

        return results

    def retrieve_context(
        self,
        query: str,
        collection_types: List[str] = ["manuals", "incidents"],
        max_results_per_collection: int = 3
    ) -> str:
        """RAG 컨텍스트 생성"""
        all_contexts = []

        for collection_type in collection_types:
            results = self.semantic_search(
                collection_type=collection_type,
                query=query,
                limit=max_results_per_collection
            )

            for result in results:
                context = f"[{collection_type}] (Score: {result['score']:.2f})\n"
                context += result['payload'].get('content', '')
                all_contexts.append(context)

        return "\n\n---\n\n".join(all_contexts)

    def rag_query(
        self,
        query: str,
        collection_types: List[str] = ["manuals"],
        system_prompt: str = "You are a helpful assistant."
    ) -> str:
        """RAG 기반 질의응답"""
        # 1. 관련 문서 검색
        context = self.retrieve_context(query, collection_types)

        # 2. LLM에 컨텍스트와 함께 질문
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
다음 정보를 참고하여 질문에 답변하세요:

<컨텍스트>
{context}
</컨텍스트>

<질문>
{query}
</질문>

답변:
            """}
        ]

        response = self.llm_service.chat_completion(messages=messages)
        return response["content"]
```

### 4.3 지식 베이스 구축 스크립트

```python
# scripts/build_knowledge_base.py
from src.core.services.rag_service import RAGService
import os
import json

def load_manuals():
    """매뉴얼 문서 로드"""
    manuals_dir = "knowledge-base/manuals"
    documents = []

    for filename in os.listdir(manuals_dir):
        if filename.endswith(".md") or filename.endswith(".txt"):
            with open(os.path.join(manuals_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append({
                    "filename": filename,
                    "content": content,
                    "type": "manual"
                })

    return documents

def load_incidents():
    """장애 사례 로드"""
    incidents_file = "knowledge-base/incidents/incidents.json"

    with open(incidents_file, 'r', encoding='utf-8') as f:
        incidents = json.load(f)

    documents = []
    for incident in incidents:
        content = f"""
        Incident ID: {incident['id']}
        Date: {incident['date']}
        System: {incident['system']}
        Symptoms: {incident['symptoms']}
        Root Cause: {incident['root_cause']}
        Resolution: {incident['resolution']}
        """
        documents.append({
            "incident_id": incident['id'],
            "content": content.strip(),
            "type": "incident"
        })

    return documents

def main():
    rag_service = RAGService()

    # 컬렉션 초기화
    print("Initializing collections...")
    rag_service.initialize_collections()

    # 매뉴얼 인덱싱
    print("Indexing manuals...")
    manuals = load_manuals()
    rag_service.index_documents("manuals", manuals)
    print(f"Indexed {len(manuals)} manuals")

    # 장애 사례 인덱싱
    print("Indexing incidents...")
    incidents = load_incidents()
    rag_service.index_documents("incidents", incidents)
    print(f"Indexed {len(incidents)} incidents")

    print("Knowledge base build complete!")

if __name__ == "__main__":
    main()
```

```bash
# 실행
python scripts/build_knowledge_base.py
```

---

## 5. MCP 서버 개발

### 5.1 MCP 프로토콜 이해

MCP (Model Context Protocol)는 LLM이 외부 시스템과 통신하기 위한 표준 프로토콜입니다.

### 5.2 Database MCP 서버

```python
# mcp-servers/database-mcp/server.py
from mcp.server import Server, Tool
from mcp.types import TextContent
import psycopg2
from typing import Dict, Any
import json

class DatabaseMCPServer:
    """Database MCP 서버"""

    def __init__(self):
        self.server = Server("database-mcp")
        self.connections = {}

    def register_tools(self):
        """Tool 등록"""

        @self.server.tool()
        async def connect_database(
            host: str,
            port: int,
            database: str,
            username: str,
            password: str
        ) -> str:
            """데이터베이스 연결"""
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database=database,
                    user=username,
                    password=password
                )
                conn_id = f"{host}:{port}/{database}"
                self.connections[conn_id] = conn
                return f"Connected to {conn_id}"
            except Exception as e:
                return f"Connection failed: {str(e)}"

        @self.server.tool()
        async def execute_query(
            connection_id: str,
            query: str
        ) -> str:
            """쿼리 실행"""
            conn = self.connections.get(connection_id)
            if not conn:
                return "Connection not found"

            try:
                cursor = conn.cursor()
                cursor.execute(query)

                if query.strip().upper().startswith("SELECT"):
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return json.dumps({
                        "columns": columns,
                        "rows": results,
                        "row_count": len(results)
                    })
                else:
                    conn.commit()
                    return f"Query executed: {cursor.rowcount} rows affected"

            except Exception as e:
                conn.rollback()
                return f"Query failed: {str(e)}"

        @self.server.tool()
        async def get_schema(
            connection_id: str,
            table_name: str = None
        ) -> str:
            """스키마 조회"""
            conn = self.connections.get(connection_id)
            if not conn:
                return "Connection not found"

            try:
                cursor = conn.cursor()

                if table_name:
                    query = f"""
                    SELECT column_name, data_type, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                    """
                else:
                    query = """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                    """

                cursor.execute(query)
                results = cursor.fetchall()
                return json.dumps(results)

            except Exception as e:
                return f"Schema query failed: {str(e)}"

    def run(self, host: str = "localhost", port: int = 5000):
        """MCP 서버 실행"""
        self.register_tools()
        self.server.run(host=host, port=port)

if __name__ == "__main__":
    server = DatabaseMCPServer()
    server.run()
```

### 5.3 ServiceNow MCP 서버

```python
# mcp-servers/servicenow-mcp/server.py
from mcp.server import Server
import requests
from typing import Dict, Any
import json
import os

class ServiceNowMCPServer:
    """ServiceNow MCP 서버"""

    def __init__(self):
        self.server = Server("servicenow-mcp")
        self.base_url = f"https://{os.getenv('SERVICENOW_INSTANCE')}/api/now"
        self.auth = (
            os.getenv('SERVICENOW_USERNAME'),
            os.getenv('SERVICENOW_PASSWORD')
        )
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def register_tools(self):
        """Tool 등록"""

        @self.server.tool()
        async def create_incident(
            title: str,
            description: str,
            severity: str = "medium",
            assigned_to: str = ""
        ) -> str:
            """인시던트 생성"""
            url = f"{self.base_url}/table/incident"

            payload = {
                "short_description": title,
                "description": description,
                "urgency": self._severity_to_urgency(severity),
                "assigned_to": assigned_to
            }

            try:
                response = requests.post(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

                result = response.json()['result']
                return json.dumps({
                    "incident_id": result['number'],
                    "sys_id": result['sys_id'],
                    "status": "created"
                })

            except Exception as e:
                return f"Failed to create incident: {str(e)}"

        @self.server.tool()
        async def update_incident(
            incident_id: str,
            **fields
        ) -> str:
            """인시던트 업데이트"""
            url = f"{self.base_url}/table/incident/{incident_id}"

            try:
                response = requests.patch(
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    json=fields
                )
                response.raise_for_status()

                return json.dumps({
                    "incident_id": incident_id,
                    "status": "updated"
                })

            except Exception as e:
                return f"Failed to update incident: {str(e)}"

        @self.server.tool()
        async def get_incident(incident_id: str) -> str:
            """인시던트 조회"""
            url = f"{self.base_url}/table/incident/{incident_id}"

            try:
                response = requests.get(
                    url,
                    auth=self.auth,
                    headers=self.headers
                )
                response.raise_for_status()

                return json.dumps(response.json()['result'])

            except Exception as e:
                return f"Failed to get incident: {str(e)}"

    def _severity_to_urgency(self, severity: str) -> str:
        """Severity를 ServiceNow Urgency로 변환"""
        mapping = {
            "low": "3",
            "medium": "2",
            "high": "1",
            "critical": "1"
        }
        return mapping.get(severity, "2")

    def run(self, host: str = "localhost", port: int = 5001):
        """MCP 서버 실행"""
        self.register_tools()
        self.server.run(host=host, port=port)

if __name__ == "__main__":
    server = ServiceNowMCPServer()
    server.run()
```

### 5.4 MCP Hub 구현

```python
# src/core/services/mcp_hub.py
from typing import Dict, Any, List
import requests

class MCPHub:
    """MCP 서버 통합 허브"""

    def __init__(self):
        self.mcp_servers = {
            "database": "http://localhost:5000",
            "servicenow": "http://localhost:5001",
            "cloud": "http://localhost:5002"
        }

    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        **kwargs
    ) -> Any:
        """MCP Tool 호출"""
        server_url = self.mcp_servers.get(server_name)
        if not server_url:
            raise ValueError(f"Unknown MCP server: {server_name}")

        url = f"{server_url}/tools/{tool_name}"

        try:
            response = requests.post(
                url,
                json=kwargs,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise Exception(f"MCP tool call failed: {str(e)}")

    def list_tools(self, server_name: str) -> List[str]:
        """서버의 Tool 목록 조회"""
        server_url = self.mcp_servers.get(server_name)
        if not server_url:
            raise ValueError(f"Unknown MCP server: {server_name}")

        url = f"{server_url}/tools"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()["tools"]

        except Exception as e:
            raise Exception(f"Failed to list tools: {str(e)}")
```

---

## 6. Agent 개발 가이드

### 6.1 Agent 개발 체크리스트

새로운 Agent를 개발할 때 다음 체크리스트를 따르세요:

- [ ] `BaseAgent` 상속
- [ ] `get_tools()` 메서드 구현
- [ ] `execute_task()` 메서드 구현
- [ ] Agent별 유즈케이스 정의
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 문서화 (docstring)

### 6.2 Agent Tool 개발

```python
# src/core/tools/custom_tool.py
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field

class CustomToolInput(BaseModel):
    """Tool 입력 스키마"""
    param1: str = Field(description="파라미터 1 설명")
    param2: int = Field(description="파라미터 2 설명")

class CustomTool(BaseTool):
    """커스텀 Tool 예시"""
    name = "custom_tool"
    description = "이 Tool의 설명을 명확하게 작성하세요"
    args_schema: Type[BaseModel] = CustomToolInput

    def _run(self, param1: str, param2: int) -> str:
        """Tool 실행 로직"""
        # 구현
        return f"Result: {param1}, {param2}"

    async def _arun(self, param1: str, param2: int) -> str:
        """비동기 실행 (선택적)"""
        return self._run(param1, param2)
```

---

## 7. API 서버 구현

### 7.1 FastAPI 서버 구조

```python
# src/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import agents, tasks, monitoring
from prometheus_client import make_asgi_app
import logging

# Logging 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Agentic AI Platform API",
    description="Multi-Agent AI System API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])

# Prometheus 메트릭 엔드포인트
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/")
async def root():
    return {"message": "Agentic AI Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 7.2 Agent 라우터

```python
# src/api/routes/agents.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from src.agents.report_agent import ReportAgent
from src.agents.monitoring_agent import MonitoringAgent
from src.agents.its_agent import ITSAgent
from src.agents.db_extract_agent import DBExtractAgent
from src.agents.change_mgmt_agent import ChangeManagementAgent
from src.agents.biz_support_agent import BizSupportAgent
from src.agents.sop_agent import SOPAgent
from src.agents.infra_agent import InfraAgent

router = APIRouter()

# Agent 인스턴스들
AGENTS = {
    "report": ReportAgent(),
    "monitoring": MonitoringAgent(),
    "its": ITSAgent(),
    "db_extract": DBExtractAgent(),
    "change_mgmt": ChangeManagementAgent(),
    "biz_support": BizSupportAgent(),
    "sop": SOPAgent(),
    "infra": InfraAgent()
}

class AgentExecuteRequest(BaseModel):
    agent_name: str
    task: Dict[str, Any]

class AgentExecuteResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    execution_time_seconds: float

@router.get("/list")
async def list_agents():
    """Agent 목록 조회"""
    return {
        "agents": [
            {
                "name": name,
                "role": agent.role,
                "goal": agent.goal
            }
            for name, agent in AGENTS.items()
        ]
    }

@router.post("/execute")
async def execute_agent(request: AgentExecuteRequest) -> AgentExecuteResponse:
    """Agent 실행"""
    import time

    agent = AGENTS.get(request.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent_name}' not found")

    try:
        start_time = time.time()
        result = await agent.execute_task(request.task)
        execution_time = time.time() - start_time

        return AgentExecuteResponse(
            success=True,
            result=result,
            execution_time_seconds=execution_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_name}/status")
async def get_agent_status(agent_name: str):
    """Agent 상태 조회"""
    agent = AGENTS.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

    return {
        "name": agent_name,
        "role": agent.role,
        "status": "ready"
    }
```

### 7.3 Task 관리 라우터

```python
# src/api/routes/tasks.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.db.models import Task
from src.db.repositories import TaskRepository

router = APIRouter()
task_repo = TaskRepository()

class TaskCreate(BaseModel):
    agent_name: str
    task_data: dict
    priority: Optional[str] = "medium"

class TaskResponse(BaseModel):
    task_id: str
    agent_name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    result: Optional[dict]

@router.post("/create")
async def create_task(task: TaskCreate) -> TaskResponse:
    """Task 생성"""
    db_task = await task_repo.create(
        agent_name=task.agent_name,
        task_data=task.task_data,
        priority=task.priority
    )
    return TaskResponse(**db_task.dict())

@router.get("/{task_id}")
async def get_task(task_id: str) -> TaskResponse:
    """Task 조회"""
    task = await task_repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task.dict())

@router.get("/")
async def list_tasks(
    agent_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[TaskResponse]:
    """Task 목록 조회"""
    tasks = await task_repo.list(
        agent_name=agent_name,
        status=status,
        limit=limit
    )
    return [TaskResponse(**task.dict()) for task in tasks]
```

### 7.4 Database 모델

```python
# src/db/models.py
from sqlalchemy import Column, String, DateTime, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_name = Column(String, nullable=False)
    task_data = Column(JSON, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(String, default="medium")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
```

---

## 8. Frontend 구현

### 8.1 React 프로젝트 초기화

```bash
cd frontend
npx create-react-app . --template typescript
npm install @mui/material @emotion/react @emotion/styled
npm install axios react-router-dom
npm install @tanstack/react-query
```

### 8.2 Agent 선택 컴포넌트

```typescript
// frontend/src/components/AgentSelector.tsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip
} from '@mui/material';
import axios from 'axios';

interface Agent {
  name: string;
  role: string;
  goal: string;
}

export const AgentSelector: React.FC<{ onSelect: (agent: string) => void }> = ({ onSelect }) => {
  const [agents, setAgents] = useState<Agent[]>([]);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await axios.get('http://localhost:8080/api/agents/list');
      setAgents(response.data.agents);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  };

  return (
    <Grid container spacing={2}>
      {agents.map((agent) => (
        <Grid item xs={12} md={6} lg={3} key={agent.name}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {agent.name}
              </Typography>
              <Chip label={agent.role} size="small" color="primary" sx={{ mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                {agent.goal}
              </Typography>
              <Button
                variant="contained"
                fullWidth
                sx={{ mt: 2 }}
                onClick={() => onSelect(agent.name)}
              >
                선택
              </Button>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};
```

### 8.3 대화형 인터페이스

```typescript
// frontend/src/components/ChatInterface.tsx
import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  CircularProgress
} from '@mui/material';
import axios from 'axios';

interface Message {
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

export const ChatInterface: React.FC<{ agentName: string }> = ({ agentName }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:8080/api/agents/execute', {
        agent_name: agentName,
        task: {
          type: 'chat',
          message: input
        }
      });

      const agentMessage: Message = {
        role: 'agent',
        content: response.data.result.response || JSON.stringify(response.data.result),
        timestamp: new Date()
      };
      setMessages([...messages, userMessage, agentMessage]);

    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
      <Paper sx={{ flex: 1, overflow: 'auto', p: 2, mb: 2 }}>
        {messages.map((msg, index) => (
          <Box
            key={index}
            sx={{
              mb: 2,
              textAlign: msg.role === 'user' ? 'right' : 'left'
            }}
          >
            <Paper
              sx={{
                display: 'inline-block',
                p: 1.5,
                maxWidth: '70%',
                bgcolor: msg.role === 'user' ? 'primary.main' : 'grey.200',
                color: msg.role === 'user' ? 'white' : 'black'
              }}
            >
              <Typography variant="body1">{msg.content}</Typography>
              <Typography variant="caption">
                {msg.timestamp.toLocaleTimeString()}
              </Typography>
            </Paper>
          </Box>
        ))}
        {loading && <CircularProgress />}
      </Paper>

      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="메시지를 입력하세요..."
          disabled={loading}
        />
        <Button
          variant="contained"
          onClick={sendMessage}
          disabled={loading}
        >
          전송
        </Button>
      </Box>
    </Box>
  );
};
```

### 8.4 Task 모니터링 대시보드

```typescript
// frontend/src/components/TaskMonitor.tsx
import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Paper
} from '@mui/material';
import axios from 'axios';

interface Task {
  task_id: string;
  agent_name: string;
  status: string;
  created_at: string;
  execution_time?: number;
}

export const TaskMonitor: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000); // 5초마다 갱신
    return () => clearInterval(interval);
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get('http://localhost:8080/api/tasks/');
      setTasks(response.data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Paper>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Task ID</TableCell>
            <TableCell>Agent</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Created At</TableCell>
            <TableCell>Execution Time</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {tasks.map((task) => (
            <TableRow key={task.task_id}>
              <TableCell>{task.task_id}</TableCell>
              <TableCell>{task.agent_name}</TableCell>
              <TableCell>
                <Chip
                  label={task.status}
                  color={getStatusColor(task.status) as any}
                  size="small"
                />
              </TableCell>
              <TableCell>{new Date(task.created_at).toLocaleString()}</TableCell>
              <TableCell>
                {task.execution_time ? `${task.execution_time.toFixed(2)}s` : '-'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  );
};
```

---

## 9. 모니터링 구축

### 9.1 Prometheus 설정

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'agentic-ai-api'
    static_configs:
      - targets: ['api:8080']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
```

### 9.2 Grafana 대시보드

```json
// monitoring/grafana/dashboards/agent-performance.json
{
  "dashboard": {
    "title": "Agent Performance Dashboard",
    "panels": [
      {
        "title": "Agent Execution Count",
        "targets": [
          {
            "expr": "sum(agent_execution_total) by (agent_name)"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Average Execution Time",
        "targets": [
          {
            "expr": "avg(agent_execution_duration_seconds) by (agent_name)"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Success Rate",
        "targets": [
          {
            "expr": "sum(rate(agent_execution_success_total[5m])) / sum(rate(agent_execution_total[5m]))"
          }
        ],
        "type": "singlestat"
      }
    ]
  }
}
```

### 9.3 Prometheus 메트릭 추가

```python
# src/api/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time

# 메트릭 정의
agent_execution_total = Counter(
    'agent_execution_total',
    'Total number of agent executions',
    ['agent_name']
)

agent_execution_success = Counter(
    'agent_execution_success_total',
    'Number of successful agent executions',
    ['agent_name']
)

agent_execution_duration = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration',
    ['agent_name']
)

active_tasks = Gauge(
    'active_tasks',
    'Number of currently active tasks'
)

# 데코레이터
def track_metrics(agent_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            agent_execution_total.labels(agent_name=agent_name).inc()
            active_tasks.inc()

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                agent_execution_success.labels(agent_name=agent_name).inc()
                return result
            finally:
                duration = time.time() - start_time
                agent_execution_duration.labels(agent_name=agent_name).observe(duration)
                active_tasks.dec()

        return wrapper
    return decorator
```

---

## 10. 배포 가이드

### 10.1 Docker 이미지 빌드

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY .env .

# 포트 노출
EXPOSE 8080

# 실행
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```bash
# 빌드
docker build -t agentic-ai-platform:latest .

# 실행
docker run -p 8080:8080 --env-file .env agentic-ai-platform:latest
```

### 10.2 Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: agentic-ai-platform:latest
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
      - qdrant
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant-data:/qdrant/storage
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
    restart: unless-stopped

volumes:
  postgres-data:
  qdrant-data:
  prometheus-data:
  grafana-data:
```

### 10.3 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t agentic-ai-platform:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push agentic-ai-platform:${{ github.sha }}
```

### 10.4 배포 체크리스트

**배포 전:**
- [ ] 모든 테스트 통과 확인
- [ ] 환경 변수 설정 확인
- [ ] Database 마이그레이션 준비
- [ ] 백업 생성
- [ ] 롤백 계획 수립

**배포:**
- [ ] Docker 이미지 빌드
- [ ] Database 마이그레이션 실행
- [ ] 서비스 배포
- [ ] Health Check 확인

**배포 후:**
- [ ] 모니터링 확인 (Grafana)
- [ ] 에러 로그 확인
- [ ] 주요 유즈케이스 테스트
- [ ] 성능 메트릭 확인

---

## 11. 트러블슈팅 가이드

### 11.1 Azure OpenAI Rate Limit

**문제:** API 호출 제한 초과

**해결방법:**
```python
# Retry 로직 추가
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(5))
def call_azure_openai_with_retry():
    return llm_service.chat_completion(messages)
```

### 11.2 Vector DB 검색 느림

**문제:** RAG 검색 성능 저하

**해결방법:**
- 인덱스 최적화
- 배치 크기 조정
- 캐싱 추가

### 11.3 Agent 실행 타임아웃

**문제:** Agent 실행 시간 초과

**해결방법:**
- Task를 비동기로 처리
- 타임아웃 시간 증가
- Task를 더 작은 단위로 분할

---

## 12. 다음 단계

1. **개발 환경 세팅 완료**
2. **공통 모듈 개발** (LLM, RAG, MCP Hub)
3. **Agent별 구현**
4. **API 서버 구축**
5. **Frontend 개발**
6. **통합 테스트**
7. **배포**

각 단계별로 본 가이드를 참조하여 구현하세요!
