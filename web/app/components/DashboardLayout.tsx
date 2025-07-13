/**
 * Componente DashboardLayout Ultra Moderno
 * Layout principal optimizado para experiencia profesional
 */
'use client'

import React, { useState, useCallback, useMemo } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import * as Icons from './ui/Icons'
import { LogOut, Menu, X, Sun, Moon, Laptop, Zap } from 'lucide-react'
import { useTheme } from 'next-themes'
import { SyncStatus } from './SyncStatus'

// Enlaces de navegación principal
interface NavLink {
  href: string
  label: string
  icon: any
  exact?: boolean
  color?: string
}

const NAV_LINKS: NavLink[] = [
  { href: '/', label: 'Dashboard', icon: Icons.Dashboard, exact: true, color: 'text-blue-600' },
  { href: '/usuarios', label: 'Usuarios', icon: Icons.Users, color: 'text-green-600' },
  { href: '/clases', label: 'Clases', icon: Icons.Calendar, color: 'text-purple-600' },
  { href: '/rutinas', label: 'Rutinas', icon: Icons.Routines, color: 'text-orange-600' },
  { href: '/pagos', label: 'Pagos', icon: Icons.Payments, color: 'text-emerald-600' },
  { href: '/asistencias', label: 'Asistencias', icon: Icons.Attendance, color: 'text-cyan-600' },
  { href: '/reportes', label: 'Reportes', icon: Icons.Reports, color: 'text-pink-600' },
  { href: '/configuracion', label: 'Configuración', icon: Icons.Settings, color: 'text-gray-600' },
]

// Componente del selector de tema ultra moderno
const ThemeSelector = React.memo(function ThemeSelector() {
  const { theme, setTheme } = useTheme()
  
  const handleThemeChange = useCallback((newTheme: string) => {
    setTheme(newTheme)
  }, [setTheme])
  
  return (
    <div className="bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-xl p-1 flex shadow-sm" role="group" aria-label="Selector de tema">
      <button
        onClick={() => handleThemeChange('light')}
        className={`p-2 rounded-lg transition-all duration-300 ${
          theme === 'light' 
            ? 'bg-gradient-to-r from-amber-400 to-yellow-500 text-white shadow-lg' 
            : 'hover:bg-gray-100 text-gray-600'
        }`}
        aria-label="Tema claro"
        aria-pressed={theme === 'light'}
      >
        <Sun size={16} />
      </button>
      <button
        onClick={() => handleThemeChange('dark')}
        className={`p-2 rounded-lg transition-all duration-300 ${
          theme === 'dark' 
            ? 'bg-gradient-to-r from-gray-700 to-gray-900 text-white shadow-lg' 
            : 'hover:bg-gray-100 text-gray-600'
        }`}
        aria-label="Tema oscuro"
        aria-pressed={theme === 'dark'}
      >
        <Moon size={16} />
      </button>
      <button
        onClick={() => handleThemeChange('system')}
        className={`p-2 rounded-lg transition-all duration-300 ${
          theme === 'system' 
            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg' 
            : 'hover:bg-gray-100 text-gray-600'
        }`}
        aria-label="Tema del sistema"
        aria-pressed={theme === 'system'}
      >
        <Laptop size={16} />
      </button>
    </div>
  )
})

