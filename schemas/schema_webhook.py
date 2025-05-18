from pydantic import BaseModel


class WebhookSchema(BaseModel):
    url: str
    secret: str
    repo_id: int
