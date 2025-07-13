'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home, ArrowLeft } from 'lucide-react'
import { Button } from './ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })

    // Callback para logging o monitoreo
    this.props.onError?.(error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined })
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  handleGoBack = () => {
    window.history.back()
  }

  render() {
    if (this.state.hasError) {
      // Si hay un fallback personalizado, usarlo
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
          <Card className="w-full max-w-md mx-auto">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-4">
                <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <CardTitle className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Algo salió mal
              </CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400">
                Ha ocurrido un error inesperado. No te preocupes, no es tu culpa.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Información del error para desarrollo */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-xs">
                  <p className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                    Error de desarrollo:
                  </p>
                  <p className="text-red-600 dark:text-red-400 font-mono break-all">
                    {this.state.error.message}
                  </p>
                  {this.state.errorInfo?.componentStack && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-gray-600 dark:text-gray-400">
                        Stack trace
                      </summary>
                      <pre className="mt-1 text-xs text-gray-500 dark:text-gray-400 overflow-auto max-h-32">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              {/* Acciones */}
              <div className="flex flex-col space-y-2">
                <Button 
                  onClick={this.handleRetry}
                  className="w-full"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Intentar de nuevo
                </Button>
                
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    onClick={this.handleGoBack}
                    className="flex-1"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Volver
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    onClick={this.handleGoHome}
                    className="flex-1"
                  >
                    <Home className="w-4 h-4 mr-2" />
                    Inicio
                  </Button>
                </div>
              </div>

              {/* Información adicional */}
              <div className="text-center text-xs text-gray-500 dark:text-gray-400">
                <p>Si el problema persiste, contacta al soporte técnico.</p>
                <p className="mt-1">Error ID: {this.state.error?.name || 'UNKNOWN'}</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

// Hook para usar en componentes funcionales
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null)

  const handleError = React.useCallback((error: Error) => {
    console.error('Error handled by useErrorHandler:', error)
    setError(error)
  }, [])

  const clearError = React.useCallback(() => {
    setError(null)
  }, [])

  return { error, handleError, clearError }
}

// Componente para mostrar errores específicos
interface ErrorDisplayProps {
  error: Error
  onRetry?: () => void
  onDismiss?: () => void
  showDetails?: boolean
}

export function ErrorDisplay({ 
  error, 
  onRetry, 
  onDismiss, 
  showDetails = false 
}: ErrorDisplayProps) {
  const [showFullDetails, setShowFullDetails] = React.useState(false)

  return (
    <Card className="border-red-200 dark:border-red-800">
      <CardHeader>
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
          <CardTitle className="text-red-900 dark:text-red-100">
            Error
          </CardTitle>
        </div>
        <CardDescription className="text-red-700 dark:text-red-300">
          {error.message || 'Ha ocurrido un error inesperado'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {showDetails && (
          <details className="text-sm">
            <summary className="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
              Ver detalles técnicos
            </summary>
            <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="font-mono text-xs text-gray-700 dark:text-gray-300 break-all">
                {error.stack}
              </p>
            </div>
          </details>
        )}

        <div className="flex space-x-2">
          {onRetry && (
            <Button onClick={onRetry} size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Reintentar
            </Button>
          )}
          {onDismiss && (
            <Button variant="outline" onClick={onDismiss} size="sm">
              Cerrar
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
} 