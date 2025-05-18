import json
import asyncio
import os
import subprocess
import hmac
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv
import traceback
from cryptography.fernet import Fernet

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.api_users import router as user_router
from api.api_main import router as main_router
from api.api_config import router as config_router
from api.api_pipeline import router as pipeline_router
from api.api_docker import router as docker_router

from api.api_users import get_db
from models.repo_model import RepoConfig, Webhook
from models.pipeline_test_model import PipelineRuns, PipelineStatusEnum

import uvicorn

load_dotenv()


webhook_app = FastAPI(version="0.3.0")

webhook_app.include_router(user_router, prefix="/auth", tags=["Auth"])
webhook_app.include_router(main_router, tags=["Main"])
webhook_app.include_router(docker_router, tags=["Docker"])
webhook_app.include_router(pipeline_router, tags=["Pipeline"])
webhook_app.include_router(config_router, tags=["RepoConfig", "Config"])

webhook_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_DIR = "ci_workspace"

GITHUB_SECRET_HEADER = os.getenv("GITHUB_SECRET_HEADER")
FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY")
if not FERNET_SECRET_KEY:
    raise RuntimeError("FERNET_SECRET_KEY is missing in .env")

fernet = Fernet(FERNET_SECRET_KEY.encode())



def verify_signature(encrypted_secret: str, payload: bytes, signature_header: str) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    received_sig = signature_header.split("=")[1]

    try:
        secret = fernet.decrypt(encrypted_secret.encode()).decode()
    except Exception:
        return False

    expected_sig = hmac.new(
        key=secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(received_sig, expected_sig)


def save_logs_to_file(run_id: int, logs: str):
    try:
        filename = f"pipeline_logs_{run_id}.txt"
        with open(filename, "w", encoding="UTF-8") as f:
            f.write(logs.strip())
        print(f"Logs for PipelineRun ID={run_id} saved to {filename}")
    except Exception as e:
        print(f"Failed to save logs for run {run_id}: {e}")


def run_command(command: list[str], working_dir: str | None = None) -> bool:
    command_output = ""
    command_output += f"Running command {' '.join(command)}"
    command_output += f" in directory: {working_dir if working_dir else ''}\n"
    success = True

    try:
        result = subprocess.run(
            command, cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        stdout_log = result.stdout.strip()
        stderr_log = result.stderr.strip()

        if stdout_log:
            command_output += f"--- STDOUT ---\n{stdout_log}\n"
        if stderr_log:
            command_output += f"--- STDERR ---\n{stderr_log}\n"
        if result.returncode != 0:
            command_output += f"Command failed (exit code {result.returncode}).\n"
            success = False
        else:
            command_output += "Command successfully executed"
            command_output += f" (exit code {result.returncode}).\n"
    except FileNotFoundError:
        print(f"Error: command '{command[0]}' not found")
        command_output += f"Error: command '{command[0]}' not found. "
        command_output += "Is tool installed or inside PATH?"
        success = False
    except subprocess.CalledProcessError as e:
        command_output += f"Error: command failed (exit code {e.returncode}).\n"
        stdout_log = e.stdout.strip() if e.stdout else ""
        stderr_log = e.stderr.strip() if e.stderr else ""
        if stdout_log:
            command_output += f"--- STDOUT ---\n{stdout_log}\n"
        if stderr_log:
            command_output += f"--- STDERR ---\n{stderr_log}\n"
        success = False
    except Exception as e:
        print(f"Error: Unexpected error: {e}")
        command_output += f"Error: Unexpected error running command: {e}\n"
        command_output += traceback.format_exc() + "\n"
        success = False
    print(f"Command {'succeeded' if success else 'failed'}.")
    return success, command_output.strip()


def build_deploy_docker(
        repo_dir: str,
        image_name: str,
        container_name: str,
        username: str) -> tuple[bool, str]:
    all_logs = ""
    build_date = datetime.utcnow().isoformat()
    try:
        commit_sha = subprocess.getoutput("git rev-parse --short HEAD")
    except Exception:
        commit_sha = "Unknown"

    all_logs += f"Starting Build and Deploy for {image_name}\n"
    all_logs += "Target platforms: linux/amd64, linux/arm64\n"
    all_logs += f"Commit: {commit_sha}\nBuild date: {build_date}\n"

    all_logs += "Building Docker image...\n"
    print("Building Multiplatform Docker image...")
    success, build_log = run_command([
        "docker", "buildx", "build",
        "--platform", "linux/amd64,linux/arm64",
        "-t", f"{username}/{image_name}",
        "--build-arg", f"BUILD_DATE={build_date}",
        "--build-arg", f"COMMIT_SHA={commit_sha}",
        "--label", f"org.opencontainers.image.created={build_date}",
        "--label", f"org.opencontainers.image.revision={commit_sha}",
        ".", "--push"
    ], working_dir=repo_dir)
    all_logs += build_log

    if not success:
        print("Error: Docker build failed. Tests or linting might have failed")
        all_logs += "Error: Docker build failed.\n"
        return False, all_logs

    # print("Building Local Docker image...")
    # if not run_command([
    #     "docker", "buildx", "build",
    #     "--platform", "linux/amd64",
    #     "-t", f"{image_name}-test",
    #     ".", "--load"
    # ], working_dir=repo_dir):
    #     raise RuntimeError("Local test image build failed")

    old_container_parts = container_name.split("-")
    old_id = int(old_container_parts[-1])-1
    old_container_name = "-".join(old_container_parts[:-1] + [str(old_id)])
    print("Stopping and removing existing container")
    _, rm_log = run_command([
        "docker", "rm", "-f", old_container_name
    ])
    all_logs += "\n--- Removing Container Logs ---\n"
    all_logs += rm_log + "\n"

    print("Running tests inside temporary container...")
    run_success, run_log = run_command([
        "docker", "run", "-d",
        "--name", container_name,
        "-p", "8080:80",
        f"{username}/{image_name}"
    ])
    all_logs += "\n--- Run container log---\n" + run_log + "\n"
    if not run_success:
        print("Error: Failed to run Docker container")
        run_command(["docker", "rm", "-f", container_name])
        return False, all_logs
    all_logs += f"Docker container '{container_name}' successfully started.\n"
    all_logs += f"--- Docker Build & Deploy finished for image: {image_name} ---\n"
    return True, all_logs


def update_pipeline_status(
    db: Session,
    run_id: int,
    status: PipelineStatusEnum,
    logs_to_append: str | None = None
):
    try:
        pipeline_run = db.query(PipelineRuns).filter(PipelineRuns.id == run_id).first()
        if pipeline_run:
            pipeline_run.status = status
            is_final_status = status in [
                PipelineStatusEnum.SUCCESS,
                PipelineStatusEnum.FAILED_GIT,
                PipelineStatusEnum.FAILED_DOCKER_BUILD,
                PipelineStatusEnum.FAILED_DOCKER_DEPLOY,
                PipelineStatusEnum.UNKNOWN
            ]
            if is_final_status and not pipeline_run.end_time:
                pipeline_run.end_time = datetime.now(tz=timezone.utc)

            if logs_to_append:
                timestamp = datetime.now(
                    tz=timezone.utc
                ).strftime('%Y-%m-%d %H:%M:%S UTC')
                new_log_entry = (
                    f"\n--- {timestamp} ---\n{logs_to_append.strip()}\n"
                )
                pipeline_run.logs = (
                    pipeline_run.logs + new_log_entry
                    if pipeline_run.logs
                    else new_log_entry.strip()
                )
                max_log_length = 20000
                if len(pipeline_run.logs) > max_log_length:
                    pipeline_run.logs = (
                        "... (logs truncated)\n"
                        + pipeline_run.logs[-max_log_length:]
                    )

            db.commit()
            print(f"PipelineRun ID={run_id} status updated to {status.name}")
        else:
            print(f"ERROR: PipelineRun with ID={run_id} not found for status update.")
    except Exception as e:
        db.rollback()
        print(f"ERROR updating status for PipelineRun ID={run_id}: {e}")
        traceback.print_exc()


def handle_git_update(config: RepoConfig) -> bool:
    repo_path = os.path.join(WORKSPACE_DIR, f"{config.id}")
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


@webhook_app.post("/webhook")
async def receive_webhook(request: Request, db=Depends(get_db)):
    print("Received Webhook")
    pipeline_id: int | None = None
    status_log = ""
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
        pushed_ref = payload_json.get("ref")
        commit_sha = payload_json.get("after")
        github_delivery_id = request.headers.get("X-GitHub-Delivery")
        repo_cloned_url = payload_json.get("repository", {}).get("clone_url")
        pushed_branch = pushed_ref.split("refs/heads/", 1)[1]

        config: RepoConfig | None = db.query(RepoConfig).filter(
            RepoConfig.repo_url == repo_cloned_url,
            RepoConfig.main_branch == pushed_branch
        ).first()

        webhook = (
            db.query(Webhook)
            .filter(
                Webhook.repo_id == config.id,
            ).first()
        )
        
        print(expected_signature)
        print(signature_header)
        print(webhook.encoded_webhook_secret)

        # if not hmac.compare_digest(expected_signature, signature_header):
        #     print("Invalid signature")
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Invalid signature error!"
        #     )

        if verify_signature(webhook.encoded_webhook_secret, payload_bytes, signature_header):
            print("Signature verified!")
        else:
            print("Invalid signature")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature error!"
            )


        print("Received payload:")

        event_type = request.headers.get("X-GitHub-Event")
        if event_type != "push":
            print("Not a push event, ignoring...")
            return {
                "message": f"Ignored event. {event_type}"
            }

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
            status_log += f"Found matching config {config.id}."
            status_log += f" Starting pipeline for commit {commit_sha[:7]}...\n"

            pipeline_run = PipelineRuns(
                config_id=config.id,
                status=PipelineStatusEnum.PENDING,
                commit_sha=commit_sha,
                trigger_event_id=github_delivery_id,
                logs=status_log.strip()
            )
            db.add(pipeline_run)
            db.commit()
            db.refresh(pipeline_run)
            pipeline_id = pipeline_run.id
            git_success = await asyncio.to_thread(handle_git_update, config)
            if not git_success:
                print("Git action unsucessfull")
                update_pipeline_status(
                    db,
                    pipeline_id,
                    PipelineStatusEnum.FAILED_GIT,
                    status_log
                )
                save_logs_to_file(pipeline_run.id, status_log)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Git action unsucessfull!"
                )

            update_pipeline_status(
                db,
                pipeline_id,
                PipelineStatusEnum.RUNNING_GIT,
                status_log
            )
            status_log = ""
            update_pipeline_status(
                db,
                pipeline_id,
                PipelineStatusEnum.RUNNING_DOCKER_BUILD
            )
            repo_path = os.path.join(WORKSPACE_DIR, "repo")
            image_name = f"ci-image-{config.main_branch}-{pipeline_id}"
            container_name = f"ci-container-{config.main_branch}-{pipeline_id}"

            deploy_success, deploy_logs = await asyncio.to_thread(
                build_deploy_docker,
                repo_path,
                image_name,
                container_name,
                config.docker_username
            )
            status_log += deploy_logs
            if not deploy_success:
                final_status = PipelineStatusEnum.FAILED_DOCKER_BUILD
                if (
                    "docker run" in deploy_logs.lower() and
                    "failed" in deploy_logs.lower()
                ):
                    final_status = PipelineStatusEnum.FAILED_DOCKER_DEPLOY
                update_pipeline_status(
                    db,
                    pipeline_id,
                    final_status,
                    status_log
                )
                save_logs_to_file(pipeline_run.id, status_log)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Docker build/deploy was unsuccessfull!"
                )

            update_pipeline_status(
                db,
                pipeline_id,
                PipelineStatusEnum.RUNNING_DOCKER_DEPLOY,
                status_log
            )
            update_pipeline_status(
                db,
                pipeline_id,
                PipelineStatusEnum.SUCCESS
            )
            save_logs_to_file(pipeline_run.id, status_log)
            return {
                "message": f"PipelineRun ID={pipeline_id} finished successfully." +
                f"App deployed as {container_name}."
            }

        else:
            print(f"'{pushed_ref}' vs '{expected_ref}' ({pushed_ref == expected_ref})")
            print(
                f"'{repo_cloned_url}' vs '{config_repo_url}'",
                f" ({repo_cloned_url == config_repo_url})"
            )
            save_logs_to_file(pipeline_run.id, status_log)
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
