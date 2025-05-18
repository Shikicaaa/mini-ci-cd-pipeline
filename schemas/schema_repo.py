from pydantic import BaseModel, HttpUrl
from typing import Optional


class RepoConfigSchema(BaseModel):
    repo_url: HttpUrl
    main_branch: str
    SSH_host: Optional[str] = None
    SSH_port: Optional[int] = None
    SSH_username: Optional[str] = None
    SSH_key_path: Optional[str] = None
    SSH_key_passphrase: Optional[str] = None
    SSH_for_deploy: bool

    class Config:
        from_attributes = True


class DockerConfig(BaseModel):
    docker_username: str
    specific_repo: Optional[str] = None
