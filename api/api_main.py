from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session, joinedload
from typing import List
import json
import os
from api.api_users import get_db, get_current_user
from models.user_model import User
from models.pipeline_test_model import PipelineRuns
from models.repo_model import RepoConfig
from schemas.schema_pipeline import PipelineRunOut
from schemas.schema_repo import RepoConfigSchema

router = APIRouter()

CONFIG_FILE = "config"


def save_config(config: RepoConfig, user: str):
    try:
        output = CONFIG_FILE + f"_{user}.json"
        with open(output, "w") as f:
            json.dump(config.model_dump(mode="json"), f, indent=4)
        print(f"Config saved in {output}.")
    except IOError as e:
        print(f"Error: cannot save config in {output}. Message: {e}")


def load_config(user: str) -> RepoConfig | None:
    output = CONFIG_FILE + f"_{user}.json"
    if not os.path.exists(output):
        return None
    try:
        with open(output, "r") as f:
            data = json.load(f)
            config = RepoConfig(**data)
            print(f"Configuration loaded from {output}")
            return config
    except (IOError, json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error: cannot load config from {output}. Message: {e}")
        return None


@router.delete("/api/config/{config_id}")
async def delete_config(
    config_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not identify user."
        )

    config = db.query(RepoConfig).filter(
        RepoConfig.id == config_id,
        RepoConfig.users.any(id=user.id)
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found or you don't have access."
        )

    try:
        db.delete(config)
        db.commit()
        return {
            "message": "Config deleted successfully!",
            "config_id": config_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: An unexpected error has occurred: '{e}'"
        )
    finally:
        db.close()


@router.post("/api/config")
async def config_repo(
    config_data: RepoConfigSchema,
    user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not identify user."
        )

    repo_url = str(config_data.repo_url)
    print(
        f"Repo url: {repo_url}",
        f"Main branch: {config_data.main_branch}"
    )

    existing_config = db.query(RepoConfig).filter(
        RepoConfig.repo_url == repo_url,
        RepoConfig.main_branch == config_data.main_branch
    ).first()

    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identical configuration exists for this user!"
        )

    try:
        config = RepoConfig(
            repo_url=repo_url,
            main_branch=config_data.main_branch
        )
        if user not in config.users:
            config.users.append(user)
        db.add(config)
        db.commit()
        db.refresh(config)
        return {
            "message": "Config saved successfuly!",
            "config": config_data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: An unexpected error has occured: '{e}'"
        )
    finally:
        db.close()


@router.post("/api/docker")
async def set_docker(
    specific_repo: str = Body(description="Can be empty, if so will fill every repo"),
    docker_username: str = Body(description="Put your docker username here"),
    user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    updated = 0
    if not specific_repo:
        configs = db.query(RepoConfig).filter(RepoConfig.users.any(id=user.id)).all()
        for config in configs:
            config.docker_username = docker_username
            updated += 1
    else:
        config = db.query(RepoConfig).filter(
            RepoConfig.users.any(id=user.id),
            RepoConfig.repo_url == specific_repo
        ).first()
        if config:
            updated += 1
            config.docker_username = docker_username
        else:
            return {"message": "No matching repo found or you don't have access."}

    db.commit()

    return {
        "message": f"Docker username set for {updated} config(s)"
    }


@router.get("/api/config")
async def get_config(
    user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    try:
        configs = db.query(RepoConfig).filter(RepoConfig.users.any(id=user.id)).all()
        if not configs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have a config file saved yet!"
            )
        else:
            return configs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: An unexpected error has occured '{e}'"
        )
    finally:
        db.close()


@router.get("/api/pipelines", response_model=List[PipelineRunOut])
async def get_pipeline(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    runs = (
        db.query(PipelineRuns)
        .join(PipelineRuns.config)
        .join(RepoConfig.users)
        .filter(User.id == user.id)
        .options(joinedload(PipelineRuns.config))
        .all()
    )
    return runs


@router.get("/api/pipelines/{pipeline_id}")
async def get_pipelines(
    pipeline_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pipeline = db.query(PipelineRuns).filter_by(id=pipeline_id).first()
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found"
        )
    config = pipeline.config
    owners = config.users

    if user not in owners:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this pipeline"
        )

    return {
        "pipeline_id": pipeline.id,
        "status": pipeline.status.name,
        "owners": [owner.username for owner in owners],
        "repo_url": config.repo_url,
        "trigger_time": pipeline.trigger_time,
        "end_time": pipeline.end_time,
        "commit_sha": pipeline.commit_sha
    }
