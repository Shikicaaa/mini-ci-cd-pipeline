import Navbar from './Navbar';

const HomePage = () => {
    return (
        <div className="flex flex-col min-h-screen bg-gray-900 text-gray-100">
            <Navbar />
            <div className="flex-grow px-6 py-12 max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold mb-6">Mini CI-CD Pipeline</h1>
                <p className="mb-4">
                    This project is a minimal CI/CD automation platform built with <strong>FastAPI</strong>. It allows users to configure their Git repositories, set up Docker-based build processes, and automate testing and build workflows via webhook triggers. As of now it is only suitable for PCs and not for mobile devices.
                </p>

                <h2 className="text-2xl font-semibold mt-8 mb-2">Technologies used:</h2>
                <ul className="list-disc list-inside mb-4">
                    <li>FastAPI</li>
                    <li>SQLAlchemy</li>
                    <li>PostgreSQL</li>
                    <li>Docker</li>
                    <li>Alembic</li>
                    <li>Pydantic</li>
                    <li>Uvicorn</li>
                </ul>

                <h2 className="text-2xl font-semibold mt-8 mb-2">About this project</h2>
                <ul className="list-disc list-inside mb-4">
                    <li>Register/login to the system</li>
                    <li>Access dashboard to manage repositories and webhooks</li>
                    <li>Webhook triggers CI/CD workflow: clone, build, test</li>
                    <li>Detects malicious content in Docker builds</li>
                </ul>

                <p className="mb-4"><strong>Deployment is currently disabled</strong> due to security concerns. Future support for remote deploy is planned.</p>

                <h2 className="text-2xl font-semibold mt-8 mb-2">How to Use</h2>
                <ol className="list-decimal list-inside mb-4">
                    <li>Register/Login through the API</li>
                    <li>Navigate to your dashboard</li>
                    <li>Add a Git repository with a valid Dockerfile</li>
                    <li>Provide your Docker Hub username</li>
                    <li>Install my <a href='https://github.com/apps/mini-ci-cd-pipeline'>GitHub APP</a></li>
                    <li>Push the code to your repository</li>
                    <li>The system will build and test the image, and return status</li>
                </ol>

                <h2 className="text-2xl font-semibold mt-8 mb-2">Future plans</h2>
                <ul className="list-disc list-inside mb-4">
                    <li>Add <strong>Celery</strong> for asynchronous job handling</li>
                    <li>Add support for remote deployment to cloud/on-prem</li>
                    <li>Responsive frontend</li>
                    <li>Implement docker sandbox</li>
                </ul>
            </div>
        </div>
    );
};

export default HomePage;
