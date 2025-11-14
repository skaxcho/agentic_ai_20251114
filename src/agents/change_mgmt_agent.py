"""
Change Management Agent

변경관리 프로세스 자동화 및 조율
- 배포 계획 수립
- 다른 Agent 조율 (ITS, Report, Monitoring)
- 변경 승인 관리
- 배포 실행 및 모니터링
"""

from typing import Dict, Any, List
import logging
from datetime import datetime
import asyncio

from src.core.base.base_agent import BaseAgent
from src.core.tools.devops_tools import (
    get_deployment_tool,
    get_pipeline_tool,
    get_resource_manager_tool
)

# Configure logging
logger = logging.getLogger(__name__)


class ChangeManagementAgent(BaseAgent):
    """Change Management Agent - 변경관리 프로세스 조율"""

    def __init__(self):
        """Initialize Change Management Agent"""
        super().__init__(
            name="Change Management Agent",
            role="Change Management Orchestrator",
            goal="변경관리 프로세스 자동화 및 조율. 배포 계획 수립, 승인 관리, 배포 실행, 모니터링 조율",
            backstory="""
            나는 변경관리 프로세스의 모든 단계를 조율하는 오케스트레이터입니다.
            배포 계획 수립부터 승인, 실행, 모니터링까지 전체 프로세스를 관리합니다.
            필요 시 ITS Agent, Report Agent, Monitoring Agent를 호출하여 협업합니다.
            안전하고 효율적인 변경 관리를 보장합니다.
            """
        )

        # Initialize tools
        self.deployment_tool = get_deployment_tool()
        self.pipeline_tool = get_pipeline_tool()
        self.resource_manager = get_resource_manager_tool()

        logger.info("ChangeManagementAgent initialized")

    def get_tools(self) -> List:
        """Get tools for this agent"""
        return [
            self.deployment_tool,
            self.pipeline_tool,
            self.resource_manager
        ]

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute change management task

        Args:
            task: Task definition with type and data

        Returns:
            Dict: Task execution result
        """
        task_type = task.get("type")
        data = task.get("data", {})

        logger.info(f"Executing change management task: {task_type}")

        try:
            if task_type == "deploy_performance_improvement":
                # UC-C-01: 성능 개선 배포 (End-to-End)
                return await self._deploy_performance_improvement(data)
            elif task_type == "emergency_patch":
                # UC-C-02: 긴급 패치 배포
                return await self._deploy_emergency_patch(data)
            elif task_type == "regular_change":
                # UC-C-03: 정기 변경 프로세스
                return await self._execute_regular_change(data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown task type: {task_type}"
                }

        except Exception as e:
            logger.error(f"Failed to execute task: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _deploy_performance_improvement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-C-01: 성능 개선 배포 (End-to-End)

        전체 프로세스 조율:
        1. 성능 분석 (Infra Agent 또는 데이터)
        2. 배포 계획 수립
        3. 변경 요청 생성 (ITS Agent)
        4. 배포 계획서 작성 (Report Agent)
        5. 배포 실행
        6. 배포 후 모니터링 (Monitoring Agent)
        7. 최종 보고서 작성 (Report Agent)

        Args:
            data: {
                "service_name": str,
                "issue": str (e.g., "High CPU usage"),
                "proposed_changes": {"cpu": "1000m", "memory": "1Gi", "replicas": 5},
                "version": str (optional)
            }

        Returns:
            Dict: 배포 완료 보고서
        """
        try:
            service_name = data.get("service_name")
            issue = data.get("issue", "Performance improvement")
            proposed_changes = data.get("proposed_changes", {})
            version = data.get("version", "latest")

            logger.info(f"Starting performance improvement deployment for {service_name}")

            # Step 1: Analyze issue using LLM
            analysis_prompt = f"""
            서비스 '{service_name}'에 다음과 같은 성능 이슈가 발생했습니다:
            {issue}

            제안된 변경 사항:
            {proposed_changes}

            이 변경 사항이 이슈를 해결하기에 적절한지 분석하고,
            배포 시 고려해야 할 리스크와 완화 전략을 제시해주세요.
            """

            analysis = await self._llm_call(analysis_prompt, temperature=0.3)

            # Step 2: Create deployment plan
            logger.info("Creating deployment plan...")
            deployment_result = self.deployment_tool.create_deployment_plan(
                service_name=service_name,
                version=version,
                environment="production",
                strategy="rolling",
                resources=proposed_changes
            )

            if not deployment_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to create deployment plan",
                    "details": deployment_result
                }

            deployment_id = deployment_result["deployment_id"]
            deployment_plan = deployment_result["deployment_plan"]

            # Step 3: Create change request (simulate ITS Agent call)
            logger.info("Creating change request...")
            change_request = await self._create_change_request(
                title=f"Performance Improvement Deployment - {service_name}",
                description=f"Issue: {issue}\nProposed changes: {proposed_changes}",
                implementation_plan=f"Deploy version {version} with updated resources",
                risk_analysis=analysis.get("content", "")
            )

            # Step 4: Generate deployment plan document (simulate Report Agent call)
            logger.info("Generating deployment plan document...")
            deployment_doc = await self._generate_deployment_document(
                service_name=service_name,
                deployment_plan=deployment_plan,
                change_request=change_request,
                analysis=analysis.get("content", "")
            )

            # Step 5: Execute deployment
            logger.info("Executing deployment...")
            exec_result = self.deployment_tool.execute_deployment(
                deployment_id=deployment_id,
                auto_approve=False
            )

            if not exec_result["success"]:
                return {
                    "success": False,
                    "error": "Deployment failed",
                    "details": exec_result
                }

            # Step 6: Post-deployment monitoring (simulate Monitoring Agent call)
            logger.info("Starting post-deployment monitoring...")
            monitoring_result = await self._post_deployment_monitoring(
                service_name=service_name,
                deployment_id=deployment_id,
                duration_minutes=5
            )

            # Step 7: Generate final report (simulate Report Agent call)
            logger.info("Generating final report...")
            final_report = await self._generate_final_report(
                service_name=service_name,
                issue=issue,
                deployment_plan=deployment_plan,
                change_request=change_request,
                deployment_result=exec_result,
                monitoring_result=monitoring_result
            )

            # Send notification
            await self._send_notification(
                subject=f"Deployment Completed: {service_name}",
                message=f"Performance improvement deployment completed successfully.\nDeployment ID: {deployment_id}",
                recipients=["ops-team@company.com"]
            )

            logger.info(f"Performance improvement deployment completed: {deployment_id}")

            return {
                "success": True,
                "deployment_id": deployment_id,
                "change_request_number": change_request.get("number"),
                "status": "completed",
                "deployment_plan": deployment_plan,
                "monitoring_result": monitoring_result,
                "final_report": final_report,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to deploy performance improvement: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _deploy_emergency_patch(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-C-02: 긴급 패치 배포

        긴급 패치의 빠른 배포를 지원:
        1. 패치 정보 검증
        2. 긴급 변경 요청 생성
        3. 배포 체크리스트 생성
        4. 빠른 배포 실행
        5. 즉시 모니터링

        Args:
            data: {
                "service_name": str,
                "patch_info": str,
                "severity": str (critical, high, medium),
                "version": str
            }

        Returns:
            Dict: 배포 체크리스트 및 결과
        """
        try:
            service_name = data.get("service_name")
            patch_info = data.get("patch_info", "")
            severity = data.get("severity", "high")
            version = data.get("version", "patch")

            logger.info(f"Starting emergency patch deployment for {service_name} - Severity: {severity}")

            # Step 1: Validate patch information
            validation_prompt = f"""
            긴급 패치 정보를 검증해주세요:
            서비스: {service_name}
            패치 내용: {patch_info}
            심각도: {severity}

            다음을 확인해주세요:
            1. 패치의 필요성과 긴급성
            2. 잠재적 리스크
            3. 롤백 준비사항
            4. 배포 체크리스트 항목
            """

            validation = await self._llm_call(validation_prompt, temperature=0.2)

            # Step 2: Create emergency change request
            logger.info("Creating emergency change request...")
            change_request = await self._create_change_request(
                title=f"EMERGENCY: Security Patch - {service_name}",
                description=patch_info,
                implementation_plan="Fast-track emergency patch deployment",
                risk_analysis=validation.get("content", ""),
                change_type="Emergency"
            )

            # Step 3: Generate deployment checklist
            checklist = await self._generate_deployment_checklist(
                service_name=service_name,
                patch_info=patch_info,
                severity=severity
            )

            # Step 4: Create and execute deployment
            deployment_result = self.deployment_tool.create_deployment_plan(
                service_name=service_name,
                version=version,
                environment="production",
                strategy="rolling"  # Fast but safe
            )

            if deployment_result["success"]:
                deployment_id = deployment_result["deployment_id"]

                # Execute immediately for emergency
                exec_result = self.deployment_tool.execute_deployment(
                    deployment_id=deployment_id,
                    auto_approve=True  # Emergency auto-approval
                )
            else:
                exec_result = deployment_result

            # Step 5: Immediate monitoring
            if exec_result.get("success"):
                monitoring_result = await self._post_deployment_monitoring(
                    service_name=service_name,
                    deployment_id=deployment_result.get("deployment_id"),
                    duration_minutes=2  # Quick check for emergency
                )
            else:
                monitoring_result = {"status": "skipped", "reason": "Deployment failed"}

            # Send urgent notification
            await self._send_notification(
                subject=f"🚨 EMERGENCY PATCH DEPLOYED: {service_name}",
                message=f"Severity: {severity}\nPatch: {patch_info}\nStatus: {exec_result.get('status', 'failed')}",
                recipients=["ops-team@company.com", "security-team@company.com"],
                priority="high"
            )

            logger.info(f"Emergency patch deployment completed: {service_name}")

            return {
                "success": exec_result.get("success", False),
                "deployment_id": deployment_result.get("deployment_id"),
                "change_request_number": change_request.get("number"),
                "checklist": checklist,
                "validation": validation.get("content", ""),
                "deployment_result": exec_result,
                "monitoring_result": monitoring_result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to deploy emergency patch: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _execute_regular_change(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-C-03: 정기 변경 프로세스

        정기 변경 프로세스 관리:
        1. 변경 요청서 검토
        2. 승인 프로세스
        3. 배포 계획 수립
        4. 단계별 배포 실행
        5. 각 단계 검증

        Args:
            data: {
                "service_name": str,
                "change_description": str,
                "version": str,
                "scheduled_time": str (optional)
            }

        Returns:
            Dict: 각 단계별 검증 결과
        """
        try:
            service_name = data.get("service_name")
            change_description = data.get("change_description", "")
            version = data.get("version", "latest")
            scheduled_time = data.get("scheduled_time")

            logger.info(f"Starting regular change process for {service_name}")

            # Step 1: Review change request
            review_prompt = f"""
            정기 변경 요청을 검토해주세요:
            서비스: {service_name}
            변경 내용: {change_description}
            버전: {version}

            다음을 평가해주세요:
            1. 변경의 타당성
            2. 리스크 평가 (Low/Medium/High)
            3. 필요한 승인 단계
            4. 권장 배포 전략
            5. 테스트 요구사항
            """

            review = await self._llm_call(review_prompt, temperature=0.3)

            # Step 2: Create change request
            logger.info("Creating change request...")
            change_request = await self._create_change_request(
                title=f"Regular Change: {service_name} - {version}",
                description=change_description,
                implementation_plan="Follow regular change process",
                risk_analysis=review.get("content", ""),
                change_type="Normal"
            )

            # Step 3: Wait for approval (simulation)
            logger.info("Waiting for approval...")
            await asyncio.sleep(1)  # Simulate approval wait
            approval_status = "approved"  # Simulate approval

            if approval_status != "approved":
                return {
                    "success": False,
                    "error": "Change request not approved",
                    "change_request": change_request
                }

            # Step 4: Create deployment plan
            deployment_result = self.deployment_tool.create_deployment_plan(
                service_name=service_name,
                version=version,
                environment="production",
                strategy="blue-green"  # Safe strategy for regular changes
            )

            if not deployment_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to create deployment plan",
                    "details": deployment_result
                }

            deployment_id = deployment_result["deployment_id"]
            deployment_plan = deployment_result["deployment_plan"]

            # Step 5: Execute deployment with stage validation
            logger.info("Executing deployment with stage validation...")
            exec_result = self.deployment_tool.execute_deployment(
                deployment_id=deployment_id,
                auto_approve=False
            )

            # Step 6: Validate each stage
            stage_validations = []
            if exec_result.get("success"):
                for stage in exec_result.get("results", []):
                    validation = await self._validate_deployment_stage(
                        service_name=service_name,
                        stage=stage
                    )
                    stage_validations.append(validation)

            # Step 7: Post-deployment validation
            final_validation = await self._post_deployment_monitoring(
                service_name=service_name,
                deployment_id=deployment_id,
                duration_minutes=10  # Thorough monitoring for regular changes
            )

            # Send completion notification
            await self._send_notification(
                subject=f"Regular Change Completed: {service_name}",
                message=f"Version {version} deployed successfully.\nAll stages validated.",
                recipients=["ops-team@company.com", "change-board@company.com"]
            )

            logger.info(f"Regular change process completed: {deployment_id}")

            return {
                "success": True,
                "deployment_id": deployment_id,
                "change_request_number": change_request.get("number"),
                "approval_status": approval_status,
                "deployment_plan": deployment_plan,
                "stage_validations": stage_validations,
                "final_validation": final_validation,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to execute regular change: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_change_request(
        self,
        title: str,
        description: str,
        implementation_plan: str,
        risk_analysis: str,
        change_type: str = "Normal"
    ) -> Dict[str, Any]:
        """
        변경 요청 생성 (ITS Agent 시뮬레이션)

        Args:
            title: 변경 제목
            description: 변경 설명
            implementation_plan: 구현 계획
            risk_analysis: 리스크 분석
            change_type: 변경 유형

        Returns:
            Dict: 변경 요청 정보
        """
        # Simulate ITS Agent call
        change_number = f"CHG{datetime.now().strftime('%Y%m%d%H%M%S')}"

        change_request = {
            "number": change_number,
            "title": title,
            "description": description,
            "type": change_type,
            "implementation_plan": implementation_plan,
            "risk_analysis": risk_analysis,
            "status": "Draft",
            "requested_by": "Change Management Agent",
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"Change request created: {change_number}")

        return change_request

    async def _generate_deployment_document(
        self,
        service_name: str,
        deployment_plan: Dict[str, Any],
        change_request: Dict[str, Any],
        analysis: str
    ) -> Dict[str, Any]:
        """
        배포 계획서 생성 (Report Agent 시뮬레이션)

        Args:
            service_name: 서비스 이름
            deployment_plan: 배포 계획
            change_request: 변경 요청
            analysis: 분석 결과

        Returns:
            Dict: 배포 계획서
        """
        doc_prompt = f"""
        다음 정보를 바탕으로 배포 계획서를 작성해주세요:

        서비스: {service_name}
        변경 요청: {change_request.get('number')}
        배포 전략: {deployment_plan.get('strategy')}

        분석 결과:
        {analysis}

        배포 계획서에는 다음이 포함되어야 합니다:
        1. 배포 개요
        2. 배포 단계
        3. 리스크 및 완화 전략
        4. 롤백 계획
        5. 검증 기준
        """

        document = await self._llm_call(doc_prompt, temperature=0.4)

        return {
            "title": f"Deployment Plan - {service_name}",
            "content": document.get("content", ""),
            "created_at": datetime.now().isoformat()
        }

    async def _post_deployment_monitoring(
        self,
        service_name: str,
        deployment_id: str,
        duration_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        배포 후 모니터링 (Monitoring Agent 시뮬레이션)

        Args:
            service_name: 서비스 이름
            deployment_id: 배포 ID
            duration_minutes: 모니터링 기간 (분)

        Returns:
            Dict: 모니터링 결과
        """
        logger.info(f"Starting post-deployment monitoring for {service_name} (duration: {duration_minutes}min)")

        # Simulate monitoring
        await asyncio.sleep(1)

        monitoring_result = {
            "service_name": service_name,
            "deployment_id": deployment_id,
            "duration_minutes": duration_minutes,
            "health_check": "passed",
            "error_rate": 0.02,
            "response_time_ms": 145,
            "cpu_usage_percent": 45,
            "memory_usage_percent": 58,
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Post-deployment monitoring completed: {service_name} - Status: healthy")

        return monitoring_result

    async def _generate_final_report(
        self,
        service_name: str,
        issue: str,
        deployment_plan: Dict[str, Any],
        change_request: Dict[str, Any],
        deployment_result: Dict[str, Any],
        monitoring_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        최종 보고서 생성 (Report Agent 시뮬레이션)

        Args:
            service_name: 서비스 이름
            issue: 이슈
            deployment_plan: 배포 계획
            change_request: 변경 요청
            deployment_result: 배포 결과
            monitoring_result: 모니터링 결과

        Returns:
            Dict: 최종 보고서
        """
        report_prompt = f"""
        배포 완료 보고서를 작성해주세요:

        서비스: {service_name}
        이슈: {issue}
        변경 요청 번호: {change_request.get('number')}
        배포 ID: {deployment_plan.get('deployment_id')}
        배포 전략: {deployment_plan.get('strategy')}

        배포 결과:
        - 상태: {deployment_result.get('status')}
        - 완료 시간: {deployment_result.get('completed_at')}

        모니터링 결과:
        - Health Check: {monitoring_result.get('health_check')}
        - Error Rate: {monitoring_result.get('error_rate')}
        - Response Time: {monitoring_result.get('response_time_ms')}ms

        보고서 형식:
        1. 요약
        2. 배포 내역
        3. 검증 결과
        4. 후속 조치 (필요시)
        """

        report = await self._llm_call(report_prompt, temperature=0.4)

        return {
            "title": f"Deployment Report - {service_name}",
            "content": report.get("content", ""),
            "created_at": datetime.now().isoformat()
        }

    async def _generate_deployment_checklist(
        self,
        service_name: str,
        patch_info: str,
        severity: str
    ) -> Dict[str, Any]:
        """
        배포 체크리스트 생성

        Args:
            service_name: 서비스 이름
            patch_info: 패치 정보
            severity: 심각도

        Returns:
            Dict: 배포 체크리스트
        """
        checklist_prompt = f"""
        긴급 패치 배포를 위한 체크리스트를 작성해주세요:

        서비스: {service_name}
        패치 내용: {patch_info}
        심각도: {severity}

        체크리스트 항목:
        1. 배포 전 확인사항
        2. 배포 중 모니터링 항목
        3. 배포 후 검증 항목
        4. 롤백 준비사항
        """

        checklist = await self._llm_call(checklist_prompt, temperature=0.3)

        return {
            "title": f"Emergency Patch Checklist - {service_name}",
            "items": checklist.get("content", ""),
            "created_at": datetime.now().isoformat()
        }

    async def _validate_deployment_stage(
        self,
        service_name: str,
        stage: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        배포 단계 검증

        Args:
            service_name: 서비스 이름
            stage: 배포 단계 정보

        Returns:
            Dict: 검증 결과
        """
        logger.info(f"Validating deployment stage: {stage.get('step')}")

        # Simulate validation
        await asyncio.sleep(0.5)

        validation = {
            "stage": stage.get("step"),
            "status": "passed",
            "timestamp": datetime.now().isoformat(),
            "checks": [
                "Health check passed",
                "No errors in logs",
                "Response time within threshold"
            ]
        }

        return validation


# Singleton instance
_change_mgmt_agent_instance = None


def get_change_mgmt_agent() -> ChangeManagementAgent:
    """ChangeManagementAgent 싱글톤 인스턴스 반환"""
    global _change_mgmt_agent_instance
    if _change_mgmt_agent_instance is None:
        _change_mgmt_agent_instance = ChangeManagementAgent()
    return _change_mgmt_agent_instance


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def test_agent():
        print("\n=== Testing Change Management Agent ===")
        agent = ChangeManagementAgent()

        # Test UC-C-01: Performance improvement deployment
        print("\n--- Test UC-C-01: Performance Improvement Deployment ---")
        result = await agent.execute_task({
            "type": "deploy_performance_improvement",
            "data": {
                "service_name": "api-service",
                "issue": "High CPU usage (90%) during peak hours",
                "proposed_changes": {
                    "cpu": "1000m",
                    "memory": "1Gi",
                    "replicas": 5
                },
                "version": "v1.2.0"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Deployment ID: {result.get('deployment_id')}")
        print(f"Change Request: {result.get('change_request_number')}")

        # Test UC-C-02: Emergency patch
        print("\n--- Test UC-C-02: Emergency Patch Deployment ---")
        result = await agent.execute_task({
            "type": "emergency_patch",
            "data": {
                "service_name": "api-service",
                "patch_info": "Critical security vulnerability fix (CVE-2024-1234)",
                "severity": "critical",
                "version": "v1.1.5-patch"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Checklist items: {len(result.get('checklist', {}).get('items', '').split('\\n'))}")

        # Test UC-C-03: Regular change
        print("\n--- Test UC-C-03: Regular Change Process ---")
        result = await agent.execute_task({
            "type": "regular_change",
            "data": {
                "service_name": "web-app",
                "change_description": "Update to new UI components and bug fixes",
                "version": "v2.0.0"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Stage validations: {len(result.get('stage_validations', []))}")

    asyncio.run(test_agent())
