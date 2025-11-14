"""
Load Testing with Locust

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random
import json


class AgenticAIUser(HttpUser):
    """
    Simulated user for load testing
    """

    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    agent_types = [
        "report", "monitoring", "its", "db_extract",
        "change_mgmt", "biz_support", "sop", "infra"
    ]

    task_types_by_agent = {
        "report": ["generate_weekly_report", "generate_meeting_minutes"],
        "monitoring": ["health_check", "database_check"],
        "its": ["create_incident", "update_configuration"],
        "db_extract": ["natural_language_query", "data_validation"],
        "change_mgmt": ["performance_deployment", "emergency_patch"],
        "biz_support": ["usage_question", "find_contact"],
        "sop": ["incident_detection", "similar_incidents"],
        "infra": ["performance_analysis", "auto_scaling"]
    }

    def on_start(self):
        """Called when a user starts"""
        self.user_id = f"load_test_user_{random.randint(1, 1000)}"

    @task(3)
    def list_agents(self):
        """List all available agents"""
        self.client.get("/api/agents/list")

    @task(2)
    def get_dashboard(self):
        """Get dashboard data"""
        self.client.get("/api/monitoring/dashboard")

    @task(1)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/api/monitoring/health")

    @task(5)
    def execute_agent_task(self):
        """Execute a task on a random agent"""
        agent_type = random.choice(self.agent_types)
        task_type = random.choice(self.task_types_by_agent[agent_type])

        payload = {
            "agent_type": agent_type,
            "task_type": task_type,
            "task_data": self._generate_task_data(agent_type, task_type),
            "user_id": self.user_id
        }

        with self.client.post(
            "/api/agents/execute",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    response.success()
                else:
                    response.failure(f"Task failed: {result.get('error')}")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(2)
    def list_tasks(self):
        """List tasks"""
        params = {
            "limit": 20,
            "offset": 0
        }
        self.client.get("/api/tasks/", params=params)

    @task(1)
    def get_task_statistics(self):
        """Get task statistics"""
        self.client.get("/api/tasks/stats/summary")

    @task(1)
    def get_agent_status(self):
        """Get status of a random agent"""
        agent_type = random.choice(self.agent_types)
        self.client.get(f"/api/agents/{agent_type}/status")

    @task(1)
    def get_metrics(self):
        """Get system metrics"""
        self.client.get("/api/monitoring/metrics")

    def _generate_task_data(self, agent_type: str, task_type: str) -> dict:
        """Generate sample task data based on agent and task type"""

        if agent_type == "report":
            return {
                "report_type": task_type,
                "period": "weekly",
                "include_charts": True
            }

        elif agent_type == "monitoring":
            return {
                "target": random.choice(["OrderManagement", "InventorySystem", "PaymentGateway"]),
                "check_type": task_type
            }

        elif agent_type == "its":
            return {
                "title": f"Sample {task_type}",
                "description": "Load test generated task",
                "priority": random.choice(["low", "medium", "high"])
            }

        elif agent_type == "db_extract":
            return {
                "query": "Get total sales for last month",
                "database": "production"
            }

        elif agent_type == "change_mgmt":
            return {
                "deployment_type": task_type,
                "target_env": "staging",
                "rollback_enabled": True
            }

        elif agent_type == "biz_support":
            return {
                "question": "How do I reset my password?",
                "user_info": {"email": f"{self.user_id}@example.com"}
            }

        elif agent_type == "sop":
            return {
                "incident_type": "high_cpu_usage",
                "severity": random.choice(["low", "medium", "high", "critical"])
            }

        elif agent_type == "infra":
            return {
                "operation": task_type,
                "target": random.choice(["web-server", "api-server", "database"])
            }

        return {}


class AdminUser(HttpUser):
    """
    Admin user with different behavior
    """

    wait_time = between(5, 15)
    weight = 1  # Fewer admin users compared to regular users

    @task
    def view_all_statistics(self):
        """View comprehensive statistics"""
        self.client.get("/api/tasks/stats/summary")
        self.client.get("/api/monitoring/dashboard")
        self.client.get("/api/monitoring/metrics")
