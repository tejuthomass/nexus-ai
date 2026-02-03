"""Gunicorn configuration for Nexus production deployment.

This module configures Gunicorn WSGI server settings optimized for:
    - 10-20 total users
    - 5-10 concurrent users
    - Efficient handling of AI API waiting time
    - Multi-worker rate limiting support

The configuration uses sync workers with threading to efficiently
handle I/O-bound AI API calls while maintaining compatibility.

Environment Variables:
    PORT: Server port (default: 8000).
    WEB_CONCURRENCY: Number of worker processes.
    THREADS_PER_WORKER: Threads per worker (default: 4).
    LOG_LEVEL: Logging level (default: info).
    ADMIN_URL_PATH: Admin panel path for display.

Usage:
    gunicorn -c gunicorn.conf.py config.wsgi:application

Functions:
    on_starting: Called before master process initialization.
    on_reload: Called during worker reload via SIGHUP.
    when_ready: Called after server starts.
    worker_int: Called when worker receives SIGINT/SIGQUIT.
    worker_abort: Called when worker receives SIGABRT.
"""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
# Formula: (2 x num_cores) + 1
# For production: Use environment variable or auto-detect
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))

# Worker class
# Use 'sync' workers for better compatibility with long-running AI API calls
# Each worker handles one request at a time but we have multiple workers
worker_class = 'sync'

# Threading
# Each worker can handle multiple threads for I/O-bound tasks (API calls)
# This allows efficient handling of waiting time during AI API calls
threads = int(os.getenv('THREADS_PER_WORKER', 4))

# Worker connections
worker_connections = 1000

# Timeout
# Set high timeout for AI API calls which can take 5-10 seconds
timeout = 120
keepalive = 5

# Graceful timeout
# Allow workers to finish current requests before restarting
graceful_timeout = 30

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'nexus-ai'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in production)
# keyfile = None
# certfile = None

# Preload app
# Load application code before forking workers for memory efficiency
preload_app = True

# Restart workers after this many requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Worker lifecycle hooks
def on_starting(server):
    """Handle server startup initialization.

    Called just before the master process is initialized. Logs
    configuration details including worker count and expected capacity.

    Args:
        server: The Arbiter instance managing the workers.
    """
    print(f"🚀 Starting Nexus server with {workers} workers and {threads} threads per worker")
    print(f"📊 Expected capacity: 10-20 users, 5-10 concurrent users")
    print(f"🔧 Configuration: {workers} workers x {threads} threads = {workers * threads} concurrent connections")


def on_reload(server):
    """Handle worker reload signal.

    Called to recycle workers during a reload via SIGHUP.

    Args:
        server: The Arbiter instance managing the workers.
    """
    print("🔄 Reloading Nexus workers...")


def when_ready(server):
    """Handle server ready state.

    Called just after the server is started and ready to accept
    connections. Logs the bind address and admin panel location.

    Args:
        server: The Arbiter instance managing the workers.
    """
    print(f"✅ Nexus server is ready at {bind}")
    print(f"🔒 Admin panel: /{os.getenv('ADMIN_URL_PATH', 'admin/')}")


def worker_int(worker):
    """Handle worker interrupt signal.

    Called when a worker receives the SIGINT or SIGQUIT signal.
    Logs the worker PID for debugging.

    Args:
        worker: The Worker instance that received the signal.
    """
    print(f"⚠️  Worker {worker.pid} received interrupt signal")


def worker_abort(worker):
    """Handle worker abort signal.

    Called when a worker receives the SIGABRT signal, indicating
    an abnormal termination.

    Args:
        worker: The Worker instance that received the signal.
    """
    print(f"❌ Worker {worker.pid} aborted")

# Capacity explanation:
# With 4 workers and 4 threads per worker:
# - 16 concurrent requests can be handled
# - Rate limiting prevents overload (50 parallel max)
# - Each user can send ~10 requests/min
# - System can comfortably handle 10-20 users
#
# Scaling:
# - For more users: Increase WEB_CONCURRENCY (workers)
# - For faster response: Increase THREADS_PER_WORKER
# - Monitor: Check worker utilization and adjust

# Performance notes:
# - Sync workers with threading is optimal for AI API waiting
# - Preload reduces memory footprint
# - Max requests prevents memory leaks
# - Graceful timeout ensures clean shutdowns
