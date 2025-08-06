# Changelog

## Unreleased

### Added

-   Initial CI workflow with linting, type-checking, testing, and security scans.
-   Multi-stage Dockerfiles for `api`, `worker`, `checkout`, `monitor`, and `frontend` services.
-   `docker-compose.dev.yml` and `docker-compose.prod.yml` for environment-specific configurations.
-   Prometheus metrics for the `api` service.
-   Pre-commit hooks for `black`, `ruff`, `isort`, and `commitizen`.
-   Mermaid diagram in `docs/architecture.md`.
-   "First 10 Minutes" onboarding guide in `docs/first-10-minutes.md`.

### Changed

-   Pinned versions in `services/api/requirements.txt` and `worker/requirements.txt`.
-   Updated `docker-compose.yml` to use `extends` for environment-specific configurations.
-   Updated `infra/prometheus.yml` to scrape `api` service metrics on port `8001`.

### Removed

-   Environment variables and commands from `docker-compose.yml` that are now in `docker-compose.dev.yml` or `docker-compose.prod.yml`.
-   Development-only volumes from `docker-compose.yml`.
-   `nginx` service and `profiles` section from `docker-compose.yml`.
