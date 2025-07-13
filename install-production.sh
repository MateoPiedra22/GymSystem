#!/bin/bash
# Script para instalar el Sistema de Gimnasio en producción

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables globales
APP_USER="gymapp"
APP_DIR="/home/gymapp/gym-system"
DB_PASSWORD=""

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Función para verificar requisitos
check_requirements() {
    log "Verificando requisitos del sistema..."
    
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    
    if ! command -v apt &> /dev/null; then
        log_error "Este script está diseñado para sistemas basados en Debian/Ubuntu"
        exit 1
    fi
    
    log "✅ Requisitos verificados"
}

# Función para actualizar sistema
update_system() {
    log "Actualizando sistema..."
    apt update && apt upgrade -y
    log "✅ Sistema actualizado"
}

# Función para instalar dependencias
install_dependencies() {
    log "Instalando dependencias básicas..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        postgresql \
        postgresql-contrib \
        nginx \
        git \
        certbot \
        python3-certbot-nginx \
        ufw \
        htop \
        curl \
        wget
    log "✅ Dependencias instaladas"
}

# Función para crear usuario de aplicación
create_app_user() {
    log "Creando usuario $APP_USER..."
    useradd -m -s /bin/bash $APP_USER
    usermod -aG sudo $APP_USER
    log "✅ Usuario $APP_USER creado"
}

# Función para configurar PostgreSQL
setup_postgresql() {
    log "Configurando PostgreSQL..."
    
    systemctl start postgresql
    systemctl enable postgresql
    
    # Generar contraseña segura
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    log "Contraseña de base de datos generada: $DB_PASSWORD"
    
    # Crear base de datos y usuario
    sudo -u postgres psql << EOF
CREATE USER gymuser WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE gym_management OWNER gymuser;
GRANT ALL PRIVILEGES ON DATABASE gym_management TO gymuser;
\q
EOF
    
    log "✅ PostgreSQL configurado"
}

# Función para configurar directorio de aplicación
setup_app_directory() {
    log "Configurando directorio de aplicación..."
    cd /home/$APP_USER
    mkdir -p gym-system
    chown -R $APP_USER:$APP_USER /home/$APP_USER
    log "✅ Directorio de aplicación configurado"
}

# Función para solicitar subida de archivos
request_file_upload() {
    log_warning "PAUSA: Necesitas subir tu código al servidor"
    echo "=============================================="
    echo ""
    echo "Opciones para subir archivos:"
    echo "1. Usar Git (recomendado)"
    echo "2. Usar FileZilla"
    echo "3. Usar SCP"
    echo ""
    read -p "Presiona Enter cuando hayas subido los archivos..." dummy
    
    # Verificar que los archivos están
    if [ ! -d "$APP_DIR" ]; then
        log_error "No se encontraron los archivos en $APP_DIR"
        echo "Por favor sube los archivos y ejecuta el script de nuevo"
        exit 1
    fi
    
    log "✅ Archivos verificados"
}

# Función para configurar Python
setup_python() {
    log "Configurando entorno Python..."
    cd $APP_DIR
    sudo -u $APP_USER python3 -m venv venv
    sudo -u $APP_USER venv/bin/pip install --upgrade pip
    sudo -u $APP_USER venv/bin/pip install -r backend/requirements.txt
    log "✅ Python configurado"
}

# Función para configurar Node.js
setup_nodejs() {
    log "Configurando aplicación web..."
    cd $APP_DIR/web
    sudo -u $APP_USER npm install
    sudo -u $APP_USER npm run build
    cd ..
    log "✅ Node.js configurado"
}

# Función para configurar variables de ambiente
setup_environment() {
    log "Configurando variables de ambiente..."
    cat > $APP_DIR/backend/.env << EOF
GYM_ENV=production
GYM_DEBUG=False
GYM_SECRET_KEY=$(openssl rand -hex 32)
GYM_JWT_SECRET_KEY=$(openssl rand -hex 32)
GYM_BACKUP_KEY=$(openssl rand -hex 32)
GYM_DB_HOST=localhost
GYM_DB_USER=gymuser
GYM_DB_PASSWORD=$DB_PASSWORD
GYM_DB_NAME=gym_management
GYM_DB_PORT=5432
EOF
    
    chown $APP_USER:$APP_USER $APP_DIR/backend/.env
    log "✅ Variables de ambiente configuradas"
}

