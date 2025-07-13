#!/bin/bash
# Script automático para desplegar en Heroku

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
APP_NAME=""
HEROKU_REGION="us"
DATABASE_PLAN="mini"

# Función de logging
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Verificar prerequisitos
check_prerequisites() {
    log "🔍 Verificando prerequisitos..."
    
    local errors=0
    
    # Verificar Heroku CLI
    if ! command -v heroku &> /dev/null; then
        error "Heroku CLI no está instalado"
        echo "📥 Descárgalo desde: https://devcenter.heroku.com/articles/heroku-cli"
        errors=$((errors + 1))
    else
        success "Heroku CLI encontrado"
    fi
    
    # Verificar Git
    if ! command -v git &> /dev/null; then
        error "Git no está instalado"
        echo "📥 Descárgalo desde: https://git-scm.com/"
        errors=$((errors + 1))
    else
        success "Git encontrado"
    fi
    
    # Verificar Node.js (para build del frontend)
    if ! command -v node &> /dev/null; then
        warning "Node.js no está instalado"
        echo "📥 Descárgalo desde: https://nodejs.org/"
    else
        success "Node.js encontrado"
    fi
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 no está instalado"
        errors=$((errors + 1))
    else
        success "Python 3 encontrado"
    fi
    
    # Verificar archivos necesarios
    check_required_files
    
    if [[ $errors -gt 0 ]]; then
        error "Errores de prerequisitos detectados. Corrige antes de continuar."
        exit 1
    fi
    
    success "Prerequisitos verificados"
}

