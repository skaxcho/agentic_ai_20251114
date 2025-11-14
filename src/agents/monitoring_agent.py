"""
Monitoring Agent Module

시스템 모니터링 Agent
- 서비스 Health Check
- DB 접속 및 데이터 검증
- 로그 파일 이상 탐지
- 스케줄 Job 실패 점검
"""

from typing import List, Dict, Any, Optional
from src.core.base.base_agent import BaseAgent
from src.core.tools.monitoring_tools import (
    get_url_health_check_tool,
    get_database_connection_tool,
    get_log_analyzer_tool
)
import logging
from datetime import datetime
import os

# Configure logging
logger = logging.getLogger(__name__)


class MonitoringAgent(BaseAgent):
    """시스템 모니터링 Agent"""

    def __init__(self):
        """Initialize Monitoring Agent"""
        super().__init__(
            name="MonitoringAgent",
            role="시스템 모니터링 전문가",
            goal="시스템의 건강 상태를 지속적으로 모니터링하고 이상을 탐지합니다",
            backstory="""
            당신은 15년 경력의 시스템 모니터링 및 운영 전문가입니다.
            수천 개의 서비스를 관리하며 장애를 사전에 예방하는 데 탁월합니다.
            Health Check, 로그 분석, 데이터베이스 모니터링, 성능 분석 등
            다양한 모니터링 기술에 정통합니다.
            """,
            verbose=True
        )

        # Tools
        self.health_checker = get_url_health_check_tool()
        self.db_checker = get_database_connection_tool()
        self.log_analyzer = get_log_analyzer_tool()

    def get_tools(self) -> List:
        """
        Monitoring Agent의 도구 목록

        Returns:
            List: Tool 리스트
        """
        return []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Task 실행

        Args:
            task: Task 정보
                - task_type: "health_check", "db_check", "log_analysis", "job_check"
                - task_data: 작업별 데이터

        Returns:
            Dict: 실행 결과
        """
        task_type = task.get("task_type")
        task_data = task.get("task_data", {})

        self._log_action(f"Executing task: {task_type}")

        try:
            if task_type == "health_check":
                result = await self._health_check(task_data)
            elif task_type == "db_check":
                result = await self._check_database(task_data)
            elif task_type == "log_analysis":
                result = await self._analyze_logs(task_data)
            elif task_type == "job_check":
                result = await self._check_scheduled_jobs(task_data)
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

    async def _health_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        서비스 Health Check

        Args:
            data: Health check 데이터
                - urls: 확인할 URL 리스트
                - alert_on_failure: 실패 시 알림 여부

        Returns:
            Dict: Health check 결과
        """
        self._log_action("Performing health check")

        urls = data.get("urls", [])
        alert_on_failure = data.get("alert_on_failure", True)

        if not urls:
            raise ValueError("No URLs provided for health check")

        # URL Health Check 수행
        check_result = self.health_checker.check_multiple_urls(urls)

        # 결과 분석
        unhealthy_services = [
            r for r in check_result["results"]
            if not r.get("is_healthy", False)
        ]

        # LLM을 사용하여 결과 분석 및 권장사항 생성
        analysis = await self._analyze_health_check_results(
            check_result,
            unhealthy_services
        )

        # 알림 전송 (실패한 서비스가 있는 경우)
        if unhealthy_services and alert_on_failure:
            await self._send_notification(
                channel="slack",
                message=f"⚠️ Health Check Alert: {len(unhealthy_services)} service(s) unhealthy\n{analysis['summary']}",
                priority="high"
            )

        self._log_action(f"Health check completed: {check_result['health_rate']:.1f}% healthy")

        return {
            "total_services": check_result["total_urls"],
            "healthy_services": check_result["healthy_urls"],
            "unhealthy_services": check_result["unhealthy_urls"],
            "health_rate": check_result["health_rate"],
            "unhealthy_list": unhealthy_services,
            "analysis": analysis,
            "checked_at": datetime.now().isoformat()
        }

    async def _check_database(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        DB 접속 및 데이터 검증

        Args:
            data: DB check 데이터
                - host: DB 호스트
                - port: DB 포트
                - database: 데이터베이스 이름
                - user: 사용자명
                - password: 비밀번호
                - validation_queries: 검증 쿼리 리스트

        Returns:
            Dict: DB check 결과
        """
        self._log_action("Checking database connection and data")

        host = data.get("host", os.getenv("POSTGRES_HOST", "localhost"))
        port = data.get("port", int(os.getenv("POSTGRES_PORT", 5432)))
        database = data.get("database", os.getenv("POSTGRES_DB", "agentic_ai"))
        user = data.get("user", os.getenv("POSTGRES_USER", "admin"))
        password = data.get("password", os.getenv("POSTGRES_PASSWORD", ""))
        validation_queries = data.get("validation_queries", [])

        # 1. DB 연결 확인
        connection_result = self.db_checker.check_postgres(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

        if not connection_result["success"]:
            raise Exception(f"Database connection failed: {connection_result.get('error')}")

        # 2. 데이터 검증 쿼리 실행
        validation_results = []
        for query in validation_queries:
            query_result = self.db_checker.execute_query(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                query=query
            )
            validation_results.append({
                "query": query,
                "success": query_result["success"],
                "result": query_result
            })

        # 3. LLM을 사용하여 DB 상태 분석
        analysis = await self._analyze_database_status(
            connection_result,
            validation_results
        )

        self._log_action("Database check completed successfully")

        return {
            "connection": {
                "status": "connected",
                "connection_time_seconds": connection_result["connection_time_seconds"],
                "version": connection_result["version"],
                "active_connections": connection_result["active_connections"]
            },
            "validation": {
                "total_queries": len(validation_queries),
                "successful_queries": sum(1 for v in validation_results if v["success"]),
                "results": validation_results
            },
            "analysis": analysis,
            "checked_at": datetime.now().isoformat()
        }

    async def _analyze_logs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        로그 파일 이상 탐지

        Args:
            data: 로그 분석 데이터
                - log_files: 로그 파일 경로 리스트
                - error_patterns: 탐지할 에러 패턴
                - alert_threshold: 알림 임계값

        Returns:
            Dict: 로그 분석 결과
        """
        self._log_action("Analyzing log files")

        log_files = data.get("log_files", [])
        error_patterns = data.get("error_patterns")
        alert_threshold = data.get("alert_threshold", 10)

        if not log_files:
            raise ValueError("No log files provided for analysis")

        # 각 로그 파일 분석
        analysis_results = []
        total_errors = 0
        total_warnings = 0

        for log_file in log_files:
            # 로그 분석
            result = self.log_analyzer.analyze_log_file(
                log_file_path=log_file,
                error_patterns=error_patterns
            )

            if result["success"]:
                analysis_results.append(result)
                total_errors += result["error_count"]
                total_warnings += result["warning_count"]

                # 이상 탐지
                anomaly_result = self.log_analyzer.detect_anomalies(log_file)
                if anomaly_result["success"] and anomaly_result["has_anomalies"]:
                    result["anomalies"] = anomaly_result["anomalies"]

        # LLM을 사용하여 로그 분석 결과 해석
        interpretation = await self._interpret_log_analysis(
            analysis_results,
            total_errors,
            total_warnings
        )

        # 알림 (에러가 임계값을 초과한 경우)
        if total_errors > alert_threshold:
            await self._send_notification(
                channel="slack",
                message=f"🔴 Log Alert: {total_errors} errors detected\n{interpretation['summary']}",
                priority="critical"
            )

        self._log_action(f"Log analysis completed: {total_errors} errors, {total_warnings} warnings")

        return {
            "total_files_analyzed": len(analysis_results),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "files": analysis_results,
            "interpretation": interpretation,
            "requires_attention": total_errors > alert_threshold,
            "analyzed_at": datetime.now().isoformat()
        }

    async def _check_scheduled_jobs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        스케줄 Job 실패 점검

        Args:
            data: Job 체크 데이터
                - jobs: Job 정보 리스트

        Returns:
            Dict: Job 체크 결과
        """
        self._log_action("Checking scheduled jobs")

        jobs = data.get("jobs", [])

        if not jobs:
            # DB에서 최근 실행된 작업 조회
            jobs = await self._get_recent_jobs_from_db()

        # Job 상태 분석
        failed_jobs = []
        timeout_jobs = []
        successful_jobs = []

        for job in jobs:
            status = job.get("status", "unknown")

            if status == "failed":
                failed_jobs.append(job)
            elif status == "timeout":
                timeout_jobs.append(job)
            elif status == "completed":
                successful_jobs.append(job)

        # LLM을 사용하여 Job 실패 원인 분석
        if failed_jobs or timeout_jobs:
            analysis = await self._analyze_job_failures(
                failed_jobs,
                timeout_jobs
            )
        else:
            analysis = {
                "summary": "모든 Job이 정상적으로 실행되었습니다.",
                "recommendations": []
            }

        # 알림 (실패한 Job이 있는 경우)
        if failed_jobs:
            await self._send_notification(
                channel="slack",
                message=f"⚠️ Job Failure Alert: {len(failed_jobs)} job(s) failed\n{analysis['summary']}",
                priority="high"
            )

        self._log_action(f"Job check completed: {len(failed_jobs)} failed, {len(successful_jobs)} successful")

        return {
            "total_jobs": len(jobs),
            "successful_jobs": len(successful_jobs),
            "failed_jobs": len(failed_jobs),
            "timeout_jobs": len(timeout_jobs),
            "failed_list": failed_jobs,
            "timeout_list": timeout_jobs,
            "analysis": analysis,
            "checked_at": datetime.now().isoformat()
        }

    async def _analyze_health_check_results(
        self,
        check_result: Dict[str, Any],
        unhealthy_services: List[Dict]
    ) -> Dict[str, str]:
        """
        Health Check 결과 분석

        Args:
            check_result: 전체 체크 결과
            unhealthy_services: 비정상 서비스 리스트

        Returns:
            Dict: 분석 결과
        """
        if not unhealthy_services:
            return {
                "summary": "모든 서비스가 정상 작동 중입니다.",
                "recommendations": []
            }

        # 비정상 서비스 정보 생성
        service_info = "\n".join([
            f"- {s['url']}: {s.get('error', 'Unknown error')}"
            for s in unhealthy_services
        ])

        messages = [
            {
                "role": "system",
                "content": "당신은 시스템 모니터링 전문가입니다. Health Check 결과를 분석하고 조치 방안을 제시하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 서비스들이 비정상 상태입니다:

{service_info}

전체 Health Rate: {check_result['health_rate']:.1f}%

이 상황을 분석하고 다음을 제공해주세요:
1. 문제 요약
2. 가능한 원인
3. 권장 조치사항
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        return {
            "summary": response["content"],
            "recommendations": []  # LLM 응답에서 추출 가능
        }

    async def _analyze_database_status(
        self,
        connection_result: Dict[str, Any],
        validation_results: List[Dict]
    ) -> Dict[str, str]:
        """
        데이터베이스 상태 분석

        Args:
            connection_result: 연결 결과
            validation_results: 검증 쿼리 결과

        Returns:
            Dict: 분석 결과
        """
        failed_validations = [v for v in validation_results if not v["success"]]

        if not failed_validations:
            return {
                "summary": f"데이터베이스 연결 정상. 활성 연결: {connection_result['active_connections']}",
                "recommendations": []
            }

        # 실패한 검증 정보
        validation_info = "\n".join([
            f"- Query: {v['query']}\n  Error: {v['result'].get('error', 'Unknown')}"
            for v in failed_validations
        ])

        messages = [
            {
                "role": "system",
                "content": "당신은 데이터베이스 전문가입니다. 데이터베이스 상태를 분석하고 문제 해결 방안을 제시하세요."
            },
            {
                "role": "user",
                "content": f"""
데이터베이스 검증 중 다음 쿼리들이 실패했습니다:

{validation_info}

DB 버전: {connection_result['version']}
활성 연결: {connection_result['active_connections']}

문제를 분석하고 해결 방안을 제시해주세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        return {
            "summary": response["content"],
            "recommendations": []
        }

    async def _interpret_log_analysis(
        self,
        analysis_results: List[Dict],
        total_errors: int,
        total_warnings: int
    ) -> Dict[str, str]:
        """
        로그 분석 결과 해석

        Args:
            analysis_results: 분석 결과 리스트
            total_errors: 총 에러 수
            total_warnings: 총 경고 수

        Returns:
            Dict: 해석 결과
        """
        # 주요 에러 패턴 추출
        error_patterns = {}
        for result in analysis_results:
            for error in result.get("errors", [])[:10]:  # 최대 10개
                pattern = error.get("pattern", "unknown")
                error_patterns[pattern] = error_patterns.get(pattern, 0) + 1

        pattern_info = "\n".join([
            f"- {pattern}: {count}회"
            for pattern, count in error_patterns.items()
        ])

        messages = [
            {
                "role": "system",
                "content": "당신은 로그 분석 전문가입니다. 로그 패턴을 분석하고 시스템 이슈를 진단하세요."
            },
            {
                "role": "user",
                "content": f"""
로그 분석 결과:
- 총 에러: {total_errors}
- 총 경고: {total_warnings}

주요 에러 패턴:
{pattern_info}

이 로그 패턴이 나타내는 시스템 상태를 분석하고 권장사항을 제시해주세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        return {
            "summary": response["content"],
            "error_patterns": error_patterns
        }

    async def _analyze_job_failures(
        self,
        failed_jobs: List[Dict],
        timeout_jobs: List[Dict]
    ) -> Dict[str, str]:
        """
        Job 실패 원인 분석

        Args:
            failed_jobs: 실패한 Job 리스트
            timeout_jobs: Timeout된 Job 리스트

        Returns:
            Dict: 분석 결과
        """
        job_info = "실패한 Job:\n"
        for job in failed_jobs:
            job_info += f"- {job.get('name', 'Unknown')}: {job.get('error', 'Unknown error')}\n"

        if timeout_jobs:
            job_info += "\nTimeout된 Job:\n"
            for job in timeout_jobs:
                job_info += f"- {job.get('name', 'Unknown')}\n"

        messages = [
            {
                "role": "system",
                "content": "당신은 Job 스케줄링 및 배치 처리 전문가입니다. Job 실패 원인을 분석하고 해결책을 제시하세요."
            },
            {
                "role": "user",
                "content": f"""
다음 Job들이 실패했습니다:

{job_info}

실패 원인을 분석하고 조치 방안을 제시해주세요.
                """
            }
        ]

        response = await self._call_llm_async(messages, temperature=0.3)

        return {
            "summary": response["content"],
            "recommendations": []
        }

    async def _get_recent_jobs_from_db(self) -> List[Dict[str, Any]]:
        """
        DB에서 최근 실행된 작업 조회

        Returns:
            List[Dict]: Job 리스트
        """
        # Simulated job data (실제로는 DB에서 조회)
        return [
            {
                "id": "job-001",
                "name": "daily_backup",
                "status": "completed",
                "started_at": "2024-03-10T02:00:00Z",
                "completed_at": "2024-03-10T02:15:00Z"
            },
            {
                "id": "job-002",
                "name": "data_sync",
                "status": "completed",
                "started_at": "2024-03-10T03:00:00Z",
                "completed_at": "2024-03-10T03:05:00Z"
            }
        ]


# Factory function
def create_monitoring_agent() -> MonitoringAgent:
    """
    MonitoringAgent 인스턴스 생성

    Returns:
        MonitoringAgent: Monitoring Agent 인스턴스
    """
    return MonitoringAgent()


if __name__ == "__main__":
    # Test the agent
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def test_monitoring_agent():
        agent = create_monitoring_agent()

        # Test health check
        print("\n=== Testing Health Check ===")
        task = {
            "task_type": "health_check",
            "task_data": {
                "urls": [
                    "https://www.google.com",
                    "https://httpstat.us/200",
                    "https://httpstat.us/500"  # This will fail
                ],
                "alert_on_failure": False
            }
        }

        result = await agent.execute_with_tracking(task)
        print(f"Result: {result}")

    asyncio.run(test_monitoring_agent())