# Función para inicializar base de datos
init_database() {
    log "Inicializando base de datos..."
    sudo -u $APP_USER $APP_DIR/venv/bin/python $APP_DIR/backend/init_database.py
    log "✅ Base de datos inicializada"
}

# Función para crear servicios systemd
create_systemd_services() {
    log "Configurando servicios automáticos..."
    
    # Servicio backend
    cat > /etc/systemd/system/gym-backend.service << EOF
[Unit]
Description=Gym Management Backend
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python backend/start_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Servicio web
    cat > /etc/systemd/system/gym-web.service << EOF
[Unit]
Description=Gym Management Web Frontend
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR/web
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    # Habilitar y iniciar servicios
    systemctl daemon-reload
    systemctl enable gym-backend
    systemctl enable gym-web
    systemctl start gym-backend
    systemctl start gym-web
    
    log "✅ Servicios systemd creados y iniciados"
}

# Función para configurar Nginx
setup_nginx() {
    log "Configurando Nginx..."
    
    cat > /etc/nginx/sites-available/gym-system << EOF
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Habilitar sitio
    ln -sf /etc/nginx/sites-available/gym-system /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # Probar configuración
    nginx -t
    systemctl reload nginx
    
    log "✅ Nginx configurado"
}

# Función para configurar firewall
setup_firewall() {
    log "Configurando firewall..."
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
    log "✅ Firewall configurado"
}

# Función para configurar backups
setup_backups() {
    log "Configurando backups automáticos..."
    
    mkdir -p /home/$APP_USER/backups
    cat > /home/$APP_USER/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/gymapp/backups"
pg_dump -h localhost -U gymuser gym_management > "$BACKUP_DIR/backup_$DATE.sql"
find "$BACKUP_DIR" -name "backup_*.sql" -mtime +7 -delete
echo "✅ Backup creado: backup_$DATE.sql"
EOF

    chmod +x /home/$APP_USER/backup.sh
    chown $APP_USER:$APP_USER /home/$APP_USER/backup.sh

    # Configurar cron para backups diarios
    echo "0 2 * * * /home/$APP_USER/backup.sh" | crontab -u $APP_USER -
    
    log "✅ Backups configurados"
}

# Función para configurar permisos finales
setup_permissions() {
    log "Configurando permisos finales..."
    chown -R $APP_USER:$APP_USER $APP_DIR
    log "✅ Permisos configurados"
}

# Función para mostrar estado de servicios
show_service_status() {
    log "Verificando servicios..."
    systemctl status gym-backend --no-pager -l
    systemctl status gym-web --no-pager -l
    systemctl status nginx --no-pager -l
}

# Función para mostrar información final
show_final_info() {
    local server_ip=$(curl -s ifconfig.me)
    
    echo ""
    echo "✅ ¡Instalación completada!"
    echo "========================="
    echo ""
    echo "🌐 Tu aplicación está disponible en:"
    echo "   http://$server_ip (IP del servidor)"
    echo "   http://tu-dominio.com (si configuraste un dominio)"
    echo ""
    echo "📚 API Documentation:"
    echo "   http://$server_ip/docs"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   Ver logs backend:    journalctl -u gym-backend -f"
    echo "   Ver logs web:        journalctl -u gym-web -f"
    echo "   Reiniciar backend:   systemctl restart gym-backend"
    echo "   Reiniciar web:       systemctl restart gym-web"
    echo "   Estado servicios:    systemctl status gym-backend gym-web nginx"
    echo "   Hacer backup:        /home/$APP_USER/backup.sh"
    echo ""
    echo "🔒 Para SSL/HTTPS (después de configurar tu dominio):"
    echo "   certbot --nginx -d tu-dominio.com -d www.tu-dominio.com"
    echo ""
    echo "📝 IMPORTANTE:"
    echo "   1. Cambia 'tu-dominio.com' en /etc/nginx/sites-available/gym-system"
    echo "   2. Cambia las contraseñas por defecto en $APP_DIR/backend/.env"
    echo "   3. Configura un dominio apuntando a tu IP: $server_ip"
    echo ""
}

# Función principal
main() {
    echo "🏋️ Instalando Sistema de Gimnasio en Producción..."
    echo "=================================================="
    
    check_requirements
    update_system
    install_dependencies
    create_app_user
    setup_postgresql
    setup_app_directory
    request_file_upload
    setup_python
    setup_nodejs
    setup_environment
    init_database
    create_systemd_services
    setup_nginx
    setup_firewall
    setup_backups
    setup_permissions
    show_service_status
    show_final_info
}

# Ejecutar función principal
main 