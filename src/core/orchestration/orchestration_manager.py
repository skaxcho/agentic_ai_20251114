"""
Orchestration Manager

모든 Agent를 관리하고 Task를 조율하는 중앙 오케스트레이터
- Agent 선택 및 라우팅
- Multi-agent 협업 조율
- Task context 공유
- Error handling 및 fallback
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
from enum import Enum

# Import all agents
from src.agents.report_agent import get_report_agent
from src.agents.monitoring_agent import get_monitoring_agent
from src.agents.its_agent import get_its_agent
from src.agents.db_extract_agent import get_db_extract_agent
from src.agents.change_mgmt_agent import get_change_mgmt_agent
from src.agents.biz_support_agent import get_biz_support_agent
from src.agents.sop_agent import get_sop_agent
from src.agents.infra_agent import get_infra_agent

# Configure logging
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Agent 유형"""
    REPORT = "report"
    MONITORING = "monitoring"
    ITS = "its"
    DB_EXTRACT = "db_extract"
    CHANGE_MGMT = "change_mgmt"
    BIZ_SUPPORT = "biz_support"
    SOP = "sop"
    INFRA = "infra"


class OrchestrationMode(Enum):
    """Orchestration 모드"""
    SEQUENTIAL = "sequential"  # 순차 실행
    PARALLEL = "parallel"  # 병렬 실행
    CONDITIONAL = "conditional"  # 조건부 실행
    DELEGATED = "delegated"  # 위임 실행


