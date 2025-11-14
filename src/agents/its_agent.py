"""
ITS (IT Service Management) Agent Module

ITSM Agent
- 구성정보 현행화
- SSL 인증서 발급 요청
- 인시던트 자동 접수
"""

from typing import List, Dict, Any, Optional
from src.core.base.base_agent import BaseAgent
from src.core.tools.servicenow_tools import get_servicenow_tool
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)


class ITSAgent(BaseAgent):
    """IT Service Management Agent"""

    def __init__(self):
        """Initialize ITS Agent"""
        super().__init__(
            name="ITSAgent",
            role="IT 서비스 관리 전문가",
            goal="IT 서비스 요청을 처리하고 구성 정보를 관리합니다",
            backstory="""
            당신은 ITIL 인증을 받은 IT 서비스 관리 전문가입니다.
            10년 이상 ServiceNow를 사용하여 수천 건의 인시던트와 변경 요청을 처리했습니다.
            구성 관리, 인시던트 관리, 변경 관리에 정통하며,
            자동화를 통해 서비스 품질을 향상시키는 데 열정적입니다.
            """,
            verbose=True
        )

        # Tools
        self.servicenow = get_servicenow_tool()

    def get_tools(self) -> List:
        """
        ITS Agent의 도구 목록

        Returns:
            List: Tool 리스트
        """
        return []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Task 실행

        Args:
            task: Task 정보
                - task_type: "update_cmdb", "request_ssl_cert", "create_incident"
                - task_data: 작업별 데이터

        Returns:
            Dict: 실행 결과
        """
        task_type = task.get("task_type")
        task_data = task.get("task_data", {})

        self._log_action(f"Executing task: {task_type}")

        try:
            if task_type == "update_cmdb":
                result = await self._update_configuration(task_data)
            elif task_type == "request_ssl_cert":
                result = await self._request_ssl_certificate(task_data)
            elif task_type == "create_incident":
                result = await self._create_incident(task_data)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            self._log_action(f"Task completed successfully: {task_type}")

            return {
                "success": True,
                "task_type": task_type,
                "result": result
            }

        except Exception as e:
            self._log_action(f"Task failed: {str(e)}", level="error")
            return {
                "success": False,
                "task_type": task_type,
                "error": str(e)
            }

    async def _update_configuration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        구성정보 현행화

        Args:
            data: 구성 정보 데이터
                - ci_name: CI 이름
                - ci_class: CI 클래스
                - changes: 변경 사항
                - discover_mode: 자동 탐지 모드 여부

        Returns:
            Dict: 업데이트 결과
        """
        self._log_action("Updating configuration information")

        ci_name = data.get("ci_name")
        ci_class = data.get("ci_class", "Server")
        changes = data.get("changes", {})
        discover_mode = data.get("discover_mode", False)

        if not ci_name:
            raise ValueError("CI name is required")

        # 자동 탐지 모드인 경우 현재 상태 수집
        if discover_mode:
            discovered_info = await self._discover_ci_information(ci_name, ci_class)
            changes.update(discovered_info)

        # LLM을 사용하여 변경사항 분석 및 검증
        validation = await self._validate_configuration_changes(
            ci_name,
            ci_class,
            changes
        )

        if not validation["is_valid"]:
            raise ValueError(f"Configuration validation failed: {validation['reason']}")

        # CMDB 업데이트
        update_result = self.servicenow.update_cmdb_item(
            ci_name=ci_name,
            ci_class=ci_class,
            attributes=changes
        )

        if not update_result["success"]:
            raise Exception(f"Failed to update CMDB: {update_result.get('error')}")

        # 변경 이력 기록을 위한 인시던트 생성
        incident_result = self.servicenow.create_incident(
            title=f"Configuration Update: {ci_name}",
            description=f"Automated configuration update for {ci_name}\nChanges: {changes}",
            urgency="3",
            impact="3",
            category="Configuration Management"
        )

        self._log_action(f"Configuration updated: {ci_name}")

        return {
            "ci_id": update_result["ci_id"],
            "ci_name": ci_name,
            "ci_class": ci_class,
            "updated_attributes": changes,
            "validation": validation,
            "incident_number": incident_result.get("incident_number"),
            "updated_at": datetime.now().isoformat()
        }

    async def _request_ssl_certificate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        SSL 인증서 발급 요청

        Args:
            data: SSL 인증서 요청 데이터
                - domain: 도메인 이름
                - certificate_type: 인증서 타입 (DV, OV, EV)
                - validity_days: 유효 기간 (일)
                - requester: 요청자

        Returns:
            Dict: 요청 결과
        """
        self._log_action("Requesting SSL certificate")

        domain = data.get("domain")
        certificate_type = data.get("certificate_type", "DV")
        validity_days = data.get("validity_days", 365)
        requester = data.get("requester", "AI Agent")

        if not domain:
            raise ValueError("Domain is required for SSL certificate request")

        # LLM을 사용하여 SSL 인증서 요청 사항 분석
        analysis = await self._analyze_ssl_requirements(
            domain,
            certificate_type,
            validity_days
        )

        # 변경 요청(Change Request) 생성
        description = f"""
