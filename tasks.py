import os
import subprocess
from datetime import datetime, timezone
import traceback
import re
import tempfile

from sqlalchemy.orm import Session

from models.repo_model import RepoConfig
from models.pipeline_test_model import PipelineRuns, PipelineStatusEnum
from db import SessionLocal
from celery import Celery

from helper.data import decrypt_data

app = Celery(
    "tasks",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
)


def save_logs_to_file(run_id: int, logs: str):
    try:
        filename = f"pipeline_logs_{run_id}.txt"
        with open(filename, "w", encoding="UTF-8") as f:
            f.write(logs.strip())
        print(f"Logs for PipelineRun ID={run_id} saved to {filename}")
    except Exception as e:
        print(f"Failed to save logs for run {run_id}: {e}")


def run_command(
    command: list[str],
    working_dir: str | None = None,
    env: dict | None = None
) -> tuple[bool, str]:
    command_output = ""
    command_output += f"Running command {' '.join(command)}"
    command_output += f" in directory: {working_dir if working_dir else ''}\n"
    success = True
    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    try:
        result = subprocess.run(
            command, cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            env=process_env
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


def find_pipeline_file(repo_dir: str) -> tuple[str | None, str | None]:
    """
    Finds dockerfile or docker-compose file in the given repository dir.
    Returns a tuple of (path, type), where type is either "dockerfile" or "compose".
    """
    compose_names = ["docker-compose.yml", "docker-compose.yaml"]
    for name in compose_names:
        compose_path = os.path.join(repo_dir, name)
        if os.path.isfile(compose_path):
            print(f"Found docker-compose file: {compose_path}")
            return compose_path, "compose"

    dockerfile_names = [
        "Dockerfile", "dockerfile", "Dockerfile.dev",
        "Dockerfile.prod", "Dockerfile.test"
    ]
    for name in dockerfile_names:
        dockerfile_path = os.path.join(repo_dir, name)
        if os.path.isfile(dockerfile_path):
            print(f"Found Dockerfile: {dockerfile_path}")
            return dockerfile_path, "dockerfile"

    print(f"No Dockerfile or docker-compose.yml found in {repo_dir}")
    return None, None


def build_push_compose_services(
    repo_dir: str,
    compose_file_path: str,
    username: str,
    base_image_name: str,
    commit_sha: str,
    build_date: str,
    main_branch: str
) -> tuple[bool, str]:
    all_logs = ""
    all_logs += f"Starting Docker Compose build for {compose_file_path}\n"

    with open(compose_file_path, "r") as f:
        compose_content = f.read()
    if not is_compose_file_safe(compose_content):
        all_logs += "Docker Compose file is not safe\n"
        return False, all_logs

    success, build_log = run_command(
        ["docker-compose", "-f", compose_file_path, "build"],
        working_dir=repo_dir
    )
    all_logs += "\n--- Docker Compose Build Logs ---\n" + build_log
    if not success:
        all_logs += "Error: Docker Compose build failed.\n"
        return False, all_logs
    all_logs += "Docker Compose build completed successfully.\n"

    # Ovde uzimam imena servisa iz compose fajla
    try:
        result = subprocess.run(
            ["docker-compose", "-f", compose_file_path, "config", "--services"],
            capture_output=True, text=True, check=True, cwd=repo_dir
        )
        services = [s.strip() for s in result.stdout.splitlines() if s.strip()]

    except Exception as e:
        all_logs += f"\nError getting services from docker-compose: {e}"
        return False, all_logs

    all_logs += f"Found services: {', '.join(services)}\n"

    build_env = os.environ.copy()
    build_env["DOCKER_USERNAME"] = username

    default_tag = f"{main_branch}-{commit_sha[:7]}"
    build_env["IMAGE_TAG"] = default_tag

    all_logs += f"Using DOCKER_USERNAME={username} and IMAGE_TAG={default_tag}"
    all_logs += "(can be overridden by compose file)\n"

    success, build_log = run_command(
        ["docker-compose", "-f", compose_file_path, "build"],
        working_dir=repo_dir,
        env=build_env
    )
    all_logs += "\n--- Docker Compose Build Logs ---\n" + build_log

    if not success:
        all_logs += "\nError: Docker Compose build failed.\n"
        return False, all_logs

    all_logs += "\nDocker Compose build successful.\n"

    try:
        result = subprocess.run(
            ["docker-compose", "-f", compose_file_path, "config", "--images"],
            capture_output=True, text=True, check=True, cwd=repo_dir, env=build_env
        )
        image_names_from_compose = [
            img.strip() for img in result.stdout.splitlines()
            if img.strip()
        ]
        all_logs += "\nImages listed by 'docker-compose config --images':"
        all_logs += f" {', '.join(image_names_from_compose)}\n"
    except Exception as e:
        all_logs += "\nError getting image names from"
        all_logs += f" 'docker-compose config --images': {e}\n"
        all_logs += "This might happen if services do not have an"
        all_logs += "'image' or 'build' directive properly set.\n"
        return False, all_logs
    if not image_names_from_compose:
        all_logs += "\nNo images found by 'docker-compose config --images'"
        all_logs += ". Nothing to push.\n"
        return True, all_logs

    all_logs += "\nAttempting to push images using 'docker-compose push'...\n"
    all_logs += "This relies on 'image:' directives in the compose file being correctly"
    all_logs += "formatted for a remote registry (e.g., 'username/imagename:tag').\n"

    success_push_all, push_all_log = run_command(
        ["docker-compose", "-f", compose_file_path, "push"],
        working_dir=repo_dir,
        env=build_env
    )
    all_logs += "\n--- Docker Compose Push All Logs ---\n" + push_all_log
    if not success_push_all:
        all_logs += "\nWarning: 'docker-compose push' (all services) reported an issue.\n"
        all_logs += "Please ensure image: directives in your docker-compose.yml are like"
        all_logs += "'${DOCKER_USERNAME}/myimage:${IMAGE_TAG}' and that you are logged"
        all_logs += "into the Docker registry.\n"
        return False, all_logs
    all_logs += "\nManually tagging and pushing images if necessary...\n"
    # push_failed_for_some = False
    # for image_name in image_names_from_compose:
    #     # npr: image_name moze biti "myproject" ili "myuser/myproject:latest"
    #     # Treba da osiguramo da je tagovano za pravog korisnika i sa pravim tagom
    #     target_image_name = ""
    #     image_parts = image_name.split('/')
    #     image_tag_parts = image_parts[-1].split(':')
    #     base_img_name_from_compose = image_tag_parts[0]
    #
    #     if len(image_parts) > 1 and image_parts[0] == username:
    #
    #         target_image_name = f"{username}/{base_img_name_from_compose}:{default_tag}"
    #     else:
    #         # Nema username, ili je pogresan, npr. imagename:tag or imagename
    #         # Koristi username iz CI konfiguracije.
    #         # base_image_name_from_compose je samo 'imagename' deo
    #         target_image_name = f"{username}/{base_img_name_from_compose}:{default_tag}"
    #
    #     if image_name != target_image_name:
    #         all_logs += f"Tagging '{image_name}' as '{target_image_name}'\n"
    #         tag_success, tag_log = run_command(
    #               ["docker", "tag", image_name, target_image_name]
    #         )
    #         all_logs += tag_log + "\n"
    #         if not tag_success:
    #           all_logs += f"Error tagging {image_name}. Skipping push for this image.\n"
    #             push_failed_for_some = True
    #             continue
    #     else:
    #         all_logs += f"Image '{image_name}' is already correctly"
    #         all_logs += "named/tagged for push.\n"
    #         target_image_name = image_name
    #
    #     all_logs += f"Pushing {target_image_name}...\n"
    #     push_success, individual_push_log = run_command(
    #           ["docker", "push", target_image_name]
    #      )
    #     all_logs += individual_push_log + "\n"
    #     if not push_success:
    #         all_logs += f"Error pushing {target_image_name}.\n"
    #         push_failed_for_some = True
    #
    # if push_failed_for_some:
    #     all_logs += "\nError: One or more images failed to push.\n"
    #     return False, all_logs #


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
                ).strftime("%Y-%m-%d %H:%M:%S UTC")
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


