"""
Crew AI Integration

Crew AI 프레임워크를 사용한 Multi-agent 협업 구현
- Agent를 Crew AI Agent로 변환
- Task delegation 및 협업
- Sequential/Hierarchical process 지원
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from src.core.base.base_agent import BaseAgent
from src.core.orchestration.orchestration_manager import AgentType

# Configure logging
logger = logging.getLogger(__name__)


class CrewAIAgent:
    """
    Crew AI Agent Wrapper

    BaseAgent를 Crew AI 호환 Agent로 변환
    """

    def __init__(self, base_agent: BaseAgent, agent_type: AgentType):
        """
        Initialize Crew AI Agent

        Args:
            base_agent: BaseAgent 인스턴스
            agent_type: Agent 유형
        """
        self.base_agent = base_agent
        self.agent_type = agent_type
        self.name = base_agent.name
        self.role = base_agent.role
        self.goal = base_agent.goal
        self.backstory = base_agent.backstory

        logger.info(f"CrewAIAgent initialized: {self.name}")

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task through base agent

        Args:
            task: Task definition

        Returns:
            Dict: Task result
        """
        return await self.base_agent.execute_task(task)

    def to_crew_agent_config(self) -> Dict[str, Any]:
        """
        Convert to Crew AI agent configuration

        Returns:
            Dict: Crew AI agent configuration
        """
        return {
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
            "verbose": True,
            "allow_delegation": True
        }


