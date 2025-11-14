"""
Task Routes

API endpoints for task management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging

from src.db.database import get_db
from src.db.repositories import TaskRepository

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class TaskCreate(BaseModel):
    """Task creation request"""
    task_type: str
    agent_type: str
    task_data: Dict[str, Any]
    user_id: Optional[str] = None
    priority: int = 5


class TaskResponse(BaseModel):
    """Task response"""
    id: str
    task_type: str
    agent_type: str
    status: str
    priority: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None


@router.post("/create", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new task

    Args:
        task: Task creation request

    Returns:
        TaskResponse: Created task
    """
    try:
        task_repo = TaskRepository(db)

        new_task = task_repo.create({
            "task_type": task.task_type,
            "agent_type": task.agent_type,
            "task_data": task.task_data,
            "user_id": task.user_id,
            "priority": task.priority,
            "status": "pending"
        })

        logger.info(f"Created task {new_task.id}")

        return TaskResponse(
            id=new_task.id,
            task_type=new_task.task_type,
            agent_type=new_task.agent_type,
            status=new_task.status,
            priority=new_task.priority,
            created_at=new_task.created_at.isoformat(),
            started_at=new_task.started_at.isoformat() if new_task.started_at else None,
            completed_at=new_task.completed_at.isoformat() if new_task.completed_at else None,
            duration_seconds=new_task.duration_seconds
        )

    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Get task by ID

    Args:
        task_id: Task ID

    Returns:
        Dict: Task details
    """
    try:
        task_repo = TaskRepository(db)
        task = task_repo.get_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        return {
            "id": task.id,
            "task_type": task.task_type,
            "agent_type": task.agent_type,
            "status": task.status,
            "priority": task.priority,
            "task_data": task.task_data,
            "result": task.result,
            "error_message": task.error_message,
            "user_id": task.user_id,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "duration_seconds": task.duration_seconds
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
async def list_tasks(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List tasks with filters

    Args:
        user_id: Filter by user ID
        status: Filter by status
        agent_type: Filter by agent type
        limit: Maximum number of tasks
        offset: Offset for pagination

    Returns:
        Dict: List of tasks
    """
    try:
        task_repo = TaskRepository(db)

        tasks = task_repo.get_all(
            user_id=user_id,
            status=status,
            agent_type=agent_type,
            limit=limit,
            offset=offset
        )

        total = task_repo.count(user_id=user_id, status=status)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "tasks": [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "agent_type": task.agent_type,
                    "status": task.status,
                    "priority": task.priority,
                    "created_at": task.created_at.isoformat(),
                    "duration_seconds": task.duration_seconds
                }
                for task in tasks
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a task

    Args:
        task_id: Task ID

    Returns:
        Dict: Deletion result
    """
    try:
        task_repo = TaskRepository(db)
        success = task_repo.delete(task_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        logger.info(f"Deleted task {task_id}")

        return {
            "success": True,
            "task_id": task_id,
            "message": "Task deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_task_statistics(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get task statistics

    Args:
        user_id: Filter by user ID

    Returns:
        Dict: Task statistics
    """
    try:
        task_repo = TaskRepository(db)

        total = task_repo.count(user_id=user_id)
        pending = task_repo.count(user_id=user_id, status="pending")
        running = task_repo.count(user_id=user_id, status="running")
        completed = task_repo.count(user_id=user_id, status="completed")
        failed = task_repo.count(user_id=user_id, status="failed")

        return {
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / total * 100) if total > 0 else 0
        }

    except Exception as e:
        logger.error(f"Failed to get task statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
