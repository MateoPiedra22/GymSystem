# 🚀 Guía de Despliegue - Sistema de Gestión de Gimnasio v6

**Guía completa para desplegar el sistema en diferentes entornos**

## 📋 Tabla de Contenidos

1. [Prerrequisitos](#prerrequisitos)
2. [Despliegue Local](#despliegue-local)
3. [Despliegue con Docker](#despliegue-con-docker)
4. [Despliegue en Producción](#despliegue-en-producción)
5. [Cloud Providers](#cloud-providers)
6. [Configuración de Base de Datos](#configuración-de-base-de-datos)
7. [SSL y Seguridad](#ssl-y-seguridad)
8. [Monitoreo y Logs](#monitoreo-y-logs)
9. [Backup y Recuperación](#backup-y-recuperación)
10. [Troubleshooting](#troubleshooting)

## 🔧 Prerrequisitos

### Requisitos del Sistema

#### **Mínimos**
- CPU: 2 cores
- RAM: 4GB
- Almacenamiento: 20GB SSD
- OS: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+

#### **Recomendados**
- CPU: 4 cores
- RAM: 8GB
- Almacenamiento: 50GB SSD
- OS: Ubuntu 22.04 LTS

### Software Necesario

#### **Backend**
- Python 3.9+
- PostgreSQL 13+
- Redis 6+ (opcional pero recomendado)
- Nginx (para producción)

#### **Frontend Web**
- Node.js 18+
- npm 9+

#### **Cliente Desktop**
- Python 3.9+
- PyQt6

## 🏠 Despliegue Local

### **1. Configuración Rápida**

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/gym-system-v6.git
cd gym-system-v6

# Ejecutar script de configuración
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh
```

### **2. Configuración Manual**

#### **Backend**
```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar configuración

# Configurar base de datos
createdb gym_system_db
python init_database.py

# Crear usuario admin
python scripts/create_admin.py

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### **Frontend Web**
```bash
cd web

# Instalar dependencias
npm ci

# Configurar variables de entorno
cp .env.local.example .env.local
nano .env.local  # Editar configuración

# Iniciar en modo desarrollo
npm run dev
```

#### **Cliente Desktop**
```bash
cd cliente

# Instalar dependencias
pip install -r requirements.txt

# Configurar settings
cp config/settings.example.json config/settings.json

# Iniciar aplicación
python main.py
```

## 🐳 Despliegue con Docker

### **1. Docker Compose (Recomendado)**

```bash
# Configurar variables de entorno
cp .env.production.example .env.production
nano .env.production

# Construir y ejecutar
docker-compose up -d

# Verificar estado
docker-compose ps
docker-compose logs -f
```

### **2. Dockerfile Individual**

#### **Backend**
```dockerfile
# Dockerfile en /backend
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Construir imagen
docker build -t gym-backend ./backend

# Ejecutar contenedor
docker run -d \
  --name gym-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  gym-backend
```

#### **Frontend**
```dockerfile
# Dockerfile en /web
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

```bash
# Construir y ejecutar
docker build -t gym-frontend ./web
docker run -d -p 3000:3000 gym-frontend
```

### **3. Docker Compose Completo**

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: gym_system
      POSTGRES_USER: gymuser
      POSTGRES_PASSWORD: gympass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gymuser"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://gymuser:gympass@postgres:5432/gym_system
      REDIS_URL: redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

## 🏭 Despliegue en Producción

### **1. Configuración del Servidor**

#### **Ubuntu 22.04**
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y redis-server
sudo apt install -y nginx
sudo apt install -y certbot python3-certbot-nginx

# Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Docker (opcional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### **2. Configuración de Base de Datos**

```bash
# PostgreSQL
sudo -u postgres psql

-- Crear base de datos y usuario
CREATE DATABASE gym_system;
CREATE USER gymuser WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE gym_system TO gymuser;
ALTER USER gymuser CREATEDB;
\q

# Configurar PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf
# Descomentar y configurar:
# listen_addresses = 'localhost'
# max_connections = 100
# shared_buffers = 256MB

sudo nano /etc/postgresql/15/main/pg_hba.conf
# Añadir línea:
# local   gym_system    gymuser                     md5

sudo systemctl restart postgresql
```

### **3. Configuración del Backend**

```bash
# Crear usuario para la aplicación
sudo useradd -m -s /bin/bash gymapp
sudo su - gymapp

# Clonar código
git clone https://github.com/tu-usuario/gym-system-v6.git
cd gym-system-v6/backend

# Configurar Python
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env
```

#### **Archivo .env de Producción**
```env
# Base de datos
DATABASE_URL=postgresql://gymuser:secure_password@localhost:5432/gym_system
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://localhost:6379/0

# Seguridad
SECRET_KEY=tu_clave_super_secreta_de_64_caracteres_o_mas
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/gym-system/app.log

# Entorno
ENVIRONMENT=production
DEBUG=false
```

```bash
# Inicializar base de datos
python init_database.py

# Crear usuario administrador
python scripts/create_admin.py

# Crear directorios de logs
sudo mkdir -p /var/log/gym-system
sudo chown gymapp:gymapp /var/log/gym-system
```

### **4. Configuración con Gunicorn**

```bash
# Instalar Gunicorn
pip install gunicorn

# Configurar Gunicorn
nano gunicorn.conf.py
```

```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
keepalive = 2
timeout = 30
graceful_timeout = 30
user = "gymapp"
group = "gymapp"
tmp_upload_dir = None
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
}
```

### **5. Servicio Systemd**

```bash
# Crear servicio
sudo nano /etc/systemd/system/gym-backend.service
```

```ini
[Unit]
Description=Gym System Backend
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
User=gymapp
Group=gymapp
WorkingDirectory=/home/gymapp/gym-system-v6/backend
Environment=PATH=/home/gymapp/gym-system-v6/backend/venv/bin
ExecStart=/home/gymapp/gym-system-v6/backend/venv/bin/gunicorn app.main:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable gym-backend
sudo systemctl start gym-backend
sudo systemctl status gym-backend
```

### **6. Configuración del Frontend**

```bash
cd /home/gymapp/gym-system-v6/web

# Instalar dependencias
npm ci --only=production

# Configurar variables de entorno
cp .env.local.example .env.local
nano .env.local
```

```env
# .env.local
NEXT_PUBLIC_API_URL=https://api.tu-gimnasio.com
NEXT_PUBLIC_WS_URL=wss://api.tu-gimnasio.com
NEXT_PUBLIC_ENVIRONMENT=production
```

```bash
# Construir para producción
npm run build

# Configurar PM2 para Node.js
sudo npm install -g pm2

# Crear archivo de configuración PM2
nano ecosystem.config.js
```

```javascript
module.exports = {
  apps: [{
    name: 'gym-frontend',
    script: 'npm',
    args: 'start',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    }
  }]
}
```

```bash
# Iniciar con PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### **7. Configuración de Nginx**

```bash
sudo nano /etc/nginx/sites-available/gym-system
```

```nginx
# /etc/nginx/sites-available/gym-system
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

# Redirigir HTTP a HTTPS
server {
    listen 80;
    server_name tu-gimnasio.com www.tu-gimnasio.com api.tu-gimnasio.com;
    return 301 https://$server_name$request_uri;
}

# Frontend
server {
    listen 443 ssl http2;
    server_name tu-gimnasio.com www.tu-gimnasio.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/tu-gimnasio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-gimnasio.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files caching
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Backend API
server {
    listen 443 ssl http2;
    server_name api.tu-gimnasio.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.tu-gimnasio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tu-gimnasio.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # File uploads
    location /uploads/ {
        client_max_body_size 50M;
        proxy_pass http://backend;
        proxy_request_buffering off;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/gym-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### **8. SSL con Let's Encrypt**

```bash
# Obtener certificados SSL
sudo certbot --nginx -d tu-gimnasio.com -d www.tu-gimnasio.com -d api.tu-gimnasio.com

# Verificar renovación automática
sudo certbot renew --dry-run

# Configurar cron para renovación
sudo crontab -e
# Añadir línea:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## ☁️ Cloud Providers

### **AWS**

#### **EC2 + RDS + ElastiCache**
```bash
# Terraform para infraestructura
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

# VPC
resource "aws_vpc" "gym_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "gym-system-vpc"
  }
}

# Subnet
resource "aws_subnet" "gym_subnet" {
  vpc_id                  = aws_vpc.gym_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-west-2a"
  map_public_ip_on_launch = true

  tags = {
    Name = "gym-system-subnet"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "gym_db" {
  identifier             = "gym-system-db"
  allocated_storage      = 20
  storage_type          = "gp2"
  engine                = "postgres"
  engine_version        = "15.4"
  instance_class        = "db.t3.micro"
  db_name               = "gym_system"
  username              = "gymuser"
  password              = var.db_password
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot   = true

  tags = {
    Name = "gym-system-db"
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "gym_cache" {
  cluster_id           = "gym-system-cache"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  security_group_ids   = [aws_security_group.elasticache.id]
}

# EC2 Instance
resource "aws_instance" "gym_server" {
  ami           = "ami-0c02fb55956c7d316" # Ubuntu 22.04 LTS
  instance_type = "t3.small"
  subnet_id     = aws_subnet.gym_subnet.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
    #!/bin/bash
    apt update
    apt install -y python3.11 python3.11-venv nodejs npm nginx
    # Script de configuración automática
  EOF

  tags = {
    Name = "gym-system-server"
  }
}
```

#### **ECS Fargate**
```yaml
# docker-compose.yml para ECS
version: '3.8'
services:
  backend:
    image: tu-cuenta/gym-backend:latest
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 1G

  frontend:
    image: tu-cuenta/gym-frontend:latest
    ports:
      - "80:3000"
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
    deploy:
      replicas: 2
```

### **Google Cloud Platform**

#### **Cloud Run + Cloud SQL**
```yaml
# cloudbuild.yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/${PROJECT_ID}/gym-backend', './backend']
  
  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/${PROJECT_ID}/gym-frontend', './web']

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'gym-backend', 
           '--image', 'gcr.io/${PROJECT_ID}/gym-backend',
           '--platform', 'managed',
           '--region', 'us-central1']
```

### **Azure**

#### **App Service + Azure Database**
```yaml
# azure-pipelines.yml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: DockerCompose@0
    displayName: 'Build services'
    inputs:
      containerregistrytype: 'Azure Container Registry'
      dockerRegistryEndpoint: 'gym-system-acr'
      dockerComposeFile: 'docker-compose.yml'
      action: 'Build services'

  - task: AzureWebApp@1
    displayName: 'Deploy to Azure Web App'
    inputs:
      azureSubscription: 'gym-system-subscription'
      appName: 'gym-system-app'
      deployToSlotOrASE: true
      resourceGroupName: 'gym-system-rg'
      slotName: 'production'
```

### **Heroku**

```bash
# Preparar para Heroku
echo "web: gunicorn app.main:app -c gunicorn.conf.py" > backend/Procfile
echo "web: npm start" > web/Procfile

# Crear aplicaciones
heroku create gym-system-api
heroku create gym-system-web

# Añadir addons
heroku addons:create heroku-postgresql:hobby-dev -a gym-system-api
heroku addons:create heroku-redis:hobby-dev -a gym-system-api

# Configurar variables
heroku config:set SECRET_KEY=tu_clave_secreta -a gym-system-api
heroku config:set ENVIRONMENT=production -a gym-system-api

# Desplegar
git subtree push --prefix=backend heroku-api main
git subtree push --prefix=web heroku-web main
```

## 📊 Monitoreo y Logs

### **Prometheus + Grafana**

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"

volumes:
  prometheus_data:
  grafana_data:
```

### **ELK Stack**

```yaml
# docker-compose.elk.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.0
    volumes:
      - ./monitoring/logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

## 💾 Backup y Recuperación

### **Script de Backup Automático**

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/gym-system"
mkdir -p $BACKUP_DIR

# Backup de base de datos
pg_dump -h localhost -U gymuser gym_system > $BACKUP_DIR/db_backup_$DATE.sql

# Backup de archivos
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /home/gymapp/gym-system-v6/uploads

# Backup de configuración
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
  /home/gymapp/gym-system-v6/backend/.env \
  /home/gymapp/gym-system-v6/web/.env.local \
  /etc/nginx/sites-available/gym-system

# Limpiar backups antiguos (más de 30 días)
find $BACKUP_DIR -type f -mtime +30 -delete

# Subir a cloud storage (opcional)
# aws s3 sync $BACKUP_DIR s3://gym-system-backups/
```

```bash
# Configurar cron para backup automático
sudo crontab -e
# Añadir línea:
# 0 2 * * * /home/gymapp/scripts/backup.sh
```

### **Script de Restauración**

```bash
#!/bin/bash
# restore.sh

if [ $# -eq 0 ]; then
    echo "Uso: $0 <fecha_backup> (formato: YYYYMMDD_HHMMSS)"
    exit 1
fi

DATE=$1
BACKUP_DIR="/backups/gym-system"

# Restaurar base de datos
sudo -u postgres psql -c "DROP DATABASE IF EXISTS gym_system;"
sudo -u postgres psql -c "CREATE DATABASE gym_system OWNER gymuser;"
psql -h localhost -U gymuser gym_system < $BACKUP_DIR/db_backup_$DATE.sql

# Restaurar archivos
tar -xzf $BACKUP_DIR/files_backup_$DATE.tar.gz -C /

# Reiniciar servicios
sudo systemctl restart gym-backend
sudo systemctl restart nginx

echo "Restauración completa desde backup del $DATE"
```

## 🔧 Troubleshooting

### **Problemas Comunes**

#### **Error de conexión a base de datos**
```bash
# Verificar estado de PostgreSQL
sudo systemctl status postgresql

# Verificar logs
sudo journalctl -u postgresql -f

# Verificar conexiones
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

#### **Error de memoria insuficiente**
```bash
# Verificar uso de memoria
free -h
ps aux --sort=-%mem | head

# Configurar swap si es necesario
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### **Error de permisos**
```bash
# Verificar permisos de archivos
ls -la /home/gymapp/gym-system-v6/

# Corregir permisos
sudo chown -R gymapp:gymapp /home/gymapp/gym-system-v6/
sudo chmod +x /home/gymapp/gym-system-v6/backend/start_server.py
```

#### **Error de SSL**
```bash
# Verificar certificados
sudo certbot certificates

# Renovar certificados
sudo certbot renew

# Verificar configuración de Nginx
sudo nginx -t
```

### **Comandos de Diagnóstico**

```bash
# Estado de servicios
sudo systemctl status gym-backend
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# Logs del sistema
sudo journalctl -u gym-backend -f
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/gym-system/app.log

# Pruebas de conectividad
curl http://localhost:8000/health
curl http://localhost:3000
telnet localhost 5432
telnet localhost 6379

# Uso de recursos
htop
iotop
netstat -tulpn
```

## 📚 Referencias Adicionales

- [Docker Documentation](https://docs.docker.com/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/)
- [Let's Encrypt](https://letsencrypt.org/docs/)
- [AWS Documentation](https://docs.aws.amazon.com/)
- [GCP Documentation](https://cloud.google.com/docs)
- [Azure Documentation](https://docs.microsoft.com/azure/)

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/gym-system-v6/issues)
- **Email**: deploy-support@gym-system.com
- **Discord**: [Canal de Despliegue](https://discord.gg/gym-deploy)

---

*Guía actualizada para Sistema de Gestión de Gimnasio v6.0* 