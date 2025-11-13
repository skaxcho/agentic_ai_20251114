"""
Base Agent Module

모든 AI Agent의 기본 클래스를 정의합니다.
공통 기능을 제공하고, 하위 Agent에서 구체적인 구현을 강제합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.core.services.llm_service import AzureOpenAIService, get_llm_service
from src.core.services.rag_service import RAGService, get_rag_service
from src.core.services.mcp_hub import MCPHub, get_mcp_hub
import logging
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """모든 Agent의 Base Class"""

    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str = "",
        verbose: bool = True,
        allow_delegation: bool = False
    ):
        """
        Initialize Base Agent

        Args:
            name: Agent 이름
            role: Agent 역할
            goal: Agent 목표
            backstory: Agent 배경 스토리
            verbose: 상세 로깅 활성화
            allow_delegation: Agent 간 위임 허용
        """
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.verbose = verbose
        self.allow_delegation = allow_delegation

        # 공통 서비스 초기화
        self.llm_service = get_llm_service()
        self.rag_service = get_rag_service()
        self.mcp_hub = get_mcp_hub()

        # Logger 설정
        self.logger = logging.getLogger(f"Agent.{name}")
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        # Crew AI Agent 인스턴스 (lazy initialization)
        self._crew_agent = None

        # Execution statistics
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_llm_calls": 0,
            "total_llm_tokens": 0
        }

        self.logger.info(f"{self.name} initialized with role: {self.role}")

    @abstractmethod
    def get_tools(self) -> List:
        """
        Agent별 Tool 정의

        하위 클래스에서 구현 필요.
        각 Agent의 특화된 도구들을 반환합니다.

        Returns:
            List: Tool 리스트
        """
        pass

    def _get_llm_config(self):
        """
        LLM 설정 (Crew AI용)

        Returns:
            AzureChatOpenAI instance
        """
        try:
            from langchain_openai import AzureChatOpenAI

            return AzureChatOpenAI(
                openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
            )
        except ImportError:
            self.logger.error("langchain_openai not installed. Install with: pip install langchain-openai")
            raise

    def create_crew_agent(self):
        """
        Crew AI Agent 생성

        Returns:
            Agent: Crew AI Agent 인스턴스
        """
        if self._crew_agent is not None:
            return self._crew_agent

        try:
            from crewai import Agent

            self._crew_agent = Agent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=self.get_tools(),
                verbose=self.verbose,
                allow_delegation=self.allow_delegation,
                llm=self._get_llm_config()
            )

            self.logger.info(f"Crew AI Agent created for {self.name}")

            return self._crew_agent

        except ImportError:
            self.logger.error("crewai not installed. Install with: pip install crewai")
            raise

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Task 실행

        하위 클래스에서 구현 필요.
        각 Agent의 특화된 작업을 수행합니다.

        Args:
            task: Task 정보
                - task_type: 작업 타입
                - task_data: 작업 데이터
                - ...

        Returns:
            Dict: 실행 결과
                - success: 성공 여부
                - result: 결과 데이터
                - error: 에러 메시지 (실패 시)
        """
        pass

    def _log_action(self, action: str, result: Any = None, level: str = "info"):
        """
        공통 로깅

        Args:
            action: 액션 설명
            result: 결과 (선택적)
            level: 로그 레벨 ("debug", "info", "warning", "error")
        """
        log_message = f"[{self.name}] {action}"
        if result is not None:
            log_message += f": {result}"

        if level == "debug":
            self.logger.debug(log_message)
        elif level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)

    async def _send_notification(
        self,
        channel: str,
        message: str,
        priority: str = "normal"
    ):
        """
        공통 알림

        Args:
            channel: 알림 채널 ("email", "slack", "teams")
            message: 알림 메시지
            priority: 우선순위 ("low", "normal", "high", "critical")
        """
        try:
            from src.core.services.notification_service import get_notification_service

            notification_service = get_notification_service()
            await notification_service.send(
                channel=channel,
                message=message,
                priority=priority,
                agent_name=self.name
            )

            self.logger.info(f"Notification sent via {channel}")

        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        LLM 호출 (통계 추적 포함)

        Args:
            messages: 메시지 리스트
            temperature: 온도 파라미터
            max_tokens: 최대 토큰 수

        Returns:
            Dict: LLM 응답
        """
        self._execution_stats["total_llm_calls"] += 1

        response = self.llm_service.chat_completion(
            messages=messages,
            temperature=temperature or float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            max_tokens=max_tokens or int(os.getenv("DEFAULT_MAX_TOKENS", "2000"))
        )

        self._execution_stats["total_llm_tokens"] += response["usage"]["total_tokens"]

        return response

    async def _call_llm_async(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        비동기 LLM 호출 (통계 추적 포함)

        Args:
            messages: 메시지 리스트
            temperature: 온도 파라미터
            max_tokens: 최대 토큰 수

        Returns:
            Dict: LLM 응답
        """
        self._execution_stats["total_llm_calls"] += 1

        response = await self.llm_service.async_chat_completion(
            messages=messages,
            temperature=temperature or float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            max_tokens=max_tokens or int(os.getenv("DEFAULT_MAX_TOKENS", "2000"))
        )

        self._execution_stats["total_llm_tokens"] += response["usage"]["total_tokens"]

        return response

    def _rag_query(
        self,
        query: str,
        collection_types: List[str] = ["manuals"],
        max_results: int = 3
    ) -> Dict[str, Any]:
        """
        RAG 쿼리 실행

        Args:
            query: 쿼리
            collection_types: 검색할 컬렉션 타입
            max_results: 최대 결과 수

        Returns:
            Dict: RAG 결과
        """
        return self.rag_service.rag_query(
            query=query,
            collection_types=collection_types,
            max_context_results=max_results
        )

    def _mcp_call(
        self,
        server_name: str,
        tool_name: str,
        **kwargs
    ) -> Any:
        """
        MCP 도구 호출

        Args:
            server_name: MCP 서버 이름
            tool_name: 도구 이름
            **kwargs: 도구 파라미터

        Returns:
            Any: 도구 실행 결과
        """
        return self.mcp_hub.call_tool(
            server_name=server_name,
            tool_name=tool_name,
            **kwargs
        )

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        실행 통계 조회

        Returns:
            Dict: 실행 통계
        """
        return {
            "agent_name": self.name,
            "role": self.role,
            "stats": self._execution_stats.copy()
        }

    def reset_stats(self):
        """실행 통계 초기화"""
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_llm_calls": 0,
            "total_llm_tokens": 0
        }
        self.logger.info(f"Execution stats reset for {self.name}")

    async def execute_with_tracking(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        통계 추적과 함께 Task 실행

        Args:
            task: Task 정보

        Returns:
            Dict: 실행 결과
        """
        self._execution_stats["total_executions"] += 1
        start_time = time.time()

        try:
            self._log_action(f"Executing task: {task.get('task_type', 'unknown')}")

            result = await self.execute_task(task)

            execution_time = time.time() - start_time

            if result.get("success", False):
                self._execution_stats["successful_executions"] += 1
                self._log_action(f"Task completed successfully in {execution_time:.2f}s")
            else:
                self._execution_stats["failed_executions"] += 1
                self._log_action(f"Task failed after {execution_time:.2f}s", level="error")

            # Add execution metadata
            result["execution_time_seconds"] = execution_time
            result["agent_name"] = self.name
            result["timestamp"] = datetime.utcnow().isoformat()

            return result

        except Exception as e:
            self._execution_stats["failed_executions"] += 1
            execution_time = time.time() - start_time

            self._log_action(f"Task execution error: {str(e)}", level="error")

            return {
                "success": False,
                "error": str(e),
                "execution_time_seconds": execution_time,
                "agent_name": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }

    def __str__(self) -> str:
        """String representation"""
        return f"{self.name} (Role: {self.role})"

    def __repr__(self) -> str:
        """Representation"""
        return f"<BaseAgent name='{self.name}' role='{self.role}'>"


if __name__ == "__main__":
    # Test by creating a simple concrete implementation
    logging.basicConfig(level=logging.INFO)

    class TestAgent(BaseAgent):
        """Test Agent for demonstration"""

        def __init__(self):
            super().__init__(
                name="TestAgent",
                role="Test Specialist",
                goal="Perform testing tasks",
                backstory="A test agent for demonstration purposes"
            )

        def get_tools(self) -> List:
            return []

        async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
            """Simple test task execution"""
            self._log_action("Executing test task")

            # Simulate some work
            import asyncio
            await asyncio.sleep(1)

            return {
                "success": True,
                "result": "Test task completed",
                "task_type": task.get("task_type", "unknown")
            }

    async def test_agent():
        agent = TestAgent()
        print(f"\n=== Testing {agent} ===")

        # Test task execution
        task = {"task_type": "test", "data": "sample data"}
        result = await agent.execute_with_tracking(task)
        print(f"Result: {result}")

        # Test stats
        stats = agent.get_execution_stats()
        print(f"\nStats: {stats}")

    # Run test
    import asyncio
    asyncio.run(test_agent())
