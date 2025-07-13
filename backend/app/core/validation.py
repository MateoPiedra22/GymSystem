import re
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date
from pydantic import BaseModel, validator, ValidationError
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

class ValidationRule:
    """Regla de validación personalizada"""
    
    def __init__(self, name: str, validator_func: Callable, error_message: str):
        self.name = name
        self.validator_func = validator_func
        self.error_message = error_message

class AdvancedValidator:
    """Validador avanzado con reglas personalizadas"""
    
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Registrar reglas de validación por defecto"""
        
        # Validación de email
        def validate_email_format(value: str) -> bool:
            try:
                validate_email(value)
                return True
            except EmailNotValidError:
                return False
        
        self.add_rule("email", validate_email_format, "Email inválido")
        
        # Validación de teléfono
        def validate_phone(value: str) -> bool:
            # Formato: +XX-XXX-XXX-XXXX o XXX-XXX-XXXX
            phone_pattern = r'^(\+\d{1,3}-)?\d{3}-\d{3}-\d{4}$'
            return bool(re.match(phone_pattern, value))
        
        self.add_rule("phone", validate_phone, "Formato de teléfono inválido")
        
        # Validación de DNI
        def validate_dni(value: str) -> bool:
            # DNI argentino: 8 dígitos
            dni_pattern = r'^\d{8}$'
            return bool(re.match(dni_pattern, value))
        
        self.add_rule("dni", validate_dni, "DNI inválido (debe tener 8 dígitos)")
        
        # Validación de código postal
        def validate_postal_code(value: str) -> bool:
            # Código postal argentino: 4 dígitos
            postal_pattern = r'^\d{4}$'
            return bool(re.match(postal_pattern, value))
        
        self.add_rule("postal_code", validate_postal_code, "Código postal inválido")
        
        # Validación de contraseña fuerte
        def validate_strong_password(value: str) -> bool:
            # Mínimo 8 caracteres, al menos una mayúscula, una minúscula, un número
            password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$'
            return bool(re.match(password_pattern, value))
        
        self.add_rule("strong_password", validate_strong_password, 
                     "La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número")
        
        # Validación de fecha futura
        def validate_future_date(value: Union[str, date, datetime]) -> bool:
            if isinstance(value, str):
                try:
                    value = datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return False
            
            return value > datetime.now()
        
        self.add_rule("future_date", validate_future_date, "La fecha debe ser futura")
        
        # Validación de fecha pasada
        def validate_past_date(value: Union[str, date, datetime]) -> bool:
            if isinstance(value, str):
                try:
                    value = datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return False
            
            return value < datetime.now()
        
        self.add_rule("past_date", validate_past_date, "La fecha debe ser pasada")
        
        # Validación de rango de edad
        def validate_age_range(min_age: int = 0, max_age: int = 120):
            def validator(value: int) -> bool:
                return min_age <= value <= max_age
            return validator
        
        self.add_rule("age_range", validate_age_range(0, 120), "Edad fuera del rango válido (0-120)")
        
        # Validación de monto positivo
        def validate_positive_amount(value: float) -> bool:
            return value > 0
        
        self.add_rule("positive_amount", validate_positive_amount, "El monto debe ser positivo")
        
        # Validación de porcentaje
        def validate_percentage(value: float) -> bool:
            return 0 <= value <= 100
        
        self.add_rule("percentage", validate_percentage, "El porcentaje debe estar entre 0 y 100")
    
    def add_rule(self, name: str, validator_func: Callable, error_message: str):
        """Agregar una nueva regla de validación"""
        self.rules[name] = ValidationRule(name, validator_func, error_message)
        logger.info(f"Regla de validación agregada: {name}")
    
    def validate(self, value: Any, rule_name: str) -> tuple[bool, Optional[str]]:
        """Validar un valor usando una regla específica"""
        if rule_name not in self.rules:
            return False, f"Regla de validación '{rule_name}' no encontrada"
        
        rule = self.rules[rule_name]
        try:
            is_valid = rule.validator_func(value)
            return is_valid, None if is_valid else rule.error_message
        except Exception as e:
            logger.error(f"Error en validación {rule_name}: {e}")
            return False, f"Error en validación: {str(e)}"
    
    def validate_multiple(self, data: Dict[str, Any], rules: Dict[str, str]) -> Dict[str, List[str]]:
        """Validar múltiples campos con diferentes reglas"""
        errors = {}
        
        for field, rule_name in rules.items():
            if field in data:
                is_valid, error_message = self.validate(data[field], rule_name)
                if not is_valid:
                    if field not in errors:
                        errors[field] = []
                    errors[field].append(error_message)
        
        return errors

# Instancia global del validador
validator_instance = AdvancedValidator()

# Modelos Pydantic con validaciones avanzadas
class UserValidation(BaseModel):
    """Modelo de validación para usuarios"""
    
    email: str
    password: str
    phone: Optional[str] = None
    dni: Optional[str] = None
    age: Optional[int] = None
    
    @validator('email')
    def validate_email(cls, v):
        is_valid, error = validator_instance.validate(v, 'email')
        if not is_valid:
            raise ValueError(error)
        return v
    
    @validator('password')
    def validate_password(cls, v):
        is_valid, error = validator_instance.validate(v, 'strong_password')
        if not is_valid:
            raise ValueError(error)
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            is_valid, error = validator_instance.validate(v, 'phone')
            if not is_valid:
                raise ValueError(error)
        return v
    
    @validator('dni')
    def validate_dni(cls, v):
        if v is not None:
            is_valid, error = validator_instance.validate(v, 'dni')
            if not is_valid:
                raise ValueError(error)
        return v
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None:
            is_valid, error = validator_instance.validate(v, 'age_range')
            if not is_valid:
                raise ValueError(error)
        return v

class PaymentValidation(BaseModel):
    """Modelo de validación para pagos"""
    
    amount: float
    payment_date: date
    description: str
    
    @validator('amount')
    def validate_amount(cls, v):
        is_valid, error = validator_instance.validate(v, 'positive_amount')
        if not is_valid:
            raise ValueError(error)
        return v
    
    @validator('payment_date')
    def validate_payment_date(cls, v):
        # Los pagos pueden ser de fechas pasadas o presentes
        if v > date.today():
            raise ValueError("La fecha de pago no puede ser futura")
        return v

class ClassValidation(BaseModel):
    """Modelo de validación para clases"""
    
    name: str
    capacity: int
    duration_minutes: int
    price: float
    
    @validator('capacity')
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("La capacidad debe ser mayor a 0")
        if v > 100:
            raise ValueError("La capacidad no puede exceder 100 personas")
        return v
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("La duración debe ser mayor a 0")
        if v > 480:  # 8 horas
            raise ValueError("La duración no puede exceder 8 horas")
        return v
    
    @validator('price')
    def validate_price(cls, v):
        is_valid, error = validator_instance.validate(v, 'positive_amount')
        if not is_valid:
            raise ValueError(error)
        return v

# Funciones de utilidad para validación
def validate_user_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validar datos de usuario"""
    rules = {
        'email': 'email',
        'password': 'strong_password',
        'phone': 'phone',
        'dni': 'dni',
        'age': 'age_range'
    }
    return validator_instance.validate_multiple(data, rules)