def handle_git_update(
    config_id: int,
    repo_url: str,
    main_branch: str,
    workspace_dir: str
) -> bool:
    repo_path = os.path.join(workspace_dir, f"{config_id}")
    if not os.path.exists(workspace_dir):
        try:
            os.makedirs(workspace_dir)
            print(f"Created directory: {workspace_dir}")
        except OSError as e:
            print(f"Error: cannot create directory {workspace_dir}: {e}")
            return False

    if os.path.exists(repo_path):
        print(f"Repo exists in {repo_path}. Trying git pull...")
        if not run_command(
            ["git", "checkout", main_branch],
            working_dir=repo_path
        ):
            print(f"Error: cannot switch to branch {main_branch}")
            return False
        if not run_command(
            ["git", "pull", "origin", main_branch],
            working_dir=repo_path
        ):
            print("Error git pull didnt work")
            return False
    else:
        print(f"Repo doesn't exist in {repo_path}. Trying git clone")
        if not run_command(
            [
                "git", "clone", "--branch",
                main_branch,
                repo_url,
                repo_path
            ]
        ):
            print("Error: git clone failed.")
            return False

    print(
        f"Code for repo {repo_url} on branch {main_branch}",
        f" is updated in {repo_path}"
    )
    return True


def is_compose_file_safe(compose_content: str) -> bool:
    if 'privileged: true' in compose_content:
        print("Warning: docker-compose file contains 'privileged: true'")
        return False
    return True


