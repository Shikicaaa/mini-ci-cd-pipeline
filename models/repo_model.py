from pydantic import HttpUrl
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from .base import Base

repo_user = Table(
    "repo_user",
    Base.metadata,
    Column("repo_config_id", Integer, ForeignKey("configs.id")),
    Column("user_id", Integer, ForeignKey("users.id"))
)


repo_pipeline = Table(
    "repo_pipeline",
    Base.metadata,
    Column("repo_config_id", Integer, ForeignKey("configs.id")),
    Column("pipeline_id", Integer, ForeignKey("pipeline_runs.id"))
)


class RepoConfig(Base):
    __tablename__ = "configs"
    id: int = Column(Integer, primary_key=True, index=True)
    repo_url: HttpUrl = Column(String)
    main_branch: str = Column(String)
    docker_username: str = Column(String)

    users = relationship(
        "User",
        secondary=repo_user,
        back_populates="configs"
    )
    pipeline_runs = relationship(
        "PipelineRuns",
        back_populates="config"
    )
