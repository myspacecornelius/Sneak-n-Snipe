"""
Celery configuration for SneakerSniper
"""

import os
from kombu import Exchange, Queue

# Broker settings
broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Performance settings
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000
worker_disable_rate_limits = False
task_compression = 'gzip'

# Task routing
task_routes = {
    'worker.tasks.process_checkout_batch': {'queue': 'checkout_high'},
    'worker.tasks.warm_account': {'queue': 'warming'},
    'worker.tasks.rotate_proxies': {'queue': 'maintenance'},
    'worker.tasks.analyze_checkout_performance': {'queue': 'analytics'},
    'worker.tasks.cleanup_old_data': {'queue': 'maintenance'},
    'worker.tasks.broadcast_update': {'queue': 'realtime'}
}

# Queue configuration
task_queues = (
    Queue('checkout_high', Exchange('checkout'), routing_key='checkout.high', priority=10),
    Queue('checkout_low', Exchange('checkout'), routing_key='checkout.low', priority=1),
    Queue('warming', Exchange('warming'), routing_key='warming.#'),
    Queue('maintenance', Exchange('maintenance'), routing_key='maintenance.#'),
    Queue('analytics', Exchange('analytics'), routing_key='analytics.#'),
    Queue('realtime', Exchange('realtime'), routing_key='realtime.#'),
)

# Task time limits
task_time_limit = 300  # 5 minutes hard limit
task_soft_time_limit = 240  # 4 minutes soft limit

# Retry settings
task_acks_late = True
task_reject_on_worker_lost = True
task_default_retry_delay = 60  # 1 minute
task_max_retries = 3

# Result backend settings
result_expires = 3600  # 1 hour
result_persistent = False
result_compression = 'gzip'

# Worker settings
worker_concurrency = os.cpu_count() * 2
worker_enable_remote_control = True
worker_send_task_events = True
task_send_sent_event = True

# Beat schedule for periodic tasks
beat_schedule = {
    'rotate-proxies': {
        'task': 'worker.tasks.rotate_proxies',
        'schedule': 300.0,  # Every 5 minutes
        'options': {'queue': 'maintenance'}
    },
    'analyze-performance': {
        'task': 'worker.tasks.analyze_checkout_performance',
        'schedule': 900.0,  # Every 15 minutes
        'options': {'queue': 'analytics'}
    },
    'daily-cleanup': {
        'task': 'worker.tasks.cleanup_old_data',
        'schedule': 86400.0,  # Daily
        'options': {'queue': 'maintenance'}
    }
}

# Monitoring
worker_hijacking_freq = 30.0
worker_stats_rate = 10.0

# Error handling
task_annotations = {
    '*': {
        'rate_limit': '100/m',
        'time_limit': 300,
        'soft_time_limit': 240,
    },
    'worker.tasks.process_checkout_batch': {
        'rate_limit': '1000/m',  # Higher rate for checkouts
        'priority': 10
    }
}