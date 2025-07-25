import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  CreditCard,
  Dumbbell,
  Calendar,
  Activity,
  UserCheck,
  MessageSquare,
  Settings,
  Menu,
  X,
  LogOut,
  Bell,
  BarChart3,
  Search,
  ChevronDown
} from 'lucide-react'
import { Button } from '../ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar'
import { Badge } from '../ui/badge'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../utils/cn'

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  roles?: string[]
}

const navigation: NavItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'Reportes',
    href: '/reports',
    icon: BarChart3,
    roles: ['admin', 'owner', 'trainer'],
  },
  {
    name: 'Usuarios',
    href: '/users',
    icon: Users,
    roles: ['admin', 'owner', 'trainer'],
  },
  {
    name: 'Pagos',
    href: '/payments',
    icon: CreditCard,
    roles: ['admin', 'owner', 'trainer'],
  },
  {
    name: 'Rutinas',
    href: '/routines',
    icon: Dumbbell,
  },
  {
    name: 'Clases',
    href: '/classes',
    icon: Calendar,
  },
  {
    name: 'Ejercicios',
    href: '/exercises',
    icon: Activity,
  },
  {
    name: 'Comunidad',
    href: '/community',
    icon: MessageSquare,
  },
  {
    name: 'Empleados',
    href: '/employees',
    icon: UserCheck,
    roles: ['admin', 'owner'],
  },
  {
    name: 'Configuración',
    href: '/configuration',
    icon: Settings,
    roles: ['admin', 'owner'],
  },
]

export function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const getCurrentPageTitle = () => {
    const currentNav = navigation.find(item => item.href === location.pathname)
    return currentNav?.name || 'Dashboard'
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const filteredNavigation = navigation.filter(item => {
    if (!item.roles) return true
    return user?.role && item.roles.includes(user.role)
  })

  return (
    <div className="min-h-screen bg-gray-50 lg:flex lg:overflow-hidden">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:relative lg:flex lg:flex-shrink-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700">
            <div className="flex items-center space-x-3">
              <div className="bg-white/20 p-2 rounded-lg backdrop-blur-sm">
                <Dumbbell className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold text-white">GymSystem</span>
            </div>
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-white/10 transition-colors"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5 text-white" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {filteredNavigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <button
                  key={item.name}
                  onClick={() => {
                    navigate(item.href)
                    setSidebarOpen(false)
                  }}
                  className={cn(
                    "w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 group relative",
                    isActive
                      ? "bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 shadow-sm border-l-4 border-blue-600"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900 hover:shadow-sm"
                  )}
                >
                  <item.icon
                    className={cn(
                      "mr-3 h-5 w-5 transition-colors",
                      isActive ? "text-blue-600" : "text-gray-400 group-hover:text-gray-600"
                    )}
                  />
                  <span className="flex-1 text-left">{item.name}</span>
                  {isActive && (
                    <div className="w-2 h-2 bg-blue-600 rounded-full" />
                  )}
                </button>
              )
            })}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center space-x-3 mb-4 p-3 bg-white rounded-xl shadow-sm">
              <Avatar className="h-12 w-12">
                <AvatarImage src={user?.profile_picture} alt={`${user?.first_name} ${user?.last_name}`} />
                <AvatarFallback className="bg-blue-100 text-blue-600 font-semibold">
                  {user?.first_name?.charAt(0)?.toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">
                  {user?.first_name} {user?.last_name}
                </p>
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary" className="text-xs capitalize">
                    {user?.role || 'Miembro'}
                  </Badge>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-green-400 rounded-full" />
                    <span className="text-xs text-gray-500">En línea</span>
                  </div>
                </div>
              </div>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              size="sm"
              className="w-full hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-0 lg:flex-1 lg:flex lg:flex-col lg:overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-6">
            <div className="flex items-center space-x-4">
              <button
                className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="h-5 w-5 text-gray-600" />
              </button>
              <div className="flex items-center space-x-3">
                <h1 className="text-xl font-semibold text-gray-900">
                  {getCurrentPageTitle()}
                </h1>
                <Badge variant="outline" className="hidden md:inline-flex">
                  {new Date().toLocaleDateString('es-ES', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </Badge>
              </div>
            </div>
            
            {/* Search and Actions */}
            <div className="flex items-center space-x-4">
              {/* Search Bar */}
              <div className="hidden md:flex items-center space-x-2 bg-gray-50 rounded-lg px-3 py-2 min-w-[300px]">
                <Search className="h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar usuarios, clases, rutinas..."
                  className="bg-transparent border-0 outline-none text-sm text-gray-600 placeholder-gray-400 flex-1"
                />
              </div>
              
              {/* Notifications */}
              <button className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                <Bell className="h-5 w-5" />
                <Badge className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-xs bg-red-500">
                  3
                </Badge>
              </button>
              
              {/* User Menu */}
              <div className="flex items-center space-x-3 pl-4 border-l border-gray-200">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.profile_picture} alt={`${user?.first_name} ${user?.last_name}`} />
                  <AvatarFallback className="bg-blue-100 text-blue-600 text-sm font-semibold">
                    {user?.first_name?.charAt(0)?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:block">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs text-gray-500 capitalize">
                    {user?.role}
                  </p>
                </div>
                <ChevronDown className="h-4 w-4 text-gray-400" />
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6 lg:flex-1 lg:overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}