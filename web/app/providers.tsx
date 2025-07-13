/**
 * Providers Optimizados
 * Configuración robusta para producción con mejor manejo de errores
 */
'use client'

import { ThemeProvider } from 'next-themes'
import { ToastProvider } from './components/Toast'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ThemeSystemProvider } from './components/ThemeProvider'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <ThemeSystemProvider>
          <ToastProvider maxToasts={5}>
            {children}
          </ToastProvider>
        </ThemeSystemProvider>
      </ThemeProvider>
    </ErrorBoundary>
  )
}
