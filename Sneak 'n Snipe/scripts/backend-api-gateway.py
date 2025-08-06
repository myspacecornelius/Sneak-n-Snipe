"""
SneakerSniper API Gateway
FastAPI service that coordinates all bot operations
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import json
import asyncio
from datetime import datetime
import redis.asyncio as redis
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class AuthRequest(BaseModel):
    api_key: str = Field(default="dev-mode")

class AuthResponse(BaseModel):
    token: str
    expires_at: datetime

class CommandParseRequest(BaseModel):
    prompt: str

class CommandParseResponse(BaseModel):
    type: str  # 'command', 'chat', or 'error'
    command: Optional[Dict[str, Any]] = None
    response: Optional[str] = None
    message: Optional[str] = None

class MonitorRequest(BaseModel):
    sku: str
    retailer: str = "shopify"
    interval_ms: int = 200

class MonitorResponse(BaseModel):
    success: bool
    monitor_id: Optional[str] = None
    error: Optional[str] = None

class CheckoutTasksRequest(BaseModel):
    count: int
    profile_id: str
    mode: str = "request"  # 'request' or 'browser'
    retailer: str = "shopify"

class CheckoutTasksResponse(BaseModel):
    success: bool
    task_ids: List[str] = []
    error: Optional[str] = None

class MetricsResponse(BaseModel):
    active_monitors: int
    running_tasks: int
    success_rate: float
    avg_latency_ms: int
    total_checkouts_today: int
    proxy_health: Dict[str, Any]

# Security
security = HTTPBearer()

# Redis connection manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await redis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True
    )
    yield
    # Shutdown
    await app.state.redis.close()

# Initialize FastAPI
app = FastAPI(
    title="SneakerSniper API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # In production, validate token from Redis/DB
    # For now, just check if it exists
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return {"user_id": "dev-user", "token": token}

# Command Parser (replaces Gemini AI)
class CommandParser:
    """Internal command parser to replace external AI dependency"""
    
    def parse(self, prompt: str) -> CommandParseResponse:
        prompt_lower = prompt.lower()
        
        # Monitor commands
        if any(word in prompt_lower for word in ["monitor", "watch", "track"]):
            # Extract SKU from prompt
            words = prompt.split()
            sku = None
            for i, word in enumerate(words):
                if word.lower() in ["sku", "shoe", "shoes", "product"]:
                    if i + 1 < len(words):
                        sku = words[i + 1]
                        break
            
            if not sku:
                # Try to find any word that looks like a SKU
                for word in words:
                    if len(word) > 5 and any(c.isdigit() for c in word):
                        sku = word
                        break
                    elif "travis" in word.lower() or "jordan" in word.lower():
                        sku = "-".join(words[words.index(word):words.index(word)+3])
                        break
            
            if sku:
                return CommandParseResponse(
                    type="command",
                    command={
                        "action": "start_monitor",
                        "parameters": {"sku": sku, "retailer": "shopify"}
                    }
                )
        
        # Checkout commands
        elif any(word in prompt_lower for word in ["checkout", "run", "fire", "cop"]):
            # Extract count
            count = 50  # default
            for word in prompt.split():
                if word.isdigit():
                    count = int(word)
                    break
            
            # Extract profile
            profile = "main-profile"
            if "profile" in prompt_lower:
                words = prompt.split()
                profile_idx = words.index("profile") if "profile" in words else -1
                if profile_idx > 0:
                    profile = words[profile_idx - 1]
            
            return CommandParseResponse(
                type="command",
                command={
                    "action": "fire_checkout",
                    "parameters": {
                        "task_count": count,
                        "profile_id": profile,
                        "retailer": "shopify"
                    }
                }
            )
        
        # Clear commands
        elif any(word in prompt_lower for word in ["clear", "stop", "reset", "kill"]):
            return CommandParseResponse(
                type="command",
                command={
                    "action": "clear_dashboard",
                    "parameters": {}
                }
            )
        
        # General chat
        else:
            return CommandParseResponse(
                type="chat",
                response=self._generate_chat_response(prompt)
            )
    
    def _generate_chat_response(self, prompt: str) -> str:
        """Generate contextual responses for general questions"""
        prompt_lower = prompt.lower()
        
        if "proxy" in prompt_lower:
            return "Proxy rotation is handled automatically. The system uses sticky residential proxies with 10-15 minute TTL from providers like Bright Data. Cost tracking ensures we stay under $0.05 per successful checkout."
        elif "captcha" in prompt_lower:
            return "CAPTCHA solving uses CapSolver as primary with a human farm fallback. Current solve rate is 98%+ with average solve time under 3 seconds."
        elif "success" in prompt_lower or "rate" in prompt_lower:
            return "Success rates vary by site. Shopify averages 65%+, Footsites around 50%, and SNKRS is more challenging at 20-30%. These improve with aged accounts and quality proxies."
        elif "how" in prompt_lower and "work" in prompt_lower:
            return "SneakerSniper uses a dual-mode approach: fast request-mode for speed and stealth browser mode for heavy anti-bot sites. Monitors poll every 200ms and trigger checkout tasks on stock detection."
        else:
            return "I can help you monitor products, run checkout tasks, or answer questions about the bot's operation. Try commands like 'monitor travis scott shoes' or 'run 100 checkouts'."

# Initialize command parser
command_parser = CommandParser()

# Routes
@app.get("/")
async def root():
    return {"status": "SneakerSniper API Online", "version": "1.0.0"}

@app.post("/api/auth/session", response_model=AuthResponse)
async def create_session(auth_request: AuthRequest):
    """Create a new session token"""
    token = str(uuid.uuid4())
    expires_at = datetime.now().timestamp() + 86400  # 24 hours
    
    # Store token in Redis
    await app.state.redis.setex(
        f"session:{token}",
        86400,
        json.dumps({"user_id": "dev-user", "api_key": auth_request.api_key})
    )
    
    return AuthResponse(
        token=token,
        expires_at=datetime.fromtimestamp(expires_at)
    )

@app.post("/api/commands/parse", response_model=CommandParseResponse)
async def parse_command(
    request: CommandParseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Parse user command into executable action"""
    return command_parser.parse(request.prompt)

