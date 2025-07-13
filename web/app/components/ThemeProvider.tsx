'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useTheme } from 'next-themes'
import { useToastActions } from './Toast'

// Tipos para el sistema de temas
export interface ThemeConfig {
  id: string
  name: string
  description?: string
  colors: {
    primary: string
    secondary: string
    accent: string
    background: string
    surface: string
    text: string
    textSecondary: string
    border: string
    success: string
    warning: string
    error: string
    info: string
  }
  dark?: {
    primary: string
    secondary: string
    accent: string
    background: string
    surface: string
    text: string
    textSecondary: string
    border: string
    success: string
    warning: string
    error: string
    info: string
  }
}

// Temas predefinidos
export const PREDEFINED_THEMES: ThemeConfig[] = [
  {
    id: 'default',
    name: 'Clásico',
    description: 'Tema clásico con colores azules',
    colors: {
      primary: '#3B82F6',
      secondary: '#6B7280',
      accent: '#F59E0B',
      background: '#FFFFFF',
      surface: '#F9FAFB',
      text: '#111827',
      textSecondary: '#6B7280',
      border: '#E5E7EB',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6'
    },
    dark: {
      primary: '#60A5FA',
      secondary: '#9CA3AF',
      accent: '#FBBF24',
      background: '#111827',
      surface: '#1F2937',
      text: '#F9FAFB',
      textSecondary: '#D1D5DB',
      border: '#374151',
      success: '#34D399',
      warning: '#FBBF24',
      error: '#F87171',
      info: '#60A5FA'
    }
  },
  {
    id: 'modern',
    name: 'Moderno',
    description: 'Tema moderno con colores vibrantes',
    colors: {
      primary: '#8B5CF6',
      secondary: '#EC4899',
      accent: '#06B6D4',
      background: '#FFFFFF',
      surface: '#F8FAFC',
      text: '#0F172A',
      textSecondary: '#64748B',
      border: '#E2E8F0',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6'
    },
    dark: {
      primary: '#A78BFA',
      secondary: '#F472B6',
      accent: '#22D3EE',
      background: '#0F172A',
      surface: '#1E293B',
      text: '#F8FAFC',
      textSecondary: '#CBD5E1',
      border: '#334155',
      success: '#34D399',
      warning: '#FBBF24',
      error: '#F87171',
      info: '#60A5FA'
    }
  },
  {
    id: 'warm',
    name: 'Cálido',
    description: 'Tema cálido con tonos naranjas y rojos',
    colors: {
      primary: '#F97316',
      secondary: '#DC2626',
      accent: '#F59E0B',
      background: '#FFFFFF',
      surface: '#FEF7F0',
      text: '#1F2937',
      textSecondary: '#6B7280',
      border: '#FED7AA',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6'
    },
    dark: {
      primary: '#FB923C',
      secondary: '#F87171',
      accent: '#FBBF24',
      background: '#1F2937',
      surface: '#2D1B69',
      text: '#F9FAFB',
      textSecondary: '#D1D5DB',
      border: '#7C2D12',
      success: '#34D399',
      warning: '#FBBF24',
      error: '#F87171',
      info: '#60A5FA'
    }
  },
  {
    id: 'nature',
    name: 'Naturaleza',
    description: 'Tema inspirado en la naturaleza con verdes',
    colors: {
      primary: '#059669',
      secondary: '#16A34A',
      accent: '#65A30D',
      background: '#FFFFFF',
      surface: '#F0FDF4',
      text: '#064E3B',
      textSecondary: '#166534',
      border: '#BBF7D0',
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6'
    },
    dark: {
      primary: '#34D399',
      secondary: '#4ADE80',
      accent: '#84CC16',
      background: '#064E3B',
      surface: '#065F46',
      text: '#ECFDF5',
      textSecondary: '#D1FAE5',
      border: '#047857',
      success: '#34D399',
      warning: '#FBBF24',
      error: '#F87171',
      info: '#60A5FA'
    }
  }
]

