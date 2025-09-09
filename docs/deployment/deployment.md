# Deployment Guide

This guide covers deploying WriteIt in various environments, from single-user installations to enterprise multi-user deployments.

## 🎯 Deployment Options

WriteIt supports multiple deployment patterns based on your needs:

| Deployment Type | Use Case | Complexity | Scale |
|----------------|----------|------------|-------|
| **Local Desktop** | Individual writers | Low | 1 user |
| **Server Multi-User** | Team/Organization | Medium | 10-100 users |
| **Container Deployment** | Cloud/Kubernetes | Medium | 10-1000 users |
| **Enterprise Integration** | Large Organizations | High | 1000+ users |

## 🖥️ Local Desktop Deployment

### Standard Installation
```bash
# Install WriteIt for single user
pip install writeit[openai,anthropic]

# Initialize workspace
writeit init ~/articles

# Configure AI providers
llm keys set openai
llm keys set anthropic

# Verify installation
writeit verify
```

### System Service (Linux/macOS)
For always-available WriteIt daemon:

```bash
# Create systemd service (Linux)
sudo cat > /etc/systemd/system/writeit-daemon.service << 'EOF'
[Unit]
Description=WriteIt Article Pipeline Daemon
After=network.target

[Service]
Type=simple
User=writeit
Group=writeit
WorkingDirectory=/home/writeit
ExecStart=/usr/local/bin/writeit daemon --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable writeit-daemon
sudo systemctl start writeit-daemon
```

```bash
# Create launchd service (macOS)
cat > ~/Library/LaunchAgents/ai.writeit.daemon.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.writeit.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/writeit</string>
        <string>daemon</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load service
launchctl load ~/Library/LaunchAgents/ai.writeit.daemon.plist
```

## 🏢 Server Multi-User Deployment

### Prerequisites
- **Linux server** (Ubuntu 20.04+ recommended)
- **Python 3.11+** with pip
- **2GB+ RAM** (4GB+ recommended)
- **10GB+ storage** (for user data)
- **SSL certificate** (for HTTPS)

### Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-pip python3.11-venv nginx

# Create WriteIt user
sudo adduser --system --group --shell /bin/bash writeit
sudo mkdir -p /opt/writeit
sudo chown writeit:writeit /opt/writeit
```

### Application Installation
```bash
# Switch to WriteIt user
sudo su - writeit

# Create virtual environment
cd /opt/writeit
python3.11 -m venv venv
source venv/bin/activate

# Install WriteIt with all providers
pip install writeit[openai,anthropic,server]

# Create configuration
mkdir -p config data logs
cat > config/writeit-server.yaml << 'EOF'
server:
  host: "127.0.0.1"
  port: 8000
  workers: 4
  
database:
  path: "/opt/writeit/data/writeit.lmdb"
  
logging:
  level: "INFO"
  file: "/opt/writeit/logs/writeit.log"
  
security:
  session_secret: "your-random-secret-key-here"
  max_users: 100
  rate_limit: "100/minute"

providers:
  openai:
    enabled: true
  anthropic:
    enabled: true
  local:
    enabled: false
