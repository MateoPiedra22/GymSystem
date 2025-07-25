from typing import Dict, Any, Optional
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TemplateEngine:
    """Simple template engine for processing message templates"""
    
    def __init__(self):
        self.variable_pattern = re.compile(r'\{([^}]+)\}')
    
    def process_template(self, template: str, data: Dict[str, Any]) -> str:
        """Process template with provided data"""
        try:
            # Replace variables in template
            def replace_variable(match):
                variable_name = match.group(1).strip()
                return self._get_variable_value(variable_name, data)
            
            processed = self.variable_pattern.sub(replace_variable, template)
            return processed
            
        except Exception as e:
            logger.error(f"Error processing template: {e}")
            return template
    
    def _get_variable_value(self, variable_name: str, data: Dict[str, Any]) -> str:
        """Get variable value from data with support for nested keys and functions"""
        try:
            # Handle nested keys (e.g., user.name)
            if '.' in variable_name:
                keys = variable_name.split('.')
                value = data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        return f"{{{variable_name}}}"
                return str(value)
            
            # Handle function calls (e.g., date_format:dd/mm/yyyy)
            if ':' in variable_name:
                func_name, param = variable_name.split(':', 1)
                return self._apply_function(func_name, param, data)
            
            # Simple variable lookup
            if variable_name in data:
                value = data[variable_name]
                if value is None:
                    return ""
                return str(value)
            
            # Variable not found, return as is
            return f"{{{variable_name}}}"
            
        except Exception as e:
            logger.error(f"Error getting variable value for {variable_name}: {e}")
            return f"{{{variable_name}}}"
    
    def _apply_function(self, func_name: str, param: str, data: Dict[str, Any]) -> str:
        """Apply template functions"""
        try:
            if func_name == 'date_format':
                # Format current date
                now = datetime.now()
                if param == 'dd/mm/yyyy':
                    return now.strftime('%d/%m/%Y')
                elif param == 'dd/mm/yyyy hh:mm':
                    return now.strftime('%d/%m/%Y %H:%M')
                elif param == 'month_name':
                    return now.strftime('%B')
                else:
                    return now.strftime(param)
            
            elif func_name == 'upper':
                if param in data:
                    return str(data[param]).upper()
                return param.upper()
            
            elif func_name == 'lower':
                if param in data:
                    return str(data[param]).lower()
                return param.lower()
            
            elif func_name == 'capitalize':
                if param in data:
                    return str(data[param]).capitalize()
                return param.capitalize()
            
            elif func_name == 'currency':
                if param in data:
                    value = float(data[param])
                    return f"${value:.2f}"
                return param
            
            elif func_name == 'default':
                # default:variable_name:default_value
                parts = param.split(':', 1)
                if len(parts) == 2:
                    var_name, default_value = parts
                    return str(data.get(var_name, default_value))
                return param
            
            # Unknown function
            return f"{{{func_name}:{param}}}"
            
        except Exception as e:
            logger.error(f"Error applying function {func_name}: {e}")
            return f"{{{func_name}:{param}}}"
    
    def validate_template(self, template: str) -> Dict[str, Any]:
        """Validate template and return required variables"""
        try:
            variables = []
            functions = []
            
            matches = self.variable_pattern.findall(template)
            
            for match in matches:
                variable_name = match.strip()
                
                if ':' in variable_name:
                    func_name, param = variable_name.split(':', 1)
                    functions.append({
                        'function': func_name,
                        'parameter': param,
                        'full': variable_name
                    })
                else:
                    variables.append(variable_name)
            
            return {
                'valid': True,
                'variables': list(set(variables)),
                'functions': functions,
                'total_placeholders': len(matches)
            }
            
        except Exception as e:
            logger.error(f"Error validating template: {e}")
            return {
                'valid': False,
                'error': str(e),
                'variables': [],
                'functions': [],
                'total_placeholders': 0
            }
    
    def get_sample_data(self, template: str) -> Dict[str, Any]:
        """Generate sample data for template testing"""
        validation = self.validate_template(template)
        
        sample_data = {}
        
        # Generate sample values for variables
        for variable in validation['variables']:
            if 'name' in variable.lower():
                sample_data[variable] = "Juan Pérez"
            elif 'amount' in variable.lower() or 'price' in variable.lower():
                sample_data[variable] = "$150.00"
            elif 'date' in variable.lower():
                sample_data[variable] = datetime.now().strftime('%d/%m/%Y')
            elif 'time' in variable.lower():
                sample_data[variable] = datetime.now().strftime('%H:%M')
            elif 'gym' in variable.lower():
                sample_data[variable] = "Gimnasio Ejemplo"
            elif 'class' in variable.lower():
                sample_data[variable] = "Yoga Matutino"
            elif 'instructor' in variable.lower():
                sample_data[variable] = "María García"
            elif 'membership' in variable.lower():
                sample_data[variable] = "Membresía Premium"
            else:
                sample_data[variable] = f"Valor de {variable}"
        
        return sample_data
    
    def preview_template(self, template: str, data: Optional[Dict[str, Any]] = None) -> str:
        """Preview template with sample or provided data"""
        if data is None:
            data = self.get_sample_data(template)
        
        return self.process_template(template, data)