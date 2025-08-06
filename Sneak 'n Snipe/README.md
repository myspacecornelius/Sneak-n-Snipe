# Sneak 'n Snipe

Welcome to Sneak 'n Snipe, a high-performance bot for copping limited-edition sneakers.

## Overview

This repository contains the full source code for the Sneak 'n Snipe bot, including:

- **Frontend**: A React-based UI for managing tasks, profiles, and proxies.
- **Backend**: A suite of Python microservices for handling API requests, monitoring sneaker releases, and processing checkouts.
- **Infrastructure**: Docker Compose, Prometheus, and Grafana configurations for local development and monitoring.

## Getting Started

To get started, you'll need to have Docker and Docker Compose installed. Then, you can run the following command to start the entire stack:

```
docker-compose up -d
```

This will start all of the services, including the frontend, backend, and databases. You can then access the frontend at `http://localhost:3000`.

## Documentation

For more detailed information about the architecture and how to contribute, please see the [documentation](docs/architecture.md).
