# SneakerSniper Optimization Plan

## Current State Analysis
- Frontend-only app using Google Gemini AI for command parsing
- Simulated monitors and checkout tasks
- No real backend infrastructure
- No actual bot functionality

## Optimization Steps

### 1. Project Restructure
First, we'll reorganize into the monorepo structure outlined in the spec:

```
sneakersniper/
├── frontend/          # Current React app (modified)
├── services/          # Python backend services
│   ├── api/          # FastAPI gateway
│   ├── monitor/      # SKU monitoring service
│   ├── checkout/     # Checkout engine
│   ├── proxy/        # Proxy management
│   └── captcha/      # CAPTCHA solving
├── worker/           # Celery workers
├── infra/            # Docker, K8s, Grafana
└── docs/             # Documentation
```

### 2. Remove External Dependencies
- Remove Google Gemini AI dependency
- Replace with internal command parser
- Move AI logic to backend API

### 3. Backend Services Implementation
Create Python services with:
- FastAPI for REST API
- Redis for task queue and caching
- PostgreSQL for persistent storage
- Celery for async task processing
- Prometheus for metrics

### 4. Frontend Updates
- Replace GenAI calls with REST API calls
- Add real-time WebSocket connections
- Implement proper state management
- Add authentication/session handling

### 5. Infrastructure Setup
- Docker Compose configuration
- Environment variable management
- Development vs production configs
- Monitoring and logging setup

## Implementation Priority
1. **Phase 1**: Basic API + Monitor Service
2. **Phase 2**: Checkout Engine + Proxy Manager
3. **Phase 3**: CAPTCHA Integration + Account Warmer
4. **Phase 4**: Telemetry + Production Hardening