// Contexto para el sistema de temas
interface ThemeContextType {
  currentTheme: ThemeConfig
  availableThemes: ThemeConfig[]
  customThemes: ThemeConfig[]
  setTheme: (themeId: string) => void
  createCustomTheme: (theme: Omit<ThemeConfig, 'id'>) => string
  updateCustomTheme: (id: string, updates: Partial<ThemeConfig>) => void
  deleteCustomTheme: (id: string) => void
  resetToDefault: () => void
  exportTheme: (themeId: string) => string
  importTheme: (themeData: string) => boolean
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

// Hook para usar el contexto de temas
export function useThemeSystem() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useThemeSystem must be used within a ThemeSystemProvider')
  }
  return context
}

// Proveedor del sistema de temas
interface ThemeSystemProviderProps {
  children: React.ReactNode
}

export function ThemeSystemProvider({ children }: ThemeSystemProviderProps) {
  const { theme: nextTheme, setTheme: setNextTheme } = useTheme()
  const [currentTheme, setCurrentTheme] = useState<ThemeConfig>(PREDEFINED_THEMES[0])
  const [customThemes, setCustomThemes] = useState<ThemeConfig[]>([])
  const { success, error: showError } = useToastActions()

  // Cargar configuración guardada
  useEffect(() => {
    const savedThemeId = localStorage.getItem('selected_theme_id')
    const savedCustomThemes = localStorage.getItem('custom_themes')
    
    if (savedCustomThemes) {
      try {
        const parsed = JSON.parse(savedCustomThemes)
        setCustomThemes(Array.isArray(parsed) ? parsed : [])
      } catch (err) {
        console.error('Error loading custom themes:', err)
      }
    }

    if (savedThemeId) {
      const theme = [...PREDEFINED_THEMES, ...customThemes].find(t => t.id === savedThemeId)
      if (theme) {
        setCurrentTheme(theme)
        applyTheme(theme)
      }
    }
  }, [])

  // Aplicar tema al DOM
  const applyTheme = useCallback((theme: ThemeConfig) => {
    const root = document.documentElement
    const isDark = nextTheme === 'dark'
    const colors = isDark && theme.dark ? theme.dark : theme.colors

    // Aplicar variables CSS
    Object.entries(colors).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value)
    })

    // Aplicar clases adicionales
    root.classList.remove('theme-default', 'theme-modern', 'theme-warm', 'theme-nature')
    root.classList.add(`theme-${theme.id}`)
  }, [nextTheme])

  // Aplicar tema cuando cambie
  useEffect(() => {
    applyTheme(currentTheme)
  }, [currentTheme, nextTheme, applyTheme])

  // Guardar temas personalizados
  useEffect(() => {
    localStorage.setItem('custom_themes', JSON.stringify(customThemes))
  }, [customThemes])

  // Cambiar tema
  const setTheme = useCallback((themeId: string) => {
    const theme = [...PREDEFINED_THEMES, ...customThemes].find(t => t.id === themeId)
    if (theme) {
      setCurrentTheme(theme)
      localStorage.setItem('selected_theme_id', themeId)
      success('Tema cambiado', `Se ha aplicado el tema "${theme.name}"`)
    } else {
      showError('Error', 'Tema no encontrado')
    }
  }, [customThemes, success, showError])

  // Crear tema personalizado
  const createCustomTheme = useCallback((theme: Omit<ThemeConfig, 'id'>): string => {
    const id = `custom-${Date.now()}`
    const newTheme: ThemeConfig = { ...theme, id }
    
    setCustomThemes(prev => [...prev, newTheme])
    success('Tema creado', `Se ha creado el tema "${theme.name}"`)
    
    return id
  }, [success])

  // Actualizar tema personalizado
  const updateCustomTheme = useCallback((id: string, updates: Partial<ThemeConfig>) => {
    setCustomThemes(prev => prev.map(theme => 
      theme.id === id ? { ...theme, ...updates } : theme
    ))
    
    if (currentTheme.id === id) {
      setCurrentTheme(prev => ({ ...prev, ...updates }))
    }
    
    success('Tema actualizado', 'Se han guardado los cambios del tema')
  }, [currentTheme.id, success])

  // Eliminar tema personalizado
  const deleteCustomTheme = useCallback((id: string) => {
    setCustomThemes(prev => prev.filter(theme => theme.id !== id))
    
    if (currentTheme.id === id) {
      setTheme('default')
    }
    
    success('Tema eliminado', 'Se ha eliminado el tema personalizado')
  }, [currentTheme.id, setTheme, success])

  // Resetear a tema por defecto
  const resetToDefault = useCallback(() => {
    setTheme('default')
    setNextTheme('system')
  }, [setTheme, setNextTheme])

  // Exportar tema
  const exportTheme = useCallback((themeId: string): string => {
    const theme = [...PREDEFINED_THEMES, ...customThemes].find(t => t.id === themeId)
    if (theme) {
      return JSON.stringify(theme, null, 2)
    }
    throw new Error('Tema no encontrado')
  }, [customThemes])

  // Importar tema
  const importTheme = useCallback((themeData: string): boolean => {
    try {
      const theme = JSON.parse(themeData) as ThemeConfig
      if (!theme.id || !theme.name || !theme.colors) {
        throw new Error('Formato de tema inválido')
      }
      
      // Generar nuevo ID para evitar conflictos
      const newId = `custom-${Date.now()}`
      const newTheme = { ...theme, id: newId }
      
      setCustomThemes(prev => [...prev, newTheme])
      success('Tema importado', `Se ha importado el tema "${theme.name}"`)
      
      return true
    } catch (err) {
      showError('Error', 'No se pudo importar el tema. Verifica el formato.')
      return false
    }
  }, [success, showError])

  const availableThemes = [...PREDEFINED_THEMES, ...customThemes]

  return (
    <ThemeContext.Provider value={{
      currentTheme,
      availableThemes,
      customThemes,
      setTheme,
      createCustomTheme,
      updateCustomTheme,
      deleteCustomTheme,
      resetToDefault,
      exportTheme,
      importTheme
    }}>
      {children}
    </ThemeContext.Provider>
  )
}

