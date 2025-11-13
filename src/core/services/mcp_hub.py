"""
MCP (Model Context Protocol) Hub Module

이 모듈은 MCP 서버들과의 통합을 제공합니다.
여러 MCP 서버(ServiceNow, Database, Cloud 등)를 관리하고 도구를 호출합니다.
"""

from typing import Dict, Any, List, Optional
import requests
import os
from dotenv import load_dotenv
import logging
from tenacity import retry, wait_exponential, stop_after_attempt

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class MCPHub:
    """MCP 서버 통합 허브"""

    def __init__(self):
        """Initialize MCP Hub"""
        # MCP 서버 URL 설정
        self.mcp_servers = {
            "database": os.getenv("MCP_DATABASE_SERVER_URL", "http://localhost:5000"),
            "servicenow": os.getenv("MCP_SERVICENOW_SERVER_URL", "http://localhost:5001"),
            "cloud": os.getenv("MCP_CLOUD_SERVER_URL", "http://localhost:5002")
        }

        # 등록된 도구 캐시
        self._tools_cache: Dict[str, List[str]] = {}

        logger.info(f"MCPHub initialized with {len(self.mcp_servers)} MCP servers")

    def register_mcp_server(
        self,
        server_name: str,
        server_url: str
    ) -> bool:
        """
        새로운 MCP 서버 등록

        Args:
            server_name: 서버 이름
            server_url: 서버 URL

        Returns:
            bool: 등록 성공 여부
        """
        try:
            self.mcp_servers[server_name] = server_url
            # Clear tools cache for this server
            if server_name in self._tools_cache:
                del self._tools_cache[server_name]

            logger.info(f"MCP server '{server_name}' registered at {server_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to register MCP server '{server_name}': {str(e)}")
            return False

    def unregister_mcp_server(self, server_name: str) -> bool:
        """
        MCP 서버 등록 해제

        Args:
            server_name: 서버 이름

        Returns:
            bool: 해제 성공 여부
        """
        try:
            if server_name in self.mcp_servers:
                del self.mcp_servers[server_name]
                if server_name in self._tools_cache:
                    del self._tools_cache[server_name]

                logger.info(f"MCP server '{server_name}' unregistered")
                return True
            else:
                logger.warning(f"MCP server '{server_name}' not found")
                return False

        except Exception as e:
            logger.error(f"Failed to unregister MCP server '{server_name}': {str(e)}")
            return False

    @retry(
        wait=wait_exponential(min=1, max=10),
        stop=stop_after_attempt(3)
    )
    def call_tool(
        self,
        server_name: str,
        tool_name: str,
        timeout: int = 30,
        **kwargs
    ) -> Any:
        """
        MCP 도구 호출

        Args:
            server_name: MCP 서버 이름 ("database", "servicenow", "cloud")
            tool_name: 도구 이름
            timeout: 타임아웃 (초)
            **kwargs: 도구 파라미터

        Returns:
            Any: 도구 실행 결과

        Raises:
            ValueError: 서버를 찾을 수 없는 경우
            Exception: 도구 호출 실패 시
        """
        server_url = self.mcp_servers.get(server_name)
        if not server_url:
            raise ValueError(f"Unknown MCP server: {server_name}")

        url = f"{server_url}/tools/{tool_name}"

        try:
            logger.debug(f"Calling MCP tool '{tool_name}' on server '{server_name}'")

            response = requests.post(
                url,
                json=kwargs,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )

            response.raise_for_status()

            result = response.json()

            logger.info(f"MCP tool '{tool_name}' executed successfully")

            return result

        except requests.exceptions.Timeout:
            logger.error(f"MCP tool call timed out after {timeout} seconds")
            raise Exception(f"MCP tool call timeout: {tool_name}")

        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to MCP server '{server_name}' at {server_url}")
            raise Exception(f"MCP server connection failed: {server_name}")

        except requests.exceptions.HTTPError as e:
            logger.error(f"MCP tool call failed with HTTP error: {str(e)}")
            raise Exception(f"MCP tool call failed: {str(e)}")

        except Exception as e:
            logger.error(f"MCP tool call failed: {str(e)}")
            raise Exception(f"MCP tool call 실패: {str(e)}")

    def list_tools(self, server_name: str, use_cache: bool = True) -> List[str]:
        """
        MCP 서버의 도구 목록 조회

        Args:
            server_name: MCP 서버 이름
            use_cache: 캐시 사용 여부

        Returns:
            List[str]: 도구 이름 리스트

        Raises:
            ValueError: 서버를 찾을 수 없는 경우
            Exception: 목록 조회 실패 시
        """
        # Check cache
        if use_cache and server_name in self._tools_cache:
            logger.debug(f"Returning cached tools for server '{server_name}'")
            return self._tools_cache[server_name]

        server_url = self.mcp_servers.get(server_name)
        if not server_url:
            raise ValueError(f"Unknown MCP server: {server_name}")

        url = f"{server_url}/tools"

        try:
            logger.debug(f"Fetching tool list from server '{server_name}'")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            tools = data.get("tools", [])

            # Cache the result
            self._tools_cache[server_name] = tools

            logger.info(f"Found {len(tools)} tools on server '{server_name}'")

            return tools

        except Exception as e:
            logger.error(f"Failed to list tools from server '{server_name}': {str(e)}")
            raise Exception(f"도구 목록 조회 실패: {str(e)}")

    def list_all_tools(self) -> Dict[str, List[str]]:
        """
        모든 MCP 서버의 도구 목록 조회

        Returns:
            Dict[str, List[str]]: 서버별 도구 목록
        """
        all_tools = {}

        for server_name in self.mcp_servers.keys():
            try:
                tools = self.list_tools(server_name)
                all_tools[server_name] = tools
            except Exception as e:
                logger.warning(f"Failed to list tools from '{server_name}': {str(e)}")
                all_tools[server_name] = []

        return all_tools

    def health_check(self, server_name: Optional[str] = None) -> Dict[str, bool]:
        """
        MCP 서버 헬스 체크

        Args:
            server_name: 특정 서버 이름 (None이면 모든 서버)

        Returns:
            Dict[str, bool]: 서버별 상태
        """
        results = {}

        servers_to_check = [server_name] if server_name else list(self.mcp_servers.keys())

        for name in servers_to_check:
            server_url = self.mcp_servers.get(name)
            if not server_url:
                results[name] = False
                continue

            try:
                response = requests.get(f"{server_url}/health", timeout=5)
                results[name] = response.status_code == 200
            except Exception:
                results[name] = False

        logger.info(f"Health check results: {results}")

        return results

    def get_tool_schema(
        self,
        server_name: str,
        tool_name: str
    ) -> Dict[str, Any]:
        """
        도구의 스키마 조회

        Args:
            server_name: MCP 서버 이름
            tool_name: 도구 이름

        Returns:
            Dict: 도구 스키마

        Raises:
            ValueError: 서버를 찾을 수 없는 경우
            Exception: 스키마 조회 실패 시
        """
        server_url = self.mcp_servers.get(server_name)
        if not server_url:
            raise ValueError(f"Unknown MCP server: {server_name}")

        url = f"{server_url}/tools/{tool_name}/schema"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            schema = response.json()

            logger.info(f"Retrieved schema for tool '{tool_name}'")

            return schema

        except Exception as e:
            logger.error(f"Failed to get tool schema: {str(e)}")
            raise Exception(f"도구 스키마 조회 실패: {str(e)}")

    def call_batch_tools(
        self,
        tool_calls: List[Dict[str, Any]],
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        여러 도구를 일괄 호출

        Args:
            tool_calls: 도구 호출 리스트
                [
                    {
                        "server_name": "database",
                        "tool_name": "execute_query",
                        "params": {...}
                    },
                    ...
                ]
            timeout: 각 호출의 타임아웃

        Returns:
            List[Dict]: 결과 리스트
                [
                    {
                        "success": True/False,
                        "result": ... or "error": ...
                    },
                    ...
                ]
        """
        results = []

        for call in tool_calls:
            server_name = call.get("server_name")
            tool_name = call.get("tool_name")
            params = call.get("params", {})

            try:
                result = self.call_tool(
                    server_name=server_name,
                    tool_name=tool_name,
                    timeout=timeout,
                    **params
                )

                results.append({
                    "success": True,
                    "server_name": server_name,
                    "tool_name": tool_name,
                    "result": result
                })

            except Exception as e:
                logger.error(f"Batch tool call failed for '{tool_name}': {str(e)}")
                results.append({
                    "success": False,
                    "server_name": server_name,
                    "tool_name": tool_name,
                    "error": str(e)
                })

        logger.info(f"Batch tool execution: {len(results)} calls completed")

        return results

    def get_servers_status(self) -> Dict[str, Any]:
        """
        모든 MCP 서버의 상태 조회

        Returns:
            Dict: 서버 상태 정보
        """
        health = self.health_check()
        all_tools = {}

        for server_name in self.mcp_servers.keys():
            try:
                tools = self.list_tools(server_name)
                all_tools[server_name] = len(tools)
            except Exception:
                all_tools[server_name] = 0

        return {
            "total_servers": len(self.mcp_servers),
            "healthy_servers": sum(1 for v in health.values() if v),
            "health": health,
            "tool_counts": all_tools
        }


# Singleton instance
_mcp_hub_instance = None


def get_mcp_hub() -> MCPHub:
    """
    MCPHub 싱글톤 인스턴스 반환

    Returns:
        MCPHub: MCP Hub 인스턴스
    """
    global _mcp_hub_instance
    if _mcp_hub_instance is None:
        _mcp_hub_instance = MCPHub()
    return _mcp_hub_instance


if __name__ == "__main__":
    # Test the service
    logging.basicConfig(level=logging.INFO)

    try:
        mcp_hub = MCPHub()

        # Test health check
        print("\n=== Testing Health Check ===")
        health = mcp_hub.health_check()
        print(f"Health status: {health}")

        # Test server status
        print("\n=== Testing Server Status ===")
        status = mcp_hub.get_servers_status()
        print(f"Server status: {status}")

        # Test custom server registration
        print("\n=== Testing Server Registration ===")
        mcp_hub.register_mcp_server("custom_server", "http://localhost:5003")
        print(f"Registered servers: {list(mcp_hub.mcp_servers.keys())}")

        # NOTE: Actual tool calls will fail if MCP servers are not running
        # This is expected behavior for testing

    except Exception as e:
        print(f"Error: {str(e)}")
