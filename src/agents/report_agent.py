"""
Report Agent Module

보고서 자동 작성 Agent
- 주간보고서 자동 작성
- 회의록 자동 생성
- 현황 조사 취합
"""

from typing import List, Dict, Any
from src.core.base.base_agent import BaseAgent
from src.core.tools.file_tools import get_onedrive_tool, get_document_generator
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """보고서 작성 Agent"""

    def __init__(self):
        """Initialize Report Agent"""
        super().__init__(
            name="ReportAgent",
            role="보고서 작성 전문가",
            goal="정확하고 포괄적인 보고서를 자동으로 작성합니다",
            backstory="""
            당신은 10년 경력의 비즈니스 애널리스트이자 기술 문서 전문가입니다.
            데이터를 분석하고 명확하고 간결한 보고서를 작성하는 데 탁월합니다.
            주간 보고서, 회의록, 현황 조사 보고서 등 다양한 형식의 문서를 작성할 수 있습니다.
            """,
            verbose=True
        )

        # Tools
        self.onedrive_tool = get_onedrive_tool()
        self.doc_generator = get_document_generator()

    def get_tools(self) -> List:
        """
        Report Agent의 도구 목록

        Returns:
            List: Tool 리스트
        """
        # Crew AI Tools will be defined here
        # For now, return empty list
        return []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Task 실행

        Args:
            task: Task 정보
                - task_type: "weekly_report", "meeting_minutes", "status_survey"
                - task_data: 작업별 데이터

        Returns:
            Dict: 실행 결과
        """
        task_type = task.get("task_type")
        task_data = task.get("task_data", {})

        self._log_action(f"Executing task: {task_type}")

        try:
            if task_type == "weekly_report":
                result = await self._generate_weekly_report(task_data)
            elif task_type == "meeting_minutes":
                result = await self._generate_meeting_minutes(task_data)
            elif task_type == "status_survey":
                result = await self._generate_status_survey(task_data)
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

    async def _generate_weekly_report(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        주간 보고서 생성

        Args:
            data: 보고서 데이터
                - period: 기간 (예: "2024-03-01 ~ 2024-03-07")
                - achievements: 주요 성과 리스트
                - issues: 이슈사항 리스트
                - next_week_plan: 다음 주 계획

        Returns:
            Dict: 생성된 보고서 정보
        """
        self._log_action("Generating weekly report")

        period = data.get("period", self._get_current_week_period())
        achievements = data.get("achievements", [])
        issues = data.get("issues", [])
        next_week_plan = data.get("next_week_plan", [])

        # LLM을 사용하여 보고서 내용 생성
        sections = await self._create_report_sections(
            period=period,
            achievements=achievements,
            issues=issues,
            next_week_plan=next_week_plan
        )

        # 보고서 파일 생성
        report_title = f"주간 업무 보고서 ({period})"
        result = self.doc_generator.generate_report(
            report_type="weekly",
            title=report_title,
            sections=sections,
            filename=f"weekly_report_{datetime.now().strftime('%Y%m%d')}.md"
        )

        if result["success"]:
            # OneDrive에 업로드 (시뮬레이션)
            upload_result = self.onedrive_tool.upload_file(
                file_path=result["file_path"],
                destination_path=f"reports/weekly/{result['filename']}",
                overwrite=True
            )

            self._log_action(f"Weekly report generated: {result['filename']}")

            return {
                "report_file": result["file_path"],
                "filename": result["filename"],
                "uploaded": upload_result["success"],
                "onedrive_path": upload_result.get("path", "")
            }
        else:
            raise Exception(f"Failed to generate report: {result.get('error')}")

    async def _generate_meeting_minutes(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        회의록 생성

        Args:
            data: 회의 데이터
                - meeting_title: 회의 제목
                - date: 회의 일시
                - attendees: 참석자 리스트
                - agenda: 안건 리스트
                - discussions: 논의 내용 (자유 텍스트 또는 음성 인식 결과)
                - action_items: 액션 아이템 리스트

        Returns:
            Dict: 생성된 회의록 정보
        """
        self._log_action("Generating meeting minutes")

        meeting_title = data.get("meeting_title", "회의")
        meeting_date = data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
        attendees = data.get("attendees", [])
        agenda = data.get("agenda", [])
        discussions = data.get("discussions", "")
        action_items = data.get("action_items", [])

        # LLM을 사용하여 회의록 정리
        formatted_minutes = await self._format_meeting_minutes(
            meeting_title=meeting_title,
            meeting_date=meeting_date,
            attendees=attendees,
            agenda=agenda,
            discussions=discussions,
            action_items=action_items
        )

        # 회의록 파일 생성
        result = self.doc_generator.generate_markdown(
            title=f"{meeting_title} 회의록",
            content=formatted_minutes,
            filename=f"meeting_minutes_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        )

        if result["success"]:
            # OneDrive에 업로드
            upload_result = self.onedrive_tool.upload_file(
                file_path=result["file_path"],
                destination_path=f"meetings/{result['filename']}",
                overwrite=True
            )

            self._log_action(f"Meeting minutes generated: {result['filename']}")

            return {
                "minutes_file": result["file_path"],
                "filename": result["filename"],
                "uploaded": upload_result["success"]
            }
        else:
            raise Exception(f"Failed to generate meeting minutes: {result.get('error')}")

    async def _generate_status_survey(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        현황 조사 보고서 생성

        Args:
            data: 현황 조사 데이터
                - survey_title: 조사 제목
                - systems: 시스템별 현황 데이터
                - analysis: 분석 요구사항

        Returns:
            Dict: 생성된 보고서 정보
        """
        self._log_action("Generating status survey report")

        survey_title = data.get("survey_title", "시스템 현황 조사")
        systems = data.get("systems", [])

        # LLM을 사용하여 현황 분석 및 요약
        analysis_result = await self._analyze_system_status(systems)

        sections = {
            "조사 개요": f"**조사 기간**: {datetime.now().strftime('%Y-%m-%d')}\n**조사 대상**: {len(systems)}개 시스템",
            "시스템별 현황": analysis_result["system_details"],
            "종합 분석": analysis_result["summary"],
            "권장사항": analysis_result["recommendations"]
        }

        # 보고서 생성
        result = self.doc_generator.generate_report(
            report_type="status",
            title=survey_title,
            sections=sections,
            filename=f"status_survey_{datetime.now().strftime('%Y%m%d')}.md"
        )

        if result["success"]:
            # OneDrive에 업로드
            upload_result = self.onedrive_tool.upload_file(
                file_path=result["file_path"],
                destination_path=f"surveys/{result['filename']}",
                overwrite=True
            )

            self._log_action(f"Status survey report generated: {result['filename']}")

            return {
                "report_file": result["file_path"],
                "filename": result["filename"],
                "uploaded": upload_result["success"],
                "systems_analyzed": len(systems)
            }
        else:
            raise Exception(f"Failed to generate status survey: {result.get('error')}")

    async def _create_report_sections(
        self,
        period: str,
        achievements: List[str],
        issues: List[str],
        next_week_plan: List[str]
    ) -> Dict[str, str]:
        """
        LLM을 사용하여 보고서 섹션 생성

        Args:
            period: 보고 기간
            achievements: 성과 리스트
            issues: 이슈 리스트
            next_week_plan: 계획 리스트

        Returns:
            Dict: 섹션별 내용
        """
        # LLM 프롬프트 구성
        messages = [
            {
                "role": "system",
                "content": "당신은 전문적인 보고서 작성 전문가입니다. 주어진 정보를 바탕으로 명확하고 간결한 보고서를 작성하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 정보를 바탕으로 주간 업무 보고서를 작성해주세요.

**보고 기간**: {period}

**주요 성과**:
{chr(10).join(['- ' + a for a in achievements]) if achievements else '- 특이사항 없음'}

**이슈사항**:
{chr(10).join(['- ' + i for i in issues]) if issues else '- 특이사항 없음'}

**다음 주 계획**:
{chr(10).join(['- ' + p for p in next_week_plan]) if next_week_plan else '- 계획 수립 중'}

각 섹션별로 상세하고 전문적인 내용을 작성해주세요.
                """
            }
        ]

        # LLM 호출
        response = await self._call_llm_async(messages)

        # 응답을 섹션으로 분리
        content = response["content"]

        # 간단한 파싱 (실제로는 더 정교한 파싱 필요)
        sections = {
            "1. 보고 기간": period,
            "2. 주요 성과": "\n".join([f"- {a}" for a in achievements]) if achievements else "- 특이사항 없음",
            "3. 이슈 사항": "\n".join([f"- {i}" for i in issues]) if issues else "- 특이사항 없음",
            "4. 다음 주 계획": "\n".join([f"- {p}" for p in next_week_plan]) if next_week_plan else "- 계획 수립 중",
            "5. 종합 의견": content
        }

        return sections

    async def _format_meeting_minutes(
        self,
        meeting_title: str,
        meeting_date: str,
        attendees: List[str],
        agenda: List[str],
        discussions: str,
        action_items: List[str]
    ) -> str:
        """
        LLM을 사용하여 회의록 정리

        Args:
            meeting_title: 회의 제목
            meeting_date: 회의 일시
            attendees: 참석자
            agenda: 안건
            discussions: 논의 내용
            action_items: 액션 아이템

        Returns:
            str: 정리된 회의록
        """
        # LLM 프롬프트
        messages = [
            {
                "role": "system",
                "content": "당신은 회의록 작성 전문가입니다. 회의 내용을 정리하여 명확하고 구조화된 회의록을 작성하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 회의 정보를 바탕으로 전문적인 회의록을 작성해주세요.

**회의 제목**: {meeting_title}
**일시**: {meeting_date}
**참석자**: {', '.join(attendees)}

**안건**:
{chr(10).join(['- ' + a for a in agenda])}

**논의 내용**:
{discussions}

**액션 아이템**:
{chr(10).join(['- ' + ai for ai in action_items])}

회의록은 다음 형식으로 작성해주세요:
- 회의 정보
- 안건별 논의 내용
- 결정 사항
- 액션 아이템 (담당자 및 기한 포함)
                """
            }
        ]

        # LLM 호출
        response = await self._call_llm_async(messages)

        return response["content"]

    async def _analyze_system_status(
        self,
        systems: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        시스템 현황 분석

        Args:
            systems: 시스템 정보 리스트

        Returns:
            Dict: 분석 결과
        """
        # 시스템 정보를 텍스트로 변환
        systems_text = ""
        for system in systems:
            systems_text += f"\n\n**{system.get('name', 'Unknown')}**:\n"
            systems_text += f"- 상태: {system.get('status', 'N/A')}\n"
            systems_text += f"- CPU: {system.get('cpu', 'N/A')}%\n"
            systems_text += f"- 메모리: {system.get('memory', 'N/A')}%\n"
            systems_text += f"- 디스크: {system.get('disk', 'N/A')}%\n"

        # LLM으로 분석
        messages = [
            {
                "role": "system",
                "content": "당신은 시스템 분석 전문가입니다. 시스템 현황 데이터를 분석하고 인사이트를 제공하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 시스템 현황 데이터를 분석하고 종합 의견과 권장사항을 제시해주세요:

{systems_text}
                """
            }
        ]

        response = await self._call_llm_async(messages)

        return {
            "system_details": systems_text,
            "summary": response["content"],
            "recommendations": "시스템 분석 결과를 바탕으로 한 권장사항은 위 분석 내용을 참고하세요."
        }

    def _get_current_week_period(self) -> str:
        """
        현재 주의 기간 반환

        Returns:
            str: 기간 (예: "2024-03-01 ~ 2024-03-07")
        """
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        return f"{start_of_week.strftime('%Y-%m-%d')} ~ {end_of_week.strftime('%Y-%m-%d')}"


# Factory function
def create_report_agent() -> ReportAgent:
    """
    ReportAgent 인스턴스 생성

    Returns:
        ReportAgent: Report Agent 인스턴스
    """
    return ReportAgent()


if __name__ == "__main__":
    # Test the agent
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def test_report_agent():
        agent = create_report_agent()

        # Test weekly report
        print("\n=== Testing Weekly Report ===")
        task = {
            "task_type": "weekly_report",
            "task_data": {
                "period": "2024-03-01 ~ 2024-03-07",
                "achievements": [
                    "Phase 1 Week 1-2 완료 - 공통 모듈 개발",
                    "Phase 1 Week 3-4 완료 - RAG 지식 베이스 구축"
                ],
                "issues": [
                    "Azure OpenAI Rate Limit 관리 필요"
                ],
                "next_week_plan": [
                    "Phase 2 시작 - Agent 개발"
                ]
            }
        }

        result = await agent.execute_with_tracking(task)
        print(f"Result: {result}")

    asyncio.run(test_report_agent())
