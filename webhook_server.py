import json
import os
import hmac
import hashlib
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import time
import logging

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from api.api_users import router as user_router
from api.api_main import router as main_router
from api.api_config import router as config_router
from api.api_pipeline import router as pipeline_router
from api.api_docker import router as docker_router

from api.api_users import get_db
from models.repo_model import RepoConfig

import uvicorn

from tasks import (
    process_push,
    handle_installation,
    handle_repos
)

load_dotenv()

webhook_app = FastAPI(version="0.4.0")

ip_attempts = {}
blacklist = {}

MAX_ATTEMPTS = 5
BLOCKTIME_SECONDS = 7200  # 2 sata
WINDOW = 60
bad_keywords = [
    "eval", "phpunit", "call_user_func", "think\\app", "base64",
    ".env", ".git", "index.php", "pearcmd", "containers/json",
    "owa", "geoserver", "logon.aspx"
]

bad_agents = ["python-requests", "curl", "wget", "nmap", "masscan"]


webhook_app.include_router(user_router, prefix="/auth", tags=["Auth"])
webhook_app.include_router(main_router, tags=["Main"])
webhook_app.include_router(docker_router, tags=["Docker"])
webhook_app.include_router(pipeline_router, tags=["Pipeline"])
webhook_app.include_router(config_router, tags=["RepoConfig", "Config"])

ORIGINS = os.getenv("ORIGINS")

webhook_app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],
    allow_origins=[ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_DIR = "ci_workspace"

GITHUB_APP_WEBHOOK_SECRET = os.getenv("GITHUB_APP_WEBHOOK_SECRET")
FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY")
if not FERNET_SECRET_KEY:
    raise RuntimeError("FERNET_SECRET_KEY is missing in .env")

fernet = Fernet(FERNET_SECRET_KEY.encode())


logging.basicConfig(
    filename="bot_firewall.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)


@webhook_app.middleware("http")
async def firewall_middleware(request: Request, call_next):
    ip = request.client.host
    path = request.url.path.lower()
    agent = request.headers.get("user-agent", "").lower()

    if ip in blacklist and time.time() - blacklist[ip] < BLOCKTIME_SECONDS:
        return JSONResponse(
            status_code=403,
            content={"detail": "Access denied (blacklisted IP)"}
        )

    is_malicious = (
        any(bad in path for bad in bad_keywords) or
        any(bot in agent for bot in bad_agents)
    )

    now = time.time()
    ip_attempts.setdefault(ip, [])
    ip_attempts[ip] = [ts for ts in ip_attempts[ip] if now - ts < WINDOW]

    if is_malicious:
        logging.info(f"Suspicious request from {ip} | Path: {path} | Agent: {agent}")
        ip_attempts[ip].append(now)

        if len(ip_attempts[ip]) >= MAX_ATTEMPTS:
            blacklist[ip] = now
            print(f"[FIREWALL] Blocked IP: {ip}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Malicious behavior detected"}
            )

    return await call_next(request)


@webhook_app.post("/webhook")
async def receive_webhook(request: Request, db=Depends(get_db)):
    print("Received Webhook")
    if not GITHUB_APP_WEBHOOK_SECRET:
        print("Webhook secret not defined")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not defined"
        )
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing signature")

    scheme, signature = signature_header.split("=", 1)
    if scheme != "sha256":
        raise HTTPException(status_code=400, detail="Unsupported signature scheme")
    print(signature_header)

    try:
        payload_bytes = await request.body()
        payload_string = payload_bytes.decode("utf-8")
        payload_json = json.loads(payload_string)

        expected_signature = hmac.new(
            GITHUB_APP_WEBHOOK_SECRET.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=403, detail="Invalid signature")

        print("Received payload:")

        event_type = request.headers.get("X-GitHub-Event")
        if event_type == "push":
            pushed_ref = payload_json.get("ref")
            commit_sha = payload_json.get("after")
            github_delivery_id = request.headers.get("X-GitHub-Delivery")
            repo_cloned_url = payload_json.get("repository", {}).get("clone_url")
            pushed_branch = pushed_ref.split("refs/heads/", 1)[1]

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
                initial_log_message = (
                    f"Webhook received for config ID {config.id}. "
                    f"Queuing pipeline for commit {commit_sha[:7]}..."
                )
                print(initial_log_message)

                process_push.delay(
                    config_id=config.id,
                    commit_sha=commit_sha,
                    github_delivery_id=github_delivery_id,
                    initial_logs=initial_log_message,
                    repo_url=str(config.repo_url),
                    main_branch=config.main_branch,
                    docker_username=config.docker_username
                )
                return {
                    "message": "Webhook processed. Pipeline task queued successfully."
                }
            else:
                return {"status": "Ignored, push does not match config"}
        elif event_type == "installation":
            installation_id = payload_json["installation"]["id"]
            handle_installation.delay(payload_json, installation_id)
            return {"status": "Installation event queued for processing"}

        elif event_type == "installation_repositories":
            installation_id = payload_json["installation"]["id"]
            handle_repos.delay(payload_json, installation_id)
            return {"status": "Installation repositories event queued for processing"}
        else:
            return {"message": f"Ignored event: {event_type}"}

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
    uvicorn.run(webhook_app, host="0.0.0.0", port=9000, log_level="info")
