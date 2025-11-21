#!/usr/bin/env python3
"""
WSGI metrics endpoint for Apache/mod_wsgi metrics collection.
This script provides Prometheus-compatible metrics for WSGI applications.
"""

import os
import sys
import threading
import time
import psutil
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Add Django to path
sys.path.append('/var/www/alyx/alyx')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alyx.settings')

# Custom metrics registry
registry = CollectorRegistry()

# WSGI Process Metrics
wsgi_requests_total = Counter(
    'wsgi_requests_total',
    'Total number of WSGI requests',
    ['method', 'status'],
    registry=registry
)

wsgi_request_duration = Histogram(
    'wsgi_request_duration_seconds',
    'WSGI request duration in seconds',
    ['method'],
    registry=registry,
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 25.0, 50.0, 75.0, 100.0, float('inf'))
)

wsgi_active_requests = Gauge(
    'wsgi_active_requests',
    'Number of active WSGI requests',
    registry=registry
)

# System Metrics
cpu_usage = Gauge(
    'wsgi_cpu_usage_percent',
    'CPU usage percentage',
    registry=registry
)

memory_usage = Gauge(
    'wsgi_memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

# Update system metrics periodically
def update_system_metrics():
    while True:
        try:
            cpu_usage.set(psutil.cpu_percent())
            memory_usage.set(psutil.virtual_memory().used)
        except Exception:
            pass
        time.sleep(10)

# Start metrics update thread
metrics_thread = threading.Thread(target=update_system_metrics, daemon=True)
metrics_thread.start()

def application(environ, start_response):
    """WSGI application that serves metrics"""
    if environ['PATH_INFO'] == '/wsgi-metrics':
        status = '200 OK'
        headers = [('Content-Type', CONTENT_TYPE_LATEST)]
        start_response(status, headers)
        return [generate_latest(registry)]
    else:
        status = '404 Not Found'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [b'Metrics endpoint not found']