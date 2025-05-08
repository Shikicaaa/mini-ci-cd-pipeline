from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from api.api_users import get_db, get_current_user
from models.user_model import User
from models.pipeline_test_model import PipelineRuns
from models.repo_model import RepoConfig
from schemas.schema_pipeline import PipelineRunOut

router = APIRouter()


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
