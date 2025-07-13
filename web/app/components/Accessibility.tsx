'use client'

import React, { useState, useEffect, useRef } from 'react'
import { ArrowRight, Volume2, VolumeX, Eye, EyeOff, ZoomIn, ZoomOut } from 'lucide-react'
import { Button } from './ui/Button'
import { useToastActions } from './Toast'

// Componente para saltar al contenido principal
export function SkipToContentLink() {
  const [isVisible, setIsVisible] = useState(false)
  const mainRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab' && !e.shiftKey) {
        setIsVisible(true)
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        setTimeout(() => setIsVisible(false), 1000)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('keyup', handleKeyUp)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('keyup', handleKeyUp)
    }
  }, [])

  const handleClick = () => {
    const main = mainRef.current || document.querySelector('main')
    if (main) {
      main.focus()
      main.scrollIntoView({ behavior: 'smooth' })
    }
  }

  if (!isVisible) return null

  return (
    <Button
      onClick={handleClick}
      className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 bg-primary text-primary-foreground px-4 py-2 rounded-lg shadow-lg focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
    >
      <ArrowRight className="w-4 h-4 mr-2" />
      Saltar al contenido
    </Button>
  )
}

// Hook para manejo de focus
export function useFocusManagement() {
  const [focusHistory, setFocusHistory] = useState<HTMLElement[]>([])
  const [currentFocusIndex, setCurrentFocusIndex] = useState(-1)

  const saveFocus = (element: HTMLElement) => {
    setFocusHistory(prev => [...prev, element])
    setCurrentFocusIndex(prev => prev + 1)
  }

  const restoreFocus = () => {
    if (currentFocusIndex >= 0 && focusHistory[currentFocusIndex]) {
      focusHistory[currentFocusIndex].focus()
    }
  }

  const clearFocusHistory = () => {
    setFocusHistory([])
    setCurrentFocusIndex(-1)
  }

  return { saveFocus, restoreFocus, clearFocusHistory }
}

// Componente de control de audio
export function AudioControl() {
  const [isMuted, setIsMuted] = useState(false)
  const { success } = useToastActions()

  const toggleMute = () => {
    setIsMuted(!isMuted)
    success(
      isMuted ? 'Audio activado' : 'Audio desactivado',
      isMuted ? 'Los sonidos están ahora activados' : 'Los sonidos están ahora desactivados'
    )
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleMute}
      aria-label={isMuted ? 'Activar audio' : 'Desactivar audio'}
      className="fixed bottom-4 right-4 z-40"
    >
      {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
    </Button>
  )
}

// Componente de control de zoom
export function ZoomControl() {
  const [zoomLevel, setZoomLevel] = useState(100)
  const { success } = useToastActions()

  const zoomIn = () => {
    if (zoomLevel < 200) {
      const newZoom = zoomLevel + 25
      setZoomLevel(newZoom)
      document.body.style.zoom = `${newZoom}%`
      success('Zoom aumentado', `Zoom: ${newZoom}%`)
    }
  }

  const zoomOut = () => {
    if (zoomLevel > 50) {
      const newZoom = zoomLevel - 25
      setZoomLevel(newZoom)
      document.body.style.zoom = `${newZoom}%`
      success('Zoom reducido', `Zoom: ${newZoom}%`)
    }
  }

  const resetZoom = () => {
    setZoomLevel(100)
    document.body.style.zoom = '100%'
    success('Zoom restablecido', 'Zoom: 100%')
  }

  return (
    <div className="fixed bottom-4 left-4 z-40 flex space-x-2">
      <Button
        variant="ghost"
        size="sm"
        onClick={zoomOut}
        disabled={zoomLevel <= 50}
        aria-label="Reducir zoom"
      >
        <ZoomOut className="w-4 h-4" />
      </Button>
      
      <Button
        variant="ghost"
        size="sm"
        onClick={resetZoom}
        aria-label="Restablecer zoom"
        className="text-xs"
      >
        {zoomLevel}%
      </Button>
      
      <Button
        variant="ghost"
        size="sm"
        onClick={zoomIn}
        disabled={zoomLevel >= 200}
        aria-label="Aumentar zoom"
      >
        <ZoomIn className="w-4 h-4" />
      </Button>
    </div>
  )
}

