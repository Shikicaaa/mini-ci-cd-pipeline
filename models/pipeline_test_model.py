from .base import Base
from sqlalchemy import (Integer, String, DateTime,
                        Text, ForeignKey, Enum as SQLAEnum)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from schemas.schema_pipeline import PipelineStatusEnum
from datetime import datetime


class PipelineRuns(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("configs.id", ondelete="CASCADE"),
        nullable=False
    )
    config = relationship("RepoConfig", back_populates="pipeline_runs")

    trigger_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[SQLAEnum] = mapped_column(
        SQLAEnum(PipelineStatusEnum),
        default=PipelineStatusEnum.PENDING,
        nullable=False
    )

    commit_sha: Mapped[str] = mapped_column(String, nullable=True)
    trigger_event_id: Mapped[str] = mapped_column(String, nullable=True, index=True)

    logs: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return (
            f"<PipelineRun(id={self.id}, config_id={self.config_id}, "
            f"status='{self.status.name}')>"
        )