# Verificar archivos necesarios
check_required_files() {
    log "📁 Verificando archivos necesarios..."
    
    local required_files=(
        "backend/requirements.txt"
        "backend/app/main.py"
        "web/package.json"
        "docker-compose.yml"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        error "Archivos faltantes:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi
    
    success "Archivos necesarios encontrados"
    return 0
}

# Validar nombre de aplicación
validate_app_name() {
    local name="$1"
    
    # Verificar formato
    if [[ ! "$name" =~ ^[a-z0-9-]+$ ]]; then
        error "Nombre inválido: solo letras minúsculas, números y guiones"
        return 1
    fi
    
    # Verificar longitud
    if [[ ${#name} -lt 3 ]] || [[ ${#name} -gt 30 ]]; then
        error "Nombre inválido: debe tener entre 3 y 30 caracteres"
        return 1
    fi
    
    # Verificar si ya existe
    if heroku apps:info --app "$name" &>/dev/null; then
        error "La aplicación '$name' ya existe en Heroku"
        return 1
    fi
    
    return 0
}

# Obtener nombre de aplicación
get_app_name() {
    log "📝 Configurando nombre de aplicación..."
    
    while true; do
        echo "¿Cómo quieres llamar tu aplicación en Heroku?"
        echo "   (solo letras minúsculas, números y guiones)"
        read -p "Nombre: " APP_NAME
        
        if validate_app_name "$APP_NAME"; then
            success "Nombre de aplicación válido: $APP_NAME"
            break
        fi
    done
}

# Configurar Git
setup_git() {
    log "🔧 Configurando Git..."
    
    # Inicializar Git si no existe
    if [[ ! -d ".git" ]]; then
        log "Inicializando repositorio Git..."
        git init
        
        # Configurar .gitignore si no existe
        if [[ ! -f ".gitignore" ]]; then
            create_gitignore
        fi
        
        git add .
        git commit -m "Primera versión del sistema de gimnasio"
        success "Repositorio Git inicializado"
    else
        success "Repositorio Git ya existe"
    fi
}

# Crear .gitignore
create_gitignore() {
    log "📄 Creando .gitignore..."
    
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
.env
.env.local
.env.production

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.next/
out/
build/
dist/

# Logs
logs/
*.log

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Heroku
.env.production
EOF
    
    success ".gitignore creado"
}

# Crear aplicación en Heroku
create_heroku_app() {
    log "🌐 Creando aplicación '$APP_NAME' en Heroku..."
    
    if heroku create "$APP_NAME" --region "$HEROKU_REGION"; then
        success "Aplicación creada: $APP_NAME"
    else
        error "Error al crear aplicación en Heroku"
        exit 1
    fi
}

# Configurar base de datos
setup_database() {
    log "🗄️ Configurando base de datos PostgreSQL..."
    
    if heroku addons:create "heroku-postgresql:$DATABASE_PLAN" --app "$APP_NAME"; then
        success "Base de datos PostgreSQL configurada"
        
        # Obtener URL de la base de datos
        local db_url=$(heroku config:get DATABASE_URL --app "$APP_NAME")
        if [[ -n "$db_url" ]]; then
            log "URL de base de datos obtenida"
        fi
    else
        error "Error al configurar base de datos"
        exit 1
    fi
}

# Configurar variables de ambiente
setup_environment() {
    log "⚙️ Configurando variables de ambiente..."
    
    local env_vars=(
        "GYM_ENV=production"
        "GYM_DEBUG=False"
        "GYM_SECRET_KEY=$(openssl rand -hex 32)"
        "GYM_JWT_SECRET_KEY=$(openssl rand -hex 32)"
        "GYM_DB_URL=\$DATABASE_URL"
        "GYM_REDIS_URL=\$REDIS_URL"
        "GYM_ALLOWED_HOSTS=$APP_NAME.herokuapp.com"
        "GYM_CORS_ORIGINS=https://$APP_NAME.herokuapp.com"
    )
    
    for var in "${env_vars[@]}"; do
        if heroku config:set "$var" --app "$APP_NAME"; then
            log "Variable configurada: ${var%%=*}"
        else
            warning "Error al configurar: ${var%%=*}"
        fi
    done
    
    success "Variables de ambiente configuradas"
}

# Crear archivos de configuración para Heroku
create_heroku_files() {
    log "📄 Creando archivos de configuración para Heroku..."
    
    # Crear Procfile
    create_procfile
    
    # Crear requirements.txt en el root
    create_root_requirements
    
    # Crear runtime.txt
    create_runtime_txt
    
    # Crear app.json
    create_app_json
    
    success "Archivos de configuración creados"
}

# Crear Procfile
create_procfile() {
    cat > Procfile << 'EOF'
web: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
EOF
    log "Procfile creado"
}

# Crear requirements.txt en el root
create_root_requirements() {
    if [[ -f "backend/requirements.txt" ]]; then
        cp backend/requirements.txt ./
        log "requirements.txt copiado al root"
    fi
}

# Crear runtime.txt
create_runtime_txt() {
    local python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "python-$python_version" > runtime.txt
    log "runtime.txt creado con Python $python_version"
}

# Crear app.json
create_app_json() {
    cat > app.json << EOF
{
  "name": "Gym System v6",
  "description": "Sistema de gestión para gimnasios",
  "repository": "https://github.com/tu-usuario/gym-system-v6",
  "logo": "https://node-js-sample.herokuapp.com/node.png",
  "keywords": ["python", "fastapi", "gym", "management"],
  "env": {
    "GYM_ENV": {
      "description": "Ambiente de la aplicación",
      "value": "production"
    },
    "GYM_DEBUG": {
      "description": "Modo debug",
      "value": "False"
    }
  },
  "addons": [
    "heroku-postgresql:mini",
    "heroku-redis:mini"
  ],
  "buildpacks": [
    {
      "url": "heroku/python"
    },
    {
      "url": "heroku/nodejs"
    }
  ]
}
EOF
    log "app.json creado"
}

# Hacer commit y deploy
deploy_to_heroku() {
    log "🚀 Desplegando a Heroku..."
    
    # Hacer commit de los cambios
    git add .
    if git commit -m "Configuración para Heroku - $APP_NAME"; then
        success "Cambios committeados"
    else
        warning "No hay cambios para committear"
    fi
    
    # Desplegar a Heroku
    if git push heroku main; then
        success "Despliegue completado"
    else
        error "Error en el despliegue"
        exit 1
    fi
}

# Inicializar base de datos
init_database() {
    log "🔧 Inicializando base de datos..."
    
    if heroku run python backend/init_database.py --app "$APP_NAME"; then
        success "Base de datos inicializada"
    else
        warning "Error al inicializar base de datos"
        log "Puedes inicializarla manualmente con: heroku run python backend/init_database.py --app $APP_NAME"
    fi
}

# Mostrar información final
show_final_info() {
    echo ""
    success "¡Despliegue completado!"
    echo ""
    echo "🌐 Tu aplicación está disponible en:"
    echo "   https://$APP_NAME.herokuapp.com"
    echo ""
    echo "📚 Documentación de la API:"
    echo "   https://$APP_NAME.herokuapp.com/docs"
    echo ""
    echo "🔧 Comandos útiles:"
    echo "   Ver logs:     heroku logs --tail --app $APP_NAME"
    echo "   Abrir app:    heroku open --app $APP_NAME"
    echo "   Ver info:     heroku info --app $APP_NAME"
    echo "   Ver config:   heroku config --app $APP_NAME"
    echo "   Escalar:      heroku ps:scale web=1 --app $APP_NAME"
    echo ""
    echo "⚠️  IMPORTANTE:"
    echo "   - Verifica que la aplicación esté funcionando"
    echo "   - Configura un dominio personalizado si es necesario"
    echo "   - Monitorea los logs para detectar problemas"
    echo ""
}

# Función principal
main() {
    echo "🚀 Configurando despliegue automático en Heroku..."
    echo ""
    
    check_prerequisites
    get_app_name
    setup_git
    create_heroku_app
    setup_database
    setup_environment
    create_heroku_files
    deploy_to_heroku
    init_database
    show_final_info
}

# Ejecutar script principal
main "$@" 