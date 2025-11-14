"""
Database Models

SQLAlchemy models for the application
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate UUID string"""
    return str(uuid.uuid4())


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    task_type = Column(String, nullable=False, index=True)
    agent_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending", index=True)  # pending, running, completed, failed
    priority = Column(Integer, default=5)  # 1-10, higher is more urgent

    # Task data
    task_data = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)

    # Metadata
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    # Relationships
    user = relationship("User", back_populates="tasks")
    executions = relationship("AgentExecution", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status})>"


class AgentExecution(Base):
    """Agent execution model"""
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False, index=True)
    agent_type = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=False)

    # Execution data
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String, nullable=False, default="running")  # running, completed, failed
    error_message = Column(Text)

    # Metrics
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    llm_calls_count = Column(Integer, default=0)
    llm_tokens_used = Column(Integer, default=0)

    # Relationships
    task = relationship("Task", back_populates="executions")

    def __repr__(self):
        return f"<AgentExecution(id={self.id}, agent={self.agent_type}, status={self.status})>"


class WorkflowExecution(Base):
    """Workflow execution model"""
    __tablename__ = "workflow_executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_name = Column(String, nullable=False, index=True)
    scenario_name = Column(String)
    mode = Column(String, nullable=False)  # sequential, parallel, conditional

    # Execution data
    workflow_config = Column(JSON)
    results = Column(JSON)
    status = Column(String, nullable=False, default="running")  # running, completed, failed

    # Metrics
    total_steps = Column(Integer)
    successful_steps = Column(Integer)
    failed_steps = Column(Integer)

    # Metadata
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, name={self.workflow_name}, status={self.status})>"


class SystemMetrics(Base):
    """System metrics model"""
    __tablename__ = "system_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    metric_type = Column(String, nullable=False, index=True)  # agent_execution, task_completion, error_rate
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String)

    # Dimensions
    agent_type = Column(String, index=True)
    task_type = Column(String, index=True)
    status = Column(String)

    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    tags = Column(JSON)

    def __repr__(self):
        return f"<SystemMetrics(type={self.metric_type}, name={self.metric_name}, value={self.metric_value})>"
