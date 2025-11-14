"""
ServiceNow Tools Module

ServiceNow ITSM 통합 도구
- 인시던트 관리
- 변경 요청 관리
- 구성 정보 관리
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import uuid

# Configure logging
logger = logging.getLogger(__name__)


class ServiceNowTool:
    """ServiceNow ITSM 통합 도구"""

    def __init__(self):
        """Initialize ServiceNow Tool"""
        # NOTE: 실제 환경에서는 ServiceNow REST API를 사용
        # 현재는 로컬 시뮬레이션
        self.incidents = {}
        self.change_requests = {}
        self.cmdb_items = {}

        logger.info("ServiceNowTool initialized (simulation mode)")

    def create_incident(
        self,
        title: str,
        description: str,
        urgency: str = "3",  # 1=High, 2=Medium, 3=Low
        impact: str = "3",   # 1=High, 2=Medium, 3=Low
        category: str = "Software",
        assigned_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        인시던트 생성

        Args:
            title: 인시던트 제목
            description: 상세 설명
            urgency: 긴급도 (1-3)
            impact: 영향도 (1-3)
            category: 카테고리
            assigned_to: 담당자

        Returns:
            Dict: 생성된 인시던트 정보
        """
        try:
            # Calculate priority based on urgency and impact
            priority = self._calculate_priority(urgency, impact)

            # Generate incident number
            incident_number = f"INC{str(uuid.uuid4())[:8].upper()}"

            incident = {
                "number": incident_number,
                "title": title,
                "description": description,
                "urgency": urgency,
                "impact": impact,
                "priority": priority,
                "category": category,
                "state": "New",
                "assigned_to": assigned_to,
                "opened_at": datetime.now().isoformat(),
                "opened_by": "AI Agent",
                "updated_at": datetime.now().isoformat()
            }

            # Store incident (simulation)
            self.incidents[incident_number] = incident

            logger.info(f"Incident created: {incident_number}")

            return {
                "success": True,
                "incident_number": incident_number,
                "incident": incident
            }

        except Exception as e:
            logger.error(f"Failed to create incident: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_incident(
        self,
        incident_number: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        인시던트 업데이트

        Args:
            incident_number: 인시던트 번호
            updates: 업데이트할 필드

        Returns:
            Dict: 업데이트 결과
        """
        try:
            if incident_number not in self.incidents:
                return {
                    "success": False,
                    "error": f"Incident not found: {incident_number}"
                }

            # Update incident
            incident = self.incidents[incident_number]
            incident.update(updates)
            incident["updated_at"] = datetime.now().isoformat()

            logger.info(f"Incident updated: {incident_number}")

            return {
                "success": True,
                "incident_number": incident_number,
                "incident": incident
            }

        except Exception as e:
            logger.error(f"Failed to update incident: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_incident(self, incident_number: str) -> Dict[str, Any]:
        """
        인시던트 조회

        Args:
            incident_number: 인시던트 번호

        Returns:
            Dict: 인시던트 정보
        """
        try:
            if incident_number not in self.incidents:
                return {
                    "success": False,
                    "error": f"Incident not found: {incident_number}"
                }

            return {
                "success": True,
                "incident": self.incidents[incident_number]
            }

        except Exception as e:
            logger.error(f"Failed to get incident: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_change_request(
        self,
        title: str,
        description: str,
        type: str = "Normal",  # Standard, Normal, Emergency
        risk: str = "Moderate",
        implementation_plan: str = "",
        backout_plan: str = "",
        scheduled_start: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        변경 요청 생성

        Args:
            title: 변경 제목
            description: 상세 설명
            type: 변경 유형
            risk: 위험도
            implementation_plan: 구현 계획
            backout_plan: 백아웃 계획
            scheduled_start: 예정 시작 시간

        Returns:
            Dict: 생성된 변경 요청 정보
        """
        try:
            # Generate change request number
            change_number = f"CHG{str(uuid.uuid4())[:8].upper()}"

            change_request = {
                "number": change_number,
                "title": title,
                "description": description,
                "type": type,
                "risk": risk,
                "state": "Draft",
                "implementation_plan": implementation_plan,
                "backout_plan": backout_plan,
                "scheduled_start": scheduled_start,
                "requested_by": "AI Agent",
                "opened_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Store change request (simulation)
            self.change_requests[change_number] = change_request

            logger.info(f"Change request created: {change_number}")

            return {
                "success": True,
                "change_number": change_number,
                "change_request": change_request
            }

        except Exception as e:
            logger.error(f"Failed to create change request: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_cmdb_item(
        self,
        ci_name: str,
        ci_class: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        CMDB(Configuration Management Database) 아이템 업데이트

        Args:
            ci_name: CI(Configuration Item) 이름
            ci_class: CI 클래스 (Server, Application, Database 등)
            attributes: CI 속성

        Returns:
            Dict: 업데이트 결과
        """
        try:
            ci_id = f"{ci_class}_{ci_name}".replace(" ", "_")

            cmdb_item = {
                "id": ci_id,
                "name": ci_name,
                "class": ci_class,
                "attributes": attributes,
                "updated_at": datetime.now().isoformat(),
                "updated_by": "AI Agent"
            }

            # Store/Update CMDB item (simulation)
            self.cmdb_items[ci_id] = cmdb_item

            logger.info(f"CMDB item updated: {ci_id}")

            return {
                "success": True,
                "ci_id": ci_id,
                "cmdb_item": cmdb_item
            }

        except Exception as e:
            logger.error(f"Failed to update CMDB item: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_cmdb_item(self, ci_id: str) -> Dict[str, Any]:
        """
        CMDB 아이템 조회

        Args:
            ci_id: CI ID

        Returns:
            Dict: CMDB 아이템 정보
        """
        try:
            if ci_id not in self.cmdb_items:
                return {
                    "success": False,
                    "error": f"CMDB item not found: {ci_id}"
                }

            return {
                "success": True,
                "cmdb_item": self.cmdb_items[ci_id]
            }

        except Exception as e:
            logger.error(f"Failed to get CMDB item: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_incidents(
        self,
        state: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        인시던트 목록 조회

        Args:
            state: 상태 필터
            assigned_to: 담당자 필터
            limit: 최대 결과 수

        Returns:
            Dict: 인시던트 목록
        """
        try:
            incidents = list(self.incidents.values())

            # Apply filters
            if state:
                incidents = [i for i in incidents if i["state"] == state]

            if assigned_to:
                incidents = [i for i in incidents if i.get("assigned_to") == assigned_to]

            # Limit results
            incidents = incidents[:limit]

            logger.info(f"Listed {len(incidents)} incidents")

            return {
                "success": True,
                "count": len(incidents),
                "incidents": incidents
            }

        except Exception as e:
            logger.error(f"Failed to list incidents: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _calculate_priority(self, urgency: str, impact: str) -> str:
        """
        긴급도와 영향도로 우선순위 계산

        Args:
            urgency: 긴급도 (1-3)
            impact: 영향도 (1-3)

        Returns:
            str: 우선순위 (1-5)
        """
        # Priority matrix
        matrix = {
            ("1", "1"): "1",  # Critical
            ("1", "2"): "2",  # High
            ("1", "3"): "3",  # Medium
            ("2", "1"): "2",  # High
            ("2", "2"): "3",  # Medium
            ("2", "3"): "4",  # Low
            ("3", "1"): "3",  # Medium
            ("3", "2"): "4",  # Low
            ("3", "3"): "5",  # Planning
        }

        return matrix.get((urgency, impact), "3")


# Singleton instance
_servicenow_tool_instance = None


def get_servicenow_tool() -> ServiceNowTool:
    """ServiceNowTool 싱글톤 인스턴스 반환"""
    global _servicenow_tool_instance
    if _servicenow_tool_instance is None:
        _servicenow_tool_instance = ServiceNowTool()
    return _servicenow_tool_instance


if __name__ == "__main__":
    # Test the tool
    logging.basicConfig(level=logging.INFO)

    print("\n=== Testing ServiceNow Tool ===")
    snow_tool = ServiceNowTool()

    # Create incident
    result = snow_tool.create_incident(
        title="Application Performance Degradation",
        description="Users reporting slow response times",
        urgency="2",
        impact="2",
        category="Performance"
    )
    print(f"Create incident: {result}")

    # Create change request
    result = snow_tool.create_change_request(
        title="Deploy Performance Optimization",
        description="Deploy code changes to improve performance",
        type="Normal",
        risk="Moderate",
        implementation_plan="Deploy to production during maintenance window",
        backout_plan="Rollback to previous version"
    )
    print(f"Create change request: {result}")

    # Update CMDB
    result = snow_tool.update_cmdb_item(
        ci_name="app-server-01",
        ci_class="Server",
        attributes={
            "ip_address": "10.0.1.10",
            "os": "Ubuntu 22.04",
            "status": "Production"
        }
    )
    print(f"Update CMDB: {result}")
