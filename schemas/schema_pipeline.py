from pydantic import BaseModel
from typing import Optional
from datetime import datetime
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


class PipelineRunOut(BaseModel):
    id: int
    config_id: int
    trigger_time: datetime
    end_time: Optional[datetime]
    status: PipelineStatusEnum
    commit_sha: Optional[str]
    trigger_event_id: Optional[str]
    logs: Optional[str]

    class Config:
        from_attributes = True
