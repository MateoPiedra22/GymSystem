'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  Home, 
  Users, 
  Calendar, 
  CreditCard, 
  BarChart3, 
  Settings, 
  Menu, 
  X, 
  ChevronDown,
  LogOut,
  User,
  Bell,
  Search
} from 'lucide-react'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'
import { useThemeSystem } from './ThemeProvider'
import { useToastActions } from './Toast'
import { ConnectionStatus } from './OfflineIndicator'

// Configuración de navegación
interface NavItem {
  id: string
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: number
  children?: Omit<NavItem, 'children'>[]
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    href: '/',
    icon: Home
  },
  {
    id: 'usuarios',
    label: 'Usuarios',
    href: '/usuarios',
    icon: Users,
    badge: 3 // Nuevos usuarios
  },
  {
    id: 'clases',
    label: 'Clases',
    href: '/clases',
    icon: Calendar,
    children: [
      { id: 'horarios', label: 'Horarios', href: '/clases/horarios', icon: Calendar },
      { id: 'instructores', label: 'Instructores', href: '/clases/instructores', icon: Users }
    ]
  },
  {
    id: 'pagos',
    label: 'Pagos',
    href: '/pagos',
    icon: CreditCard,
    badge: 5 // Pagos pendientes
  },
  {
    id: 'reportes',
    label: 'Reportes',
    href: '/reportes',
    icon: BarChart3
  },
  {
    id: 'configuracion',
    label: 'Configuración',
    href: '/configuracion',
    icon: Settings
  }
]

// Componente de navegación principal
export function Navigation() {
  const pathname = usePathname()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())
  const { currentTheme } = useThemeSystem()
  const { success } = useToastActions()

  // Cerrar menú móvil al cambiar de ruta
  useEffect(() => {
    setIsMobileMenuOpen(false)
  }, [pathname])

  // Expandir elementos activos automáticamente
  useEffect(() => {
    if (!pathname) return
    
    const activeItem = NAV_ITEMS.find(item => 
      item.href === pathname || 
      item.children?.some(child => child.href === pathname)
    )
    
    if (activeItem && activeItem.children) {
      setExpandedItems(prev => new Set(Array.from(prev).concat(activeItem.id)))
    }
  }, [pathname])

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev)
      if (newSet.has(itemId)) {
        newSet.delete(itemId)
      } else {
        newSet.add(itemId)
      }
      return newSet
    })
  }

  const isActive = (href: string) => {
    if (!pathname) return false
    if (href === '/') {
      return pathname === '/'
    }
    return pathname.startsWith(href)
  }

  const handleLogout = () => {
    // Simular logout
    success('Sesión cerrada', 'Has cerrado sesión correctamente')
    // Aquí iría la lógica real de logout
  }

  return (
    <>
      {/* Navegación móvil */}
      <div className="lg:hidden">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="fixed top-4 left-4 z-50"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>

        {/* Overlay móvil */}
        {isMobileMenuOpen && (
          <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" />
        )}

        {/* Menú móvil */}
        <div className={`
          fixed top-0 left-0 h-full w-64 bg-surface border-r border-border z-50 transform transition-transform duration-300 ease-in-out lg:hidden
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
        `}>
                  <MobileNavigation 
          items={NAV_ITEMS}
          pathname={pathname || ''}
          expandedItems={expandedItems}
          onToggleExpanded={toggleExpanded}
          onLogout={handleLogout}
        />
        </div>
      </div>

      {/* Navegación desktop */}
      <div className="hidden lg:block">
        <DesktopNavigation 
          items={NAV_ITEMS}
          pathname={pathname || ''}
          expandedItems={expandedItems}
          onToggleExpanded={toggleExpanded}
          onLogout={handleLogout}
        />
      </div>
    </>
  )
}

// Componente de navegación móvil
interface MobileNavigationProps {
  items: NavItem[]
  pathname: string
  expandedItems: Set<string>
  onToggleExpanded: (itemId: string) => void
  onLogout: () => void
}

function MobileNavigation({ 
  items, 
  pathname, 
  expandedItems, 
  onToggleExpanded, 
  onLogout 
}: MobileNavigationProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Header móvil */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">G</span>
          </div>
          <div>
            <h1 className="font-semibold text-foreground">GymSystem</h1>
            <ConnectionStatus className="text-xs" />
          </div>
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex-1 overflow-y-auto p-4">
        <ul className="space-y-2">
          {items.map((item) => (
            <MobileNavItem
              key={item.id}
              item={item}
              pathname={pathname}
              isExpanded={expandedItems.has(item.id)}
              onToggleExpanded={() => onToggleExpanded(item.id)}
            />
          ))}
        </ul>
      </nav>

      {/* Footer móvil */}
      <div className="p-4 border-t border-border">
        <Button
          variant="ghost"
          onClick={onLogout}
          className="w-full justify-start"
        >
          <LogOut className="w-4 h-4 mr-3" />
          Cerrar sesión
        </Button>
      </div>
    </div>
  )
}

// Componente de navegación desktop
interface DesktopNavigationProps {
  items: NavItem[]
  pathname: string
  expandedItems: Set<string>
  onToggleExpanded: (itemId: string) => void
  onLogout: () => void
}

