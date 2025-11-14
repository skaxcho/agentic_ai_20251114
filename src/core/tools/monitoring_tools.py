"""
Monitoring Tools Module

모니터링 관련 도구들을 제공합니다.
Health Check, Database 연결, 로그 분석 등
"""

from typing import Dict, Any, List, Optional
import requests
import logging
from datetime import datetime
import re
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class URLHealthCheckTool:
    """URL Health Check 도구"""

    def __init__(self):
        """Initialize URL Health Check Tool"""
        logger.info("URLHealthCheckTool initialized")

    def check_url(
        self,
        url: str,
        timeout: int = 10,
        expected_status: int = 200
    ) -> Dict[str, Any]:
        """
        URL Health Check 수행

        Args:
            url: 확인할 URL
            timeout: 타임아웃 (초)
            expected_status: 기대하는 HTTP 상태 코드

        Returns:
            Dict: Health check 결과
        """
        try:
            start_time = datetime.now()

            response = requests.get(url, timeout=timeout)

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            is_healthy = response.status_code == expected_status

            logger.info(f"Health check: {url} - Status: {response.status_code}, Time: {response_time:.3f}s")

            return {
                "success": True,
                "url": url,
                "status_code": response.status_code,
                "response_time_seconds": response_time,
                "is_healthy": is_healthy,
                "checked_at": start_time.isoformat()
            }

        except requests.exceptions.Timeout:
            logger.error(f"Health check timeout: {url}")
            return {
                "success": False,
                "url": url,
                "error": "Timeout",
                "is_healthy": False
            }

        except requests.exceptions.ConnectionError:
            logger.error(f"Health check connection error: {url}")
            return {
                "success": False,
                "url": url,
                "error": "Connection Error",
                "is_healthy": False
            }

        except Exception as e:
            logger.error(f"Health check failed: {url} - {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "is_healthy": False
            }

    def check_multiple_urls(
        self,
        urls: List[str],
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        여러 URL을 동시에 확인

        Args:
            urls: URL 리스트
            timeout: 타임아웃 (초)

        Returns:
            Dict: 전체 결과
        """
        results = []
        healthy_count = 0
        total_count = len(urls)

        for url in urls:
            result = self.check_url(url, timeout)
            results.append(result)

            if result.get("is_healthy"):
                healthy_count += 1

        logger.info(f"Checked {total_count} URLs: {healthy_count} healthy, {total_count - healthy_count} unhealthy")

        return {
            "total_urls": total_count,
            "healthy_urls": healthy_count,
            "unhealthy_urls": total_count - healthy_count,
            "health_rate": (healthy_count / total_count * 100) if total_count > 0 else 0,
            "results": results
        }


class DatabaseConnectionTool:
    """Database 연결 확인 도구"""

    def __init__(self):
        """Initialize Database Connection Tool"""
        logger.info("DatabaseConnectionTool initialized")

    def check_postgres(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ) -> Dict[str, Any]:
        """
        PostgreSQL 연결 확인

        Args:
            host: DB 호스트
            port: DB 포트
            database: 데이터베이스 이름
            user: 사용자명
            password: 비밀번호

        Returns:
            Dict: 연결 확인 결과
        """
        try:
            import psycopg2

            start_time = datetime.now()

            # Try to connect
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=10
            )

            end_time = datetime.now()
            connection_time = (end_time - start_time).total_seconds()

            # Get database info
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]

            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            active_connections = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            logger.info(f"PostgreSQL connection successful: {host}:{port}/{database}")

            return {
                "success": True,
                "is_healthy": True,
                "connection_time_seconds": connection_time,
                "version": version,
                "active_connections": active_connections,
                "checked_at": start_time.isoformat()
            }

        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {str(e)}")
            return {
                "success": False,
                "is_healthy": False,
                "error": str(e)
            }

    def execute_query(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        query: str
    ) -> Dict[str, Any]:
        """
        쿼리 실행 및 결과 확인

        Args:
            host: DB 호스트
            port: DB 포트
            database: 데이터베이스 이름
            user: 사용자명
            password: 비밀번호
            query: 실행할 쿼리

        Returns:
            Dict: 쿼리 실행 결과
        """
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=10
            )

            cursor = conn.cursor()
            cursor.execute(query)

            # Fetch results if it's a SELECT query
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                cursor.close()
                conn.close()

                logger.info(f"Query executed successfully: {len(results)} rows returned")

                return {
                    "success": True,
                    "columns": columns,
                    "rows": results,
                    "row_count": len(results)
                }
            else:
                conn.commit()
                cursor.close()
                conn.close()

                return {
                    "success": True,
                    "message": "Query executed successfully"
                }

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class LogAnalyzerTool:
    """로그 분석 도구"""

    def __init__(self):
        """Initialize Log Analyzer Tool"""
        self.error_patterns = [
            r"ERROR",
            r"CRITICAL",
            r"Exception",
            r"Traceback",
            r"Failed",
            r"Timeout"
        ]

        logger.info("LogAnalyzerTool initialized")

    def analyze_log_file(
        self,
        log_file_path: str,
        error_patterns: Optional[List[str]] = None,
        max_lines: int = 1000
    ) -> Dict[str, Any]:
        """
        로그 파일 분석

        Args:
            log_file_path: 로그 파일 경로
            error_patterns: 탐지할 에러 패턴 (정규식)
            max_lines: 분석할 최대 라인 수

        Returns:
            Dict: 분석 결과
        """
        try:
            log_path = Path(log_file_path)

            if not log_path.exists():
                return {
                    "success": False,
                    "error": f"Log file not found: {log_file_path}"
                }

            patterns = error_patterns or self.error_patterns

            errors = []
            warnings = []
            total_lines = 0

            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    total_lines += 1

                    if total_lines > max_lines:
                        break

                    # Check for error patterns
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            errors.append({
                                "line_number": total_lines,
                                "content": line.strip(),
                                "pattern": pattern
                            })
                            break

                    # Check for warnings
                    if re.search(r"WARNING|WARN", line, re.IGNORECASE):
                        warnings.append({
                            "line_number": total_lines,
                            "content": line.strip()
                        })

            logger.info(f"Log analysis completed: {total_lines} lines, {len(errors)} errors, {len(warnings)} warnings")

            return {
                "success": True,
                "log_file": log_file_path,
                "total_lines": total_lines,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "errors": errors[:100],  # Limit to first 100
                "warnings": warnings[:100],
                "has_critical_errors": len(errors) > 0
            }

        except Exception as e:
            logger.error(f"Log analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def detect_anomalies(
        self,
        log_file_path: str,
        time_window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        로그에서 이상 패턴 탐지

        Args:
            log_file_path: 로그 파일 경로
            time_window_minutes: 시간 윈도우 (분)

        Returns:
            Dict: 탐지 결과
        """
        try:
            # Simple anomaly detection based on error frequency
            analysis = self.analyze_log_file(log_file_path)

            if not analysis["success"]:
                return analysis

            error_count = analysis["error_count"]
            warning_count = analysis["warning_count"]

            # Thresholds
            error_threshold = 10
            warning_threshold = 50

            anomalies = []

            if error_count > error_threshold:
                anomalies.append({
                    "type": "high_error_rate",
                    "severity": "critical",
                    "message": f"High error rate detected: {error_count} errors"
                })

            if warning_count > warning_threshold:
                anomalies.append({
                    "type": "high_warning_rate",
                    "severity": "warning",
                    "message": f"High warning rate detected: {warning_count} warnings"
                })

            logger.info(f"Anomaly detection completed: {len(anomalies)} anomalies found")

            return {
                "success": True,
                "anomaly_count": len(anomalies),
                "anomalies": anomalies,
                "has_anomalies": len(anomalies) > 0
            }

        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instances
_url_health_check_instance = None
_db_connection_instance = None
_log_analyzer_instance = None


def get_url_health_check_tool() -> URLHealthCheckTool:
    """URLHealthCheckTool 싱글톤 인스턴스 반환"""
    global _url_health_check_instance
    if _url_health_check_instance is None:
        _url_health_check_instance = URLHealthCheckTool()
    return _url_health_check_instance


def get_database_connection_tool() -> DatabaseConnectionTool:
    """DatabaseConnectionTool 싱글톤 인스턴스 반환"""
    global _db_connection_instance
    if _db_connection_instance is None:
        _db_connection_instance = DatabaseConnectionTool()
    return _db_connection_instance


def get_log_analyzer_tool() -> LogAnalyzerTool:
    """LogAnalyzerTool 싱글톤 인스턴스 반환"""
    global _log_analyzer_instance
    if _log_analyzer_instance is None:
        _log_analyzer_instance = LogAnalyzerTool()
    return _log_analyzer_instance


if __name__ == "__main__":
    # Test the tools
    logging.basicConfig(level=logging.INFO)

    # Test URL Health Check
    print("\n=== Testing URL Health Check ===")
    health_checker = URLHealthCheckTool()

    # Test with a public URL
    result = health_checker.check_url("https://www.google.com")
    print(f"Health check result: {result}")

    # Test Database Connection (requires PostgreSQL running)
    print("\n=== Testing Database Connection ===")
    db_checker = DatabaseConnectionTool()
    # Uncomment if PostgreSQL is running
    # result = db_checker.check_postgres(
    #     host="localhost",
    #     port=5432,
    #     database="agentic_ai",
    #     user="admin",
    #     password="secure_password"
    # )
    # print(f"DB connection result: {result}")

    print("\nMonitoring tools ready!")
