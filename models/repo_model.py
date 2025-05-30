from sqlalchemy import (
    Column, Integer, String,
    ForeignKey, Table, Boolean,
    BigInteger, Enum as SQLAlchemyEnum
)
import enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base


class GitHostPlatform(enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    GENERIC = "generic"


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
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_url: Mapped[str] = mapped_column(String)
    main_branch: Mapped[str] = mapped_column(String)
    platform: Mapped[GitHostPlatform] = mapped_column(
        SQLAlchemyEnum(
            GitHostPlatform,
            native_enum=False,
            values_callable=lambda enum: [e.value for e in enum]
        ),
        default=GitHostPlatform.GITHUB
    )

    # Docker info
    docker_username: Mapped[str | None] = mapped_column(String, nullable=True)

    # Installation info
    installation_id: Mapped[BigInteger] = mapped_column(BigInteger, nullable=True)

    # SSH for cloning configuration
    use_ssh_for_clone: Mapped[bool] = mapped_column(Boolean, default=False)
    git_ssh_private_key_encrypted: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
    git_ssh_key_passphrase_encrypted: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )
    git_ssh_host_key: Mapped[str | None] = mapped_column(String, nullable=True)

    # SSH  for deploy configuration
    SSH_host: Mapped[str | None] = mapped_column(String, nullable=True)
    SSH_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    SSH_username: Mapped[str | None] = mapped_column(String, nullable=True)
    SSH_key_path: Mapped[str | None] = mapped_column(String, nullable=True)
    SSH_key_passphrase: Mapped[str | None] = mapped_column(String, nullable=True)
    SSH_for_deploy: Mapped[bool] = mapped_column(Boolean)

    webhooks = relationship("Webhook", back_populates="repo_config")

    users = relationship(
        "User",
        secondary=repo_user,
        back_populates="configs"
    )
    pipeline_runs = relationship(
        "PipelineRuns",
        back_populates="config"
    )


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(ForeignKey("configs.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    webhook_url: Mapped[str] = mapped_column(nullable=False)
    encoded_webhook_secret: Mapped[str] = mapped_column(nullable=False)

    repo_config: Mapped[RepoConfig] = relationship(
        "RepoConfig", back_populates="webhooks"
    )

    user = relationship("User", back_populates="webhooks")