function DesktopNavigation({ 
  items, 
  pathname, 
  expandedItems, 
  onToggleExpanded, 
  onLogout 
}: DesktopNavigationProps) {
  return (
    <div className="w-64 h-screen bg-surface border-r border-border flex flex-col">
      {/* Header desktop */}
      <div className="p-6 border-b border-border">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
            <span className="text-white font-bold">G</span>
          </div>
          <div>
            <h1 className="font-bold text-lg text-foreground">GymSystem</h1>
            <ConnectionStatus className="text-xs" />
          </div>
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex-1 overflow-y-auto p-4">
        <ul className="space-y-1">
          {items.map((item) => (
            <DesktopNavItem
              key={item.id}
              item={item}
              pathname={pathname}
              isExpanded={expandedItems.has(item.id)}
              onToggleExpanded={() => onToggleExpanded(item.id)}
            />
          ))}
        </ul>
      </nav>

      {/* Footer desktop */}
      <div className="p-4 border-t border-border">
        <Button
          variant="ghost"
          onClick={onLogout}
          className="w-full justify-start"
        >
          <LogOut className="w-4 h-4 mr-3" />
          Cerrar sesión
        </Button>
      </div>
    </div>
  )
}

// Componente de item de navegación móvil
interface MobileNavItemProps {
  item: NavItem
  pathname: string
  isExpanded: boolean
  onToggleExpanded: () => void
}

function MobileNavItem({ item, pathname, isExpanded, onToggleExpanded }: MobileNavItemProps) {
  const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
  const hasChildren = item.children && item.children.length > 0

  return (
    <li>
      <div className="space-y-1">
        <Link
          href={item.href}
          className={`
            flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors
            ${isActive 
              ? 'bg-primary text-primary-foreground' 
              : 'text-foreground hover:bg-muted'
            }
          `}
          onClick={hasChildren ? onToggleExpanded : undefined}
        >
          <div className="flex items-center space-x-3">
            <item.icon className="w-4 h-4" />
            <span>{item.label}</span>
          </div>
          <div className="flex items-center space-x-2">
            {item.badge && (
              <Badge variant="secondary" className="text-xs">
                {item.badge}
              </Badge>
            )}
            {hasChildren && (
              <ChevronDown className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
            )}
          </div>
        </Link>

        {/* Subitems */}
        {hasChildren && isExpanded && (
          <ul className="ml-6 space-y-1">
            {item.children!.map((child) => (
              <li key={child.id}>
                <Link
                  href={child.href}
                  className={`
                    flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-colors
                    ${pathname === child.href 
                      ? 'bg-primary/10 text-primary' 
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                    }
                  `}
                >
                  <child.icon className="w-4 h-4" />
                  <span>{child.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </li>
  )
}

// Componente de item de navegación desktop
interface DesktopNavItemProps {
  item: NavItem
  pathname: string
  isExpanded: boolean
  onToggleExpanded: () => void
}

function DesktopNavItem({ item, pathname, isExpanded, onToggleExpanded }: DesktopNavItemProps) {
  const isActive = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
  const hasChildren = item.children && item.children.length > 0

  return (
    <li>
      <div className="space-y-1">
        <Link
          href={item.href}
          className={`
            flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${isActive 
              ? 'bg-primary text-primary-foreground shadow-sm' 
              : 'text-foreground hover:bg-muted hover:shadow-sm'
            }
          `}
          onClick={hasChildren ? onToggleExpanded : undefined}
        >
          <div className="flex items-center space-x-3">
            <item.icon className="w-4 h-4" />
            <span>{item.label}</span>
          </div>
          <div className="flex items-center space-x-2">
            {item.badge && (
              <Badge variant="secondary" className="text-xs">
                {item.badge}
              </Badge>
            )}
            {hasChildren && (
              <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
            )}
          </div>
        </Link>

        {/* Subitems */}
        {hasChildren && (
          <div className={`
            overflow-hidden transition-all duration-300 ease-in-out
            ${isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'}
          `}>
            <ul className="ml-6 space-y-1 pt-1">
              {item.children!.map((child) => (
                <li key={child.id}>
                  <Link
                    href={child.href}
                    className={`
                      flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-all duration-200
                      ${pathname === child.href 
                        ? 'bg-primary/10 text-primary shadow-sm' 
                        : 'text-muted-foreground hover:text-foreground hover:bg-muted hover:shadow-sm'
                      }
                    `}
                  >
                    <child.icon className="w-4 h-4" />
                    <span>{child.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </li>
  )
}

// Componente de barra superior
export function TopBar() {
  const [searchQuery, setSearchQuery] = useState('')
  const { success } = useToastActions()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      success('Búsqueda iniciada', `Buscando: "${searchQuery}"`)
      // Aquí iría la lógica de búsqueda
    }
  }

  return (
    <div className="h-16 bg-surface border-b border-border flex items-center justify-between px-6">
      {/* Búsqueda Global */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar en todo el sistema..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-muted border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
          {searchQuery && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-surface border border-border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
              <div className="p-4">
                <div className="text-sm text-muted-foreground mb-2">
                  Resultados para "{searchQuery}"
                </div>
                <div className="space-y-2">
                  <div className="p-2 hover:bg-muted rounded cursor-pointer">
                    <div className="font-medium">Usuarios</div>
                    <div className="text-sm text-muted-foreground">Buscar en usuarios del sistema</div>
                  </div>
                  <div className="p-2 hover:bg-muted rounded cursor-pointer">
                    <div className="font-medium">Clases</div>
                    <div className="text-sm text-muted-foreground">Buscar en clases y horarios</div>
                  </div>
                  <div className="p-2 hover:bg-muted rounded cursor-pointer">
                    <div className="font-medium">Pagos</div>
                    <div className="text-sm text-muted-foreground">Buscar en pagos y cuotas</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Acciones */}
      <div className="flex items-center space-x-4">
        {/* Notificaciones */}
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="w-5 h-5" />
          <Badge variant="destructive" className="absolute -top-1 -right-1 w-5 h-5 text-xs">
            3
          </Badge>
        </Button>

        {/* Perfil */}
        <Button variant="ghost" size="sm">
          <User className="w-5 h-5" />
        </Button>
      </div>
    </div>
  )
} 