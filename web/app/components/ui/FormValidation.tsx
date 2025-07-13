/**
 * Componente de validación de formularios
 * Proporciona validaciones consistentes y mensajes de error claros
 */
'use client'

import React from 'react'
import { AlertCircle } from 'lucide-react'

interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: any) => boolean | string
  message?: string
}

interface ValidationResult {
  isValid: boolean
  message?: string
}

export const validateField = (value: any, rules: ValidationRule): ValidationResult => {
  // Validación requerida
  if (rules.required && (!value || value.toString().trim() === '')) {
    return {
      isValid: false,
      message: rules.message || 'Este campo es obligatorio'
    }
  }

  // Si no hay valor y no es requerido, es válido
  if (!value || value.toString().trim() === '') {
    return { isValid: true }
  }

  const stringValue = value.toString().trim()

  // Validación de longitud mínima
  if (rules.minLength && stringValue.length < rules.minLength) {
    return {
      isValid: false,
      message: rules.message || `Mínimo ${rules.minLength} caracteres`
    }
  }

  // Validación de longitud máxima
  if (rules.maxLength && stringValue.length > rules.maxLength) {
    return {
      isValid: false,
      message: rules.message || `Máximo ${rules.maxLength} caracteres`
    }
  }

  // Validación de patrón
  if (rules.pattern && !rules.pattern.test(stringValue)) {
    return {
      isValid: false,
      message: rules.message || 'Formato inválido'
    }
  }

  // Validación personalizada
  if (rules.custom) {
    const result = rules.custom(value)
    if (typeof result === 'string') {
      return {
        isValid: false,
        message: result
      }
    }
    if (!result) {
      return {
        isValid: false,
        message: rules.message || 'Valor inválido'
      }
    }
  }

  return { isValid: true }
}

// Reglas de validación predefinidas
export const validationRules = {
  required: { required: true },
  email: {
    required: true,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    message: 'Ingresa un email válido'
  },
  phone: {
    pattern: /^[\+]?[1-9][\d]{0,15}$/,
    message: 'Ingresa un teléfono válido'
  },
  password: {
    required: true,
    minLength: 8,
    pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
    message: 'La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial'
  },
  username: {
    required: true,
    minLength: 3,
    maxLength: 50,
    pattern: /^[a-zA-Z0-9_.-]+$/,
    message: 'El usuario debe tener entre 3 y 50 caracteres, solo letras, números, puntos, guiones y guiones bajos'
  },
  name: {
    required: true,
    minLength: 2,
    maxLength: 100,
    pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/,
    message: 'El nombre debe tener entre 2 y 100 caracteres, solo letras y espacios'
  },
  price: {
    pattern: /^\d+(\.\d{1,2})?$/,
    message: 'Ingresa un precio válido (ej: 100.50)'
  },
  positiveNumber: {
    custom: (value: any) => {
      const num = parseFloat(value)
      return !isNaN(num) && num > 0
    },
    message: 'Debe ser un número positivo'
  },
  date: {
    custom: (value: any) => {
      const date = new Date(value)
      return !isNaN(date.getTime())
    },
    message: 'Ingresa una fecha válida'
  },
  futureDate: {
    custom: (value: any) => {
      const date = new Date(value)
      return !isNaN(date.getTime()) && date > new Date()
    },
    message: 'La fecha debe ser futura'
  }
}

interface ValidationMessageProps {
  message: string
  className?: string
}

export const ValidationMessage: React.FC<ValidationMessageProps> = ({ 
  message, 
  className = '' 
}) => (
  <div className={`flex items-center text-sm text-red-600 mt-1 ${className}`}>
    <AlertCircle className="h-4 w-4 mr-1 flex-shrink-0" />
    <span>{message}</span>
  </div>
)

interface FormFieldProps {
  label: string
  name: string
  value: string
  onChange: (value: string) => void
  onBlur?: () => void
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'date' | 'textarea'
  placeholder?: string
  required?: boolean
  disabled?: boolean
  error?: string
  className?: string
  rows?: number
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  name,
  value,
  onChange,
  onBlur,
  type = 'text',
  placeholder,
  required = false,
  disabled = false,
  error,
  className = '',
  rows = 3
}) => {
  const inputId = `field-${name}`

  return (
    <div className={`space-y-1 ${className}`}>
      <label htmlFor={inputId} className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      {type === 'textarea' ? (
        <textarea
          id={inputId}
          name={name}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          placeholder={placeholder}
          disabled={disabled}
          rows={rows}
          className={`
            block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
            ${error ? 'border-red-300' : 'border-gray-300'}
          `}
        />
      ) : (
        <input
          id={inputId}
          name={name}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          className={`
            block w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
            ${error ? 'border-red-300' : 'border-gray-300'}
          `}
        />
      )}
      
      {error && <ValidationMessage message={error} />}
    </div>
  )
}

// Hook para manejar validaciones de formularios
export const useFormValidation = <T extends Record<string, any>>(initialValues: T) => {
  const [values, setValues] = React.useState<T>(initialValues)
  const [errors, setErrors] = React.useState<Partial<Record<keyof T, string>>>({})
  const [touched, setTouched] = React.useState<Partial<Record<keyof T, boolean>>>({})

  const validateFieldInForm = (name: keyof T, value: any, rules: ValidationRule) => {
    const result = validateField(value, rules)
    setErrors(prev => ({
      ...prev,
      [name]: result.isValid ? undefined : result.message
    }))
    return result.isValid
  }

  const handleChange = (name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }))
    
    // Limpiar error si el campo está siendo editado
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }

  const handleBlur = (name: keyof T) => {
    setTouched(prev => ({ ...prev, [name]: true }))
  }

  const validateForm = (validationSchema: Record<keyof T, ValidationRule>) => {
    const newErrors: Partial<Record<keyof T, string>> = {}
    let isValid = true

    Object.keys(validationSchema).forEach((key) => {
      const fieldKey = key as keyof T
      const result = validateField(values[fieldKey], validationSchema[fieldKey])
      if (!result.isValid) {
        newErrors[fieldKey] = result.message
        isValid = false
      }
    })

    setErrors(newErrors)
    return isValid
  }

  const resetForm = () => {
    setValues(initialValues)
    setErrors({})
    setTouched({})
  }

      return {
      values,
      errors,
      touched,
      handleChange,
      handleBlur,
      validateField: validateFieldInForm,
      validateForm,
      resetForm,
      setValues
    }
} 