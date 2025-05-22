from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
import os
import string
import random
from cryptography.fernet import Fernet
from api.api_users import get_db, get_current_user
from models.user_model import User
from models.repo_model import RepoConfig, Webhook
from schemas.schema_webhook import WebhookSchema
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

router = APIRouter()


FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY")
if not FERNET_SECRET_KEY:
    raise RuntimeError("FERNET_SECRET_KEY is missing in .env")

fernet = Fernet(FERNET_SECRET_KEY.encode())


@router.delete("/api/webhook/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    db.delete(webhook)
    db.commit()


@router.get("/api/webhook/generate")
async def generate_webhook(
    repo_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    webhook = db.query(Webhook).filter(Webhook.repo_id == repo_id).first()

    if webhook:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook already exists for this configuration!"
        )

    secret = ''.join(random.choices(string.ascii_letters + string.digits, k=256))
    return {
        "url": "test",
        "secret": secret
    }


@router.post("/api/webhook/confirm")
async def confirm_webhook(
    payload: WebhookSchema,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    url = payload.url
    secret = payload.secret
    repo_id = payload.repo_id
    print("PROSAO")

    repo = (
        db.query(RepoConfig)
        .filter(RepoConfig.id == repo_id)
        .first()
    )
    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repository not found"
        )
    encrypted_secret = fernet.encrypt(secret.encode()).decode()

    webhook = Webhook(
        repo_id=repo.id,
        user_id=user.id,
        webhook_url=url,
        encoded_webhook_secret=encrypted_secret
    )
    db.add(webhook)
    db.commit()


@router.get("/api/webhooks")
async def get_webhooks(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    webhooks = (
        db.query(Webhook)
        .join(RepoConfig.users)
        .filter(User.id == user.id)
        .options(joinedload(Webhook.repo_config))
        .all()
    )

    return webhooks
