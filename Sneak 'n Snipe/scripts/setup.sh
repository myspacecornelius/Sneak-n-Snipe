#!/bin/bash

# SneakerSniper Bot Engine - Setup Script
# This script initializes the project structure and dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ASCII Art Banner
echo -e "${GREEN}"
cat << "EOF"
   ____                 _             ____       _                 
  / ___| _ __   ___  __| | ___  _ __ / ___| _ __ (_)_ __   ___ _ __ 
  \___ \| '_ \ / _ \/ _` |/ _ \| '__| \___ \| '_ \| | '_ \ / _ \ '__|
   ___) | | | |  __/ (_| |  __/| |     ___) | | | | | |_) |  __/ |   
  |____/|_| |_|\___|\__,_|\___||_|    |____/|_| |_|_| .__/ \___|_|   
                                                     |_|              
                        Bot Engine v2.0
EOF
echo -e "${NC}"

echo -e "${BLUE}Starting SneakerSniper setup...${NC}\n"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Node.js is not installed. Frontend hot-reload will not work.${NC}"
else
    echo -e "${GREEN}✓ Node.js found ($(node --version))${NC}"
fi

echo ""

# Create directory structure
echo -e "${YELLOW}Creating project structure...${NC}"

# Service directories
mkdir -p services/{api,monitor,checkout,proxy,captcha,warmer}
mkdir -p worker
mkdir -p frontend/{src,public}

# Infrastructure directories
mkdir -p infra/{grafana/{dashboards,datasources},nginx,alerts}
mkdir -p docs

echo -e "${GREEN}✓ Directory structure created${NC}"

# Copy Python requirements to service directories
echo -e "${YELLOW}Setting up Python services...${NC}"

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}Creating requirements.txt...${NC}"
    cat > requirements.txt << 'EOL'
# Core Dependencies
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
redis[hiredis]==5.0.1
pydantic==2.5.3
python-multipart==0.0.6

# Async Support
asyncio==3.4.3
aiofiles==23.2.1

# Database
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Task Queue
celery==5.3.4
flower==2.0.1

# Web Scraping & Automation
playwright==1.41.0
beautifulsoup4==4.12.3
lxml==5.1.0

# Monitoring & Metrics
prometheus-client==0.19.0

# Utilities
pyyaml==6.0.1
structlog==24.1.0
tenacity==8.2.3
python-dotenv==1.0.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.3
black==23.12.1
EOL
fi

# Copy requirements to each service
for service in api monitor checkout proxy captcha warmer; do
    cp requirements.txt services/$service/
    touch services/$service/__init__.py
done

cp requirements.txt worker/

echo -e "${GREEN}✓ Python services configured${NC}"

# Create service Dockerfiles
echo -e "${YELLOW}Creating Dockerfiles...${NC}"

# Create a base Dockerfile template for services
for service in monitor checkout proxy captcha warmer; do
    if [ ! -f "services/$service/Dockerfile" ]; then
        cat > services/$service/Dockerfile << 'EOL'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 sneakersniper && chown -R sneakersniper:sneakersniper /app
USER sneakersniper

CMD ["python", "service.py"]
EOL
    fi
done

# Worker Dockerfile
if [ ! -f "worker/Dockerfile" ]; then
    cat > worker/Dockerfile << 'EOL'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER nobody

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
EOL
fi

echo -e "${GREEN}✓ Dockerfiles created${NC}"

# Create environment file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created (please update with your values)${NC}"
    else
        echo -e "${YELLOW}No .env.example found, creating basic .env${NC}"
        cat > .env << 'EOL'
# Basic configuration
ENVIRONMENT=development
DEBUG=true
API_SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/sneakersniper
REDIS_URL=redis://redis:6379

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOL
    fi
fi

# Create Grafana dashboard
echo -e "${YELLOW}Setting up Grafana dashboards...${NC}"

mkdir -p infra/grafana/dashboards
cat > infra/grafana/dashboards/sneakersniper.json << 'EOL'
{
  "dashboard": {
    "title": "SneakerSniper Bot Engine",
    "panels": [
      {
        "title": "Active Monitors",
        "targets": [{"expr": "sneakersniper_monitors_active"}],
        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 8}
      },
      {
        "title": "Checkout Success Rate",
        "targets": [{"expr": "sneakersniper_checkout_success_rate"}],
        "gridPos": {"x": 6, "y": 0, "w": 6, "h": 8}
      },
      {
        "title": "Average Latency",
        "targets": [{"expr": "sneakersniper_monitors_poll_latency_ms"}],
        "gridPos": {"x": 12, "y": 0, "w": 6, "h": 8}
      },
      {
        "title": "Proxy Health",
        "targets": [{"expr": "sneakersniper_proxy_health_score"}],
        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 8}
      }
    ]
  }
}
EOL

echo -e "${GREEN}✓ Grafana dashboards created${NC}"

# Initialize frontend
echo -e "${YELLOW}Setting up frontend...${NC}"

cd frontend
if [ ! -f "package.json" ] && command -v npm &> /dev/null; then
    npm init -y
    npm install --save-dev vite typescript @types/node
    npm install marked
fi
cd ..

echo -e "${GREEN}✓ Frontend initialized${NC}"

# Create docker network
echo -e "${YELLOW}Creating Docker network...${NC}"
docker network create sneakersniper-net 2>/dev/null || true
echo -e "${GREEN}✓ Docker network ready${NC}"

# Create initial migration
echo -e "${YELLOW}Creating database migrations...${NC}"

mkdir -p services/api/alembic/versions
cat > services/api/alembic.ini << 'EOL'
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://postgres:postgres@postgres:5432/sneakersniper

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOL

echo -e "${GREEN}✓ Database migrations configured${NC}"

# Create systemd service files (optional)
echo -e "${YELLOW}Creating systemd service files (optional)...${NC}"

mkdir -p infra/systemd
cat > infra/systemd/sneakersniper.service << 'EOL'
[Unit]
Description=SneakerSniper Bot Engine
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/sneakersniper
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=always
User=sneakersniper

[Install]
WantedBy=multi-user.target
EOL

echo -e "${GREEN}✓ Systemd service files created${NC}"

# Final setup steps
echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Update the .env file with your API keys and configuration"
echo "2. Run 'make dev' or 'docker-compose up --build' to start the services"
echo "3. Access the frontend at http://localhost:5173"
echo "4. Access the API at http://localhost:8000/docs"
echo "5. Access Grafana at http://localhost:3000 (admin/admin)"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "- Add your proxy provider credentials to .env"
echo "- Add your CAPTCHA solver API keys to .env"
echo "- Configure retailer-specific settings as needed"
echo ""
echo -e "${GREEN}Happy botting! 🚀${NC}"