// Componente para mostrar preview de tema
interface ThemePreviewProps {
  theme: ThemeConfig
  selected?: boolean
  onClick?: () => void
  onDelete?: () => void
}

export function ThemePreview({ theme, selected, onClick, onDelete }: ThemePreviewProps) {
  return (
    <div 
      className={`relative p-4 border rounded-lg cursor-pointer transition-all duration-200 ${
        selected 
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-medium text-gray-900 dark:text-gray-100">
          {theme.name}
        </h3>
        {selected && (
          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
        )}
      </div>
      
      {theme.description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          {theme.description}
        </p>
      )}
      
      {/* Preview de colores */}
      <div className="flex space-x-2">
        <div 
          className="w-6 h-6 rounded border border-gray-200 dark:border-gray-600"
          style={{ backgroundColor: theme.colors.primary }}
        />
        <div 
          className="w-6 h-6 rounded border border-gray-200 dark:border-gray-600"
          style={{ backgroundColor: theme.colors.secondary }}
        />
        <div 
          className="w-6 h-6 rounded border border-gray-200 dark:border-gray-600"
          style={{ backgroundColor: theme.colors.accent }}
        />
        <div 
          className="w-6 h-6 rounded border border-gray-200 dark:border-gray-600"
          style={{ backgroundColor: theme.colors.success }}
        />
      </div>
      
      {/* Botón de eliminar para temas personalizados */}
      {onDelete && theme.id.startsWith('custom-') && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="absolute top-2 right-2 p-1 text-red-500 hover:text-red-700 dark:hover:text-red-400"
        >
          ×
        </button>
      )}
    </div>
  )
} 