def is_dockerfile_safe(dockerfile_content: str) -> bool:
    banned_patterns = [
        'docker.sock',
        'privileged',
        'ADD http',
        'ADD https',
        'curl .*\\|',
        'wget .*\\|',
        'chmod 777',
        'chown root',
        '--cap-add',
    ]
    for pattern in banned_patterns:
        if re.search(pattern, dockerfile_content, re.IGNORECASE):
            return False
    return True


def find_dockerfile(repo_dir: str) -> str | None:
    possible_names = [
        "Dockerfile",
        "dockerfile",
        "Dockerfile.dev",
        "Dockerfile.prod",
        "Dockerfile.test"
    ]
    print(repo_dir)
    for name in possible_names:
        dockerfile_path = os.path.join(repo_dir, name)
        if os.path.isfile(dockerfile_path):
            return dockerfile_path

    return None


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
    dockerfile_loc = find_dockerfile(repo_dir)
    if dockerfile_loc is None:
        all_logs += "Docker image not found\n"
        return False, all_logs

    all_logs += f"Docker image found at {dockerfile_loc}\n"
    with open(dockerfile_loc, "r") as f:
        dockerfile = f.read()

    if not is_dockerfile_safe(dockerfile):
        all_logs += "Docker image is not safe\n"
        return False, all_logs

    all_logs += "Docker image is safe...\n"
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

    old_container_parts = container_name.split("-")
    old_id = int(old_container_parts[-1])-1
    old_container_name = "-".join(old_container_parts[:-1] + [str(old_id)])
    print("Stopping and removing existing container")
    _, rm_log = run_command([
        "docker", "rm", "-f", old_container_name
    ])
    all_logs += "\n--- Removing Container Logs ---\n"
    all_logs += rm_log + "\n"

    # print("Running tests inside temporary container...")
    # run_success, run_log = run_command([
    #     "docker", "run", "-d",
    #     "--name", container_name,
    #     "-p", "8080:80",
    #     f"{username}/{image_name}"
    # ])
    # all_logs += "\n--- Run container log---\n" + run_log + "\n"
    # if not run_success:
    #     print("Error: Failed to run Docker container")
    #     run_command(["docker", "rm", "-f", container_name])
    #     return False, all_logs
    # all_logs += f"Docker container '{container_name}' successfully started.\n"
    # all_logs += f"--- Docker Build & Deploy finished for image: {image_name} ---\n"
    all_logs += "Skipped deploy due to security reasons.\n"
    return True, all_logs


