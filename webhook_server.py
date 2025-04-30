import json
import os
import subprocess

from fastapi import FastAPI, HTTPException, Request, status

from models.repo_model import RepoConfig

import uvicorn

webhook_app = FastAPI()

CONFIG_FILE = "config.json"
WORKSPACE_DIR = "ci_workspace"


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
            print("Error: git clone failed")
            return False

    print(
        f"Code for repo {repo_url_str} on branch {config.main_branch}",
        f" is updated in {repo_path}"
    )


def save_config(config: RepoConfig):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config.model_dump(), f, indent=4)
        print(f"Config saved in {CONFIG_FILE}.")
    except IOError as e:
        print(f"Error: cannot save config in {CONFIG_FILE}. Message: {e}")


def load_config() -> RepoConfig | None:
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "w") as f:
            data = json.load(f)
            config = RepoConfig(**data)
            print(f"Configuration loaded from {CONFIG_FILE}")
            return config
    except (IOError, json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Error: cannot load config from {CONFIG_FILE}. Message: {e}")
        return None


@webhook_app.post("/config")
async def config_repo(config_data: RepoConfig):
    print(
        f"Repo url: {config_data.repo_url}",
        f"Main branch: {config_data.main_branch}"
    )
    save_config(config_data)
    return {
        "message": "Config saved successfuly!",
        "config": config_data
    }


@webhook_app.get("/config")
async def get_config():
    config = load_config()
    if config:
        return config
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a config file saved yet!"
        )


@webhook_app.post("/webhook")
async def receive_webhook(request: Request):
    print("Received Webhook")

    try:
        payload_bytes = await request.body()
        payload_string = payload_bytes.decode("utf-8")
        payload_json = json.loads(payload_string)

        config = load_config()

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
        except KeyError as e:
            print(f"Missing key in payload. Key: '{e}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing key in payload. Key: '{e}'"
            )

        expected_ref = f"refs/heads/{config.main_branch}"
        config_repo_url = str(payload_json["ref"])

        if pushed_ref == expected_ref and repo_cloned_url == config_repo_url:
            print(f"Detected push on {config.main_branch} {config.repo_url}.")
            print("Pulling the code.")

            success = handle_git_update(config)

            if success:
                print("Git action successfull")
                return {
                    "message": "Webhook processed, code updated"
                }
            else:
                print("Git action unsucessfull")
                raise HTTPException(
                    status_code=status.HTTP_500_BAD_REQUEST,
                    detail="Git action unsucessfull"
                )
        else:
            print("Ignoring webhook, does not apply to configured repo")
            return {
                "status": "Webhook ignored, does not apply to configured repo"
            }

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