class CrewAITask:
    """
    Crew AI Task Wrapper

    Task를 Crew AI 호환 형식으로 변환
    """

    def __init__(
        self,
        description: str,
        agent: CrewAIAgent,
        expected_output: str,
        task_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Crew AI Task

        Args:
            description: Task 설명
            agent: 담당 Agent
            expected_output: 기대 출력
            task_data: Task 데이터
        """
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.task_data = task_data or {}

        logger.info(f"CrewAITask created: {description}")

    def to_crew_task_config(self) -> Dict[str, Any]:
        """
        Convert to Crew AI task configuration

        Returns:
            Dict: Crew AI task configuration
        """
        return {
            "description": self.description,
            "expected_output": self.expected_output,
            "agent": self.agent.to_crew_agent_config()
        }


class CrewAICrew:
    """
    Crew AI Crew

    여러 Agent를 조율하는 Crew
    """

    def __init__(
        self,
        agents: List[CrewAIAgent],
        tasks: List[CrewAITask],
        process: str = "sequential"  # sequential, hierarchical
    ):
        """
        Initialize Crew

        Args:
            agents: Agent 리스트
            tasks: Task 리스트
            process: 프로세스 유형 (sequential, hierarchical)
        """
        self.agents = agents
        self.tasks = tasks
        self.process = process

        logger.info(f"CrewAICrew initialized: {len(agents)} agents, {len(tasks)} tasks, process={process}")

    async def kickoff(self) -> Dict[str, Any]:
        """
        Crew 실행

        Returns:
            Dict: 실행 결과
        """
        try:
            logger.info(f"Crew kickoff started: {self.process} process")

            results = []
            crew_context = {}

            if self.process == "sequential":
                # Sequential execution
                for i, task in enumerate(self.tasks):
                    logger.info(f"Executing task {i+1}/{len(self.tasks)}: {task.description}")

                    # Add previous results to context
                    task.task_data["crew_context"] = crew_context

                    # Execute task
                    task_result = await task.agent.execute_task(task.task_data)

                    results.append({
                        "task_description": task.description,
                        "agent": task.agent.name,
                        "result": task_result
                    })

                    # Update context
                    if task_result.get("success"):
                        crew_context[task.agent.agent_type.value] = task_result

            elif self.process == "hierarchical":
                # Hierarchical execution with manager
                # Manager delegates tasks to agents
                logger.info("Hierarchical process: Manager delegating tasks")

                manager_agent = self.agents[0]  # First agent is manager

                for task in self.tasks:
                    # Manager reviews and delegates
                    delegation_decision = {
                        "task": task.description,
                        "assigned_agent": task.agent.name,
                        "context": crew_context
                    }

                    logger.info(f"Manager delegating: {task.description} to {task.agent.name}")

                    task.task_data["delegation_decision"] = delegation_decision
                    task.task_data["crew_context"] = crew_context

                    # Execute task
                    task_result = await task.agent.execute_task(task.task_data)

                    results.append({
                        "task_description": task.description,
                        "agent": task.agent.name,
                        "delegated_by": manager_agent.name,
                        "result": task_result
                    })

                    # Update context
                    if task_result.get("success"):
                        crew_context[task.agent.agent_type.value] = task_result

            # Calculate success
            success_count = sum(1 for r in results if r["result"].get("success", False))
            all_success = success_count == len(results)

            logger.info(f"Crew kickoff completed: {success_count}/{len(results)} tasks successful")

            return {
                "success": all_success,
                "process": self.process,
                "total_tasks": len(results),
                "successful_tasks": success_count,
                "results": results,
                "crew_context": crew_context,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Crew kickoff failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class CrewAIManager:
    """
    Crew AI Manager

    Crew AI 프레임워크를 사용한 Agent 협업 관리
    """

    def __init__(self, orchestration_manager):
        """
        Initialize Crew AI Manager

        Args:
            orchestration_manager: OrchestrationManager 인스턴스
        """
        self.orchestration_manager = orchestration_manager

        # Convert all agents to Crew AI agents
        self.crew_agents = {}

        for agent_type, agent in orchestration_manager.agents.items():
            self.crew_agents[agent_type] = CrewAIAgent(
                base_agent=agent,
                agent_type=agent_type
            )

        logger.info(f"CrewAIManager initialized with {len(self.crew_agents)} agents")

    def create_crew(
        self,
        agent_types: List[AgentType],
        tasks: List[Dict[str, Any]],
        process: str = "sequential"
    ) -> CrewAICrew:
        """
        Create a Crew with specified agents and tasks

        Args:
            agent_types: Agent 유형 리스트
            tasks: Task 정의 리스트
            process: 프로세스 유형

        Returns:
            CrewAICrew: 생성된 Crew
        """
        # Get Crew AI agents
        agents = [self.crew_agents[agent_type] for agent_type in agent_types]

        # Create Crew AI tasks
        crew_tasks = []

        for task_def in tasks:
            agent_type = AgentType(task_def["agent"])
            agent = self.crew_agents[agent_type]

            crew_task = CrewAITask(
                description=task_def.get("description", task_def["task"].get("type", "Task")),
                agent=agent,
                expected_output=task_def.get("expected_output", "Task result"),
                task_data=task_def["task"]
            )

            crew_tasks.append(crew_task)

        # Create Crew
        crew = CrewAICrew(
            agents=agents,
            tasks=crew_tasks,
            process=process
        )

        return crew

    async def execute_crew_workflow(
        self,
        agent_types: List[AgentType],
        tasks: List[Dict[str, Any]],
        process: str = "sequential"
    ) -> Dict[str, Any]:
        """
        Execute a Crew workflow

        Args:
            agent_types: Agent 유형 리스트
            tasks: Task 정의 리스트
            process: 프로세스 유형

        Returns:
            Dict: 실행 결과
        """
        try:
            # Create Crew
            crew = self.create_crew(
                agent_types=agent_types,
                tasks=tasks,
                process=process
            )

            # Execute Crew
            result = await crew.kickoff()

            return result

        except Exception as e:
            logger.error(f"Failed to execute Crew workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


if __name__ == "__main__":
    import asyncio
    from src.core.orchestration import get_orchestration_manager

    logging.basicConfig(level=logging.INFO)

    async def test_crew_ai():
        print("\n=== Testing Crew AI Integration ===")

        # Get orchestration manager
        orch_manager = get_orchestration_manager()

        # Create Crew AI manager
        crew_manager = CrewAIManager(orch_manager)

        # Test: Sequential Crew
        print("\n--- Test: Sequential Crew ---")

        agent_types = [
            AgentType.MONITORING,
            AgentType.SOP,
            AgentType.REPORT
        ]

        tasks = [
            {
                "agent": "monitoring",
                "description": "Monitor system health and detect issues",
                "expected_output": "Health check report with identified issues",
                "task": {
                    "type": "health_check",
                    "data": {"urls": ["http://api.example.com"]}
                }
            },
            {
                "agent": "sop",
                "description": "Analyze incident and provide remediation guide",
                "expected_output": "Incident analysis with remediation steps",
                "task": {
                    "type": "incident_detection_response",
                    "data": {
                        "service_name": "api-service",
                        "monitoring_result": {"cpu_usage": 90}
                    }
                }
            },
            {
                "agent": "report",
                "description": "Generate incident report",
                "expected_output": "Comprehensive incident report",
                "task": {
                    "type": "generate_document",
                    "data": {
                        "document_type": "incident_report",
                        "title": "System Incident Report"
                    }
                }
            }
        ]

        result = await crew_manager.execute_crew_workflow(
            agent_types=agent_types,
            tasks=tasks,
            process="sequential"
        )

        print(f"Sequential Crew result: {result.get('success')}")
        print(f"Tasks completed: {result.get('successful_tasks')}/{result.get('total_tasks')}")

        # Test: Hierarchical Crew
        print("\n--- Test: Hierarchical Crew ---")

        result = await crew_manager.execute_crew_workflow(
            agent_types=agent_types,
            tasks=tasks,
            process="hierarchical"
        )

        print(f"Hierarchical Crew result: {result.get('success')}")
        print(f"Tasks completed: {result.get('successful_tasks')}/{result.get('total_tasks')}")

    asyncio.run(test_crew_ai())
