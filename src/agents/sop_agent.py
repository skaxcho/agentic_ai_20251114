"""
SOP (Standard Operating Procedure) Agent

표준운영절차 기반 장애 대응
- 장애 자동 감지 및 조치
- 유사 장애 사례 검색
- 장애 전파 및 보고
"""

from typing import Dict, Any, List
import logging
from datetime import datetime
import asyncio

from src.core.base.base_agent import BaseAgent

# Configure logging
logger = logging.getLogger(__name__)


class SOPAgent(BaseAgent):
    """SOP Agent - 표준운영절차 기반 장애 대응"""

    def __init__(self):
        """Initialize SOP Agent"""
        super().__init__(
            name="SOP Agent",
            role="Standard Operating Procedure Specialist",
            goal="장애 상황 판단 및 자동 조치. 표준운영절차(SOP)에 따라 장애를 신속하게 대응",
            backstory="""
            나는 표준운영절차(SOP) 전문가입니다.
            장애 발생 시 신속하게 상황을 판단하고, 과거 유사 사례를 검색하여
            최적의 조치 방법을 제시합니다.
            자동화된 조치가 가능한 경우 즉시 실행하며,
            관련 담당자에게 신속하게 알림을 전파합니다.
            """
        )

        logger.info("SOPAgent initialized")

    def get_tools(self) -> List:
        """Get tools for this agent"""
        return [
            # Monitoring Agent accessible through execute_task
            # RAG for knowledge base search
            # Notification through self._send_notification
        ]

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute SOP task

        Args:
            task: Task definition with type and data

        Returns:
            Dict: Task execution result
        """
        task_type = task.get("type")
        data = task.get("data", {})

        logger.info(f"Executing SOP task: {task_type}")

        try:
            if task_type == "incident_detection_response":
                # UC-S-01: 장애 자동 감지 및 조치
                return await self._incident_detection_response(data)
            elif task_type == "search_similar_incidents":
                # UC-S-02: 유사 장애 사례 검색
                return await self._search_similar_incidents(data)
            elif task_type == "incident_notification":
                # UC-S-03: 장애 전파 및 보고
                return await self._incident_notification(data)
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

    async def _incident_detection_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-S-01: 장애 자동 감지 및 조치

        모니터링 결과를 분석하여 장애를 감지하고 자동 조치

        Args:
            data: {
                "monitoring_result": Dict (from Monitoring Agent),
                "service_name": str,
                "severity": str (optional)
            }

        Returns:
            Dict: 조치 가이드 및 실행 결과
        """
        try:
            monitoring_result = data.get("monitoring_result", {})
            service_name = data.get("service_name", "")
            severity = data.get("severity")

            logger.info(f"Processing incident detection for {service_name}")

            # Step 1: Analyze monitoring result
            analysis_prompt = f"""
            모니터링 결과를 분석하여 장애 여부를 판단해주세요:

            서비스: {service_name}
            모니터링 결과:
            {monitoring_result}

            다음을 분석해주세요:
            1. 장애 발생 여부 (Yes/No)
            2. 장애 유형 (성능, 가용성, 에러 등)
            3. 심각도 (Critical/High/Medium/Low)
            4. 영향 범위
            5. 추정 원인
            """

            analysis = await self._llm_call(analysis_prompt, temperature=0.2)
            analysis_content = analysis.get("content", "")

            # Step 2: Determine if this is an incident
            is_incident = "장애 발생 여부: Yes" in analysis_content or "장애 발생 여부: yes" in analysis_content

            if not is_incident:
                logger.info("No incident detected")
                return {
                    "success": True,
                    "is_incident": False,
                    "analysis": analysis_content,
                    "message": "No incident detected",
                    "timestamp": datetime.now().isoformat()
                }

            # Step 3: Search for similar incidents
            logger.info("Searching for similar incidents...")
            similar_incidents = await self._search_similar_incidents({
                "symptoms": analysis_content,
                "service_name": service_name
            })

            # Step 4: Generate remediation guide
            remediation_prompt = f"""
            장애 조치 가이드를 생성해주세요:

            서비스: {service_name}
            분석 결과:
            {analysis_content}

            유사 장애 사례:
            {similar_incidents.get('summary', '유사 사례 없음')}

            다음 형식으로 조치 가이드를 작성해주세요:
            1. 즉시 조치 사항 (자동화 가능)
            2. 수동 조치 사항
            3. 모니터링 사항
            4. 에스컬레이션 기준
            5. 예상 복구 시간
            """

            remediation_guide = await self._llm_call(remediation_prompt, temperature=0.3)

            # Step 5: Execute automated remediation (if applicable)
            logger.info("Checking for automated remediation...")
            auto_remediation_result = await self._execute_auto_remediation(
                service_name=service_name,
                incident_type=analysis_content,
                remediation_guide=remediation_guide.get("content", "")
            )

            # Step 6: Create incident record
            incident_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            incident = {
                "incident_id": incident_id,
                "service_name": service_name,
                "detected_at": datetime.now().isoformat(),
                "severity": severity or "High",
                "status": "Detected",
                "monitoring_result": monitoring_result,
                "analysis": analysis_content,
                "similar_incidents": similar_incidents.get("incidents", [])[:3],
                "remediation_guide": remediation_guide.get("content", ""),
                "auto_remediation": auto_remediation_result
            }

            # Step 7: Notify stakeholders
            await self._incident_notification({
                "incident": incident,
                "urgency": "high" if severity in ["Critical", "High"] else "medium"
            })

            logger.info(f"Incident detection and response completed: {incident_id}")

            return {
                "success": True,
                "is_incident": True,
                "incident": incident,
                "analysis": analysis_content,
                "similar_incidents": similar_incidents.get("incidents", [])[:3],
                "remediation_guide": remediation_guide.get("content", ""),
                "auto_remediation_executed": auto_remediation_result.get("executed", False),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to process incident detection: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _search_similar_incidents(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-S-02: 유사 장애 사례 검색

        과거 장애 사례에서 유사한 케이스 검색

        Args:
            data: {
                "symptoms": str,
                "service_name": str (optional),
                "incident_type": str (optional)
            }

        Returns:
            Dict: 유사 장애 사례 목록
        """
        try:
            symptoms = data.get("symptoms", "")
            service_name = data.get("service_name")
            incident_type = data.get("incident_type")

            if not symptoms:
                return {
                    "success": False,
                    "error": "Symptoms are required"
                }

            logger.info(f"Searching for similar incidents: {symptoms[:50]}...")

            # Step 1: Prepare search query
            search_query = symptoms
            if service_name:
                search_query = f"{service_name} {symptoms}"

            # Step 2: Search incident history using RAG
            logger.info("Searching incident history...")

            rag_result = await self._rag_query(
                query=search_query,
                collection_types=["incidents"],
                top_k=10
            )

            if not rag_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to search incidents",
                    "details": rag_result
                }

            # Step 3: Extract and rank incidents
            incidents = []
            sources = rag_result.get("sources", [])

            for source in sources:
                metadata = source.get("metadata", {})
                incidents.append({
                    "incident_id": metadata.get("id", "Unknown"),
                    "title": metadata.get("title", "Unknown"),
                    "service": metadata.get("service", "Unknown"),
                    "symptoms": metadata.get("symptoms", ""),
                    "root_cause": metadata.get("root_cause", ""),
                    "resolution": metadata.get("resolution", ""),
                    "resolution_time": metadata.get("resolution_time", ""),
                    "similarity_score": source.get("score", 0.0)
                })

            # Step 4: Generate summary
            summary_prompt = f"""
            유사 장애 사례를 요약해주세요:

            현재 증상: {symptoms}
            찾은 사례 수: {len(incidents)}

            주요 사례 (Top 3):
            {incidents[:3]}

            다음을 요약해주세요:
            1. 공통 패턴
            2. 주요 원인
            3. 효과적인 해결 방법
            4. 예방 조치
            """

            summary = await self._llm_call(summary_prompt, temperature=0.4)

            # Step 5: Extract lessons learned
            lessons_prompt = f"""
            과거 사례에서 얻을 수 있는 교훈을 정리해주세요:

            유사 사례들:
            {incidents[:5]}

            다음을 작성해주세요:
            1. 반복되는 문제점
            2. 효과적이었던 대응
            3. 향후 개선 사항
            """

            lessons = await self._llm_call(lessons_prompt, temperature=0.4)

            logger.info(f"Found {len(incidents)} similar incidents")

            return {
                "success": True,
                "symptoms": symptoms,
                "incident_count": len(incidents),
                "incidents": incidents,
                "summary": summary.get("content", ""),
                "lessons_learned": lessons.get("content", ""),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to search similar incidents: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _incident_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        UC-S-03: 장애 전파 및 보고

        장애 정보를 관련자에게 전파

        Args:
            data: {
                "incident": Dict,
                "urgency": str (high, medium, low),
                "additional_recipients": List[str] (optional)
            }

        Returns:
            Dict: 알림 발송 결과
        """
        try:
            incident = data.get("incident", {})
            urgency = data.get("urgency", "medium")
            additional_recipients = data.get("additional_recipients", [])

            if not incident:
                return {
                    "success": False,
                    "error": "Incident information is required"
                }

            logger.info(f"Notifying incident: {incident.get('incident_id', 'Unknown')}")

            # Step 1: Determine notification recipients
            recipients = await self._determine_notification_recipients(
                incident=incident,
                urgency=urgency
            )

            # Add additional recipients
            recipients.extend(additional_recipients)
            recipients = list(set(recipients))  # Remove duplicates

            # Step 2: Generate notification messages for different channels
            # Email notification
            email_subject = self._generate_email_subject(incident, urgency)
            email_body = await self._generate_email_body(incident, urgency)

            # Slack notification
            slack_message = await self._generate_slack_message(incident, urgency)

            # Step 3: Send notifications
            logger.info(f"Sending notifications to {len(recipients)} recipients...")

            # Send email
            email_result = await self._send_notification(
                subject=email_subject,
                message=email_body,
                recipients=recipients,
                priority="high" if urgency == "high" else "normal"
            )

            # Simulate Slack notification
            slack_result = {
                "success": True,
                "channel": "#incident-alerts",
                "message": slack_message
            }

            # Step 4: Create incident report
            incident_report = await self._generate_incident_report(incident)

            # Step 5: Track notification delivery
            notifications_sent = []

            for recipient in recipients:
                notifications_sent.append({
                    "recipient": recipient,
                    "email_sent": True,
                    "slack_sent": True,
                    "timestamp": datetime.now().isoformat()
                })

            logger.info(f"Notifications sent successfully: {len(notifications_sent)} recipients")

            return {
                "success": True,
                "incident_id": incident.get("incident_id"),
                "urgency": urgency,
                "recipients": recipients,
                "notification_count": len(notifications_sent),
                "notifications_sent": notifications_sent,
                "email_subject": email_subject,
                "slack_channel": "#incident-alerts",
                "incident_report": incident_report,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send incident notification: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _execute_auto_remediation(
        self,
        service_name: str,
        incident_type: str,
        remediation_guide: str
    ) -> Dict[str, Any]:
        """
        자동 조치 실행

        Args:
            service_name: 서비스 이름
            incident_type: 장애 유형
            remediation_guide: 조치 가이드

        Returns:
            Dict: 자동 조치 결과
        """
        try:
            logger.info(f"Checking for automated remediation: {service_name}")

            # Step 1: Determine if automated remediation is applicable
            auto_check_prompt = f"""
            다음 장애에 대해 자동화된 조치가 가능한지 판단해주세요:

            서비스: {service_name}
            장애 유형: {incident_type}
            조치 가이드: {remediation_guide}

            자동 조치 가능 여부: Yes/No
            가능한 경우, 실행할 명령: [명령어]
            """

            auto_check = await self._llm_call(auto_check_prompt, temperature=0.2)
            auto_check_content = auto_check.get("content", "")

            is_auto_applicable = "자동 조치 가능 여부: Yes" in auto_check_content

            if not is_auto_applicable:
                return {
                    "executed": False,
                    "reason": "Automated remediation not applicable",
                    "recommendation": "Manual intervention required"
                }

            # Step 2: Execute automated actions (simulation)
            logger.info("Executing automated remediation...")

            # Simulate common auto-remediation actions
            actions_executed = []

            # Example: Restart service
            if "restart" in remediation_guide.lower():
                actions_executed.append({
                    "action": "Service Restart",
                    "status": "Success",
                    "timestamp": datetime.now().isoformat()
                })

            # Example: Clear cache
            if "cache" in remediation_guide.lower():
                actions_executed.append({
                    "action": "Cache Clear",
                    "status": "Success",
                    "timestamp": datetime.now().isoformat()
                })

            # Example: Scale up
            if "scale" in remediation_guide.lower() or "replica" in remediation_guide.lower():
                actions_executed.append({
                    "action": "Scale Up Replicas",
                    "status": "Success",
                    "details": "Scaled from 3 to 5 replicas",
                    "timestamp": datetime.now().isoformat()
                })

            # Wait for actions to complete (simulation)
            await asyncio.sleep(1)

            logger.info(f"Automated remediation completed: {len(actions_executed)} actions")

            return {
                "executed": True,
                "actions_executed": actions_executed,
                "action_count": len(actions_executed),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to execute auto remediation: {str(e)}")
            return {
                "executed": False,
                "error": str(e)
            }

    async def _determine_notification_recipients(
        self,
        incident: Dict[str, Any],
        urgency: str
    ) -> List[str]:
        """
        알림 수신자 결정

        Args:
            incident: 장애 정보
            urgency: 긴급도

        Returns:
            List[str]: 수신자 이메일 목록
        """
        recipients = []

        # Base recipients
        recipients.append("ops-team@company.com")

        # Add based on urgency
        if urgency == "high":
            recipients.extend([
                "ops-manager@company.com",
                "cto@company.com"
            ])

        # Add based on service
        service_name = incident.get("service_name", "")
        if service_name:
            # Search for service owner in contacts
            contact_search = await self._rag_query(
                query=f"{service_name} 담당자",
                collection_types=["contacts"],
                top_k=3
            )

            sources = contact_search.get("sources", [])
            for source in sources:
                email = source.get("metadata", {}).get("email")
                if email:
                    recipients.append(email)

        return recipients

    def _generate_email_subject(self, incident: Dict[str, Any], urgency: str) -> str:
        """이메일 제목 생성"""
        severity = incident.get("severity", "Unknown")
        service_name = incident.get("service_name", "Unknown Service")
        incident_id = incident.get("incident_id", "Unknown")

        prefix = "🚨" if urgency == "high" else "⚠️"

        return f"{prefix} [{severity}] {service_name} Incident - {incident_id}"

    async def _generate_email_body(self, incident: Dict[str, Any], urgency: str) -> str:
        """이메일 본문 생성"""
        email_prompt = f"""
        장애 알림 이메일을 작성해주세요:

        장애 ID: {incident.get('incident_id')}
        서비스: {incident.get('service_name')}
        심각도: {incident.get('severity')}
        발생 시간: {incident.get('detected_at')}

        분석:
        {incident.get('analysis', '')}

        조치 가이드:
        {incident.get('remediation_guide', '')}

        이메일 형식:
        - 상황 요약
        - 영향 범위
        - 조치 사항
        - 담당자 정보
        """

        email = await self._llm_call(email_prompt, temperature=0.4)
        return email.get("content", "")

    async def _generate_slack_message(self, incident: Dict[str, Any], urgency: str) -> str:
        """Slack 메시지 생성"""
        slack_prompt = f"""
        Slack 알림 메시지를 작성해주세요 (간결하게):

        장애 ID: {incident.get('incident_id')}
        서비스: {incident.get('service_name')}
        심각도: {incident.get('severity')}

        분석: {incident.get('analysis', '')[:200]}

        Slack 형식으로 간결하게 작성해주세요.
        """

        slack = await self._llm_call(slack_prompt, temperature=0.4)
        return slack.get("content", "")

    async def _generate_incident_report(self, incident: Dict[str, Any]) -> str:
        """장애 보고서 생성"""
        report_prompt = f"""
        장애 보고서를 작성해주세요:

        {incident}

        보고서 형식:
        1. 개요
        2. 발생 경위
        3. 영향 범위
        4. 조치 내역
        5. 근본 원인 분석
        6. 재발 방지 대책
        """

        report = await self._llm_call(report_prompt, temperature=0.4)
        return report.get("content", "")


# Singleton instance
_sop_agent_instance = None


def get_sop_agent() -> SOPAgent:
    """SOPAgent 싱글톤 인스턴스 반환"""
    global _sop_agent_instance
    if _sop_agent_instance is None:
        _sop_agent_instance = SOPAgent()
    return _sop_agent_instance


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def test_agent():
        print("\n=== Testing SOP Agent ===")
        agent = SOPAgent()

        # Test UC-S-01: Incident detection and response
        print("\n--- Test UC-S-01: Incident Detection and Response ---")
        result = await agent.execute_task({
            "type": "incident_detection_response",
            "data": {
                "service_name": "api-service",
                "monitoring_result": {
                    "cpu_usage": 95,
                    "memory_usage": 88,
                    "error_rate": 12.5,
                    "response_time_ms": 3500
                },
                "severity": "High"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Is Incident: {result.get('is_incident')}")
        if result.get('is_incident'):
            print(f"Incident ID: {result.get('incident', {}).get('incident_id')}")
            print(f"Auto remediation: {result.get('auto_remediation_executed')}")

        # Test UC-S-02: Search similar incidents
        print("\n--- Test UC-S-02: Search Similar Incidents ---")
        result = await agent.execute_task({
            "type": "search_similar_incidents",
            "data": {
                "symptoms": "High CPU usage and slow response time",
                "service_name": "api-service"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Similar incidents found: {result.get('incident_count', 0)}")

        # Test UC-S-03: Incident notification
        print("\n--- Test UC-S-03: Incident Notification ---")
        result = await agent.execute_task({
            "type": "incident_notification",
            "data": {
                "incident": {
                    "incident_id": "INC-20251114123456",
                    "service_name": "api-service",
                    "severity": "High",
                    "analysis": "High CPU usage detected"
                },
                "urgency": "high"
            }
        })
        print(f"Result: {result.get('success')}")
        print(f"Notifications sent: {result.get('notification_count', 0)}")

    asyncio.run(test_agent())
