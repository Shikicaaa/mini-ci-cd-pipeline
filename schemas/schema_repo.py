from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum


class GitHostPlatform(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    GENERIC = "generic"


class RepoConfigSchema(BaseModel):
    repo_url: HttpUrl
    main_branch: str
    docker_username: Optional[str] = None
    platform: GitHostPlatform = GitHostPlatform.GITHUB
    installation_id: Optional[int] = None
    use_ssh_for_clone: bool = False
    git_ssh_private_key_encrypted: Optional[str] = None
    git_ssh_key_passphrase_encrypted: Optional[str] = None
    git_ssh_host_key: Optional[str] = None
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