def validate_payment_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validar datos de pago"""
    rules = {
        'amount': 'positive_amount'
    }
    return validator_instance.validate_multiple(data, rules)

def validate_class_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validar datos de clase"""
    rules = {
        'price': 'positive_amount'
    }
    return validator_instance.validate_multiple(data, rules)

def sanitize_input(value: str) -> str:
    """Sanitizar entrada de texto"""
    if not isinstance(value, str):
        return str(value)
    
    # Eliminar caracteres peligrosos
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}']
    for char in dangerous_chars:
        value = value.replace(char, '')
    
    # Eliminar espacios extra
    value = ' '.join(value.split())
    
    return value.strip()

def validate_file_upload(filename: str, allowed_extensions: List[str], max_size_mb: int = 10) -> tuple[bool, Optional[str]]:
    """Validar archivo subido"""
    import os
    
    # Verificar extensión
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in allowed_extensions:
        return False, f"Tipo de archivo no permitido. Permitidos: {', '.join(allowed_extensions)}"
    
    # Verificar tamaño (esto se haría con el archivo real)
    # Por ahora solo validamos el nombre
    if len(filename) > 255:
        return False, "Nombre de archivo demasiado largo"
    
    return True, None

def validate_date_range(start_date: date, end_date: date) -> tuple[bool, Optional[str]]:
    """Validar rango de fechas"""
    if start_date > end_date:
        return False, "La fecha de inicio no puede ser posterior a la fecha de fin"
    
    if start_date < date(1900, 1, 1):
        return False, "La fecha de inicio no puede ser anterior a 1900"
    
    if end_date > date(2100, 12, 31):
        return False, "La fecha de fin no puede ser posterior a 2100"
    
    return True, None

# Decorador para validación automática
def validate_request_data(validation_model: type[BaseModel]):
    """Decorador para validar datos de request automáticamente"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Buscar datos en kwargs
            data = kwargs.get('data') or kwargs.get('user_data') or kwargs.get('request_data')
            
            if data:
                try:
                    validated_data = validation_model(**data)
                    # Reemplazar datos originales con datos validados
                    for key, value in validated_data.dict().items():
                        if key in kwargs:
                            kwargs[key] = value
                except ValidationError as e:
                    logger.error(f"Error de validación: {e}")
                    from fastapi import HTTPException
                    raise HTTPException(status_code=422, detail=str(e))
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 