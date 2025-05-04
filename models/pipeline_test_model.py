from .base import Base
from sqlalchemy import (Column, Integer, String, DateTime,
                        Text, ForeignKey, Enum as SQLAEnum)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum


class PipelineStatusEnum(enum.Enum):
    PENDING = "PENDING"
    RUNNING_GIT = "RUNNING_GIT"
    RUNNING_DOCKER_BUILD = "RUNNING_DOCKER_BUILD"
    RUNNING_DOCKER_DEPLOY = "RUNNING_DOCKER_DEPLOY"
    SUCCESS = "SUCCESS"
    FAILED_GIT = "FAILED_GIT"
    FAILED_DOCKER_BUILD = "FAILED_DOCKER_BUILD"
    FAILED_DOCKER_DEPLOY = "FAILED_DOCKER_DEPLOY"
    UNKNOWN = "UNKNOWN"


class PipelineRuns(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    config = relationship("RepoConfig")

    trigger_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        SQLAEnum(PipelineStatusEnum),
        default=PipelineStatusEnum.PENDING,
        nullable=False
    )

    commit_sha = Column(String, nullable=True)
    trigger_event_id = Column(String, nullable=True, index=True)

    logs = Column(Text, nullable=True)

    def __repr__(self):
        return f"<PipelineRun(id={self.id}, id={self.config_id}, '{self.status.name}')>"
