"""
Script de inicialización de la base de datos
Este script se puede ejecutar directamente para inicializar la base de datos
"""
import os
import sys
import uuid
import secrets
import string
from datetime import datetime, date, time

# Añadir el directorio parent al path para permitir las importaciones
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.core.database import init_database, create_test_database
from app.core.config import settings
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_secure_password(length=16):
    """Genera contraseña segura aleatoria"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Verificar que cumple criterios de seguridad
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in "!@#$%^&*" for c in password)):
            return password

def create_user_safely(db, user_data):
    """Crear usuario de forma segura con manejo de errores"""
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(user_data['model']).filter(
            user_data['model'].email == user_data['email']
        ).first()
        
        if existing_user:
            logger.warning(f"Usuario {user_data['email']} ya existe, omitiendo creación")
            return existing_user
        
        # Crear nuevo usuario
        user = user_data['model']()
        for key, value in user_data.items():
            if key != 'model':
                setattr(user, key, value)
        
        db.add(user)
        db.flush()  # Para obtener el ID sin hacer commit
        logger.info(f"Usuario {user_data['email']} creado con éxito")
        return user
        
    except Exception as e:
        logger.error(f"Error creando usuario {user_data['email']}: {e}")
        db.rollback()
        return None

def _create_test_users(db):
    """Crear usuarios de prueba"""
    from app.models.usuarios import Usuario
    from app.core.auth import get_password_hash
    
    # Generar contraseñas seguras
    test_password = generate_secure_password()
    instructor_password = generate_secure_password()
    
    # Crear usuario de prueba
    test_user_data = {
        'model': Usuario,
        'id': str(uuid.uuid4()),
        'username': "test",
        'email': "test@gymsoft.com",
        'nombre': "Usuario",
        'apellido': "Prueba",
        'hashed_password': get_password_hash(test_password),
        'salt': "",
        'es_admin': False,
        'esta_activo': True,
        'fecha_registro': datetime.utcnow()
    }
    
    test_user = create_user_safely(db, test_user_data)
    if not test_user:
        logger.error("Error creando usuario de prueba")
        return None, None
    
    logger.info("Usuario de prueba creado con éxito")
    
    # Crear instructor de ejemplo
    instructor_user_data = {
        'model': Usuario,
        'id': str(uuid.uuid4()),
        'username': "instructor1",
        'email': "instructor1@gymsoft.com",
        'nombre': "Carlos",
        'apellido': "Mendoza",
        'hashed_password': get_password_hash(instructor_password),
        'salt': "",
        'es_admin': False,
        'esta_activo': True,
        'fecha_registro': datetime.utcnow()
    }
    
    instructor_user = create_user_safely(db, instructor_user_data)
    if not instructor_user:
        logger.error("Error creando instructor de prueba")
        return test_user, None
    
    logger.info("Instructor de ejemplo creado con éxito")
    
    return test_user, instructor_user

def _create_instructor_employee(db, instructor_user):
    """Crear empleado instructor"""
    from app.models.empleados import Empleado, Departamento, TipoContrato, EstadoEmpleado
    
    try:
        instructor_empleado = Empleado()
        instructor_empleado.numero_empleado = "EMP-2024-002"
        instructor_empleado.nombre = "Carlos"
        instructor_empleado.apellido = "Mendoza"
        instructor_empleado.email = "instructor1@gymsoft.com"
        instructor_empleado.telefono = "987654321"
        instructor_empleado.direccion = "Av. Fitness 123"
        instructor_empleado.fecha_nacimiento = date(1985, 5, 15)
        instructor_empleado.dni = "12345678"
        instructor_empleado.cargo = "Instructor Senior"
        instructor_empleado.departamento = Departamento.ENTRENAMIENTO
        instructor_empleado.fecha_ingreso = date(2023, 1, 15)
        instructor_empleado.tipo_contrato = TipoContrato.TIEMPO_COMPLETO
        instructor_empleado.estado = EstadoEmpleado.ACTIVO
        instructor_empleado.salario_base = 2500.00
        instructor_empleado.comisiones_porcentaje = 5.0
        instructor_empleado.usuario_id = instructor_user.id
        instructor_empleado.certificaciones = '["Certificación Personal Trainer", "Nutrición Deportiva", "CrossFit Level 2"]'
        
        db.add(instructor_empleado)
        db.flush()
        logger.info("Instructor de ejemplo creado con éxito")
        return instructor_empleado
        
    except Exception as e:
        logger.error(f"Error creando empleado instructor: {e}")
        db.rollback()
        return None

def _create_sample_class(db, instructor_empleado, test_user):
    """Crear clase de ejemplo"""
    from app.models.clases import Clase, HorarioClase, DiaSemana, NivelDificultad
    
    try:
        # Crear clase
        clase_template = Clase()
        clase_template.nombre = "CrossFit Beginners"
        clase_template.descripcion = "Clase de introducción a CrossFit para principiantes"
        clase_template.duracion_minutos = 60
        clase_template.capacidad_maxima = 15
        clase_template.nivel = NivelDificultad.PRINCIPIANTE
        clase_template.esta_activa = True
        
        db.add(clase_template)
        db.flush()

        # Crear horario asociado
        horario = HorarioClase()
        horario.dia = DiaSemana.LUNES
        horario.hora_inicio = time(18, 0)
        horario.capacidad_maxima = 15
        horario.plazas_disponibles = 15
        horario.clase_id = clase_template.id
        horario.instructor_id = instructor_empleado.id
        
        db.add(horario)

        # Inscribir usuario de prueba a la clase/hora
        if test_user:
            horario.participantes.append(test_user)
        
        logger.info("Clase de ejemplo creada con éxito")
        return clase_template
        
    except Exception as e:
        logger.error(f"Error creando clase de ejemplo: {e}")
        db.rollback()
        return None

def _create_sample_exercises_and_routine(db, test_user, instructor_id_fallback):
    """Crear ejercicios y rutina de ejemplo"""
    from app.models.rutinas import Ejercicio, Rutina, TipoEjercicio, NivelDificultad
    
    try:
        # Crear ejercicios base
        ejercicio_pushups = Ejercicio()
        ejercicio_pushups.nombre = "Push Ups"
        ejercicio_pushups.descripcion = "Flexiones clásicas de pecho"
        ejercicio_pushups.tipo = TipoEjercicio.FUERZA
        ejercicio_pushups.dificultad = NivelDificultad.PRINCIPIANTE
        ejercicio_pushups.musculos_trabajados = "Pectorales, Tríceps, Hombros"
        
        ejercicio_squat = Ejercicio()
        ejercicio_squat.nombre = "Air Squats"
        ejercicio_squat.descripcion = "Sentadillas con peso corporal"
        ejercicio_squat.tipo = TipoEjercicio.FUERZA
        ejercicio_squat.dificultad = NivelDificultad.PRINCIPIANTE
        ejercicio_squat.musculos_trabajados = "Cuádriceps, Glúteos"
        
        db.add_all([ejercicio_pushups, ejercicio_squat])

        # Crear rutina básica
        rutina_basica = Rutina()
        rutina_basica.nombre = "Rutina Principiante 1"
        rutina_basica.descripcion = "Rutina básica de cuerpo completo para nuevos socios"
        rutina_basica.nivel = NivelDificultad.PRINCIPIANTE
        rutina_basica.usuario_id = test_user.id if test_user else ""
        rutina_basica.creador_id = instructor_id_fallback
        rutina_basica.duracion_estimada = 45
        rutina_basica.calorias_estimadas = 300
        rutina_basica.dias_semana = ["Lunes", "Miércoles", "Viernes"]
        rutina_basica.objetivo = "Mejorar la fuerza general"
        
        rutina_basica.ejercicios.extend([ejercicio_pushups, ejercicio_squat])
        db.add(rutina_basica)
        
        logger.info("Ejercicios y rutina de ejemplo creados con éxito")
        return True
        
    except Exception as e:
        logger.error(f"Error creando ejercicios y rutina: {e}")
        db.rollback()
        return False

def _create_sample_payment(db, test_user):
    """Crear pago de ejemplo"""
    from app.models.pagos import Pago, MetodoPago, EstadoPago, ConceptoPago
    from app.models.tipos_cuota import TipoCuota
    
    try:
        tipo_cuota_basica = db.query(TipoCuota).filter(TipoCuota.codigo == "MENS-BAS").first()
        if tipo_cuota_basica and test_user:
            pago_id = str(uuid.uuid4())
            pago_ejemplo = Pago()
            pago_ejemplo.id = pago_id
            pago_ejemplo.numero_recibo = "REC-2024-00001"
            pago_ejemplo.monto = tipo_cuota_basica.precio
            pago_ejemplo.monto_pagado = tipo_cuota_basica.precio
            pago_ejemplo.monto_final = tipo_cuota_basica.precio
            pago_ejemplo.metodo_pago = MetodoPago.EFECTIVO
            pago_ejemplo.estado = EstadoPago.PAGADO
            pago_ejemplo.concepto = ConceptoPago.MEMBRESIA
            pago_ejemplo.usuario_id = test_user.id
            pago_ejemplo.tipo_cuota_id = tipo_cuota_basica.id
            pago_ejemplo.descripcion = "Pago de membresía mensual básica"
            
            db.add(pago_ejemplo)
            logger.info("Pago de ejemplo creado con éxito")
            return True
        else:
            logger.warning("No se pudo crear pago de ejemplo (tipo de cuota o usuario no encontrado)")
            return False
            
    except Exception as e:
        logger.error(f"Error creando pago de ejemplo: {e}")
        db.rollback()
        return False

def populate_test_data():
    """Poblar la base de datos con datos de prueba"""
    if settings.ENV != "development":
        logger.warning("Ignorando población de datos de prueba en entorno no-desarrollo")
        return False
    
    try:
        from app.core.database import SessionLocal
        from app.models.usuarios import Usuario
        
        db = SessionLocal()
        
        # Verificar si ya existe un usuario admin
        admin_exists = db.query(Usuario).filter(Usuario.username == "admin").first()
        
        if not admin_exists:
            logger.info("El usuario admin no existe, será creado por el script de arranque. Creando otros usuarios de prueba.")
            
            # Crear usuarios de prueba
            test_user, instructor_user = _create_test_users(db)
            if not test_user or not instructor_user:
                db.close()
                return False
            
            # Obtener el admin creado por el script de arranque para asociarlo como creador
            admin_user = db.query(Usuario).filter(Usuario.username == settings.ADMIN_USERNAME).first()
            instructor_id_fallback = admin_user.id if admin_user else None
            
            # Crear empleado instructor
            instructor_empleado = _create_instructor_employee(db, instructor_user)
            if not instructor_empleado:
                db.close()
                return False
            
            # Crear datos adicionales de prueba
            try:
                # Crear clase de ejemplo
                _create_sample_class(db, instructor_empleado, test_user)
                
                # Crear ejercicios y rutina
                _create_sample_exercises_and_routine(db, test_user, instructor_id_fallback)
                
                # Crear pago de ejemplo
                _create_sample_payment(db, test_user)
                
                db.commit()
                logger.info("Datos adicionales de prueba creados (clases, rutina, pago)")
                
            except Exception as e:
                logger.error(f"Error creando datos adicionales de prueba: {e}")
                db.rollback()
                db.close()
                return False
            
        else:
            logger.info("Usuarios de prueba ya existen, omitiendo creación")
            
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Error al insertar datos de prueba: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

if __name__ == "__main__":
    # Este bloque permite ejecutar este script directamente para inicializar la BD
    logger.info("Iniciando proceso de inicialización de base de datos...")
    
    try:
        init_result = init_database()
        
        if init_result:
            logger.info("Base de datos inicializada correctamente")
            
            if "--with-test-data" in sys.argv or settings.ENV == "development":
                logger.info("Poblando base de datos con datos de prueba...")
                populate_result = populate_test_data()
                if populate_result:
                    logger.info("Datos de prueba creados exitosamente")
                else:
                    logger.error("Error creando datos de prueba")
                    sys.exit(1)
        else:
            logger.error("Error al inicializar la base de datos")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error inesperado durante la inicialización: {e}")
        sys.exit(1)
