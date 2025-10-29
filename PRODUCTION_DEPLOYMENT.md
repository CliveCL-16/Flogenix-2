# Flogenix Enterprise Deployment Guide

## 🚀 Production Deployment Instructions

### Prerequisites
- Python 3.9+ installed
- Node.js 18+ installed
- PostgreSQL or MySQL database (for production)
- OpenAI API key
- Domain name and SSL certificate (for production)

### Environment Setup

#### 1. Backend Environment Variables
Create a `.env` file in the `backend` directory:

```bash
# Database Configuration
DATABASE_URL="postgresql://username:password@localhost:5432/flogenix_production"

# Security
SECRET_KEY="your-super-secret-key-here-change-this-in-production"
JWT_SECRET_KEY="your-jwt-secret-key-here-change-this-too"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Configuration
OPENAI_API_KEY="your-openai-api-key"
OPENAI_MODEL="gpt-4"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY="your-azure-key"

# Email Configuration (optional)
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USERNAME="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"

# Redis Configuration (for caching)
REDIS_URL="redis://localhost:6379"

# Application Settings
DEBUG=False
ENVIRONMENT="production"
CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

#### 2. Frontend Environment Variables
Create a `.env` file in the `frontend` directory:

```bash
VITE_API_URL=https://api.yourdomain.com
VITE_WEBSOCKET_URL=wss://api.yourdomain.com
VITE_ENVIRONMENT=production
```

### Database Setup

#### 1. Production Database Migration
```bash
cd backend

# Install production dependencies
pip install psycopg2-binary  # For PostgreSQL
# OR
pip install PyMySQL  # For MySQL

# Run database migrations
python -c "
from app.core.database import engine, Base
from app.core.models import *
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
```

#### 2. Create Admin User
```bash
python -c "
from app.core.database import SessionLocal
from app.core.security import auth_service
from app.core.models import UserRole

db = SessionLocal()
admin_data = {
    'email': 'admin@yourdomain.com',
    'username': 'admin',
    'password': 'YourSecureAdminPassword123!',
    'first_name': 'System',
    'last_name': 'Administrator'
}

admin_user = auth_service.create_user(db, admin_data)
admin_user.role = UserRole.ADMIN
db.commit()
db.close()
print('Admin user created successfully')
"
```

### Backend Deployment

#### Option 1: Docker Deployment (Recommended)

Create `Dockerfile` in backend directory:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main_enterprise:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/flogenix
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: flogenix
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
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
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

Deploy with Docker:
```bash
docker-compose up -d
```

#### Option 2: Traditional Server Deployment

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib redis-server

# Setup Python environment
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install production server
pip install gunicorn uvicorn[standard]

# Start the application
gunicorn main_enterprise:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend Deployment

#### Build for Production
```bash
cd frontend
npm install
npm run build
```

#### Deploy to Web Server
```bash
# Copy built files to web server
sudo cp -r dist/* /var/www/html/

# OR deploy to Nginx
sudo cp -r dist/* /usr/share/nginx/html/
```

#### Nginx Configuration
Create `/etc/nginx/sites-available/flogenix`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    root /usr/share/nginx/html;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /api/notifications/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/flogenix /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate Setup

#### Using Let's Encrypt (Free)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### System Services

#### Backend Service
Create `/etc/systemd/system/flogenix-backend.service`:
```ini
[Unit]
Description=Flogenix Backend API
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/path/to/backend
Environment=PATH=/path/to/backend/venv/bin
ExecStart=/path/to/backend/venv/bin/gunicorn main_enterprise:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable flogenix-backend
sudo systemctl start flogenix-backend
sudo systemctl status flogenix-backend
```

### Monitoring and Logging

#### Application Logging
Backend logs are available at:
- Systemd journal: `sudo journalctl -u flogenix-backend -f`
- Application logs: Check logs directory in backend

#### Health Monitoring
```bash
# Check API health
curl https://yourdomain.com/api/health

# Check WebSocket
wscat -c wss://yourdomain.com/api/notifications/ws?token=YOUR_TOKEN
```

### Performance Optimization

#### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_claims_user_id ON claims(user_id);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_created_at ON claims(created_at);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(is_read);
```

#### Redis Caching
Configure Redis for session storage and caching:
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru

sudo systemctl restart redis
```

#### CDN Setup
- Use CloudFlare or AWS CloudFront for static assets
- Configure proper caching headers
- Enable gzip compression

### Security Checklist

#### ✅ Pre-deployment Security
- [ ] Change all default passwords
- [ ] Use strong, unique SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable database encryption
- [ ] Configure firewall rules
- [ ] Set up backup procedures
- [ ] Enable access logging
- [ ] Implement intrusion detection

#### Firewall Configuration
```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### Backup Strategy

#### Database Backup
```bash
#!/bin/bash
# Create backup script: /usr/local/bin/backup-flogenix.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/flogenix"
DB_NAME="flogenix"

mkdir -p $BACKUP_DIR

# Database backup
pg_dump $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Setup cron job:
```bash
# Add to crontab
0 2 * * * /usr/local/bin/backup-flogenix.sh
```

### Scaling Considerations

#### Load Balancing
For high traffic, consider:
- Multiple backend instances behind load balancer
- Database read replicas
- Redis clustering
- CDN for static assets

#### Container Orchestration
For enterprise scale:
- Kubernetes deployment
- Auto-scaling policies
- Health checks and circuit breakers
- Distributed logging and monitoring

### Troubleshooting

#### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   sudo systemctl status postgresql
   
   # Check connections
   sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
   ```

2. **CORS Issues**
   - Verify CORS_ORIGINS in environment variables
   - Check browser developer console
   - Ensure frontend URL matches CORS settings

3. **WebSocket Connection Fails**
   - Check proxy configuration
   - Verify authentication token
   - Check firewall rules

4. **High Memory Usage**
   ```bash
   # Monitor memory
   htop
   
   # Check application memory
   ps aux | grep gunicorn
   ```

#### Performance Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Application metrics
curl https://yourdomain.com/api/admin/metrics
```

### Maintenance

#### Regular Tasks
- [ ] Update dependencies monthly
- [ ] Monitor disk space
- [ ] Review application logs
- [ ] Test backup restoration
- [ ] Security updates
- [ ] SSL certificate renewal
- [ ] Performance optimization
- [ ] Database maintenance

#### Update Procedure
```bash
# 1. Backup system
/usr/local/bin/backup-flogenix.sh

# 2. Update backend
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt

# 3. Update frontend
cd frontend
npm update
npm run build

# 4. Restart services
sudo systemctl restart flogenix-backend
sudo systemctl reload nginx

# 5. Verify deployment
curl https://yourdomain.com/api/health
```

### Support and Documentation

#### API Documentation
- Production API docs: `https://yourdomain.com/docs`
- OpenAPI spec: `https://yourdomain.com/openapi.json`

#### Monitoring Dashboards
- System health: `https://yourdomain.com/api/health`
- Admin metrics: `https://yourdomain.com/admin/dashboard`

For additional support or enterprise features, contact the development team.

---

**🎉 Congratulations! Your Flogenix Enterprise system is now ready for production deployment.**