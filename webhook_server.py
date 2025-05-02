import json
import os
import subprocess
import hmac
import hashlib
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.security import OAuth2PasswordBearer

from api.api_users import router as user_router
from api.api_users import get_current_user, get_db
from models.user_model import User
from models.repo_model import RepoConfig
from schemas.schema_repo import RepoConfigSchema

import uvicorn

load_dotenv()


webhook_app = FastAPI()

webhook_app.include_router(user_router, prefix="/auth", tags=["Auth"])

CONFIG_FILE = "config"
WORKSPACE_DIR = "ci_workspace"

GITHUB_SECRET_HEADER = os.getenv("GITHUB_SECRET_HEADER")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def build_deploy_docker(repo_dir: str, image_name: str, container_name: str) -> bool:
    try:
        build_date = datetime.utcnow().isoformat()
        commit_sha = subprocess.getoutput("git rev-parse --short HEAD")

        print("Building Multiplatform Docker image...")
        if not run_command([
            "docker", "buildx", "build",
            "--platform", "linux/amd64,linux/arm64",
            "-t", image_name,
            "--build-arg", f"BUILD_DATE={build_date}",
            "--build-arg", f"COMMIT_SHA={commit_sha}",
            "--label", f"org.opencontainers.image.created={build_date}",
            "--label", f"org.opencontainers.image.revision={commit_sha}",
            ".", "--push"
        ], working_dir=repo_dir):
            raise RuntimeError("Docker multi-platform build failed")

        print("Building Local Docker image...")
        if not run_command([
            "docker", "buildx", "build",
            "--platform", "linux/amd64",
            "-t", f"{image_name}-test",
            ".", "--load"
        ], working_dir=repo_dir):
            raise RuntimeError("Local test image build failed")

        print("Running tests inside temporary container...")
        test_command = ["pytest"]
        if not run_command(
            ["docker", "run", "--rm", f"{image_name}-test"] + test_command
        ):
            raise RuntimeError("Tests failed inside container")

        print("Cleaning up old container...")
        run_command(["docker", "rm", "-f", f"{container_name}-test"])

        print("Running new container in background...")
        if not run_command([
            "docker", "run", "-d", "--name", container_name,
            "-p", "8080:80", f"{image_name}-test"
        ]):
            raise RuntimeError("Docker run failed")

        print("Build, test and deploy successful!")
        return True

    except Exception as e:
        print(f"Error during build/deploy: {e}")
        return False


def run_command(command: list[str], working_dir: str | None = None) -> bool:
    print(
        f"Running command {' '.join(command)}",
        f" in directory: {working_dir if working_dir else ''}"
    )
    try:
        result = subprocess.run(
            command, cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        print(f"Command run successfully (exit code {result.returncode}).")
        return True
    except FileNotFoundError:
        print(f"Error: command '{command[0]}' not found")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed (exit code {e.returncode}).")
        print("STDOUT:")
        print(e.stdout)
        print("STDERR:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Error: Unexpected error: {e}")
        return False


def handle_git_update(config: RepoConfig) -> bool:
    repo_path = os.path.join(WORKSPACE_DIR, "repo")
    if not os.path.exists(WORKSPACE_DIR):
        try:
            os.makedirs(WORKSPACE_DIR)
            print(f"Created directory: {WORKSPACE_DIR}")
        except OSError as e:
            print(f"Error: cannot create directory {WORKSPACE_DIR}: {e}")
            return False
    repo_url_str = str(config.repo_url)

    if os.path.exists(repo_path):
        print(f"Repo exists in {repo_path}. Trying git pull...")
        if not run_command(
            ["git", "checkout", config.main_branch],
            working_dir=repo_path
        ):
            print(f"Error: cannot switch to branch {config.main_branch}.")
            return False
        if not run_command(
            ["git", "pull", "origin", config.main_branch],
            working_dir=repo_path
        ):
            print("Error git pull didnt work")
            return False
    else:
        print(f"Repo doesn't exist in {repo_path}. Trying git clone")
        if not run_command(
            [
                "git", "clone", "--branch",
                config.main_branch,
                repo_url_str,
                repo_path
            ]
        ):
            print("Error: git clone failed.")
            return False

    print(
        f"Code for repo {repo_url_str} on branch {config.main_branch}",
        f" is updated in {repo_path}"
    )
    return True


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


@webhook_app.post("/config")
async def config_repo(
    config_data: RepoConfigSchema,
    user: User = Depends(get_current_user),
    db=Depends(get_db)
):
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


@webhook_app.get("/config")
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


@webhook_app.post("/webhook")
async def receive_webhook(request: Request, db=Depends(get_db)):
    print("Received Webhook")

    if not GITHUB_SECRET_HEADER:
        print("Webhook secret not defined")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not defined"
        )
    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        print("No signature header")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No signature header!"
        )

    try:
        payload_bytes = await request.body()
        payload_string = payload_bytes.decode("utf-8")
        payload_json = json.loads(payload_string)

        expected_signature = "sha256=" + hmac.new(
            key=GITHUB_SECRET_HEADER.encode(),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, signature_header):
            print("Invalid signature")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature error!"
            )

        print("Signature verified!")

        print("Received payload:")

        event_type = request.headers.get("X-GitHub-Event")
        if event_type != "push":
            print("Not a push event, ignoring...")
            return {
                "message": f"Ignored event. {event_type}"
            }

        try:
            pushed_ref = payload_json["ref"]
            repo_cloned_url = payload_json["repository"]["clone_url"]
            pushed_branch = pushed_ref.split("refs/heads/", 1)[1]
        except KeyError as e:
            print(f"Missing key in payload. Key: '{e}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing key in payload. Key: '{e}'"
            )

        config: RepoConfig | None = db.query(RepoConfig).filter(
            RepoConfig.repo_url == repo_cloned_url,
            RepoConfig.main_branch == pushed_branch
        ).first()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Config doesn't exist in database"
            )

        expected_ref = f"refs/heads/{config.main_branch}"
        config_repo_url = str(config.repo_url)

        if pushed_ref == expected_ref and repo_cloned_url == config_repo_url:
            print(f"Detected push on {config.main_branch} {config.repo_url}.")
            print("Pulling the code.")

            git_success = handle_git_update(config)

            if not git_success:
                print("Git action unsucessfull")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Git action unsucessfull!"
                )

            repo_path = os.path.join(WORKSPACE_DIR, "repo")
            image_name = f"ci-image-{config.main_branch}-{config.id}"
            container_name = f"ci-container-{config.main_branch}-{config.id}"

            deploy_success = build_deploy_docker(
                repo_dir=repo_path,
                image_name=image_name,
                container_name=container_name
            )
            if not deploy_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Docker build/deploy was unsuccessfull!"
                )

        else:
            print(f"'{pushed_ref}' vs '{expected_ref}' ({pushed_ref == expected_ref})")
            print(
                f"'{repo_cloned_url}' vs '{config_repo_url}'",
                f" ({repo_cloned_url == config_repo_url})"
            )
            return {"status": "Ignored does not match config"}

    except json.JSONDecodeError:
        print("Error, json cannot be parsed!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error, json cannot be parsed!")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error, an error occured {e}"
        )

if __name__ == "__main__":
    print("Starting webhook server!")
    uvicorn.run(webhook_app, host="127.0.0.1", port=9000, log_level="info")
