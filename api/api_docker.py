from fastapi import APIRouter, Depends
from api.api_users import get_db, get_current_user
from models.user_model import User
from models.repo_model import RepoConfig
from schemas.schema_repo import DockerConfig

router = APIRouter()


@router.post("/api/docker")
async def set_docker(
    docker_config: DockerConfig,
    user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    updated = 0
    if not docker_config.specific_repo:
        configs = db.query(RepoConfig).filter(RepoConfig.users.any(id=user.id)).all()
        for config in configs:
            config.docker_username = docker_config.docker_username
            updated += 1
    else:
        config = db.query(RepoConfig).filter(
            RepoConfig.users.any(id=user.id),
            RepoConfig.repo_url == config.specific_repo
        ).first()
        if config:
            updated += 1
            config.docker_username = docker_config.docker_username
        else:
            return {"message": "No matching repo found or you don't have access."}

    db.commit()

    return {
        "message": f"Docker username set for {updated} config(s)"
    }