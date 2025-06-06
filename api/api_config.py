from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from api.api_users import get_db, get_current_user
from models.user_model import User
from models.repo_model import RepoConfig
from schemas.schema_repo import RepoConfigSchema
from pydantic import HttpUrl
import json
import os

CONFIG_FILE = "config"

router = APIRouter()


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


@router.put("/api/config/{config_id}")
async def update_config(
    config_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    config_data: RepoConfigSchema = Body(...),
):
    print(config_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    config = db.query(RepoConfig).filter(
        RepoConfig.id == config_id,
        RepoConfig.users.any(id=user.id)
    ).first()

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Config with id: {config_id} not found"
        )

    input_data = config_data.model_dump(mode="python")
    data = {}
    for key, value in input_data.items():
        if isinstance(value, HttpUrl):
            value = str(value)
        if (new_val := getattr(config, key)) != value:
            data[key] = value
        else:
            data[key] = new_val

    for key in RepoConfigSchema.model_fields.keys():
        if key not in data:
            data[key] = getattr(config, key)

    for key, value in data.items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)

    return config


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


@router.post("/api/config")
async def config_repo(
    config_data: RepoConfigSchema,
    user: User = Depends(get_current_user),
    db=Depends(get_db)
):
    from helper.data import encrypt_data

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not identify user."
        )

    repo_url = str(config_data.repo_url)
    if not repo_url.startswith("https://"):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repo URL must start with 'https://'."
        )
    valid_domains = ["github.com", "gitlab.com", "bitbucket.org"]
    if not any(domain in repo_url for domain in valid_domains):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Repo URL must be from a valid domain: github.com, " +
                "gitlab.com, or bitbucket.org."
            )
        )
    if repo_url.endswith(".com"):
        repo_url = repo_url[:-4]
        repo_url += ".git"
    if not repo_url.endswith(".git"):
        repo_url += ".git"
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

    if config_data.git_ssh_private_key_encrypted:
        config_data.git_ssh_private_key_encrypted = encrypt_data(
            config_data.git_ssh_private_key_encrypted
        )
    if config_data.git_ssh_key_passphrase_encrypted:
        config_data.git_ssh_key_passphrase_encrypted = encrypt_data(
            config_data.git_ssh_key_passphrase_encrypted
        )
    for key, value in config_data.model_dump(mode="python").items():
        print(f"{key}: {value}")
    try:
        config = RepoConfig(
            repo_url=repo_url,
            main_branch=config_data.main_branch,
            platform=config_data.platform,
            installation_id=config_data.installation_id,
            use_ssh_for_clone=config_data.use_ssh_for_clone,
            git_ssh_private_key_encrypted=config_data.git_ssh_private_key_encrypted,
            git_ssh_key_passphrase_encrypted=config_data.git_ssh_key_passphrase_encrypted,
            git_ssh_host_key=config_data.git_ssh_host_key,
            SSH_host=config_data.SSH_host,
            SSH_port=config_data.SSH_port,
            SSH_username=config_data.SSH_username,
            SSH_key_path=config_data.SSH_key_path,
            SSH_key_passphrase=config_data.SSH_key_passphrase,
            SSH_for_deploy=config_data.SSH_for_deploy
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
        print(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: An unexpected error has occured: '{e}'"
        )


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
