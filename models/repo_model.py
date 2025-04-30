from pydantic import BaseModel, HttpUrl


class RepoConfig(BaseModel):
    repo_url: HttpUrl
    main_branch: str
