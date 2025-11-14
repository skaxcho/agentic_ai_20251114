"""
API Integration Tests

Tests all API endpoints for correct functionality
"""

import pytest
import asyncio
from httpx import AsyncClient
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.api.main import app


@pytest.mark.asyncio
class TestAgentEndpoints:
    """Test Agent API endpoints"""

    async def test_list_agents(self):
        """Test GET /api/agents/list"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/agents/list")

            assert response.status_code == 200
            agents = response.json()
            assert isinstance(agents, list)
            assert len(agents) == 8  # Should have 8 agents

            # Check agent structure
            for agent in agents:
                assert "type" in agent
                assert "name" in agent
                assert "role" in agent
                assert "status" in agent

    async def test_execute_agent_task(self):
        """Test POST /api/agents/execute"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "agent_type": "monitoring",
                "task_type": "health_check",
                "task_data": {
                    "target": "OrderManagement",
                    "check_type": "health_check"
                },
                "user_id": "test_user"
            }

            response = await client.post("/api/agents/execute", json=payload)

            assert response.status_code == 200
            result = response.json()
            assert "success" in result
            assert "task_id" in result
            assert "agent_type" in result
            assert result["agent_type"] == "monitoring"

    async def test_get_agent_status(self):
        """Test GET /api/agents/{agent_name}/status"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/agents/monitoring/status")

            assert response.status_code == 200
            status = response.json()
            assert "agent_type" in status
            assert "name" in status
            assert "role" in status
            assert "statistics" in status

    async def test_invalid_agent_type(self):
        """Test with invalid agent type"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/agents/invalid_agent/status")

            assert response.status_code == 404


@pytest.mark.asyncio
class TestTaskEndpoints:
    """Test Task API endpoints"""

    async def test_create_task(self):
        """Test POST /api/tasks/create"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "task_type": "health_check",
                "agent_type": "monitoring",
                "task_data": {"target": "TestSystem"},
                "user_id": "test_user"
            }

            response = await client.post("/api/tasks/create", json=payload)

            assert response.status_code == 200
            task = response.json()
            assert "id" in task
            assert "status" in task
            assert task["status"] == "pending"

    async def test_list_tasks(self):
        """Test GET /api/tasks/"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/tasks/")

            assert response.status_code == 200
            result = response.json()
            assert "total" in result
            assert "tasks" in result
            assert isinstance(result["tasks"], list)

    async def test_get_task_statistics(self):
        """Test GET /api/tasks/stats/summary"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/tasks/stats/summary")

            assert response.status_code == 200
            stats = response.json()
            assert "total_tasks" in stats
            assert "completed_tasks" in stats
            assert "failed_tasks" in stats
            assert "success_rate" in stats


@pytest.mark.asyncio
class TestWorkflowEndpoints:
    """Test Workflow API endpoints"""

    async def test_execute_workflow(self):
        """Test POST /api/workflows/execute"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "workflow": [
                    {
                        "agent_type": "monitoring",
                        "task": {
                            "type": "health_check",
                            "data": {"target": "OrderManagement"}
                        }
                    },
                    {
                        "agent_type": "report",
                        "task": {
                            "type": "system_status_report",
                            "data": {"system": "OrderManagement"}
                        }
                    }
                ],
                "mode": "sequential",
                "user_id": "test_user"
            }

            response = await client.post("/api/workflows/execute", json=payload)

            assert response.status_code == 200
            result = response.json()
            assert "success" in result
            assert "workflow_id" in result
            assert "results" in result


@pytest.mark.asyncio
class TestMonitoringEndpoints:
    """Test Monitoring API endpoints"""

    async def test_health_check(self):
        """Test GET /api/monitoring/health"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/monitoring/health")

            assert response.status_code == 200
            health = response.json()
            assert "status" in health
            assert health["status"] in ["healthy", "unhealthy"]

    async def test_get_metrics(self):
        """Test GET /api/monitoring/metrics"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/monitoring/metrics")

            assert response.status_code == 200
            metrics = response.json()
            assert "system" in metrics
            assert "tasks" in metrics
            assert "agents" in metrics

    async def test_get_dashboard_data(self):
        """Test GET /api/monitoring/dashboard"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/monitoring/dashboard")

            assert response.status_code == 200
            dashboard = response.json()
            assert "overview" in dashboard
            assert "task_statistics" in dashboard
            assert "system_resources" in dashboard


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
