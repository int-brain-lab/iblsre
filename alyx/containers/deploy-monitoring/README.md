# Alyx Monitoring Setup

This directory contains the monitoring variant of the Alyx Django application with comprehensive Prometheus and Grafana monitoring.

## Overview

The monitoring setup includes:

- **Alyx Django Application** with Prometheus metrics
- **Apache HTTP Server** with mod_status for metrics
- **PostgreSQL Database** with pg_stat monitoring
- **Prometheus** for metrics collection and storage
- **Grafana** for visualization and dashboards
- **Loki** for log aggregation
- **Promtail** for log collection
- **Node Exporter** for system metrics

## Quick Start

1. **Copy and configure the environment file:**
   ```bash
   cp template.env .env
   # Edit .env with your specific configuration
   ```

2. **Build the monitoring container:**
   ```bash
   cd ../docker
   ./build-containers.sh --monitoring
   ```

3. **Start the monitoring stack:**
   ```bash
   docker-compose up -d
   ```

4. **Access the services:**
   - Alyx Application: http://localhost:8080
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin_password_change_me)
   - Loki: http://localhost:3100

## Services and Ports

| Service | Port | Description |
|---------|------|-------------|
| Alyx Apache | 80, 443, 8080 | Main Django application |
| Prometheus | 9090 | Metrics storage and queries |
| Grafana | 3000 | Visualization dashboards |
| Loki | 3100 | Log aggregation |
| Node Exporter | 9100 | System metrics |
| Postgres Exporter | 9187 | PostgreSQL metrics |
| Apache Exporter | 9117 | Apache metrics |

## Metrics Collected

### Django Metrics (via django-prometheus)
- HTTP request rates and response times
- Database query metrics
- Cache usage statistics
- Model operation counters
- Custom application metrics

### Apache Metrics
- Worker status (busy/idle)
- Request processing statistics
- Connection metrics
- Server uptime and status

### PostgreSQL Metrics
- Connection counts
- Query performance
- Database size and activity
- Replication status

### System Metrics
- CPU, memory, disk usage
- Network I/O
- File system metrics
- Process statistics

## Log Collection

### Log Sources
- **Apache Access Logs**: HTTP request logs with detailed timing
- **Apache Error Logs**: Server error and warning messages
- **Django Application Logs**: Application-level logging in JSON format
- **Container Logs**: Docker container stdout/stderr

### Log Processing
- Structured JSON logging for Django
- Apache log parsing with regex
- Container log aggregation
- Real-time log streaming to Loki

## Grafana Dashboards

The setup includes pre-configured dashboards:

1. **Alyx Application Monitoring** - Overview of Django performance
2. **Apache Server Metrics** - Web server performance
3. **PostgreSQL Database** - Database performance and health
4. **System Overview** - Host system metrics
5. **Log Analysis** - Log aggregation and search

## Configuration Files

- `docker-compose.yaml` - Complete monitoring stack
- `prometheus.yml` - Prometheus scraping configuration
- `loki-config.yml` - Loki log aggregation settings
- `promtail-config.yml` - Log collection configuration
- `grafana/` - Dashboard and datasource provisioning

## Environment Variables

Key configuration options in `.env`:

```env
# Application
APACHE_SERVER_NAME=your-domain.com
DJANGO_SECRET_KEY=your-secret-key
DJANGO_LOG_LEVEL=INFO

# Database
POSTGRES_HOST=alyx_postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change-this-password
```

## Monitoring Best Practices

### Alerting
Configure Prometheus alerts for:
- High error rates (>5% 5xx responses)
- Slow response times (>2s 95th percentile)
- Database connection issues
- High resource usage (>80% CPU/memory)

### Retention
- Prometheus: 30 days (configurable)
- Loki: 7 days default
- Grafana: Persistent dashboards

### Security
- Change default Grafana credentials
- Restrict metrics endpoints to internal networks
- Use SSL/TLS for production deployments
- Configure proper firewall rules

## Troubleshooting

### Common Issues

1. **Container fails to start:**
   ```bash
   docker-compose logs [service-name]
   ```

2. **Metrics not appearing:**
   - Check Prometheus targets: http://localhost:9090/targets
   - Verify service connectivity
   - Review container logs

3. **Grafana dashboard issues:**
   - Verify datasource configuration
   - Check Prometheus query syntax
   - Ensure proper permissions

### Health Checks

Monitor service health:
```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs -f alyx_apache_monitoring

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

## Scaling and Performance

### For High-Traffic Deployments

1. **Resource Allocation:**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 2G
   ```

2. **Prometheus Storage:**
   - Use external storage for retention >30 days
   - Configure recording rules for frequently-used queries
   - Consider Prometheus federation for multiple instances

3. **Database Optimization:**
   - Enable connection pooling
   - Monitor query performance
   - Configure appropriate shared_buffers

## Migration from Standard Setup

To migrate from the standard Alyx deployment:

1. Stop the current deployment
2. Backup your data
3. Update docker-compose.yaml to use monitoring variant
4. Restart with new configuration
5. Import existing data if needed

## Support and Documentation

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Django-Prometheus](https://github.com/korfuri/django-prometheus)
- [Alyx Documentation](https://github.com/cortex-lab/alyx)