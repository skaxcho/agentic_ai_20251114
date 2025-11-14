"""
Test Data Generator

Generates sample data for testing the Agentic AI system
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import asyncio


class TestDataGenerator:
    """Generate test data for validation"""

    def __init__(self):
        self.system_names = ["OrderManagement", "InventorySystem", "PaymentGateway", "CRM"]
        self.agent_types = [
            "report", "monitoring", "its", "db_extract",
            "change_mgmt", "biz_support", "sop", "infra"
        ]
        self.statuses = ["pending", "running", "completed", "failed"]

    def generate_orders(self, count: int = 1000) -> List[Dict]:
        """Generate sample order data"""
        orders = []
        start_date = datetime.now() - timedelta(days=90)

        for i in range(count):
            order_date = start_date + timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            order = {
                "order_id": f"ORD-{i+1:06d}",
                "customer_id": f"CUST-{random.randint(1, 100):04d}",
                "order_date": order_date.isoformat(),
                "total_amount": round(random.uniform(10.0, 1000.0), 2),
                "status": random.choice(["pending", "processing", "shipped", "delivered", "cancelled"]),
                "items": random.randint(1, 5),
                "payment_method": random.choice(["credit_card", "paypal", "bank_transfer"]),
                "shipping_country": random.choice(["US", "UK", "CA", "AU", "DE"])
            }
            orders.append(order)

        return orders

    def generate_log_entries(self, count: int = 5000) -> List[Dict]:
        """Generate sample log data"""
        logs = []
        start_time = datetime.now() - timedelta(hours=24)

        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        components = ["API", "Database", "Cache", "Queue", "Worker"]

        for i in range(count):
            log_time = start_time + timedelta(seconds=random.randint(0, 86400))

            level = random.choice(log_levels)
            component = random.choice(components)

            # Generate realistic log messages
            if level == "ERROR":
                message = f"{component}: Connection timeout after 30 seconds"
            elif level == "WARNING":
                message = f"{component}: High memory usage detected (85%)"
            else:
                message = f"{component}: Operation completed successfully"

            log = {
                "timestamp": log_time.isoformat(),
                "level": level,
                "component": component,
                "message": message,
                "system": random.choice(self.system_names)
            }
            logs.append(log)

        return logs

    def generate_performance_metrics(self, count: int = 1000) -> List[Dict]:
        """Generate sample performance metrics"""
        metrics = []
        start_time = datetime.now() - timedelta(hours=24)

        for i in range(count):
            metric_time = start_time + timedelta(seconds=random.randint(0, 86400))

            metric = {
                "timestamp": metric_time.isoformat(),
                "system": random.choice(self.system_names),
                "cpu_usage": round(random.uniform(10.0, 90.0), 2),
                "memory_usage": round(random.uniform(30.0, 85.0), 2),
                "disk_usage": round(random.uniform(40.0, 80.0), 2),
                "network_in_mbps": round(random.uniform(0.5, 100.0), 2),
                "network_out_mbps": round(random.uniform(0.5, 100.0), 2),
                "response_time_ms": round(random.uniform(50.0, 2000.0), 2),
                "requests_per_sec": random.randint(10, 500)
            }
            metrics.append(metric)

        return metrics

    def generate_tasks(self, count: int = 100) -> List[Dict]:
        """Generate sample task data"""
        tasks = []
        start_time = datetime.now() - timedelta(days=7)

        task_types_by_agent = {
            "report": ["generate_weekly_report", "generate_meeting_minutes", "system_status_report"],
            "monitoring": ["health_check", "database_check", "log_analysis", "schedule_check"],
            "its": ["create_incident", "update_configuration", "ssl_certificate"],
            "db_extract": ["natural_language_query", "data_validation", "complex_statistics"],
            "change_mgmt": ["performance_deployment", "emergency_patch", "regular_change"],
            "biz_support": ["usage_question", "find_contact", "account_request"],
            "sop": ["incident_detection", "similar_incidents", "auto_remediation"],
            "infra": ["performance_analysis", "auto_scaling", "automated_patching"]
        }

        for i in range(count):
            agent_type = random.choice(self.agent_types)
            task_type = random.choice(task_types_by_agent[agent_type])

            created_at = start_time + timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23)
            )

            status = random.choice(self.statuses)
            duration = random.randint(1, 300) if status in ["completed", "failed"] else None

            task = {
                "task_id": f"TASK-{i+1:06d}",
                "agent_type": agent_type,
                "task_type": task_type,
                "status": status,
                "created_at": created_at.isoformat(),
                "duration_seconds": duration,
                "user_id": f"user-{random.randint(1, 20)}",
                "success": status == "completed"
            }

            if status == "completed":
                task["completed_at"] = (created_at + timedelta(seconds=duration)).isoformat()

            tasks.append(task)

        return tasks

    def save_test_data(self, output_dir: str = "./test-data"):
        """Save all test data to files"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # Generate data
        print("Generating test data...")

        orders = self.generate_orders(1000)
        logs = self.generate_log_entries(5000)
        metrics = self.generate_performance_metrics(1000)
        tasks = self.generate_tasks(100)

        # Save to files
        print(f"Saving {len(orders)} orders...")
        with open(f"{output_dir}/orders.json", "w") as f:
            json.dump(orders, f, indent=2)

        print(f"Saving {len(logs)} log entries...")
        with open(f"{output_dir}/logs.json", "w") as f:
            json.dump(logs, f, indent=2)

        print(f"Saving {len(metrics)} metrics...")
        with open(f"{output_dir}/metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"Saving {len(tasks)} tasks...")
        with open(f"{output_dir}/tasks.json", "w") as f:
            json.dump(tasks, f, indent=2)

        print(f"\nTest data generated successfully in {output_dir}/")
        print(f"  - {len(orders)} orders")
        print(f"  - {len(logs)} log entries")
        print(f"  - {len(metrics)} performance metrics")
        print(f"  - {len(tasks)} tasks")


if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.save_test_data()
