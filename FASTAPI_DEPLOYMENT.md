# FastAPI Deployment Guide

## 1. Server Requirements

### System Requirements
- Python 3.8 or higher
- Git
- Nginx
- Supervisor (for process management)

### Python Dependencies
```bash
pip install fastapi uvicorn gunicorn torch transformers pandas httpx python-dotenv
```

## 2. Project Structure Setup

Create a production-ready project structure:

```
/opt/nuanz-fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py           # Your app.py renamed to main.py
│   ├── mf_client.py
│   └── models/
├── requirements.txt
├── gunicorn_config.py
└── .env
```

## 3. Create Requirements File

```bash
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
gunicorn==21.2.0
torch==2.1.0
transformers==4.34.1
pandas==2.1.2
httpx==0.25.1
python-dotenv==1.0.0
```

## 4. Gunicorn Configuration

Create `gunicorn_config.py`:

```python
# gunicorn_config.py
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = "unix:/tmp/nuanz-fastapi.sock"
accesslog = "/var/log/nuanz-fastapi/access.log"
errorlog = "/var/log/nuanz-fastapi/error.log"
```

## 5. Nginx Configuration

Create an Nginx configuration file:

```nginx
# /etc/nginx/sites-available/nuanz-fastapi.conf
server {
    listen 80;
    server_name boondfs.in www.boondfs.in;

    location / {
        proxy_pass http://unix:/tmp/nuanz-fastapi.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
    }

    # SSL configuration (once you have SSL certificates)
    # listen 443 ssl;
    # ssl_certificate /path/to/fullchain.pem;
    # ssl_certificate_key /path/to/privkey.pem;
}
```

## 6. Supervisor Configuration

Create a supervisor configuration:

```ini
# /etc/supervisor/conf.d/nuanz-fastapi.conf
[program:nuanz-fastapi]
directory=/opt/nuanz-fastapi
command=gunicorn -c gunicorn_config.py app.main:app
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/nuanz-fastapi/supervisor-err.log
stdout_logfile=/var/log/nuanz-fastapi/supervisor-out.log
```

## 7. Deployment Steps

1. **Server Setup**:
   ```bash
   # Install system dependencies
   sudo apt update
   sudo apt install python3-pip python3-dev nginx supervisor

   # Create project directory
   sudo mkdir -p /opt/nuanz-fastapi
   sudo chown -R www-data:www-data /opt/nuanz-fastapi

   # Create log directory
   sudo mkdir -p /var/log/nuanz-fastapi
   sudo chown -R www-data:www-data /var/log/nuanz-fastapi
   ```

2. **Clone and Setup Project**:
   ```bash
   cd /opt
   sudo -u www-data git clone https://github.com/gkyuva1000/nuanz-fast-api-service.git nuanz-fastapi
   cd nuanz-fastapi
   sudo -u www-data pip install -r requirements.txt
   ```

3. **Configure Nginx**:
   ```bash
   # Create and enable site configuration
   sudo ln -s /etc/nginx/sites-available/nuanz-fastapi.conf /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **Start Application**:
   ```bash
   # Start supervisor
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start nuanz-fastapi
   ```

5. **Monitor Logs**:
   ```bash
   # Check application logs
   sudo tail -f /var/log/nuanz-fastapi/access.log
   sudo tail -f /var/log/nuanz-fastapi/error.log
   ```

## 8. SSL Configuration

1. Install Certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. Obtain SSL certificate:
   ```bash
   sudo certbot --nginx -d boondfs.in -d www.boondfs.in
   ```

## 9. Environment Variables

Create `.env` file in the project root:

```env
ENVIRONMENT=production
ALLOW_ORIGINS=https://boondfs.in,https://www.boondfs.in
```

## 10. Update FastAPI CORS Settings

Update your FastAPI application to use environment variables for CORS:

```python
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOW_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Maintenance and Monitoring

1. **Restart Application**:
   ```bash
   sudo supervisorctl restart nuanz-fastapi
   ```

2. **View Logs**:
   ```bash
   # Application logs
   sudo tail -f /var/log/nuanz-fastapi/access.log
   sudo tail -f /var/log/nuanz-fastapi/error.log
   
   # Supervisor logs
   sudo tail -f /var/log/nuanz-fastapi/supervisor-err.log
   sudo tail -f /var/log/nuanz-fastapi/supervisor-out.log
   ```

3. **Update Application**:
   ```bash
   cd /opt/nuanz-fastapi
   sudo -u www-data git pull
   sudo supervisorctl restart nuanz-fastapi
   ```

## Troubleshooting

1. Check application status:
   ```bash
   sudo supervisorctl status nuanz-fastapi
   ```

2. Check Nginx status:
   ```bash
   sudo systemctl status nginx
   ```

3. Test Nginx configuration:
   ```bash
   sudo nginx -t
   ```

4. Check for errors in logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```