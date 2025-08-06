"""
SneakerSniper Proxy Manager
Intelligent proxy rotation and health monitoring
"""

"""
SneakerSniper Proxy Manager
Intelligent proxy rotation and health monitoring for high-stakes sneaker drops.

This module provides a comprehensive system for managing and optimizing a pool of
proxies from various providers. It focuses on performance, stealth, and reliability
by continuously monitoring proxy health, managing costs, and providing a simple
interface for other services to consume proxies.

Core Features:
- Pluggable provider system (e.g., Bright Data, Oxylabs).
- Redis-backed state management for persistence and scalability.
- Continuous health monitoring and scoring based on success rate, response time, and recency.
- Automatic provisioning and burning of proxies based on health.
- Cost tracking and alerting to prevent budget overruns.
- Intelligent proxy selection based on user-defined requirements.
- Asynchronous, high-performance design using asyncio and httpx.
"""

import asyncio
import json
import time
import httpx
import os
import redis.asyncio as redis
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import logging
import random
from abc import ABC, abstractmethod
from collections import defaultdict

# Configure logging for better debugging and operational visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Proxy:
    """Proxy configuration and stats"""
    url: str
    provider: str
    proxy_type: str  # 'residential', 'isp', 'datacenter'
    location: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    sticky_session_id: Optional[str] = None
    requests: int = 0
    failures: int = 0
    success: int = 0
    total_bandwidth_mb: float = 0.0
    last_used: Optional[datetime] = None
    last_error: Optional[str] = None
    response_times: List[float] = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []
    
    @property
    def auth_url(self) -> str:
        """Get proxy URL with authentication"""
        if self.username and self.password:
            protocol, rest = self.url.split('://', 1)
            return f"{protocol}://{self.username}:{self.password}@{rest}"
        return self.url
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        total = self.requests
        return (self.failures / total * 100) if total > 0 else 0
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0
        return sum(self.response_times[-100:]) / len(self.response_times[-100:])
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        if self.requests == 0:
            return 100
        
        # Factors: success rate (60%), response time (30%), recency (10%)
        success_rate = (self.success / self.requests) * 60 if self.requests > 0 else 60
        
        # Response time score (lower is better, <500ms = full score)
        avg_time = self.avg_response_time
        time_score = max(0, 30 - (avg_time / 50)) if avg_time > 0 else 30
        
        # Recency score
        if self.last_used:
            minutes_ago = (datetime.now() - self.last_used).total_seconds() / 60
            recency_score = max(0, 10 - (minutes_ago / 6))  # Lose 1 point per 6 minutes
        else:
            recency_score = 10
            
        return min(100, success_rate + time_score + recency_score)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        data['last_used'] = self.last_used.isoformat() if self.last_used else None
        data['response_times'] = json.dumps(self.response_times[-100:])  # Keep last 100
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Proxy':
        """Create from dictionary"""
        if data.get('last_used'):
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        if data.get('response_times'):
            data['response_times'] = json.loads(data['response_times'])
        return cls(**data)

class ProxyProvider(ABC):
    """Abstract base for proxy providers"""
    
    @abstractmethod
    async def get_proxies(self, count: int = 10) -> List[Proxy]:
        """Get new proxies from provider"""
        pass
    
    @abstractmethod
    async def rotate_ip(self, proxy: Proxy) -> Proxy:
        """Rotate IP for sticky session proxy"""
        pass

class BrightDataProvider(ProxyProvider):
    """Bright Data (Luminati) proxy provider"""
    
    def __init__(self, customer_id: str, password: str, zone: str):
        self.customer_id = customer_id
        self.password = password
        self.zone = zone
        self.base_url = f"http://zproxy.lum-superproxy.io:22225"
        
    async def get_proxies(self, count: int = 10) -> List[Proxy]:
        """Get ISP proxies from Bright Data"""
        proxies = []
        
        for i in range(count):
            # Generate sticky session ID
            session_id = f"session_{int(time.time())}_{i}"
            
            proxy = Proxy(
                url=self.base_url,
                provider="bright_data",
                proxy_type="isp",
                username=f"{self.customer_id}-zone-{self.zone}-session-{session_id}",
                password=self.password,
                sticky_session_id=session_id,
                location="us"
            )
            proxies.append(proxy)
            
        return proxies
    
    async def rotate_ip(self, proxy: Proxy) -> Proxy:
        """Rotate IP by changing session ID"""
        new_session_id = f"session_{int(time.time())}_{random.randint(1000, 9999)}"
        proxy.sticky_session_id = new_session_id
        proxy.username = f"{self.customer_id}-zone-{self.zone}-session-{new_session_id}"
        return proxy