@app.task(name="tasks.process_push")
def process_push(
    config_id: int,
    commit_sha: str,
    github_delivery_id: str,
    initial_logs: str,
    repo_url: str,
    main_branch: str,
    docker_username: str
):
    db_task = SessionLocal()
    pipeline_id = None
    status_log = initial_logs
    WORKSPACE_DIR = "ci_workspace"
    ssh_key_path = None

    try:
        config = (
            db_task.query(RepoConfig)
            .filter(RepoConfig.id == config_id).first()
        )
        if not config:
            print(f"Config ID: {config_id} not found in Celery Task!")
            return
        pipeline_run = PipelineRuns(
            config_id=config_id,
            status=PipelineStatusEnum.PENDING,
            commit_sha=commit_sha,
            trigger_event_id=github_delivery_id,
            logs=status_log.strip()
        )
        db_task.add(pipeline_run)
        db_task.commit()
        db_task.refresh(pipeline_run)
        pipeline_id = pipeline_run.id
        print(f"Celery task started for PipelineRun ID={pipeline_id}")
        update_pipeline_status(
            db_task,
            pipeline_id,
            PipelineStatusEnum.RUNNING_GIT,
            "Starting Git operations..."
        )
        repo_path_celery = os.path.join(WORKSPACE_DIR, str(config_id))
        if not os.path.exists(WORKSPACE_DIR):
            try:
                os.makedirs(WORKSPACE_DIR)
            except OSError as e:
                status_log += f"\nError: cannot create directory {WORKSPACE_DIR}: {e}"
                update_pipeline_status(
                    db_task,
                    pipeline_id,
                    PipelineStatusEnum.FAILED_GIT,
                    status_log
                )
                # save_logs_to_file(pipeline_id, status_log)
                db_task.close()
                return

        git_command_env = os.environ.copy()
        actual_repo_url = config.repo_url

        if config.use_ssh_for_clone and config.git_ssh_private_key_encrypted:
            status_log += "\nAttempting to use SSH for cloning...\n"
            try:
                private_key = decrypt_data(config.git_ssh_private_key_encrypted)

                if actual_repo_url.startswith("https://"):
                    actual_repo_url = actual_repo_url.replace(
                        "https://",
                        "git@"
                    ).replace(
                        "/",
                        ":",
                        1
                    )
                    if not actual_repo_url.endswith(".git"):
                        actual_repo_url += ".git"
                    status_log += f"\nConverted repo URL to SSH format: {actual_repo_url}"

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    mode='w',
                    prefix='ssh_key_'
                ) as tmp_key_file:
                    os.chmod(tmp_key_file.name, 0o600)
                    tmp_key_file.write(private_key)
                    ssh_key_path = tmp_key_file.name

                git_command_env["GIT_SSH_COMMAND"] = (
                    f"ssh -i {ssh_key_path} "
                    "-o IdentitiesOnly=yes "
                    "-o StrictHostKeyChecking=no "
                    "-o UserKnownHostsFile=/dev/null"
                )
                status_log += f"\nUsing temporary SSH key: {ssh_key_path}"
            except Exception as e:
                status_log += f"\nError setting up SSH key: {e}."
                status_log += "Falling back to default git auth.\n"

        git_success_flag = True
        git_log_output = ""
        if os.path.exists(repo_path_celery):
            success_checkout, log_checkout = run_command(
                ["git", "checkout", main_branch],
                working_dir=repo_path_celery,
                env=git_command_env
            )
            git_log_output += log_checkout + "\n"
            if not success_checkout:
                git_success_flag = False
            else:
                success_pull, log_pull = run_command(
                    ["git", "pull", "origin", main_branch],
                    working_dir=repo_path_celery,
                    env=git_command_env
                )
                git_log_output += log_pull
                if not success_pull:
                    git_success_flag = False
        else:
            success_clone, log_clone = run_command(
                [
                    "git",
                    "clone",
                    "--branch",
                    main_branch,
                    actual_repo_url,
                    repo_path_celery
                ],
                env=git_command_env
            )
            git_log_output += log_clone
            if not success_clone:
                git_success_flag = False

        status_log += "\n--- Git Logs ---\n" + git_log_output
        if not git_success_flag:
            update_pipeline_status(
                db_task,
                pipeline_id,
                PipelineStatusEnum.FAILED_GIT,
                status_log
            )
            # save_logs_to_file(pipeline_id, status_log)
            db_task.close()
            return
        update_pipeline_status(
            db_task,
            pipeline_id,
            PipelineStatusEnum.RUNNING_DOCKER_BUILD,
            "Git operations successful. Starting Docker build..."
        )
        pipeline_file_path, pipeline_file_type = find_pipeline_file(repo_path_celery)
        if not pipeline_file_path:
            status_log += "No dockerfile or dockercompose file found in the repository.\n"
            update_pipeline_status(
                db_task,
                pipeline_id,
                PipelineStatusEnum.FAILED_DOCKER_BUILD,
                status_log
            )
            db_task.close()
            return
        all_deploy_logs = ""
        build_date = datetime.utcnow().isoformat()
        try:
            commit_sha_short = subprocess.getoutput(
                f"git -C {repo_path_celery} rev-parse --short HEAD"
            ).strip()
        except Exception:
            commit_sha_short = "Unknown"

        current_docker_username = config.docker_username
        if not current_docker_username:
            error_msg = "Docker username not configured for this repository."
            status_log += f"\n{error_msg}\n"
            update_pipeline_status(
                db_task,
                pipeline_id,
                PipelineStatusEnum.FAILED_DOCKER_BUILD,
                error_msg
            )
            return

        if (pipeline_file_type == "dockerfile"):
            all_deploy_logs += f"Docker image found at {pipeline_file_path}\n"
            try:
                with open(pipeline_file_path, "r", encoding="UTF-8") as f:
                    dockerfile_content = f.read()
            except Exception as e:
                error_msg = f"Error reading Dockerfile {pipeline_file_path}: {e}"
                status_log += f"\n{error_msg}\n"
                update_pipeline_status(
                    db_task,
                    pipeline_id,
                    PipelineStatusEnum.FAILED_DOCKER_BUILD,
                    error_msg
                )
                return
            if not is_dockerfile_safe(dockerfile_content):
                all_deploy_logs += "Dockerfile is not safe\n"
                update_pipeline_status(
                    db_task,
                    pipeline_id,
                    PipelineStatusEnum.FAILED_DOCKER_BUILD,
                    status_log + "\n" + all_deploy_logs
                )
                return
            all_deploy_logs += "Dockerfile is safe...\n"
            repo_name_part = config.repo_url.split('/')[-1].replace('.git', '')
            safe_branch_name = main_branch.replace('/', '-')
            generated_image_name = f"ci-{repo_name_part}-{safe_branch_name}-"
            generated_image_name += f"{config_id}-{commit_sha_short}"
            generated_container_name = f"ci-container-{config_id}-{commit_sha_short}"
            all_deploy_logs += "Generated image name:"
            all_deploy_logs += f" {current_docker_username}/{generated_image_name}\n"
            build_success, build_log_output = build_deploy_docker(
                repo_dir=repo_path_celery,
                image_name=generated_image_name,
                container_name=generated_container_name,
                username=docker_username
            )
            all_deploy_logs += build_log_output
        elif (pipeline_file_type == "compose"):
            update_pipeline_status(
                db_task,
                pipeline_id,
                PipelineStatusEnum.RUNNING_DOCKER_BUILD,
                "Starting Docker Compose operations..."
            )
            build_success, compose_log_output = build_push_compose_services(
                repo_dir=repo_path_celery,
                compose_file_path=pipeline_file_path,
                username=current_docker_username,
                commit_sha=commit_sha_short,
                build_date=build_date,
                main_branch=main_branch
            )
            all_deploy_logs += compose_log_output

        status_log += "\n--- Docker Operations Logs ---\n" + all_deploy_logs

        if not build_success:
            update_pipeline_status(
                db_task,
                pipeline_id,
                PipelineStatusEnum.FAILED_DOCKER_BUILD,
                status_log
            )
            return

        status_log += "\nSkipped deploy due to security reasons (in Celery task).\n"
        update_pipeline_status(
            db_task,
            pipeline_id,
            PipelineStatusEnum.SUCCESS,
            "Pipeline finished successfully."
        )
        # TODO Implementirati notifikacije korisniku o uspehu

    except Exception as e:
        tb_str = traceback.format_exc()
        error_message = (
            "Unhandled exception in Celery task for PipelineRun" +
            f"ID={pipeline_id}: {e}\n{tb_str}"
        )
        print(error_message)
        status_log += f"\n--- ERROR ---\n{error_message}"
        if pipeline_id:
            update_pipeline_status(
                db_task,
                pipeline_id,
                PipelineStatusEnum.UNKNOWN,
                status_log
            )
            # save_logs_to_file(pipeline_id, status_log)
    finally:
        if ssh_key_path and os.path.exists(ssh_key_path):
            os.remove(ssh_key_path)
            print(f"Removed temporary SSH key: {ssh_key_path}")
        if pipeline_id:
            final_run = (
                db_task.query(PipelineRuns).
                filter(PipelineRuns.id == pipeline_id).
                first()
            )
            if final_run and final_run.logs:
                save_logs_to_file(pipeline_id, final_run.logs)
        db_task.close()


