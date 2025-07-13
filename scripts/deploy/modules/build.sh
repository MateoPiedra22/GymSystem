#!/bin/bash

# Módulo de Build para Scripts de Despliegue
# Construye imágenes Docker y maneja el proceso de construcción

# Construir imágenes
build_images() {
    log "🏗️  Construyendo imágenes..."
    
    # Verificar Dockerfile
    validate_dockerfiles
    
    # Preparar argumentos de build
    local build_args=$(prepare_build_args)
    
    # Construir imágenes
    execute_build "$build_args"
    
    # Verificar imágenes construidas
    verify_built_images
    
    success "Imágenes construidas"
}

# Validar Dockerfiles
validate_dockerfiles() {
    log "🔍 Validando Dockerfiles..."
    
    local dockerfiles=("backend/Dockerfile" "web/Dockerfile")
    local errors=0
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ ! -f "$dockerfile" ]]; then
            error "Dockerfile no encontrado: $dockerfile"
            errors=$((errors + 1))
        else
            debug "Dockerfile encontrado: $dockerfile"
        fi
    done
    
    if [[ $errors -gt 0 ]]; then
        error "Errores en Dockerfiles detectados"
        exit 1
    fi
}

# Preparar argumentos de build
prepare_build_args() {
    local build_args=""
    
    if [[ "$FORCE_RECREATE" == "true" ]]; then
        build_args="--no-cache --force-rm"
        debug "Build forzado habilitado"
    fi
    
    # Agregar argumentos específicos por ambiente
    case $ENVIRONMENT in
        "production")
            build_args="$build_args --build-arg NODE_ENV=production --build-arg PYTHON_ENV=production"
            ;;
        "staging")
            build_args="$build_args --build-arg NODE_ENV=staging --build-arg PYTHON_ENV=staging"
            ;;
        "development")
            build_args="$build_args --build-arg NODE_ENV=development --build-arg PYTHON_ENV=development"
            ;;
    esac
    
    echo "$build_args"
}

# Ejecutar build
execute_build() {
    local build_args="$1"
    
    log "🔨 Ejecutando build con argumentos: $build_args"
    
    # Construir imágenes en paralelo si es posible
    if [[ "$PARALLEL_BUILD" == "true" ]]; then
        build_parallel "$build_args"
    else
        build_sequential "$build_args"
    fi
}

# Construir imágenes en paralelo
build_parallel() {
    local build_args="$1"
    
    log "⚡ Construyendo imágenes en paralelo..."
    
    # Construir backend y frontend en paralelo
    docker-compose build $build_args backend &
    local backend_pid=$!
    
    docker-compose build $build_args frontend &
    local frontend_pid=$!
    
    # Esperar a que terminen ambos builds
    wait $backend_pid
    local backend_result=$?
    
    wait $frontend_pid
    local frontend_result=$?
    
    if [[ $backend_result -ne 0 ]] || [[ $frontend_result -ne 0 ]]; then
        error "Error en build paralelo"
        exit 1
    fi
    
    debug "Build paralelo completado"
}

# Construir imágenes secuencialmente
build_sequential() {
    local build_args="$1"
    
    log "🔄 Construyendo imágenes secuencialmente..."
    
    docker-compose build $build_args
    
    if [[ $? -ne 0 ]]; then
        error "Error en build secuencial"
        exit 1
    fi
    
    debug "Build secuencial completado"
}

# Verificar imágenes construidas
verify_built_images() {
    log "✅ Verificando imágenes construidas..."
    
    local required_images=("gym-system-v6_backend" "gym-system-v6_frontend")
    local missing_images=()
    
    for image in "${required_images[@]}"; do
        if ! docker image inspect "$image" &>/dev/null; then
            missing_images+=("$image")
        else
            debug "Imagen encontrada: $image"
        fi
    done
    
    if [[ ${#missing_images[@]} -gt 0 ]]; then
        error "Imágenes faltantes: ${missing_images[*]}"
        exit 1
    fi
    
    # Mostrar información de las imágenes
    show_image_info
}

# Mostrar información de las imágenes
show_image_info() {
    log "📊 Información de imágenes:"
    
    local images=("gym-system-v6_backend" "gym-system-v6_frontend")
    
    for image in "${images[@]}"; do
        if docker image inspect "$image" &>/dev/null; then
            local size=$(docker image inspect "$image" --format='{{.Size}}' | numfmt --to=iec)
            local created=$(docker image inspect "$image" --format='{{.Created}}' | cut -d'T' -f1)
            echo "  $image: $size (creada: $created)"
        fi
    done
}

# Limpiar imágenes no utilizadas
cleanup_images() {
    if [[ "$CLEANUP_IMAGES" == "true" ]]; then
        log "🧹 Limpiando imágenes no utilizadas..."
        
        docker image prune -f
        
        debug "Limpieza de imágenes completada"
    fi
}

# Verificar espacio en disco para build
check_build_space() {
    log "💾 Verificando espacio en disco para build..."
    
    local required_space=2  # GB requeridos para build
    local available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [[ $available_space -lt $required_space ]]; then
        warning "Espacio en disco bajo para build: ${available_space}GB disponible, ${required_space}GB requeridos"
        warning "Considera limpiar imágenes Docker: docker system prune -a"
    else
        debug "Espacio en disco OK para build: ${available_space}GB disponible"
    fi
}

# Optimizar build
optimize_build() {
    if [[ "$OPTIMIZE_BUILD" == "true" ]]; then
        log "⚡ Optimizando build..."
        
        # Usar buildkit si está disponible
        export DOCKER_BUILDKIT=1
        export COMPOSE_DOCKER_CLI_BUILD=1
        
        debug "BuildKit habilitado"
    fi
} 