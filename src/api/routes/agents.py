"""
Agent Routes

API endpoints for agent operations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from src.core.orchestration import get_orchestration_manager, AgentType
from src.db.database import get_db
from src.db.repositories import TaskRepository, AgentExecutionRepository

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class AgentTaskRequest(BaseModel):
    """Agent task execution request"""
    agent_type: str
    task_type: str
    task_data: Dict[str, Any]
    user_id: Optional[str] = None


class AgentTaskResponse(BaseModel):
    """Agent task execution response"""
    success: bool
    task_id: Optional[str] = None
    agent_type: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentInfo(BaseModel):
    """Agent information"""
    type: str
    name: str
    role: str
    goal: str
    status: str
    total_executions: int
    successful_executions: int
    success_rate: float


@router.get("/list", response_model=List[AgentInfo])
async def list_agents(db: Session = Depends(get_db)):
    """
    Get list of all available agents

    Returns:
        List[AgentInfo]: List of agent information
    """
    try:
        manager = get_orchestration_manager()
        status = manager.get_agent_status()

        agents_info = []

        for agent_type_str, agent_stats in status["agents"].items():
            agents_info.append(AgentInfo(
                type=agent_type_str,
                name=agent_stats["name"],
                role=agent_stats["role"],
                goal="Agent goal",  # Could be fetched from agent
                status="active",
                total_executions=agent_stats["total_executions"],
                successful_executions=agent_stats["successful_executions"],
                success_rate=agent_stats["successful_executions"] / max(agent_stats["total_executions"], 1) * 100
            ))

        logger.info(f"Retrieved {len(agents_info)} agents")

        return agents_info

    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=AgentTaskResponse)
async def execute_agent_task(
    request: AgentTaskRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a task on a specific agent

    Args:
        request: Agent task execution request

    Returns:
        AgentTaskResponse: Task execution result
    """
    try:
        # Validate agent type
        try:
            agent_type = AgentType(request.agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {request.agent_type}"
            )

        # Create task in database
        task_repo = TaskRepository(db)
        task = task_repo.create({
            "task_type": request.task_type,
            "agent_type": request.agent_type,
            "task_data": request.task_data,
            "user_id": request.user_id,
            "status": "pending"
        })

        logger.info(f"Created task {task.id} for agent {request.agent_type}")

        # Update task status to running
        task_repo.update_status(task.id, "running")

        # Execute task
        manager = get_orchestration_manager()

        task_definition = {
            "type": request.task_type,
            "data": request.task_data
        }

        result = await manager.execute_task(
            agent_type=agent_type,
            task=task_definition
        )

        # Update task with result
        if result.get("success"):
            task_repo.update_status(task.id, "completed", result=result)
        else:
            task_repo.update_status(
                task.id,
                "failed",
                error_message=result.get("error", "Unknown error")
            )

        logger.info(f"Task {task.id} completed: {result.get('success')}")

        return AgentTaskResponse(
            success=result.get("success", False),
            task_id=task.id,
            agent_type=request.agent_type,
            result=result,
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute agent task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}/status")
async def get_agent_status(
    agent_name: str,
    db: Session = Depends(get_db)
):
    """
    Get status of a specific agent

    Args:
        agent_name: Agent type name

    Returns:
        Dict: Agent status information
    """
    try:
        # Validate agent name
        try:
            agent_type = AgentType(agent_name)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Agent not found: {agent_name}"
            )

        manager = get_orchestration_manager()
        agent = manager.agents.get(agent_type)

        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent not found: {agent_name}"
            )

        # Get execution history from orchestration manager
        history = manager.get_execution_history(agent_type=agent_type, limit=10)

        # Get statistics from database
        execution_repo = AgentExecutionRepository(db)
        stats = execution_repo.get_statistics(agent_type=agent_name)

        return {
            "agent_type": agent_name,
            "name": agent.name,
            "role": agent.role,
            "goal": agent.goal,
            "status": "active",
            "statistics": stats,
            "recent_executions": history,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_name}/history")
async def get_agent_history(
    agent_name: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get execution history for a specific agent

    Args:
        agent_name: Agent type name
        limit: Maximum number of records
        offset: Offset for pagination

    Returns:
        Dict: Execution history
    """
    try:
        # Validate agent name
        try:
            AgentType(agent_name)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Agent not found: {agent_name}"
            )

        execution_repo = AgentExecutionRepository(db)
        executions = execution_repo.get_all(
            agent_type=agent_name,
            limit=limit,
            offset=offset
        )

        return {
            "agent_type": agent_name,
            "total": len(executions),
            "limit": limit,
            "offset": offset,
            "executions": [
                {
                    "id": exec.id,
                    "task_id": exec.task_id,
                    "status": exec.status,
                    "started_at": exec.started_at.isoformat() if exec.started_at else None,
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                    "duration_seconds": exec.duration_seconds
                }
                for exec in executions
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
