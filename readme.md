# Mini CI-CD Pipeline
This project is a minimal CI/CD automation platform built with **FastAPI**. It allows users to configure their Git repositories, set up Docker-based build processes, and automate testing and build workflows via webhook triggers.
As of now it is only suitable for PCs and not for mobile devices.
## Technologies used:
- FastAPI
- SQLAlchemy
- PostgreSQL
- Docker
- Alembic
- Pydantic
- Uvicorn

## About this project
- This project allows users to register/login to the system
- After logging in, users can access their **dashboard** to:
    - Add git repositories (such as GitHub, GitLab, BitBucket)
    - Configure Docker Hub username
    - Register webhook for automated actions

Once the webhook is configured on a repository (with signature):
1. A **push** on specified branch triggers the webhook
2. The platform:
    - Clones the repository
    - Looks for a 'dockerfile' or CI configuration (for example '*.yml')
    - Attempts to build a Docker image
    - If Docker image contains malicious content or potential hazard it stops the build
    - Runs tests (If defined in dockerfile/CI file)
    - Returns status of the pipeline

**Deployment is currently disabled** due to security concerns. Future support for remote deploy is planned.

## How to Use

1. **Register/Login** through the API.
2. Navigate to your **dashboard**.
3. Add a Git repository with a valid `Dockerfile`.
4. Provide your **Docker Hub username**.
5. Set up a **webhook** in your Git provider pointing to:
6. Push the code to your repository.
7. The system will:
- Pull the repo
- Try to build the Docker image
- Run any defined tests
- Return status (success/failure)

## Example Webhook workflow

```mermaid
sequenceDiagram
 participant GitHub
 participant Webhook Endpoint
 participant CI Service

 GitHub->>Webhook Endpoint: Push event
 Webhook Endpoint->>CI Service: Clone repo, check Dockerfile
 CI Service->>CI Service: Build image, run tests
 CI Service-->>Webhook Endpoint: Send result
 ```

 ## Future plans
 - ✅ Add **Celery** for asynchronous job handling
 - Add support for **remote deployment to cloud or on-prem environments**
 - Responsive frontend
 - ✅? Implement docker sandbox
 - Fully develop ssh connection
