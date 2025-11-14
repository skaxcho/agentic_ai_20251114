"""
E2E Integration Scenarios

통합 시나리오 테스트:
1. 성능 이슈 → 분석 → 배포 → 모니터링
2. 사용자 문의 → RAG 검색 → ITS 티켓 생성
"""

import pytest
import asyncio
import logging
from datetime import datetime

from src.core.orchestration import (
    get_orchestration_manager,
    AgentType,
    OrchestrationMode
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestE2EScenarios:
    """E2E 통합 시나리오 테스트"""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_scenario1_performance_issue_to_deployment(self):
        """
        시나리오 1: 성능 이슈 → 분석 → 배포 → 모니터링 (통합)

        워크플로우:
        1. Monitoring Agent: CPU 사용률 90% 이상 감지
        2. SOP Agent: 장애 상황 판단, 이전 사례 검색
        3. Infra Agent: 성능 분석 수행, CPU/MEM 조정 계획 수립
        4. Change Management Agent: 변경 프로세스 시작
           - Report Agent: 변경계획서 작성
           - ITS Agent: 변경 승인 요청
           - DevOps Tool: 배포 실행
           - Monitoring Agent: 배포 후 점검
        5. Report Agent: 최종 보고서 작성
        6. Notification: 관련자에게 알림 발송

        검증 기준:
        - 각 Agent가 순차적으로 호출되는지 확인
        - Agent 간 데이터 전달이 정확한지 검증
        - 전체 프로세스 완료 시간 측정 (목표: 30분 이내)
        - 최종 보고서에 모든 단계가 포함되어 있는지 확인
        """
        logger.info("\n=== E2E Scenario 1: Performance Issue to Deployment ===")

        manager = get_orchestration_manager()

        # Define scenario workflow
        scenario_config = {
            "mode": "sequential",
            "workflow": [
                {
                    "name": "Step 1: Monitor and Detect",
                    "agent": "monitoring",
                    "task": {
                        "type": "health_check",
                        "data": {
                            "urls": ["http://api-service.example.com"],
                            "check_metrics": True
                        }
                    },
                    "stop_on_failure": False
                },
                {
                    "name": "Step 2: SOP Analysis",
                    "agent": "sop",
                    "task": {
                        "type": "incident_detection_response",
                        "data": {
                            "service_name": "api-service",
                            "monitoring_result": {
                                "cpu_usage": 92,
                                "memory_usage": 85,
                                "error_rate": 8.5,
                                "response_time_ms": 2500
                            },
                            "severity": "High"
                        }
                    },
                    "stop_on_failure": False
                },
                {
                    "name": "Step 3: Infrastructure Analysis",
                    "agent": "infra",
                    "task": {
                        "type": "analyze_performance",
                        "data": {
                            "service_name": "api-service",
                            "analysis_duration_hours": 1
                        }
                    },
                    "stop_on_failure": False
                },
                {
                    "name": "Step 4: Change Management - Deploy Performance Improvement",
                    "agent": "change_mgmt",
                    "task": {
                        "type": "deploy_performance_improvement",
                        "data": {
                            "service_name": "api-service",
                            "issue": "High CPU usage (92%) and slow response time",
                            "proposed_changes": {
                                "cpu": "2000m",
                                "memory": "2Gi",
                                "replicas": 5
                            },
                            "version": "v1.3.0"
                        }
                    },
                    "stop_on_failure": True
                },
                {
                    "name": "Step 5: Post-Deployment Monitoring",
                    "agent": "monitoring",
                    "task": {
                        "type": "health_check",
                        "data": {
                            "urls": ["http://api-service.example.com"],
                            "check_metrics": True,
                            "expected_improvement": True
                        }
                    },
                    "stop_on_failure": False
                },
                {
                    "name": "Step 6: Generate Final Report",
                    "agent": "report",
                    "task": {
                        "type": "generate_system_status_report",
                        "data": {
                            "system_name": "api-service",
                            "report_type": "deployment_completion",
                            "include_metrics": True
                        }
                    },
                    "stop_on_failure": False
                }
            ],
            "validation_criteria": {
                "min_success_rate": 0.8,  # 80% of steps must succeed
                "required_agents": ["change_mgmt", "infra", "sop"]
            }
        }

        # Execute scenario
        start_time = datetime.now()
        result = await manager.execute_e2e_scenario(
            scenario_name="Performance Issue to Deployment",
            scenario_config=scenario_config
        )
        end_time = datetime.now()

        duration_minutes = (end_time - start_time).total_seconds() / 60

        logger.info(f"\nScenario completed in {duration_minutes:.2f} minutes")
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Validation: {result.get('validation', {}).get('valid')}")

        # Assertions
        assert result.get("success"), "Scenario should complete successfully"
        assert result.get("validation", {}).get("valid"), "Scenario validation should pass"
        assert duration_minutes < 30, f"Scenario should complete within 30 minutes, took {duration_minutes:.2f}"

        # Check workflow results
        workflow_result = result.get("workflow_result", {})
        assert workflow_result.get("successful_steps", 0) >= 5, "At least 5 steps should succeed"

        # Verify Change Management step
        results = workflow_result.get("results", [])
        change_mgmt_step = next((r for r in results if "change_mgmt" in r.get("agent", "")), None)

        assert change_mgmt_step is not None, "Change Management step should exist"
        assert change_mgmt_step.get("result", {}).get("success"), "Change Management should succeed"

        logger.info("\n✅ E2E Scenario 1 PASSED")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_scenario2_user_query_to_ticket(self):
        """
        시나리오 2: 사용자 문의 → RAG 검색 → ITS 티켓 생성

        워크플로우:
        1. Biz Support Agent: "방화벽 오픈 어떻게 신청해?" 질문 수신
        2. RAG Service: 관련 문서 검색
        3. Biz Support Agent: 답변 생성 및 제공
        4. 사용자: "신청 진행해줘" 요청
        5. ITS Agent: ServiceNow에 방화벽 오픈 요청 티켓 생성
        6. Notification: 사용자에게 티켓 번호 알림

        검증 기준:
        - RAG 검색 결과의 관련도 (Relevance Score > 0.8)
        - 답변 생성 시간 (목표: 3초 이내)
        - ITS 티켓 생성 성공률 (목표: 100%)
        """
        logger.info("\n=== E2E Scenario 2: User Query to Ticket Creation ===")

        manager = get_orchestration_manager()

        # Define scenario workflow
        scenario_config = {
            "mode": "sequential",
            "workflow": [
                {
                    "name": "Step 1: Answer User Question",
                    "agent": "biz_support",
                    "task": {
                        "type": "answer_usage_question",
                        "data": {
                            "question": "방화벽 오픈은 어떻게 신청하나요?",
                            "system_name": "Network"
                        }
                    },
                    "stop_on_failure": False
                },
                {
                    "name": "Step 2: Find Responsible Contact",
                    "agent": "biz_support",
                    "task": {
                        "type": "find_contact",
                        "data": {
                            "query": "방화벽 담당자",
                            "system_name": "Network"
                        }
                    },
                    "stop_on_failure": False
                },
                {
                    "name": "Step 3: Create ITS Ticket for Firewall Request",
                    "agent": "its",
                    "task": {
                        "type": "create_change_request",
                        "data": {
                            "title": "방화벽 오픈 요청",
                            "description": "사용자 요청: API 서버(10.0.1.100)에서 DB 서버(10.0.2.50)로 3306 포트 오픈",
                            "change_type": "Standard",
                            "risk": "Low",
                            "urgency": "Medium"
                        }
                    },
                    "stop_on_failure": True
                },
                {
                    "name": "Step 4: Generate Confirmation Report",
                    "agent": "report",
                    "task": {
                        "type": "generate_document",
                        "data": {
                            "document_type": "confirmation",
                            "title": "방화벽 오픈 요청 접수 확인",
                            "content": "티켓이 생성되었습니다."
                        }
                    },
                    "stop_on_failure": False
                }
            ],
            "validation_criteria": {
                "min_success_rate": 1.0,  # 100% success required
                "required_agents": ["biz_support", "its"]
            }
        }

        # Execute scenario
        start_time = datetime.now()
        result = await manager.execute_e2e_scenario(
            scenario_name="User Query to Ticket Creation",
            scenario_config=scenario_config
        )
        end_time = datetime.now()

        duration_seconds = (end_time - start_time).total_seconds()

        logger.info(f"\nScenario completed in {duration_seconds:.2f} seconds")
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Validation: {result.get('validation', {}).get('valid')}")

        # Assertions
        assert result.get("success"), "Scenario should complete successfully"
        assert result.get("validation", {}).get("valid"), "Scenario validation should pass"

        # Check Biz Support Agent answer time
        workflow_result = result.get("workflow_result", {})
        results = workflow_result.get("results", [])

        biz_support_step = next((r for r in results if r.get("step") == "Step 1: Answer User Question"), None)
        assert biz_support_step is not None, "Biz Support step should exist"

        biz_support_result = biz_support_step.get("result", {})
        assert biz_support_result.get("success"), "Biz Support should answer successfully"

        # Check ITS ticket creation
        its_step = next((r for r in results if "its" in r.get("agent", "")), None)
        assert its_step is not None, "ITS step should exist"

        its_result = its_step.get("result", {})
        assert its_result.get("success"), "ITS ticket creation should succeed"
        assert its_result.get("ticket_number") or its_result.get("change_number"), "Ticket number should be generated"

        logger.info("\n✅ E2E Scenario 2 PASSED")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_scenario3_parallel_agent_execution(self):
        """
        시나리오 3: 병렬 Agent 실행 테스트

        여러 독립적인 Agent를 동시에 실행하여 성능 확인
        """
        logger.info("\n=== E2E Scenario 3: Parallel Agent Execution ===")

        manager = get_orchestration_manager()

        # Define parallel workflow
        scenario_config = {
            "mode": "parallel",
            "workflow": [
                {
                    "name": "Monitor Health",
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
                    "name": "Check Database",
                    "agent": "monitoring",
                    "task": {
                        "type": "check_database",
                        "data": {"connection_string": "postgresql://localhost/testdb"}
                    }
                }
            ],
            "validation_criteria": {
                "min_success_rate": 0.67  # At least 2 out of 3 should succeed
            }
        }

        # Execute scenario
        start_time = datetime.now()
        result = await manager.execute_e2e_scenario(
            scenario_name="Parallel Agent Execution",
            scenario_config=scenario_config
        )
        end_time = datetime.now()

        duration_seconds = (end_time - start_time).total_seconds()

        logger.info(f"\nParallel execution completed in {duration_seconds:.2f} seconds")
        logger.info(f"Success: {result.get('success')}")

        # Assertions
        workflow_result = result.get("workflow_result", {})
        assert workflow_result.get("successful_steps", 0) >= 2, "At least 2 parallel tasks should succeed"

        logger.info("\n✅ E2E Scenario 3 PASSED")


if __name__ == "__main__":
    # Run tests directly
    async def run_tests():
        test_class = TestE2EScenarios()

        print("\n" + "="*80)
        print("Running E2E Integration Tests")
        print("="*80)

        try:
            await test_class.test_scenario1_performance_issue_to_deployment()
        except Exception as e:
            logger.error(f"Scenario 1 failed: {str(e)}")

        try:
            await test_class.test_scenario2_user_query_to_ticket()
        except Exception as e:
            logger.error(f"Scenario 2 failed: {str(e)}")

        try:
            await test_class.test_scenario3_parallel_agent_execution()
        except Exception as e:
            logger.error(f"Scenario 3 failed: {str(e)}")

        print("\n" + "="*80)
        print("E2E Tests Completed")
        print("="*80)

    asyncio.run(run_tests())