@app.task(name="tasks.handle_installation")
def handle_installation(payload_json: dict, installation_id: int):
    db_task = SessionLocal()
    try:
        repositories = payload_json.get("repositories", [])
        for repo in repositories:
            repo_url = f"https://github.com/{repo['full_name']}.git"
            config = (
                db_task.query(RepoConfig).
                filter(RepoConfig.repo_url == repo_url).
                first()
            )
            if config:
                config.installation_id = installation_id
            else:
                new_config = RepoConfig(
                    repo_url=repo_url,
                    main_branch="main",
                    installation_id=installation_id,
                    SSH_for_deploy=False
                )
                db_task.add(new_config)
        db_task.commit()
        print(
            "Celery task: Installation info saved for installation ID ",
            f"{installation_id}"
        )
    except Exception as e:
        db_task.rollback()
        print(f"Error in Celery task handle_installation_event_task: {e}")
    finally:
        db_task.close()


@app.task(name="tasks.handle_repos")
def handle_repos(payload_json: dict, installation_id: int):
    db_task = SessionLocal()
    try:
        repos_added = payload_json.get("repositories_added", [])
        for repo in repos_added:
            repo_url = repo.get("clone_url")
            if not repo_url and "full_name" in repo:
                repo_url = f"https://github.com/{repo['full_name']}.git"

            if not repo_url:
                print(f"Skipping repo, no clone_url or full_name: {repo}")
                continue

            config = (
                db_task.query(RepoConfig)
                .filter(RepoConfig.repo_url == repo_url)
                .first()
            )
            if config:
                config.installation_id = installation_id
            else:
                new_config = RepoConfig(
                    repo_url=repo_url,
                    main_branch="main",
                    installation_id=installation_id,
                    SSH_for_deploy=False
                )
                db_task.add(new_config)
        db_task.commit()
        print(
            "Celery task: Repositories added to installation ID",
            f"{installation_id}"
        )
    except Exception as e:
        db_task.rollback()
        print(f"Error in Celery task handle_installation_repositories_event_task: {e}")
    finally:
        db_task.close()