class OrchestrationManager:
    """Orchestration Manager - 모든 Agent 관리 및 조율"""

    def __init__(self):
        """Initialize Orchestration Manager"""
        # Initialize all agents
        self.agents = {
            AgentType.REPORT: get_report_agent(),
            AgentType.MONITORING: get_monitoring_agent(),
            AgentType.ITS: get_its_agent(),
            AgentType.DB_EXTRACT: get_db_extract_agent(),
            AgentType.CHANGE_MGMT: get_change_mgmt_agent(),
            AgentType.BIZ_SUPPORT: get_biz_support_agent(),
            AgentType.SOP: get_sop_agent(),
            AgentType.INFRA: get_infra_agent()
        }

        # Task execution history
        self.execution_history = []

        # Shared context for multi-agent collaboration
        self.shared_context = {}

        logger.info("OrchestrationManager initialized with 8 agents")

    async def execute_task(
        self,
        agent_type: AgentType,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        단일 Agent에게 Task 실행 요청

        Args:
            agent_type: Agent 유형
            task: Task 정의
            context: 공유 컨텍스트 (optional)

        Returns:
            Dict: Task 실행 결과
        """
        try:
            agent = self.agents.get(agent_type)

            if not agent:
                return {
                    "success": False,
                    "error": f"Agent not found: {agent_type}"
                }

            logger.info(f"Executing task on {agent_type.value} agent")

            # Add context to task if provided
            if context:
                task["context"] = context

            # Execute task
            start_time = datetime.now()
            result = await agent.execute_task(task)
            end_time = datetime.now()

            # Record execution
            execution_record = {
                "agent_type": agent_type.value,
                "task_type": task.get("type"),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds(),
                "success": result.get("success", False)
            }

            self.execution_history.append(execution_record)

            logger.info(f"Task completed on {agent_type.value} agent - Success: {result.get('success')}")

            return result

        except Exception as e:
            logger.error(f"Failed to execute task on {agent_type.value}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "agent_type": agent_type.value
            }

    async def orchestrate_workflow(
        self,
        workflow: List[Dict[str, Any]],
        mode: OrchestrationMode = OrchestrationMode.SEQUENTIAL
    ) -> Dict[str, Any]:
        """
        Multi-agent 워크플로우 실행

        Args:
            workflow: 워크플로우 정의 (Agent + Task 리스트)
            mode: Orchestration 모드

        Returns:
            Dict: 워크플로우 실행 결과
        """
        try:
            workflow_id = f"WF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            logger.info(f"Starting workflow {workflow_id} - Mode: {mode.value}, Steps: {len(workflow)}")

            results = []
            workflow_context = {}

            if mode == OrchestrationMode.SEQUENTIAL:
                # 순차 실행
                for step in workflow:
                    agent_type = AgentType(step["agent"])
                    task = step["task"]

                    # Add previous results to context
                    task_result = await self.execute_task(
                        agent_type=agent_type,
                        task=task,
                        context=workflow_context
                    )

                    results.append({
                        "step": step.get("name", f"Step {len(results) + 1}"),
                        "agent": agent_type.value,
                        "result": task_result
                    })

                    # Update shared context
                    if task_result.get("success"):
                        workflow_context[agent_type.value] = task_result

                    # Stop on failure if configured
                    if not task_result.get("success") and step.get("stop_on_failure", False):
                        logger.warning(f"Workflow stopped due to failure at step: {step.get('name')}")
                        break

            elif mode == OrchestrationMode.PARALLEL:
                # 병렬 실행
                tasks = []

                for step in workflow:
                    agent_type = AgentType(step["agent"])
                    task = step["task"]

                    tasks.append(
                        self.execute_task(
                            agent_type=agent_type,
                            task=task,
                            context=workflow_context
                        )
                    )

                # Wait for all tasks
                task_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, task_result in enumerate(task_results):
                    if isinstance(task_result, Exception):
                        results.append({
                            "step": workflow[i].get("name", f"Step {i + 1}"),
                            "agent": workflow[i]["agent"],
                            "result": {
                                "success": False,
                                "error": str(task_result)
                            }
                        })
                    else:
                        results.append({
                            "step": workflow[i].get("name", f"Step {i + 1}"),
                            "agent": workflow[i]["agent"],
                            "result": task_result
                        })

            elif mode == OrchestrationMode.CONDITIONAL:
                # 조건부 실행
                for step in workflow:
                    # Check condition
                    condition = step.get("condition")

                    if condition:
                        # Evaluate condition based on previous results
                        should_execute = self._evaluate_condition(condition, workflow_context)

                        if not should_execute:
                            logger.info(f"Skipping step {step.get('name')} - Condition not met")
                            continue

                    agent_type = AgentType(step["agent"])
                    task = step["task"]

                    task_result = await self.execute_task(
                        agent_type=agent_type,
                        task=task,
                        context=workflow_context
                    )

                    results.append({
                        "step": step.get("name", f"Step {len(results) + 1}"),
                        "agent": agent_type.value,
                        "result": task_result
                    })

                    # Update context
                    if task_result.get("success"):
                        workflow_context[agent_type.value] = task_result

            # Calculate workflow success
            success_count = sum(1 for r in results if r["result"].get("success", False))
            workflow_success = success_count == len(results)

            logger.info(f"Workflow {workflow_id} completed - Success rate: {success_count}/{len(results)}")

            return {
                "success": workflow_success,
                "workflow_id": workflow_id,
                "mode": mode.value,
                "total_steps": len(workflow),
                "successful_steps": success_count,
                "results": results,
                "workflow_context": workflow_context,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to orchestrate workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_e2e_scenario(
        self,
        scenario_name: str,
        scenario_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        E2E 시나리오 실행

        Args:
            scenario_name: 시나리오 이름
            scenario_config: 시나리오 설정

        Returns:
            Dict: 시나리오 실행 결과
        """
        try:
            logger.info(f"Executing E2E scenario: {scenario_name}")

            scenario_id = f"E2E-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Get scenario workflow
            workflow = scenario_config.get("workflow", [])
            mode = OrchestrationMode(scenario_config.get("mode", "sequential"))

            # Execute workflow
            workflow_result = await self.orchestrate_workflow(
                workflow=workflow,
                mode=mode
            )

            # Validate scenario completion
            validation_criteria = scenario_config.get("validation_criteria", {})
            validation_result = self._validate_scenario(workflow_result, validation_criteria)

            logger.info(f"E2E scenario {scenario_name} completed - Valid: {validation_result.get('valid')}")

            return {
                "success": workflow_result.get("success", False),
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "workflow_result": workflow_result,
                "validation": validation_result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to execute E2E scenario {scenario_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "scenario_name": scenario_name
            }

    def select_agent(self, user_query: str) -> AgentType:
        """
        사용자 쿼리를 분석하여 적절한 Agent 선택

        Args:
            user_query: 사용자 쿼리

        Returns:
            AgentType: 선택된 Agent 유형
        """
        query_lower = user_query.lower()

        # Simple keyword-based routing
        if any(word in query_lower for word in ["보고서", "report", "회의록", "주간"]):
            return AgentType.REPORT

        if any(word in query_lower for word in ["모니터링", "health", "점검", "상태"]):
            return AgentType.MONITORING

        if any(word in query_lower for word in ["티켓", "incident", "인시던트", "its"]):
            return AgentType.ITS

        if any(word in query_lower for word in ["쿼리", "sql", "데이터", "database"]):
            return AgentType.DB_EXTRACT

        if any(word in query_lower for word in ["배포", "deploy", "변경", "패치"]):
            return AgentType.CHANGE_MGMT

        if any(word in query_lower for word in ["문의", "사용법", "담당자", "계정"]):
            return AgentType.BIZ_SUPPORT

        if any(word in query_lower for word in ["장애", "sop", "조치", "incident"]):
            return AgentType.SOP

        if any(word in query_lower for word in ["성능", "스케일", "인프라", "scale"]):
            return AgentType.INFRA

        # Default to Biz Support for general queries
        return AgentType.BIZ_SUPPORT

    def get_agent_status(self) -> Dict[str, Any]:
        """
        모든 Agent 상태 조회

        Returns:
            Dict: Agent 상태 정보
        """
        status = {
            "total_agents": len(self.agents),
            "agents": {},
            "total_executions": len(self.execution_history),
            "timestamp": datetime.now().isoformat()
        }

        for agent_type, agent in self.agents.items():
            agent_executions = [
                e for e in self.execution_history
                if e["agent_type"] == agent_type.value
            ]

            status["agents"][agent_type.value] = {
                "name": agent.name,
                "role": agent.role,
                "total_executions": len(agent_executions),
                "successful_executions": sum(1 for e in agent_executions if e["success"])
            }

        return status

    def get_execution_history(
        self,
        agent_type: Optional[AgentType] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        실행 히스토리 조회

        Args:
            agent_type: Agent 유형 (optional)
            limit: 최대 개수

        Returns:
            List[Dict]: 실행 히스토리
        """
        history = self.execution_history

        if agent_type:
            history = [h for h in history if h["agent_type"] == agent_type.value]

        # Return most recent
        return history[-limit:]

    def _evaluate_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        조건 평가

        Args:
            condition: 조건 정의
            context: 실행 컨텍스트

        Returns:
            bool: 조건 만족 여부
        """
        # Simplified condition evaluation
        condition_type = condition.get("type")

        if condition_type == "agent_success":
            agent = condition.get("agent")
            return context.get(agent, {}).get("success", False)

        if condition_type == "field_equals":
            agent = condition.get("agent")
            field = condition.get("field")
            value = condition.get("value")

            agent_result = context.get(agent, {})
            return agent_result.get(field) == value

        # Default: execute
        return True

    def _validate_scenario(
        self,
        workflow_result: Dict[str, Any],
        validation_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        시나리오 검증

        Args:
            workflow_result: 워크플로우 실행 결과
            validation_criteria: 검증 기준

        Returns:
            Dict: 검증 결과
        """
        validations = []
        all_valid = True

        # Check minimum success rate
        min_success_rate = validation_criteria.get("min_success_rate", 1.0)
        success_rate = workflow_result.get("successful_steps", 0) / max(workflow_result.get("total_steps", 1), 1)

        validations.append({
            "criterion": "Minimum success rate",
            "expected": f">= {min_success_rate * 100}%",
            "actual": f"{success_rate * 100:.1f}%",
            "valid": success_rate >= min_success_rate
        })

        if success_rate < min_success_rate:
            all_valid = False

        # Check specific agent results
        required_agents = validation_criteria.get("required_agents", [])

        for agent in required_agents:
            agent_result = workflow_result.get("workflow_context", {}).get(agent, {})
            agent_success = agent_result.get("success", False)

            validations.append({
                "criterion": f"{agent} agent success",
                "expected": "True",
                "actual": str(agent_success),
                "valid": agent_success
            })

            if not agent_success:
                all_valid = False

        return {
            "valid": all_valid,
            "validations": validations,
            "success_rate": success_rate
        }


# Singleton instance
_orchestration_manager_instance = None


def get_orchestration_manager() -> OrchestrationManager:
    """OrchestrationManager 싱글톤 인스턴스 반환"""
    global _orchestration_manager_instance
    if _orchestration_manager_instance is None:
        _orchestration_manager_instance = OrchestrationManager()
    return _orchestration_manager_instance


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def test_orchestration():
        print("\n=== Testing Orchestration Manager ===")
        manager = OrchestrationManager()

        # Test 1: Single agent execution
        print("\n--- Test 1: Single Agent Execution ---")
        result = await manager.execute_task(
            agent_type=AgentType.MONITORING,
            task={
                "type": "health_check",
                "data": {
                    "urls": ["http://api.example.com"]
                }
            }
        )
        print(f"Result: {result.get('success')}")

        # Test 2: Sequential workflow
        print("\n--- Test 2: Sequential Workflow ---")
        workflow = [
            {
                "name": "Monitor System",
                "agent": "monitoring",
                "task": {
                    "type": "health_check",
                    "data": {"urls": ["http://api.example.com"]}
                }
            },
            {
                "name": "Analyze Performance",
                "agent": "infra",
                "task": {
                    "type": "analyze_performance",
                    "data": {"service_name": "api-service"}
                }
            },
            {
                "name": "Generate Report",
                "agent": "report",
                "task": {
                    "type": "generate_weekly_report",
                    "data": {"week": "2025-W46"}
                }
            }
        ]

        result = await manager.orchestrate_workflow(
            workflow=workflow,
            mode=OrchestrationMode.SEQUENTIAL
        )
        print(f"Workflow success: {result.get('success')}")
        print(f"Steps completed: {result.get('successful_steps')}/{result.get('total_steps')}")

        # Test 3: Agent status
        print("\n--- Test 3: Agent Status ---")
        status = manager.get_agent_status()
        print(f"Total agents: {status['total_agents']}")
        print(f"Total executions: {status['total_executions']}")

    asyncio.run(test_orchestration())
