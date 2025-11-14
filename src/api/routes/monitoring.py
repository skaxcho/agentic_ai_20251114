"""
Monitoring Routes

API endpoints for system monitoring and metrics
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
import psutil
import time
from datetime import datetime, timedelta

from src.core.orchestration import get_orchestration_manager
from src.db.database import get_db, check_db_connection
from src.db.repositories import (
    TaskRepository,
    AgentExecutionRepository,
    SystemMetricsRepository
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        Dict: System health status
    """
    try:
        # Check database
        db_healthy = check_db_connection()

        # Check orchestration manager
        manager_healthy = False
        try:
            manager = get_orchestration_manager()
            manager_healthy = len(manager.agents) == 8
        except Exception:
            pass

        # Overall health
        healthy = db_healthy and manager_healthy

        return {
            "status": "healthy" if healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "orchestration_manager": "active" if manager_healthy else "inactive",
            "agents_count": 8 if manager_healthy else 0,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """
    Get system metrics

    Returns:
        Dict: System metrics
    """
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Task statistics
        task_repo = TaskRepository(db)
        task_stats = {
            "total": task_repo.count(),
            "pending": task_repo.count(status="pending"),
            "running": task_repo.count(status="running"),
            "completed": task_repo.count(status="completed"),
            "failed": task_repo.count(status="failed")
        }

        # Agent statistics
        manager = get_orchestration_manager()
        agent_status = manager.get_agent_status()

        # Recent execution history
        execution_repo = AgentExecutionRepository(db)
        recent_executions = execution_repo.get_all(limit=10)

        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                }
            },
            "tasks": task_stats,
            "agents": {
                "total": agent_status["total_agents"],
                "total_executions": agent_status["total_executions"],
                "agents": agent_status["agents"]
            },
            "recent_executions": [
                {
                    "id": exec.id,
                    "agent_type": exec.agent_type,
                    "status": exec.status,
                    "duration_seconds": exec.duration_seconds
                }
                for exec in recent_executions
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/agents/{agent_type}")
async def get_agent_metrics(
    agent_type: str,
    db: Session = Depends(get_db)
):
    """
    Get metrics for a specific agent

    Args:
        agent_type: Agent type

    Returns:
        Dict: Agent metrics
    """
    try:
        execution_repo = AgentExecutionRepository(db)

        # Get statistics
        stats = execution_repo.get_statistics(agent_type=agent_type)

        # Get recent executions
        recent = execution_repo.get_all(agent_type=agent_type, limit=20)

        # Calculate average duration
        durations = [e.duration_seconds for e in recent if e.duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "agent_type": agent_type,
            "statistics": stats,
            "average_duration_seconds": avg_duration,
            "recent_executions_count": len(recent),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get agent metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/timeseries")
async def get_timeseries_metrics(
    metric_type: Optional[str] = None,
    agent_type: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get time series metrics

    Args:
        metric_type: Metric type filter
        agent_type: Agent type filter
        hours: Number of hours to look back

    Returns:
        Dict: Time series metrics
    """
    try:
        metrics_repo = SystemMetricsRepository(db)

        # Get latest metrics
        metrics = metrics_repo.get_latest(
            metric_type=metric_type,
            agent_type=agent_type,
            limit=hours * 60  # Assuming 1 metric per minute
        )

        # Group by time buckets (hourly)
        time_buckets = {}

        for metric in metrics:
            bucket = metric.timestamp.replace(minute=0, second=0, microsecond=0)
            bucket_key = bucket.isoformat()

            if bucket_key not in time_buckets:
                time_buckets[bucket_key] = []

            time_buckets[bucket_key].append({
                "metric_name": metric.metric_name,
                "metric_value": metric.metric_value,
                "agent_type": metric.agent_type
            })

        return {
            "metric_type": metric_type,
            "agent_type": agent_type,
            "hours": hours,
            "data": time_buckets,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get timeseries metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Get dashboard data (combined metrics)

    Returns:
        Dict: Dashboard data
    """
    try:
        # Get various metrics
        task_repo = TaskRepository(db)
        execution_repo = AgentExecutionRepository(db)
        manager = get_orchestration_manager()

        # Task statistics
        task_stats = {
            "total": task_repo.count(),
            "pending": task_repo.count(status="pending"),
            "running": task_repo.count(status="running"),
            "completed": task_repo.count(status="completed"),
            "failed": task_repo.count(status="failed")
        }
        task_stats["success_rate"] = (
            task_stats["completed"] / task_stats["total"] * 100
            if task_stats["total"] > 0 else 0
        )

        # Agent statistics
        agent_stats = {}
        for agent_type in ["report", "monitoring", "its", "db_extract",
                          "change_mgmt", "biz_support", "sop", "infra"]:
            stats = execution_repo.get_statistics(agent_type=agent_type)
            agent_stats[agent_type] = stats

        # Recent activity
        recent_tasks = task_repo.get_all(limit=10)
        recent_executions = execution_repo.get_all(limit=10)

        # System health
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory_percent = psutil.virtual_memory().percent

        return {
            "overview": {
                "total_tasks": task_stats["total"],
                "success_rate": task_stats["success_rate"],
                "active_agents": 8,
                "system_health": "healthy" if cpu_percent < 80 and memory_percent < 80 else "warning"
            },
            "tasks": task_stats,
            "agents": agent_stats,
            "recent_tasks": [
                {
                    "id": task.id,
                    "type": task.task_type,
                    "agent": task.agent_type,
                    "status": task.status,
                    "created_at": task.created_at.isoformat()
                }
                for task in recent_tasks
            ],
            "recent_executions": [
                {
                    "id": exec.id,
                    "agent": exec.agent_type,
                    "status": exec.status,
                    "duration": exec.duration_seconds
                }
                for exec in recent_executions
            ],
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/record")
async def record_metric(
    metric_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Record a custom metric

    Args:
        metric_data: Metric data

    Returns:
        Dict: Success response
    """
    try:
        metrics_repo = SystemMetricsRepository(db)

        metric = metrics_repo.create(metric_data)

        return {
            "success": True,
            "metric_id": metric.id,
            "timestamp": metric.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to record metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