// Componente de control de contraste
export function ContrastControl() {
  const [highContrast, setHighContrast] = useState(false)
  const { success } = useToastActions()

  const toggleContrast = () => {
    const newContrast = !highContrast
    setHighContrast(newContrast)
    
    if (newContrast) {
      document.documentElement.classList.add('high-contrast')
      success('Alto contraste activado', 'Se ha activado el modo de alto contraste')
    } else {
      document.documentElement.classList.remove('high-contrast')
      success('Alto contraste desactivado', 'Se ha desactivado el modo de alto contraste')
    }
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleContrast}
      aria-label={highContrast ? 'Desactivar alto contraste' : 'Activar alto contraste'}
      className="fixed bottom-4 right-16 z-40"
    >
      <Eye className={`w-5 h-5 ${highContrast ? 'text-primary' : ''}`} />
    </Button>
  )
}

// Componente de anuncios de pantalla
interface ScreenReaderAnnouncementProps {
  message: string
  priority?: 'polite' | 'assertive'
}

export function ScreenReaderAnnouncement({ 
  message, 
  priority = 'polite' 
}: ScreenReaderAnnouncementProps) {
  const [announcements, setAnnouncements] = useState<string[]>([])

  useEffect(() => {
    if (message) {
      setAnnouncements(prev => [...prev, message])
      
      // Limpiar anuncios antiguos
      setTimeout(() => {
        setAnnouncements(prev => prev.slice(1))
      }, 1000)
    }
  }, [message])

  return (
    <div
      aria-live={priority}
      aria-atomic="true"
      className="sr-only"
    >
      {announcements.map((announcement, index) => (
        <div key={index}>{announcement}</div>
      ))}
    </div>
  )
}

// Hook para anuncios de pantalla
export function useScreenReader() {
  const [announcement, setAnnouncement] = useState('')

  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    setAnnouncement(message)
  }

  return { announce, announcement }
}

// Componente de navegación por teclado
export function KeyboardNavigation() {
  const [showHelp, setShowHelp] = useState(false)
  const { success } = useToastActions()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Navegación por teclado
      switch (e.key) {
        case 'h':
        case 'H':
          if (e.ctrlKey) {
            e.preventDefault()
            window.location.href = '/'
            success('Navegación', 'Página de inicio')
          }
          break
        case 'n':
        case 'N':
          if (e.ctrlKey) {
            e.preventDefault()
            window.location.href = '/usuarios'
            success('Navegación', 'Página de usuarios')
          }
          break
        case 'c':
        case 'C':
          if (e.ctrlKey) {
            e.preventDefault()
            window.location.href = '/clases'
            success('Navegación', 'Página de clases')
          }
          break
        case 'p':
        case 'P':
          if (e.ctrlKey) {
            e.preventDefault()
            window.location.href = '/pagos'
            success('Navegación', 'Página de pagos')
          }
          break
        case 'r':
        case 'R':
          if (e.ctrlKey) {
            e.preventDefault()
            window.location.href = '/reportes'
            success('Navegación', 'Página de reportes')
          }
          break
        case 's':
        case 'S':
          if (e.ctrlKey) {
            e.preventDefault()
            window.location.href = '/configuracion'
            success('Navegación', 'Página de configuración')
          }
          break
        case '?':
          if (e.ctrlKey) {
            e.preventDefault()
            setShowHelp(!showHelp)
            success('Ayuda', showHelp ? 'Ayuda oculta' : 'Ayuda mostrada')
          }
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [showHelp, success])

  return (
    <>
      {showHelp && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-surface border border-border rounded-lg p-6 max-w-md w-full">
            <h2 className="text-lg font-semibold mb-4">Atajos de teclado</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Ctrl + H</span>
                <span>Inicio</span>
              </div>
              <div className="flex justify-between">
                <span>Ctrl + N</span>
                <span>Usuarios</span>
              </div>
              <div className="flex justify-between">
                <span>Ctrl + C</span>
                <span>Clases</span>
              </div>
              <div className="flex justify-between">
                <span>Ctrl + P</span>
                <span>Pagos</span>
              </div>
              <div className="flex justify-between">
                <span>Ctrl + R</span>
                <span>Reportes</span>
              </div>
              <div className="flex justify-between">
                <span>Ctrl + S</span>
                <span>Configuración</span>
              </div>
              <div className="flex justify-between">
                <span>Ctrl + ?</span>
                <span>Mostrar/Ocultar ayuda</span>
              </div>
            </div>
            <Button
              onClick={() => setShowHelp(false)}
              className="w-full mt-4"
            >
              Cerrar
            </Button>
          </div>
        </div>
      )}
    </>
  )
}

