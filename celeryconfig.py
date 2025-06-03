# Celery configuration file
import os
from dotenv import load_dotenv

load_dotenv()

# Broker and backend configuration
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

# Task configuration
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Task routing
task_routes = {
    'celery_tasks.calculate_5min_average_prices': {'queue': 'analytics'},
    'celery_tasks.process_s3_trading_data': {'queue': 'analytics'},
    'celery_tasks.generate_trading_signals': {'queue': 'signals'},
    'celery_tasks.cleanup_old_data': {'queue': 'maintenance'},
}

# Worker configuration
worker_prefetch_multiplier = 1
task_acks_late = True
worker_max_tasks_per_child = 1000

# Result backend configuration
result_expires = 3600  # 1 hour

# Task execution configuration
task_always_eager = False
task_eager_propagates = True
task_ignore_result = False

# Error handling
task_reject_on_worker_lost = True
task_acks_on_failure_or_timeout = True

# Logging
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Security
worker_disable_rate_limits = False
worker_enable_remote_control = False
