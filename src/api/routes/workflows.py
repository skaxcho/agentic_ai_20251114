"""
Workflow Routes

API endpoints for workflow orchestration
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import logging

from src.core.orchestration import get_orchestration_manager, OrchestrationMode
from src.db.database import get_db
from src.db.repositories import WorkflowExecutionRepository

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class WorkflowStep(BaseModel):
    """Workflow step"""
    name: str
    agent: str
    task: Dict[str, Any]
    stop_on_failure: bool = False


class WorkflowExecuteRequest(BaseModel):
    """Workflow execution request"""
    workflow_name: str
    mode: str = "sequential"  # sequential, parallel, conditional
    workflow: List[WorkflowStep]
    user_id: str = None


@router.post("/execute")
async def execute_workflow(
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a workflow

    Args:
        request: Workflow execution request

    Returns:
        Dict: Workflow execution result
    """
    try:
        # Validate mode
        try:
            mode = OrchestrationMode(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workflow mode: {request.mode}"
            )

        # Create workflow execution record
        workflow_repo = WorkflowExecutionRepository(db)
        workflow_exec = workflow_repo.create({
            "workflow_name": request.workflow_name,
            "mode": request.mode,
            "workflow_config": {
                "workflow": [step.dict() for step in request.workflow]
            },
            "user_id": request.user_id,
            "status": "running",
            "total_steps": len(request.workflow)
        })

        logger.info(f"Created workflow execution {workflow_exec.id}")

        # Execute workflow
        manager = get_orchestration_manager()

        workflow_steps = [step.dict() for step in request.workflow]

        result = await manager.orchestrate_workflow(
            workflow=workflow_steps,
            mode=mode
        )

        # Update workflow execution with result
        if result.get("success"):
            workflow_repo.update_status(
                workflow_exec.id,
                "completed",
                results=result.get("results"),
                successful_steps=result.get("successful_steps"),
                failed_steps=result.get("total_steps", 0) - result.get("successful_steps", 0)
            )
        else:
            workflow_repo.update_status(
                workflow_exec.id,
                "failed",
                results=result.get("results"),
                successful_steps=result.get("successful_steps", 0),
                failed_steps=result.get("total_steps", 0) - result.get("successful_steps", 0)
            )

        logger.info(f"Workflow {workflow_exec.id} completed: {result.get('success')}")

        return {
            "success": result.get("success"),
            "workflow_id": workflow_exec.id,
            "workflow_name": request.workflow_name,
            "mode": request.mode,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """
    Get workflow execution by ID

    Args:
        workflow_id: Workflow execution ID

    Returns:
        Dict: Workflow details
    """
    try:
        workflow_repo = WorkflowExecutionRepository(db)
        workflow = workflow_repo.get_by_id(workflow_id)

        if not workflow:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow not found: {workflow_id}"
            )

        return {
            "id": workflow.id,
            "workflow_name": workflow.workflow_name,
            "scenario_name": workflow.scenario_name,
            "mode": workflow.mode,
            "status": workflow.status,
            "total_steps": workflow.total_steps,
            "successful_steps": workflow.successful_steps,
            "failed_steps": workflow.failed_steps,
            "workflow_config": workflow.workflow_config,
            "results": workflow.results,
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "duration_seconds": workflow.duration_seconds
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_workflows(
    workflow_name: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List workflow executions

    Args:
        workflow_name: Filter by workflow name
        status: Filter by status
        limit: Maximum number of workflows
        offset: Offset for pagination

    Returns:
        Dict: List of workflows
    """
    try:
        workflow_repo = WorkflowExecutionRepository(db)

        workflows = workflow_repo.get_all(
            workflow_name=workflow_name,
            status=status,
            limit=limit,
            offset=offset
        )

        return {
            "total": len(workflows),
            "limit": limit,
            "offset": offset,
            "workflows": [
                {
                    "id": wf.id,
                    "workflow_name": wf.workflow_name,
                    "mode": wf.mode,
                    "status": wf.status,
                    "total_steps": wf.total_steps,
                    "successful_steps": wf.successful_steps,
                    "created_at": wf.created_at.isoformat(),
                    "duration_seconds": wf.duration_seconds
                }
                for wf in workflows
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scenarios/{scenario_name}")
async def execute_scenario(
    scenario_name: str,
    scenario_config: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Execute a predefined E2E scenario

    Args:
        scenario_name: Scenario name
        scenario_config: Scenario configuration

    Returns:
        Dict: Scenario execution result
    """
    try:
        # Create workflow execution record
        workflow_repo = WorkflowExecutionRepository(db)
        workflow_exec = workflow_repo.create({
            "workflow_name": "E2E Scenario",
            "scenario_name": scenario_name,
            "mode": scenario_config.get("mode", "sequential"),
            "workflow_config": scenario_config,
            "status": "running"
        })

        logger.info(f"Created E2E scenario execution {workflow_exec.id}")

        # Execute scenario
        manager = get_orchestration_manager()

        result = await manager.execute_e2e_scenario(
            scenario_name=scenario_name,
            scenario_config=scenario_config
        )

        # Update workflow execution
        workflow_result = result.get("workflow_result", {})

        if result.get("success"):
            workflow_repo.update_status(
                workflow_exec.id,
                "completed",
                results=workflow_result.get("results"),
                total_steps=workflow_result.get("total_steps"),
                successful_steps=workflow_result.get("successful_steps"),
                failed_steps=workflow_result.get("total_steps", 0) - workflow_result.get("successful_steps", 0)
            )
        else:
            workflow_repo.update_status(
                workflow_exec.id,
                "failed",
                results=workflow_result.get("results")
            )

        logger.info(f"E2E scenario {scenario_name} completed: {result.get('success')}")

        return {
            "success": result.get("success"),
            "workflow_id": workflow_exec.id,
            "scenario_name": scenario_name,
            "result": result
        }

    except Exception as e:
        logger.error(f"Failed to execute scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