// Componente de indicador de carga accesible
interface AccessibleLoadingProps {
  message?: string
  progress?: number
  className?: string
}

export function AccessibleLoading({ 
  message = 'Cargando...', 
  progress,
  className = '' 
}: AccessibleLoadingProps) {
  return (
    <div 
      className={`flex items-center space-x-3 ${className}`}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent" />
      <span className="text-sm text-muted-foreground">{message}</span>
      {progress !== undefined && (
        <div className="flex-1 max-w-xs">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground">{progress}%</span>
        </div>
      )}
    </div>
  )
}

// Componente de error accesible
interface AccessibleErrorProps {
  title: string
  message: string
  onRetry?: () => void
  className?: string
}

export function AccessibleError({ 
  title, 
  message, 
  onRetry, 
  className = '' 
}: AccessibleErrorProps) {
  return (
    <div 
      className={`p-4 border border-error rounded-lg bg-error/10 ${className}`}
      role="alert"
      aria-live="assertive"
    >
      <h3 className="font-semibold text-error mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-3">{message}</p>
      {onRetry && (
        <Button
          onClick={onRetry}
          variant="outline"
          size="sm"
          aria-label="Reintentar acción"
        >
          Reintentar
        </Button>
      )}
    </div>
  )
}

// Componente de breadcrumb accesible
interface BreadcrumbItem {
  label: string
  href?: string
}

interface AccessibleBreadcrumbProps {
  items: BreadcrumbItem[]
  className?: string
}

export function AccessibleBreadcrumb({ items, className = '' }: AccessibleBreadcrumbProps) {
  return (
    <nav 
      aria-label="Breadcrumb"
      className={className}
    >
      <ol className="flex items-center space-x-2 text-sm">
        {items.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <span className="mx-2 text-muted-foreground">/</span>
            )}
            {item.href ? (
              <a
                href={item.href}
                className="text-primary hover:text-primary/80 transition-colors"
                aria-current={index === items.length - 1 ? 'page' : undefined}
              >
                {item.label}
              </a>
            ) : (
              <span 
                className="text-muted-foreground"
                aria-current={index === items.length - 1 ? 'page' : undefined}
              >
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

// Componente de panel de accesibilidad
export function AccessibilityPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const { success } = useToastActions()

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Panel de accesibilidad"
        className="fixed bottom-4 right-24 z-40"
      >
        <Eye className="w-5 h-5" />
      </Button>

      {isOpen && (
        <div className="fixed bottom-16 right-4 z-40 bg-surface border border-border rounded-lg shadow-lg p-4 w-64">
          <h3 className="font-semibold mb-3">Accesibilidad</h3>
          <div className="space-y-3">
            <AudioControl />
            <ZoomControl />
            <ContrastControl />
            <KeyboardNavigation />
          </div>
          <Button
            onClick={() => setIsOpen(false)}
            variant="outline"
            size="sm"
            className="w-full mt-3"
          >
            Cerrar
          </Button>
        </div>
      )}
    </>
  )
} 