SSL 인증서 발급 요청

**도메인**: {domain}
**인증서 타입**: {certificate_type}
**유효 기간**: {validity_days}일
**요청자**: {requester}

**분석 결과**:
{analysis['summary']}

**필요 작업**:
1. DNS 레코드 검증
2. 인증서 발급 요청
3. 인증서 설치 및 테스트
4. 자동 갱신 설정
        """

        change_result = self.servicenow.create_change_request(
            title=f"SSL Certificate Request: {domain}",
            description=description,
            type="Normal",
            risk="Low",
            implementation_plan=analysis.get("implementation_plan", ""),
            backout_plan="Remove certificate and revert to previous configuration"
        )

        if not change_result["success"]:
            raise Exception(f"Failed to create change request: {change_result.get('error')}")

        self._log_action(f"SSL certificate request created: {change_result['change_number']}")

        return {
            "change_number": change_result["change_number"],
            "domain": domain,
            "certificate_type": certificate_type,
            "validity_days": validity_days,
            "analysis": analysis,
            "status": "Requested",
            "requested_at": datetime.now().isoformat()
        }

    async def _create_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        인시던트 자동 접수

        Args:
            data: 인시던트 데이터
                - title: 제목
                - description: 설명
                - source: 출처 (monitoring, user_report, automated)
                - severity: 심각도
                - affected_services: 영향받는 서비스

        Returns:
            Dict: 생성된 인시던트 정보
        """
        self._log_action("Creating incident")

        title = data.get("title")
        description = data.get("description", "")
        source = data.get("source", "automated")
        severity = data.get("severity", "medium")
        affected_services = data.get("affected_services", [])

        if not title:
            raise ValueError("Incident title is required")

        # LLM을 사용하여 인시던트 분류 및 우선순위 결정
        classification = await self._classify_incident(
            title,
            description,
            severity,
            affected_services
        )

        # 유사한 과거 인시던트 검색 (RAG 활용)
        similar_incidents = await self._find_similar_incidents(
            title,
            description
        )

        # 인시던트 생성
        incident_description = f"""
{description}

**출처**: {source}
**영향받는 서비스**: {', '.join(affected_services) if affected_services else 'N/A'}

**AI 분석**:
- 카테고리: {classification['category']}
- 예상 원인: {classification['root_cause']}
- 권장 조치: {classification['recommended_action']}

**유사 인시던트**:
{self._format_similar_incidents(similar_incidents)}
        """

        incident_result = self.servicenow.create_incident(
            title=title,
            description=incident_description,
            urgency=classification["urgency"],
            impact=classification["impact"],
            category=classification["category"],
            assigned_to=classification.get("suggested_assignee")
        )

        if not incident_result["success"]:
            raise Exception(f"Failed to create incident: {incident_result.get('error')}")

        # 긴급한 경우 알림 전송
        if classification["urgency"] == "1" or classification["impact"] == "1":
            await self._send_notification(
                channel="slack",
                message=f"🚨 Critical Incident Created: {incident_result['incident_number']}\n{title}",
                priority="critical"
            )

        self._log_action(f"Incident created: {incident_result['incident_number']}")

        return {
            "incident_number": incident_result["incident_number"],
            "title": title,
            "priority": incident_result["incident"]["priority"],
            "classification": classification,
            "similar_incidents": similar_incidents,
            "created_at": datetime.now().isoformat()
        }

    async def _discover_ci_information(
        self,
        ci_name: str,
        ci_class: str
    ) -> Dict[str, Any]:
        """
        CI 정보 자동 탐지

        Args:
            ci_name: CI 이름
            ci_class: CI 클래스

        Returns:
            Dict: 탐지된 정보
        """
        # Simulated discovery (실제로는 네트워크 스캔, API 호출 등 수행)
        discovered_info = {
            "last_scanned": datetime.now().isoformat(),
            "discovery_method": "automated",
            "status": "Active"
        }

        if ci_class == "Server":
            discovered_info.update({
                "cpu_cores": 8,
                "memory_gb": 32,
                "disk_gb": 500
            })
        elif ci_class == "Application":
            discovered_info.update({
                "version": "1.0.0",
                "framework": "FastAPI"
            })

        return discovered_info

    async def _validate_configuration_changes(
        self,
        ci_name: str,
        ci_class: str,
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        구성 변경사항 검증

        Args:
            ci_name: CI 이름
            ci_class: CI 클래스
            changes: 변경사항

        Returns:
            Dict: 검증 결과
        """
        messages = [
            {
                "role": "system",
                "content": "당신은 CMDB 관리 전문가입니다. 구성 변경사항을 검증하고 잠재적 문제를 식별하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 구성 변경사항을 검증해주세요:

CI Name: {ci_name}
CI Class: {ci_class}
Changes: {changes}

변경사항이 유효한지, 잠재적 문제는 없는지 분석해주세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        return {
            "is_valid": True,  # 실제로는 LLM 응답 파싱
            "reason": response["content"],
            "warnings": []
        }

    async def _analyze_ssl_requirements(
        self,
        domain: str,
        certificate_type: str,
        validity_days: int
    ) -> Dict[str, str]:
        """
        SSL 인증서 요구사항 분석

        Args:
            domain: 도메인
            certificate_type: 인증서 타입
            validity_days: 유효 기간

        Returns:
            Dict: 분석 결과
        """
        messages = [
            {
                "role": "system",
                "content": "당신은 SSL/TLS 인증서 전문가입니다. SSL 인증서 발급 요구사항을 분석하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 SSL 인증서 요청을 분석해주세요:

Domain: {domain}
Certificate Type: {certificate_type}
Validity: {validity_days} days

필요한 검증 절차와 구현 계획을 제시해주세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        return {
            "summary": response["content"],
            "implementation_plan": "1. DNS 검증\n2. 인증서 요청 제출\n3. 인증서 설치\n4. 테스트"
        }

    async def _classify_incident(
        self,
        title: str,
        description: str,
        severity: str,
        affected_services: List[str]
    ) -> Dict[str, str]:
        """
        인시던트 분류 및 우선순위 결정

        Args:
            title: 제목
            description: 설명
            severity: 심각도
            affected_services: 영향받는 서비스

        Returns:
            Dict: 분류 결과
        """
        messages = [
            {
                "role": "system",
                "content": "당신은 ITIL 전문가입니다. 인시던트를 분석하고 분류하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 인시던트를 분류하고 우선순위를 결정해주세요:

Title: {title}
Description: {description}
Severity: {severity}
Affected Services: {', '.join(affected_services)}

다음을 제공해주세요:
1. 카테고리 (Software, Hardware, Network, Performance 등)
2. Urgency (1=High, 2=Medium, 3=Low)
3. Impact (1=High, 2=Medium, 3=Low)
4. 예상 원인
5. 권장 조치사항
6. 담당자 제안
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        # Parse response (간단한 예시)
        return {
            "category": "Software",
            "urgency": "2",
            "impact": "2",
            "root_cause": "분석 중...",
            "recommended_action": response["content"],
            "suggested_assignee": None
        }

    async def _find_similar_incidents(
        self,
        title: str,
        description: str
    ) -> List[Dict[str, Any]]:
        """
        유사한 과거 인시던트 검색 (RAG)

        Args:
            title: 제목
            description: 설명

        Returns:
            List[Dict]: 유사 인시던트 리스트
        """
        # RAG를 사용하여 유사 인시던트 검색
        query = f"{title}\n{description}"

        try:
            results = self.rag_service.semantic_search(
                collection_type="incidents",
                query=query,
                limit=3,
                score_threshold=0.7
            )

            similar_incidents = []
            for result in results:
                similar_incidents.append({
                    "incident_id": result["payload"].get("incident_id"),
                    "title": result["payload"].get("title"),
                    "similarity_score": result["score"],
                    "solution": result["payload"].get("solution", "")[:200]
                })

            return similar_incidents

        except Exception as e:
            self._log_action(f"Failed to search similar incidents: {str(e)}", level="warning")
            return []

    def _format_similar_incidents(
        self,
        similar_incidents: List[Dict[str, Any]]
    ) -> str:
        """
        유사 인시던트를 포맷팅

        Args:
            similar_incidents: 유사 인시던트 리스트

        Returns:
            str: 포맷된 문자열
        """
        if not similar_incidents:
            return "유사한 인시던트가 없습니다."

        formatted = []
        for incident in similar_incidents:
            formatted.append(
                f"- {incident['incident_id']}: {incident['title']} "
                f"(유사도: {incident['similarity_score']:.2f})"
            )

        return "\n".join(formatted)


# Factory function
def create_its_agent() -> ITSAgent:
    """
    ITSAgent 인스턴스 생성

    Returns:
        ITSAgent: ITS Agent 인스턴스
    """
    return ITSAgent()


if __name__ == "__main__":
    # Test the agent
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def test_its_agent():
        agent = create_its_agent()

        # Test create incident
        print("\n=== Testing Create Incident ===")
        task = {
            "task_type": "create_incident",
            "task_data": {
                "title": "Application Server Not Responding",
                "description": "Users cannot access the application. Server appears to be down.",
                "source": "monitoring",
                "severity": "high",
                "affected_services": ["web-app", "api-server"]
            }
        }

        result = await agent.execute_with_tracking(task)
        print(f"Result: {result}")

    asyncio.run(test_its_agent())
