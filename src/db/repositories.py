"""
Database Repositories

Repository pattern implementation for database access
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from src.db.models import Task, AgentExecution, User, WorkflowExecution, SystemMetrics


class TaskRepository:
    """Task repository"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, task_data: Dict[str, Any]) -> Task:
        """Create a new task"""
        task = Task(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.db.query(Task).filter(Task.id == task_id).first()

    def get_all(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        agent_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """Get all tasks with filters"""
        query = self.db.query(Task)

        if user_id:
            query = query.filter(Task.user_id == user_id)
        if status:
            query = query.filter(Task.status == status)
        if agent_type:
            query = query.filter(Task.agent_type == agent_type)

        return query.order_by(desc(Task.created_at)).offset(offset).limit(limit).all()

    def update_status(self, task_id: str, status: str, **kwargs) -> Optional[Task]:
        """Update task status"""
        task = self.get_by_id(task_id)
        if task:
            task.status = status

            if status == "running" and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status in ["completed", "failed"]:
                task.completed_at = datetime.utcnow()
                if task.started_at:
                    task.duration_seconds = (task.completed_at - task.started_at).total_seconds()

            # Update other fields
            for key, value in kwargs.items():
                setattr(task, key, value)

            self.db.commit()
            self.db.refresh(task)

        return task

    def update_result(self, task_id: str, result: Dict[str, Any]) -> Optional[Task]:
        """Update task result"""
        task = self.get_by_id(task_id)
        if task:
            task.result = result
            self.db.commit()
            self.db.refresh(task)
        return task

    def delete(self, task_id: str) -> bool:
        """Delete task"""
        task = self.get_by_id(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False

    def count(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Count tasks"""
        query = self.db.query(Task)

        if user_id:
            query = query.filter(Task.user_id == user_id)
        if status:
            query = query.filter(Task.status == status)

        return query.count()


class AgentExecutionRepository:
    """Agent execution repository"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, execution_data: Dict[str, Any]) -> AgentExecution:
        """Create a new agent execution"""
        execution = AgentExecution(**execution_data)
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def get_by_id(self, execution_id: str) -> Optional[AgentExecution]:
        """Get execution by ID"""
        return self.db.query(AgentExecution).filter(AgentExecution.id == execution_id).first()

    def get_by_task_id(self, task_id: str) -> List[AgentExecution]:
        """Get all executions for a task"""
        return self.db.query(AgentExecution).filter(
            AgentExecution.task_id == task_id
        ).order_by(AgentExecution.started_at).all()

    def get_all(
        self,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AgentExecution]:
        """Get all executions with filters"""
        query = self.db.query(AgentExecution)

        if agent_type:
            query = query.filter(AgentExecution.agent_type == agent_type)
        if status:
            query = query.filter(AgentExecution.status == status)

        return query.order_by(desc(AgentExecution.started_at)).offset(offset).limit(limit).all()

    def update_status(self, execution_id: str, status: str, **kwargs) -> Optional[AgentExecution]:
        """Update execution status"""
        execution = self.get_by_id(execution_id)
        if execution:
            execution.status = status

            if status in ["completed", "failed"]:
                execution.completed_at = datetime.utcnow()
                if execution.started_at:
                    execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()

            # Update other fields
            for key, value in kwargs.items():
                setattr(execution, key, value)

            self.db.commit()
            self.db.refresh(execution)

        return execution

    def get_statistics(
        self,
        agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get execution statistics"""
        query = self.db.query(AgentExecution)

        if agent_type:
            query = query.filter(AgentExecution.agent_type == agent_type)

        total = query.count()
        completed = query.filter(AgentExecution.status == "completed").count()
        failed = query.filter(AgentExecution.status == "failed").count()
        running = query.filter(AgentExecution.status == "running").count()

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "success_rate": (completed / total * 100) if total > 0 else 0
        }


class UserRepository:
    """User repository"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users"""
        return self.db.query(User).order_by(User.created_at).offset(offset).limit(limit).all()

    def update(self, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
        """Update user"""
        user = self.get_by_id(user_id)
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user

    def delete(self, user_id: str) -> bool:
        """Delete user"""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False


class WorkflowExecutionRepository:
    """Workflow execution repository"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, workflow_data: Dict[str, Any]) -> WorkflowExecution:
        """Create a new workflow execution"""
        workflow = WorkflowExecution(**workflow_data)
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_by_id(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Get workflow by ID"""
        return self.db.query(WorkflowExecution).filter(WorkflowExecution.id == workflow_id).first()

    def get_all(
        self,
        workflow_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """Get all workflows with filters"""
        query = self.db.query(WorkflowExecution)

        if workflow_name:
            query = query.filter(WorkflowExecution.workflow_name == workflow_name)
        if status:
            query = query.filter(WorkflowExecution.status == status)

        return query.order_by(desc(WorkflowExecution.created_at)).offset(offset).limit(limit).all()

    def update_status(self, workflow_id: str, status: str, **kwargs) -> Optional[WorkflowExecution]:
        """Update workflow status"""
        workflow = self.get_by_id(workflow_id)
        if workflow:
            workflow.status = status

            if status == "running" and not workflow.started_at:
                workflow.started_at = datetime.utcnow()
            elif status in ["completed", "failed"]:
                workflow.completed_at = datetime.utcnow()
                if workflow.started_at:
                    workflow.duration_seconds = (workflow.completed_at - workflow.started_at).total_seconds()

            # Update other fields
            for key, value in kwargs.items():
                setattr(workflow, key, value)

            self.db.commit()
            self.db.refresh(workflow)

        return workflow


class SystemMetricsRepository:
    """System metrics repository"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, metric_data: Dict[str, Any]) -> SystemMetrics:
        """Create a new metric"""
        metric = SystemMetrics(**metric_data)
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric

    def get_latest(
        self,
        metric_type: Optional[str] = None,
        agent_type: Optional[str] = None,
        limit: int = 100
    ) -> List[SystemMetrics]:
        """Get latest metrics"""
        query = self.db.query(SystemMetrics)

        if metric_type:
            query = query.filter(SystemMetrics.metric_type == metric_type)
        if agent_type:
            query = query.filter(SystemMetrics.agent_type == agent_type)

        return query.order_by(desc(SystemMetrics.timestamp)).limit(limit).all()

    def get_aggregated(
        self,
        metric_type: str,
        metric_name: str,
        agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated metrics"""
        from sqlalchemy import func

        query = self.db.query(
            func.avg(SystemMetrics.metric_value).label("avg"),
            func.min(SystemMetrics.metric_value).label("min"),
            func.max(SystemMetrics.metric_value).label("max"),
            func.count(SystemMetrics.id).label("count")
        ).filter(
            SystemMetrics.metric_type == metric_type,
            SystemMetrics.metric_name == metric_name
        )

        if agent_type:
            query = query.filter(SystemMetrics.agent_type == agent_type)

        result = query.first()

        return {
            "average": float(result.avg) if result.avg else 0,
            "minimum": float(result.min) if result.min else 0,
            "maximum": float(result.max) if result.max else 0,
            "count": result.count
        }