class OxylabsProvider(ProxyProvider):
    """Oxylabs proxy provider"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.base_url = "http://pr.oxylabs.io:7777"
        
    async def get_proxies(self, count: int = 10) -> List[Proxy]:
        """Get residential proxies from Oxylabs"""
        proxies = []
        
        for i in range(count):
            proxy = Proxy(
                url=self.base_url,
                provider="oxylabs",
                proxy_type="residential",
                username=f"customer-{self.username}-cc-us-sessid-{int(time.time())}{i}",
                password=self.password,
                location="us"
            )
            proxies.append(proxy)
            
        return proxies
    
    async def rotate_ip(self, proxy: Proxy) -> Proxy:
        """Rotate IP by changing session in username"""
        parts = proxy.username.split('-')
        parts[-1] = str(int(time.time())) + str(random.randint(100, 999))
        proxy.username = '-'.join(parts)
        return proxy

class ProxyManager:
    """Main proxy management service"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.providers: Dict[str, ProxyProvider] = {}
        self.cost_tracker = defaultdict(float)
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
    async def start(self):
        """Start the proxy manager service"""
        logger.info("Starting SneakerSniper Proxy Manager...")
        
        # Connect to Redis
        self.redis_client = await redis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True
        )
        
        # Initialize providers from environment
        self._init_providers()
        
        # Load existing proxies
        await self._load_proxies()
        
        # Start background tasks
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._cost_monitor())
        asyncio.create_task(self._rotation_scheduler())
        
        logger.info("Proxy Manager started successfully")
    
    def _init_providers(self):
        """Initialize proxy providers from config"""
        # In production, load from environment variables
        # Example initialization:
        if all(key in os.environ for key in ['BRIGHT_DATA_CUSTOMER', 'BRIGHT_DATA_PASSWORD', 'BRIGHT_DATA_ZONE']):
            self.providers['bright_data'] = BrightDataProvider(
                customer_id=os.environ['BRIGHT_DATA_CUSTOMER'],
                password=os.environ['BRIGHT_DATA_PASSWORD'],
                zone=os.environ['BRIGHT_DATA_ZONE']
            )
        
        if all(key in os.environ for key in ['OXYLABS_USERNAME', 'OXYLABS_PASSWORD']):
            self.providers['oxylabs'] = OxylabsProvider(
                username=os.environ['OXYLABS_USERNAME'],
                password=os.environ['OXYLABS_PASSWORD']
            )
    
    async def get_proxy(self, requirements: Dict[str, Any] = None) -> Optional[Proxy]:
        """Get best available proxy based on requirements"""
        requirements = requirements or {}
        proxy_type = requirements.get('type', 'any')
        location = requirements.get('location', 'any')
        min_health_score = requirements.get('min_health_score', 70)
        
        # Get all active proxies
        proxy_urls = await self.redis_client.smembers("proxies:active")
        
        if not proxy_urls:
            # No proxies available, get new ones
            await self._provision_proxies(10)
            proxy_urls = await self.redis_client.smembers("proxies:active")
        
        # Score and sort proxies
        scored_proxies = []
        for proxy_url in proxy_urls:
            proxy_data = await self.redis_client.hgetall(f"proxy:{proxy_url}")
            if not proxy_data:
                continue
                
            proxy = Proxy.from_dict(proxy_data)
            
            # Filter by requirements
            if proxy_type != 'any' and proxy.proxy_type != proxy_type:
                continue
            if location != 'any' and proxy.location != location:
                continue
            if proxy.health_score < min_health_score:
                continue
                
            scored_proxies.append((proxy.health_score, proxy))
        
        if not scored_proxies:
            logger.warning("No proxies match requirements")
            return None
        
        # Sort by health score (descending)
        scored_proxies.sort(key=lambda x: x[0], reverse=True)
        
        # Get best proxy
        best_proxy = scored_proxies[0][1]
        
        # Update last used
        best_proxy.last_used = datetime.now()
        await self._save_proxy(best_proxy)
        
        return best_proxy
    
    async def report_usage(self, proxy: Proxy, success: bool, response_time: float, 
                          bandwidth_mb: float = 0.0, error: Optional[str] = None):
        """Report proxy usage statistics"""
        proxy.requests += 1
        
        if success:
            proxy.success += 1
        else:
            proxy.failures += 1
            proxy.last_error = error
            
        proxy.response_times.append(response_time)
        proxy.total_bandwidth_mb += bandwidth_mb
        
        # Update cost tracking
        self.cost_tracker[proxy.provider] += self._calculate_cost(proxy, bandwidth_mb)
        
        # Save updated stats
        await self._save_proxy(proxy)
        
        # Check if proxy should be burned
        if proxy.failure_rate > 30 and proxy.requests > 10:
            await self._burn_proxy(proxy)
    
    async def _provision_proxies(self, count: int):
        """Provision new proxies from providers"""
        logger.info(f"Provisioning {count} new proxies")
        
        # Distribute across providers
        proxies_per_provider = count // len(self.providers) if self.providers else count
        
        for provider_name, provider in self.providers.items():
            try:
                new_proxies = await provider.get_proxies(proxies_per_provider)
                
                for proxy in new_proxies:
                    await self._save_proxy(proxy)
                    await self.redis_client.sadd("proxies:active", proxy.url)
                    
                logger.info(f"Provisioned {len(new_proxies)} proxies from {provider_name}")
                
            except Exception as e:
                logger.error(f"Failed to provision from {provider_name}: {e}")
    
    async def _save_proxy(self, proxy: Proxy):
        """Save proxy to Redis"""
        await self.redis_client.hset(
            f"proxy:{proxy.url}",
            mapping=proxy.to_dict()
        )
    
    async def _burn_proxy(self, proxy: Proxy):
        """Mark proxy as burned"""
        logger.warning(f"Burning proxy {proxy.url} - {proxy.failure_rate:.1f}% failure rate")
        
        # Remove from active set
        await self.redis_client.srem("proxies:active", proxy.url)
        await self.redis_client.sadd("proxies:burned", proxy.url)
        
        # Set expiry on proxy data (keep for 24h for analysis)
        await self.redis_client.expire(f"proxy:{proxy.url}", 86400)
        
        # Alert
        await self.redis_client.publish(
            "system_alerts",
            json.dumps({
                "type": "alert",
                "payload": {
                    "message": f"Proxy burned: {proxy.provider} proxy with {proxy.failure_rate:.1f}% failure rate",
                    "severity": "warning",
                    "proxy_url": proxy.url
                }
            })
        )
    
    async def _health_monitor(self):
        """Monitor proxy health periodically"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                active_proxies = await self.redis_client.smembers("proxies:active")
                healthy_count = 0
                unhealthy_count = 0
                
                for proxy_url in active_proxies:
                    proxy_data = await self.redis_client.hgetall(f"proxy:{proxy_url}")
                    if not proxy_data:
                        continue
                        
                    proxy = Proxy.from_dict(proxy_data)
                    
                    if proxy.health_score < 50:
                        unhealthy_count += 1
                        # Consider burning very unhealthy proxies
                        if proxy.health_score < 20:
                            await self._burn_proxy(proxy)
                    else:
                        healthy_count += 1
                
                # Provision more if needed
                if healthy_count < 10:
                    await self._provision_proxies(20 - healthy_count)
                    
                # Update metrics
                await self.redis_client.hset(
                    "metrics:proxy_health",
                    mapping={
                        "healthy": healthy_count,
                        "unhealthy": unhealthy_count,
                        "total": len(active_proxies),
                        "last_check": datetime.now().isoformat()
                    }
                )
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    async def _cost_monitor(self):
        """Monitor proxy costs"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Calculate hourly costs
                hourly_costs = {}
                total_cost = 0
                
                for provider, cost in self.cost_tracker.items():
                    hourly_costs[provider] = round(cost, 2)
                    total_cost += cost
                
                # Reset hourly tracker
                self.cost_tracker.clear()
                
                # Update daily total
                daily_total = float(await self.redis_client.get("metrics:proxy_cost_today") or 0)
                daily_total += total_cost
                
                await self.redis_client.set("metrics:proxy_cost_today", daily_total)
                await self.redis_client.hset(
                    "metrics:proxy_cost_breakdown",
                    mapping=hourly_costs
                )
                
                # Alert if costs are high
                if total_cost > 5.0:  # $5/hour threshold
                    await self.redis_client.publish(
                        "system_alerts",
                        json.dumps({
                            "type": "alert",
                            "payload": {
                                "message": f"⚠️ High proxy costs: ${total_cost:.2f}/hour",
                                "severity": "warning",
                                "breakdown": hourly_costs
                            }
                        })
                    )
                    
            except Exception as e:
                logger.error(f"Cost monitor error: {e}")
    
    async def _rotation_scheduler(self):
        """Schedule proxy rotation for sticky sessions"""
        while True:
            try:
                await asyncio.sleep(600)  # Every 10 minutes
                
                active_proxies = await self.redis_client.smembers("proxies:active")
                
                for proxy_url in active_proxies:
                    proxy_data = await self.redis_client.hgetall(f"proxy:{proxy_url}")
                    if not proxy_data:
                        continue
                        
                    proxy = Proxy.from_dict(proxy_data)
                    
                    # Rotate if sticky session is older than 15 minutes
                    if proxy.sticky_session_id and proxy.last_used:
                        age_minutes = (datetime.now() - proxy.last_used).total_seconds() / 60
                        if age_minutes > 15:
                            provider = self.providers.get(proxy.provider)
                            if provider:
                                rotated_proxy = await provider.rotate_ip(proxy)
                                await self._save_proxy(rotated_proxy)
                                logger.info(f"Rotated sticky session for {proxy.provider}")
                                
            except Exception as e:
                logger.error(f"Rotation scheduler error: {e}")
    
    def _calculate_cost(self, proxy: Proxy, bandwidth_mb: float) -> float:
        """Calculate cost for proxy usage"""
        # Cost model (example rates)
        cost_per_gb = {
            'residential': 15.0,  # $15/GB
            'isp': 3.0,          # $3/GB  
            'datacenter': 0.5    # $0.50/GB
        }
        
        base_rate = cost_per_gb.get(proxy.proxy_type, 1.0)
        bandwidth_cost = (bandwidth_mb / 1024) * base_rate
        
        # Add per-request cost for residential
        if proxy.proxy_type == 'residential':
            bandwidth_cost += 0.001  # $0.001 per request
            
        return bandwidth_cost
    
    async def _load_proxies(self):
        """Load existing proxies from Redis"""
        active_count = await self.redis_client.scard("proxies:active")
        burned_count = await self.redis_client.scard("proxies:burned")
        
        logger.info(f"Loaded {active_count} active proxies, {burned_count} burned")
        
        # Ensure minimum proxy count
        if active_count < 10:
            await self._provision_proxies(20)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        active_proxies = await self.redis_client.smembers("proxies:active")
        burned_proxies = await self.redis_client.smembers("proxies:burned")
        
        stats = {
            'active': len(active_proxies),
            'burned': len(burned_proxies),
            'providers': list(self.providers.keys()),
            'cost_today': float(await self.redis_client.get("metrics:proxy_cost_today") or 0),
            'health_breakdown': {
                'excellent': 0,  # 90-100
                'good': 0,       # 70-89
                'fair': 0,       # 50-69
                'poor': 0        # <50
            }
        }
        
        # Analyze health scores
        for proxy_url in active_proxies:
            proxy_data = await self.redis_client.hgetall(f"proxy:{proxy_url}")
            if proxy_data:
                proxy = Proxy.from_dict(proxy_data)
                score = proxy.health_score
                
                if score >= 90:
                    stats['health_breakdown']['excellent'] += 1
                elif score >= 70:
                    stats['health_breakdown']['good'] += 1
                elif score >= 50:
                    stats['health_breakdown']['fair'] += 1
                else:
                    stats['health_breakdown']['poor'] += 1
                    
        return stats
    
    async def shutdown(self):
        """Gracefully shutdown the service"""
        logger.info("Shutting down Proxy Manager...")
        
        # Save final stats
        stats = await self.get_stats()
        await self.redis_client.set(
            "proxy_manager:final_stats",
            json.dumps(stats)
        )
        
        # Close connections
        await self.http_client.aclose()
        await self.redis_client.close()
        
        logger.info("Proxy Manager shutdown complete")

# HTTP proxy client wrapper
class ProxiedClient:
    """HTTP client with automatic proxy rotation"""
    
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with proxy"""
        # Get a proxy
        proxy = await self.proxy_manager.get_proxy(kwargs.pop('proxy_requirements', {}))
        if not proxy:
            raise Exception("No proxy available")
            
        # Configure proxy
        proxies = {
            "http://": proxy.auth_url,
            "https://": proxy.auth_url
        }
        
        # Make request
        start_time = time.time()
        success = False
        error = None
        
        try:
            async with httpx.AsyncClient(proxies=proxies, timeout=10.0) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                success = True
                return response
                
        except Exception as e:
            error = str(e)
            raise
            
        finally:
            # Report usage
            response_time = (time.time() - start_time) * 1000
            bandwidth_mb = len(response.content) / (1024 * 1024) if success else 0
            
            await self.proxy_manager.report_usage(
                proxy=proxy,
                success=success,
                response_time=response_time,
                bandwidth_mb=bandwidth_mb,
                error=error
            )

async def main():
    """Main entry point"""
    import os
    
    manager = ProxyManager()
    
    try:
        await manager.start()
        # Keep service running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())