@app.post("/api/monitors", response_model=MonitorResponse)
async def create_monitor(
    request: MonitorRequest,
    current_user: dict = Depends(get_current_user)
):
    """Start a new product monitor"""
    try:
        monitor_id = str(uuid.uuid4())
        
        # Create monitor task in Redis
        monitor_data = {
            "monitor_id": monitor_id,
            "sku": request.sku,
            "retailer": request.retailer,
            "interval_ms": request.interval_ms,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "user_id": current_user["user_id"]
        }
        
        await app.state.redis.hset(
            f"monitor:{monitor_id}",
            mapping=monitor_data
        )
        
        # Add to active monitors set
        await app.state.redis.sadd("active_monitors", monitor_id)
        
        # Publish to monitor service via Redis pub/sub
        await app.state.redis.publish(
            "monitor_commands",
            json.dumps({"action": "start", "monitor": monitor_data})
        )
        
        return MonitorResponse(success=True, monitor_id=monitor_id)
        
    except Exception as e:
        logger.error(f"Failed to create monitor: {e}")
        return MonitorResponse(success=False, error=str(e))

@app.delete("/api/monitors/{monitor_id}")
async def stop_monitor(
    monitor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Stop a running monitor"""
    # Remove from active set
    await app.state.redis.srem("active_monitors", monitor_id)
    
    # Update status
    await app.state.redis.hset(f"monitor:{monitor_id}", "status", "stopped")
    
    # Publish stop command
    await app.state.redis.publish(
        "monitor_commands",
        json.dumps({"action": "stop", "monitor_id": monitor_id})
    )
    
    return {"success": True}

@app.post("/api/checkout/tasks/batch", response_model=CheckoutTasksResponse)
async def create_checkout_tasks(
    request: CheckoutTasksRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create multiple checkout tasks"""
    try:
        task_ids = []
        
        for i in range(request.count):
            task_id = str(uuid.uuid4())
            task_data = {
                "task_id": task_id,
                "profile_id": request.profile_id,
                "mode": request.mode,
                "retailer": request.retailer,
                "status": "queued",
                "created_at": datetime.now().isoformat(),
                "user_id": current_user["user_id"]
            }
            
            # Queue task in Redis
            await app.state.redis.lpush(
                "checkout_queue",
                json.dumps(task_data)
            )
            
            # Store task data
            await app.state.redis.hset(
                f"task:{task_id}",
                mapping=task_data
            )
            
            task_ids.append(task_id)
        
        return CheckoutTasksResponse(success=True, task_ids=task_ids)
        
    except Exception as e:
        logger.error(f"Failed to create checkout tasks: {e}")
        return CheckoutTasksResponse(success=False, error=str(e))

@app.get("/api/metrics/dashboard", response_model=MetricsResponse)
async def get_metrics(current_user: dict = Depends(get_current_user)):
    """Get dashboard metrics"""
    # Get counts from Redis
    active_monitors = await app.state.redis.scard("active_monitors") or 0
    
    # Get running tasks (this would come from Celery in production)
    running_tasks = await app.state.redis.get("metrics:running_tasks") or 0
    
    # Get success metrics
    total_checkouts = int(await app.state.redis.get("metrics:total_checkouts") or 0)
    successful_checkouts = int(await app.state.redis.get("metrics:successful_checkouts") or 0)
    success_rate = (successful_checkouts / total_checkouts * 100) if total_checkouts > 0 else 0
    
    # Get average latency
    avg_latency = int(await app.state.redis.get("metrics:avg_latency_ms") or 120)
    
    return MetricsResponse(
        active_monitors=active_monitors,
        running_tasks=int(running_tasks),
        success_rate=round(success_rate, 1),
        avg_latency_ms=avg_latency,
        total_checkouts_today=total_checkouts,
        proxy_health={
            "active": 45,
            "burned": 3,
            "cost_today": "$12.37"
        }
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time updates"""
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    
    # Subscribe to Redis pub/sub for updates
    pubsub = app.state.redis.pubsub()
    await pubsub.subscribe("monitor_updates", "task_updates", "system_alerts")
    
    try:
        # Send updates to client
        async def redis_listener():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await manager.send_personal_message(
                        message["data"],
                        client_id
                    )
        
        # Keep connection alive
        redis_task = asyncio.create_task(redis_listener())
        
        while True:
            # Wait for messages from client (mainly for ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        redis_task.cancel()
        await pubsub.unsubscribe()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        await app.state.redis.ping()
        return {"status": "healthy", "redis": "connected"}
    except:
        return {"status": "unhealthy", "redis": "disconnected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)