// Componente del sidebar ultra moderno
const Sidebar = React.memo(function Sidebar({ 
  isOpen, 
  onClose, 
  pathname 
}: { 
  isOpen: boolean
  onClose: () => void
  pathname: string | null
}) {
  const isActive = useCallback((href: string, exact = false) => {
    if (!pathname) return false
    if (exact) return pathname === href
    return pathname.startsWith(href)
  }, [pathname])

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-50 md:relative transform transition-all duration-300 ease-in-out 
        w-64 bg-white/95 backdrop-blur-xl border-r border-gray-200/50 pt-16 md:pt-0 md:translate-x-0 
        shadow-2xl md:shadow-none ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      style={{
        background: 'linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,250,252,0.95) 100%)'
      }}
      aria-hidden={!isOpen}
    >
      {/* Logo en el sidebar */}
      <div className="p-6 border-b border-gray-200/50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Zap className="text-white" size={20} />
          </div>
          <div>
            <h2 className="font-bold text-gray-900">GymSystem</h2>
            <p className="text-xs text-gray-500">v6.0 Professional</p>
          </div>
        </div>
      </div>

      <nav className="p-4 space-y-2" role="navigation" aria-label="Navegación principal">
        {NAV_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`group flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300 
              focus:outline-none focus:ring-2 focus:ring-indigo-500/50 relative overflow-hidden ${
              isActive(link.href, link.exact)
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg transform scale-[1.02]'
                : 'hover:bg-gray-50 hover:shadow-md hover:transform hover:translate-x-1 text-gray-700'
            }`}
            onClick={onClose}
            aria-current={isActive(link.href, link.exact) ? 'page' : undefined}
          >
            <div className={`p-1.5 rounded-lg transition-all duration-300 ${
              isActive(link.href, link.exact)
                ? 'bg-white/20'
                : 'bg-white shadow-sm group-hover:shadow-md'
            }`}>
              <link.icon 
                size={18} 
                className={isActive(link.href, link.exact) ? 'text-white' : link.color}
                aria-hidden="true" 
              />
            </div>
            <span className="font-medium">{link.label}</span>
            
            {/* Indicador de página activa */}
            {isActive(link.href, link.exact) && (
              <div className="absolute right-2 w-2 h-2 bg-white rounded-full animate-pulse"></div>
            )}
          </Link>
        ))}
      </nav>

      {/* Footer del sidebar */}
      <div className="absolute bottom-4 left-4 right-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-200/50">
        <div className="text-center">
          <p className="text-xs text-gray-600 mb-1">Sistema funcionando</p>
          <div className="w-full h-1 bg-gray-200 rounded-full overflow-hidden">
            <div className="w-full h-full bg-gradient-to-r from-green-400 to-emerald-500 animate-pulse"></div>
          </div>
        </div>
      </div>
    </aside>
  )
})

// Componente del header ultra moderno
const Header = React.memo(function Header({ 
  onToggleSidebar, 
  sidebarOpen 
}: { 
  onToggleSidebar: () => void
  sidebarOpen: boolean 
}) {
  return (
    <header className="sticky top-0 z-40 border-b border-gray-200/50 bg-white/95 backdrop-blur-xl">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Lado izquierdo */}
        <div className="flex items-center space-x-4">
          {/* Botón de menú (móvil) */}
          <button
            onClick={onToggleSidebar}
            className="md:hidden p-2 rounded-xl bg-gray-100 hover:bg-gray-200 transition-all duration-300 
                       focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            aria-label={sidebarOpen ? 'Cerrar menú' : 'Abrir menú'}
            aria-expanded={sidebarOpen}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center md:hidden">
              <Zap className="text-white" size={16} />
            </div>
            <span className="font-bold text-xl gradient-gym-text">
              <span className="md:hidden">Gym</span>
              <span className="hidden md:inline">Sistema de Gestión de Gimnasio</span>
            </span>
          </div>
        </div>
        
        {/* Lado derecho */}
        <div className="flex items-center space-x-3">
          <ThemeSelector />
          <SyncStatus />
          
          {/* Botón de perfil/logout mejorado */}
          <Link 
            href="/login" 
            className="p-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-xl transition-all duration-300 
                       focus:outline-none focus:ring-2 focus:ring-red-500/50 hover:shadow-md" 
            aria-label="Cerrar sesión"
          >
            <LogOut size={20} />
          </Link>
        </div>
      </div>
    </header>
  )
})

interface DashboardLayoutProps {
  children: React.ReactNode
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()
  
  const toggleSidebar = useCallback(() => {
    setSidebarOpen(prev => !prev)
  }, [])

  const closeSidebar = useCallback(() => {
    setSidebarOpen(false)
  }, [])

  // Overlay mejorado
  const sidebarOverlay = useMemo(() => {
    if (!sidebarOpen) return null
    
    return (
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm md:hidden animate-fade-in"
        onClick={closeSidebar}
        aria-hidden="true"
      />
    )
  }, [sidebarOpen, closeSidebar])

  return (
    <div className="min-h-screen flex flex-col" style={{
      background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f1f5f9 100%)'
    }}>
      <Header onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} />
      
      <div className="flex-1 flex">
        <Sidebar 
          isOpen={sidebarOpen} 
          onClose={closeSidebar} 
          pathname={pathname}
        />
        
        {sidebarOverlay}
        
        {/* Contenido principal ultra moderno */}
        <main 
          className="flex-1 p-6 overflow-auto"
          role="main"
          aria-label="Contenido principal"
        >
          <div className="max-w-7xl mx-auto animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
