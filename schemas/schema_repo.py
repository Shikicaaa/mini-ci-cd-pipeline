from pydantic import BaseModel, HttpUrl


class RepoConfigSchema(BaseModel):
    repo_url: HttpUrl
    main_branch: str

    class Config:
        from_attributes = True
