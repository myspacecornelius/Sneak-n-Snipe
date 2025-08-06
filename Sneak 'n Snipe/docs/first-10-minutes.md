# First 10 Minutes: Onboarding Guide

Welcome to the Sneak 'n Snipe project! This guide will help you get started with the development environment in under 10 minutes.

## 1. Prerequisites

Before you begin, ensure you have the following installed:

-   **Docker Desktop**: Includes Docker Engine and Docker Compose. Download from [Docker's official website](https://www.docker.com/products/docker-desktop).
-   **Git**: For version control. Download from [Git's official website](https://git-scm.com/downloads).
-   **Python 3.11+**: While most services run in Docker, some local tooling might require Python. Download from [Python's official website](https://www.python.org/downloads/).
-   **Node.js 18+**: For the frontend development. Download from [Node.js official website](https://nodejs.org/en/download/).

## 2. Clone the Repository

First, clone the project repository to your local machine:

```bash
git clone https://github.com/your-username/Sneak-n-Snipe.git
cd Sneak-n-Snipe
```

## 3. Set up Pre-commit Hooks

We use pre-commit hooks to maintain code quality and consistency. Install them by running:

```bash
pip install pre-commit
pre-commit install
```

This will set up hooks that run automatically before each commit, checking for formatting, linting, and other issues.

## 4. Start the Development Environment

Our entire development environment is containerized using Docker Compose. To spin up all services (frontend, API, databases, etc.), simply run:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This command will:

-   Build the Docker images for all services.
-   Start all containers in detached mode.
-   Mount local volumes for live code reloading during development.

## 5. Access the Applications

Once the containers are up and running (this might take a few minutes the first time):

-   **Frontend**: Open your web browser and navigate to `http://localhost:5173`.
-   **API Documentation (Swagger UI)**: Access the API documentation at `http://localhost:8000/docs`.
-   **Grafana**: Access the Grafana dashboard at `http://localhost:3000` (default credentials: `admin`/`admin`).
-   **Prometheus**: Access the Prometheus UI at `http://localhost:9090`.

## 6. Running Tests

To run the backend tests, you can execute them within the `api` service container:

```bash
docker compose exec api pytest
```

## 7. Stopping the Environment

When you're done developing, stop all services with:

```bash
docker compose down
```

This will stop and remove all containers, networks, and volumes created by `docker compose up`.

That's it! You're now ready to start contributing to Sneak 'n Snipe. If you encounter any issues, please refer to the `README.md` or reach out to the team.