EOF
```

### Nginx Configuration
```bash
# Create Nginx configuration
sudo cat > /etc/nginx/sites-available/writeit << 'EOF'
server {
    listen 80;
    server_name writeit.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name writeit.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/writeit.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/writeit.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=writeit:10m rate=10r/s;
    limit_req zone=writeit burst=20 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files
    location /static {
        alias /opt/writeit/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/writeit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d writeit.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

### Process Management (Supervisor)
```bash
# Install Supervisor
sudo apt install supervisor

# Create Supervisor configuration
sudo cat > /etc/supervisor/conf.d/writeit.conf << 'EOF'
[program:writeit]
command=/opt/writeit/venv/bin/writeit server --config /opt/writeit/config/writeit-server.yaml
directory=/opt/writeit
user=writeit
group=writeit
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/writeit/logs/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/writeit/venv/bin"
EOF

# Start WriteIt
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start writeit
```

## 🐳 Container Deployment

### Docker Setup
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    liblmdb-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash writeit

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
RUN chown -R writeit:writeit /app

# Switch to app user
USER writeit

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["writeit", "server", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  writeit:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - writeit_data:/app/data
      - writeit_config:/app/config
    environment:
      - WRITEIT_CONFIG=/app/config/writeit.yaml
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - writeit
    restart: unless-stopped

volumes:
  writeit_data:
  writeit_config:
```

### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: writeit
  labels:
    app: writeit
spec:
  replicas: 3
  selector:
    matchLabels:
      app: writeit
  template:
    metadata:
      labels:
        app: writeit
    spec:
      containers:
      - name: writeit
        image: writeit:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-credentials
              key: openai-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-credentials
              key: anthropic-key
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
          requests:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: writeit-data

---
apiVersion: v1
kind: Service
metadata:
  name: writeit-service
spec:
  selector:
    app: writeit
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: writeit-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

## 🏢 Enterprise Integration

### Active Directory Integration
```python
# config/auth.py
from ldap3 import Server, Connection, ALL

class ADAuthenticator:
    def __init__(self, server_url: str, base_dn: str):
        self.server = Server(server_url, get_info=ALL)
        self.base_dn = base_dn
    
    def authenticate(self, username: str, password: str) -> bool:
        user_dn = f"uid={username},{self.base_dn}"
        try:
            conn = Connection(self.server, user_dn, password, auto_bind=True)
            return True
        except:
            return False
    
    def get_user_groups(self, username: str) -> List[str]:
        # Implementation for group membership
        pass
```

### SSO Integration (SAML/OAuth)
```yaml
# config/sso.yaml
sso:
  enabled: true
  provider: "azure_ad"  # or "okta", "google", "saml"
  
  azure_ad:
    tenant_id: "your-tenant-id"
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    
  saml:
    entity_id: "writeit-production"
    sso_url: "https://sso.company.com/saml/login"
    x509_cert: "/path/to/cert.pem"
```

### Enterprise Monitoring
```yaml
# config/monitoring.yaml
monitoring:
  enabled: true
  
  metrics:
    prometheus:
      enabled: true
      port: 9090
    
  logging:
    syslog:
      enabled: true
      facility: "local0"
    
  alerting:
    slack:
      webhook_url: "https://hooks.slack.com/..."
    email:
      smtp_server: "smtp.company.com"
      from_address: "writeit@company.com"
```

## 📊 Performance Tuning

### Database Optimization
```yaml
# config/performance.yaml
database:
  lmdb:
    map_size: "10GB"  # Adjust based on expected data
    max_readers: 256  # For high concurrency
    sync_mode: "meta_sync"  # Balance durability/performance
    
  caching:
    enabled: true
    max_memory: "1GB"
    ttl: 3600  # 1 hour
```

### Resource Scaling
```yaml
# Horizontal scaling configuration
scaling:
  min_replicas: 2
  max_replicas: 10
  
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## 🔒 Security Considerations

### Network Security
```bash
# Firewall configuration (UFW)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Fail2ban for brute force protection
sudo apt install fail2ban
sudo cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[writeIt-auth]
enabled = true
port = 8000
logpath = /opt/writeit/logs/writeit.log
maxretry = 3
EOF
```

### Data Security
```yaml
# config/security.yaml
security:
  encryption:
    at_rest: true
    key_rotation: true
    key_rotation_days: 90
    
  data_retention:
    user_data_days: 365
    pipeline_logs_days: 90
    system_logs_days: 30
    
  backup:
    enabled: true
    frequency: "daily"
    retention_days: 30
    encryption: true
```

## 🔧 Maintenance

### Backup Procedures
```bash
#!/bin/bash
# backup-writeit.sh

BACKUP_DIR="/backup/writeit/$(date +%Y%m%d)"
DATA_DIR="/opt/writeit/data"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup LMDB database
cp -r $DATA_DIR/*.lmdb $BACKUP_DIR/

# Backup configuration
cp -r /opt/writeit/config $BACKUP_DIR/

# Create archive
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR.tar.gz s3://company-backups/writeit/

# Clean old backups (keep 30 days)
find /backup/writeit/ -name "*.tar.gz" -mtime +30 -delete
```

### Health Monitoring
```bash
#!/bin/bash
# health-check.sh

# Check WriteIt service
if ! systemctl is-active --quiet writeit; then
    echo "ERROR: WriteIt service is not running"
    systemctl restart writeit
fi

# Check disk space
DISK_USAGE=$(df /opt/writeit | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "WARNING: Disk usage is $DISK_USAGE%"
fi

# Check API health
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: WriteIt API is not responding"
fi

# Check log errors
ERROR_COUNT=$(tail -100 /opt/writeit/logs/writeit.log | grep -c ERROR)
if [ $ERROR_COUNT -gt 5 ]; then
    echo "WARNING: $ERROR_COUNT errors in recent logs"
fi
```

### Update Procedures
```bash
#!/bin/bash
# update-writeit.sh

# Backup before update
./backup-writeit.sh

# Update WriteIt
sudo su - writeit -c "
    source /opt/writeit/venv/bin/activate
    pip install --upgrade writeit
"

# Restart services
sudo supervisorctl restart writeit
sudo systemctl reload nginx

# Run health check
./health-check.sh
```

## 📈 Monitoring & Alerting

### Prometheus Metrics
WriteIt exposes metrics for monitoring:

```
# Application metrics
writeit_pipelines_total{status="completed"}
writeit_pipelines_total{status="failed"}
writeit_response_time_seconds{endpoint="/pipeline/start"}
writeit_active_users_current
writeit_llm_tokens_used_total{provider="openai"}

# System metrics
writeit_memory_usage_bytes
writeit_disk_usage_bytes{mount="/opt/writeit"}
writeit_database_size_bytes
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "WriteIt Monitoring",
    "panels": [
      {
        "title": "Pipeline Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(writeit_pipelines_total{status=\"completed\"}[5m]) / rate(writeit_pipelines_total[5m]) * 100"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "graph",
        "targets": [
          {
            "expr": "writeit_active_users_current"
          }
        ]
      }
    ]
  }
}
```

This deployment guide provides comprehensive coverage for running WriteIt at any scale, from individual use to enterprise deployments with thousands of users.