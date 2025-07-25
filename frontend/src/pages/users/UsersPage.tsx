import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '../../components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../../components/ui/dialog'
import { Checkbox } from '../../components/ui/checkbox'
import { Textarea } from '../../components/ui/textarea'
import {
  Search,
  Filter,
  Plus,
  Edit,
  Eye,
  QrCode,
  UserPlus,
  Download,
  MoreHorizontal,
  XCircle,
  Users,
  Calendar,
  DollarSign,
  Mail,
  Phone,
  CreditCard,
  Settings,
  Trash2,
  UserCheck,
  UserX,
  TrendingUp,
  BarChart3,
  Target,
  Upload,
  MessageSquare,
  Zap,
  Bell,
  RefreshCw,
  FileText,
  Shield
} from 'lucide-react'
import { useUserStore } from '../../store'
import { UserProfile } from '../../types/user'
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'

const membershipTypes = ['Todos', 'Mensual', 'Estudiante', 'Funcional', 'Semanal', 'Diaria', 'Promocional']
const statusOptions = ['Todos', 'active', 'inactive', 'suspended']
const roleOptions = ['Todos', 'admin', 'owner', 'trainer', 'member']

// Mock data for analytics
const membershipGrowthData = [
  { month: 'Ene', nuevos: 15, cancelados: 3, total: 120 },
  { month: 'Feb', nuevos: 22, cancelados: 5, total: 137 },
  { month: 'Mar', nuevos: 18, cancelados: 2, total: 153 },
  { month: 'Abr', nuevos: 25, cancelados: 4, total: 174 },
  { month: 'May', nuevos: 20, cancelados: 6, total: 188 },
  { month: 'Jun', nuevos: 28, cancelados: 3, total: 213 }
]

const membershipTypeDistribution = [
  { name: 'Mensual', value: 45, color: '#3B82F6' },
  { name: 'Estudiante', value: 25, color: '#10B981' },
  { name: 'Funcional', value: 15, color: '#F59E0B' },
  { name: 'Semanal', value: 10, color: '#EF4444' },
  { name: 'Diaria', value: 5, color: '#8B5CF6' }
]

const attendanceData = [
  { day: 'Lun', checkins: 45, checkouts: 42 },
  { day: 'Mar', checkins: 52, checkouts: 48 },
  { day: 'Mié', checkins: 38, checkouts: 35 },
  { day: 'Jue', checkins: 48, checkouts: 45 },
  { day: 'Vie', checkins: 55, checkouts: 52 },
  { day: 'Sáb', checkins: 35, checkouts: 33 },
  { day: 'Dom', checkins: 25, checkouts: 22 }
]

const quickStats = [
  {
    title: 'Total Miembros',
    value: '213',
    change: '+12.5%',
    trend: 'up',
    icon: Users,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50'
  },
  {
    title: 'Nuevos Este Mes',
    value: '28',
    change: '+15.8%',
    trend: 'up',
    icon: UserPlus,
    color: 'text-green-600',
    bgColor: 'bg-green-50'
  },
  {
    title: 'Check-ins Hoy',
    value: '87',
    change: '+8.2%',
    trend: 'up',
    icon: UserCheck,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50'
  },
  {
    title: 'Tasa Retención',
    value: '94.2%',
    change: '+2.1%',
    trend: 'up',
    icon: Target,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50'
  }
]

export function UsersPage() {
  const { 
    users, 
    loading, 
    error, 
    totalPages, 
    currentPage, 
    getUsers, 
    searchUsers, 
    setCurrentPage 
  } = useUserStore()
  
  const [filteredUsers, setFilteredUsers] = useState<UserProfile[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedMembershipType, setSelectedMembershipType] = useState('Todos')
  const [selectedStatus, setSelectedStatus] = useState('Todos')
  const [selectedRole, setSelectedRole] = useState('Todos')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedUsers, setSelectedUsers] = useState<number[]>([])
  const [usersPerPage] = useState(10)
  const [activeTab, setActiveTab] = useState('list')
  const [showNewUserDialog, setShowNewUserDialog] = useState(false)
  const [showUserDetailsDialog, setShowUserDetailsDialog] = useState(false)
  const [selectedUser, setSelectedUser] = useState<UserProfile | null>(null)
  const [showBulkActionsDialog, setShowBulkActionsDialog] = useState(false)

  // Load users on component mount
  useEffect(() => {
    getUsers({ page: 1, limit: usersPerPage })
  }, [])

  // Filter users based on search and filters
  useEffect(() => {
    if (!users) {
      setFilteredUsers([])
      return
    }

    let filtered = users

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(user =>
        `${user.first_name} ${user.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.phone?.includes(searchTerm)
      )
    }

    // Membership type filter
    if (selectedMembershipType !== 'Todos') {
      filtered = filtered.filter(user => user.user_type === selectedMembershipType)
    }

    // Status filter
    if (selectedStatus !== 'Todos') {
      filtered = filtered.filter(user => user.status === selectedStatus)
    }

    // Role filter
    if (selectedRole !== 'Todos') {
      filtered = filtered.filter(user => user.role === selectedRole)
    }

    setFilteredUsers(filtered)
  }, [users, searchTerm, selectedMembershipType, selectedStatus, selectedRole])

  // Pagination
  const indexOfLastUser = currentPage * usersPerPage
  const indexOfFirstUser = indexOfLastUser - usersPerPage
  const currentUsers = filteredUsers.slice(indexOfFirstUser, indexOfLastUser)
  const totalPagesCalculated = Math.ceil(filteredUsers.length / usersPerPage)
  const finalTotalPages = totalPages || totalPagesCalculated

  const handleSelectUser = (userId: number) => {
    setSelectedUsers(prev =>
      prev.includes(userId)
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    )
  }

  const handleSelectAll = () => {
    if (selectedUsers.length === currentUsers.length) {
      setSelectedUsers([])
    } else {
      setSelectedUsers(currentUsers.map(user => user.id))
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Activo'
      case 'inactive':
        return 'Inactivo'
      case 'suspended':
        return 'Suspendido'
      default:
        return 'Desconocido'
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'default'
      case 'inactive':
        return 'destructive'
      case 'suspended':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  const getRoleText = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrador'
      case 'owner':
        return 'Dueño'
      case 'trainer':
        return 'Entrenador'
      case 'member':
        return 'Miembro'
      default:
        return role
    }
  }

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'admin':
      case 'owner':
        return 'destructive'
      case 'trainer':
        return 'secondary'
      default:
        return 'outline'
    }
  }

  // Handle search with debounce
  const handleSearch = (term: string) => {
    setSearchTerm(term)
    if (term.length > 2) {
      searchUsers({ query: term, page: 1, limit: usersPerPage })
    } else if (term.length === 0) {
      getUsers({ page: 1, limit: usersPerPage })
    }
  }

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    getUsers({ page, limit: usersPerPage })
  }

  const handleViewUser = (user: UserProfile) => {
    setSelectedUser(user)
    setShowUserDetailsDialog(true)
  }

  const handleQuickAction = (action: string) => {
    console.log('Quick action:', action)
    // TODO: Implement quick actions
  }

  if (loading && !users) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Cargando usuarios...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Usuarios</h1>
          <p className="text-gray-600 mt-1">Administra miembros, entrenadores y personal del gimnasio</p>
          <div className="flex items-center space-x-4 mt-2">
            <Badge variant="outline" className="text-xs">
              Total: {filteredUsers.length} usuarios
            </Badge>
            <Badge className="bg-green-100 text-green-800 text-xs">
              {selectedUsers.length} seleccionados
            </Badge>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm" onClick={() => handleQuickAction('export')}>
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleQuickAction('import')}>
            <Upload className="h-4 w-4 mr-2" />
            Importar
          </Button>
          <Dialog open={showNewUserDialog} onOpenChange={setShowNewUserDialog}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                Nuevo Usuario
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Crear Nuevo Usuario</DialogTitle>
                <DialogDescription>
                  Completa la información para registrar un nuevo usuario en el sistema.
                </DialogDescription>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">Nombre</Label>
                  <Input id="firstName" placeholder="Nombre" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Apellido</Label>
                  <Input id="lastName" placeholder="Apellido" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" placeholder="email@ejemplo.com" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Teléfono</Label>
                  <Input id="phone" placeholder="+1234567890" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Rol</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar rol" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="member">Miembro</SelectItem>
                      <SelectItem value="trainer">Entrenador</SelectItem>
                      <SelectItem value="admin">Administrador</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="membershipType">Tipo de Membresía</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar membresía" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Mensual">Mensual</SelectItem>
                      <SelectItem value="Estudiante">Estudiante</SelectItem>
                      <SelectItem value="Funcional">Funcional</SelectItem>
                      <SelectItem value="Semanal">Semanal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="col-span-2 space-y-2">
                  <Label htmlFor="address">Dirección</Label>
                  <Textarea id="address" placeholder="Dirección completa" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowNewUserDialog(false)}>
                  Cancelar
                </Button>
                <Button onClick={() => setShowNewUserDialog(false)}>
                  Crear Usuario
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickStats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Card key={index} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                      <Icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                      <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex items-center">
                  <TrendingUp className="h-4 w-4 mr-1 text-green-500" />
                  <span className="text-sm font-medium text-green-600">{stat.change}</span>
                  <span className="text-sm text-gray-500 ml-1">vs mes anterior</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="list">Lista de Usuarios</TabsTrigger>
          <TabsTrigger value="analytics">Análisis</TabsTrigger>
          <TabsTrigger value="checkins">Check-ins</TabsTrigger>
          <TabsTrigger value="reports">Reportes</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-6">
          {/* Search and Filters */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-4 mb-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    type="text"
                    placeholder="Buscar por nombre, email o teléfono..."
                    value={searchTerm}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className={showFilters ? "bg-gray-50" : ""}
                >
                  <Filter className="h-4 w-4 mr-2" />
                  Filtros
                </Button>
                {selectedUsers.length > 0 && (
                  <Dialog open={showBulkActionsDialog} onOpenChange={setShowBulkActionsDialog}>
                    <DialogTrigger asChild>
                      <Button variant="outline">
                        <Settings className="h-4 w-4 mr-2" />
                        Acciones en Lote ({selectedUsers.length})
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Acciones en Lote</DialogTitle>
                        <DialogDescription>
                          Selecciona una acción para aplicar a {selectedUsers.length} usuarios seleccionados.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="grid grid-cols-2 gap-4 py-4">
                        <Button variant="outline" className="justify-start">
                          <Mail className="h-4 w-4 mr-2" />
                          Enviar Email
                        </Button>
                        <Button variant="outline" className="justify-start">
                          <MessageSquare className="h-4 w-4 mr-2" />
                          Enviar SMS
                        </Button>
                        <Button variant="outline" className="justify-start">
                          <UserCheck className="h-4 w-4 mr-2" />
                          Activar Usuarios
                        </Button>
                        <Button variant="outline" className="justify-start">
                          <UserX className="h-4 w-4 mr-2" />
                          Suspender Usuarios
                        </Button>
                        <Button variant="outline" className="justify-start">
                          <Download className="h-4 w-4 mr-2" />
                          Exportar Datos
                        </Button>
                        <Button variant="outline" className="justify-start text-red-600">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Eliminar Usuarios
                        </Button>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowBulkActionsDialog(false)}>
                          Cancelar
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                )}
              </div>

              {/* Filters */}
              {showFilters && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                  <div className="space-y-2">
                    <Label>Tipo de Membresía</Label>
                    <Select value={selectedMembershipType} onValueChange={setSelectedMembershipType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {membershipTypes.map(type => (
                          <SelectItem key={type} value={type}>{type}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Estado</Label>
                    <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {statusOptions.map(status => (
                          <SelectItem key={status} value={status}>
                            {status === 'Todos' ? 'Todos' : getStatusText(status)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Rol</Label>
                    <Select value={selectedRole} onValueChange={setSelectedRole}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {roleOptions.map(role => (
                          <SelectItem key={role} value={role}>
                            {role === 'Todos' ? 'Todos' : getRoleText(role)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="h-5 w-5 mr-2 text-yellow-500" />
                Acciones Rápidas
              </CardTitle>
              <CardDescription>Herramientas y funciones de uso frecuente</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <Button variant="outline" className="justify-start" onClick={() => handleQuickAction('qr-checkin')}>
                  <QrCode className="h-4 w-4 mr-2" />
                  Check-in QR
                </Button>
                <Button variant="outline" className="justify-start" onClick={() => handleQuickAction('bulk-register')}>
                  <UserPlus className="h-4 w-4 mr-2" />
                  Registro Masivo
                </Button>
                <Button variant="outline" className="justify-start" onClick={() => handleQuickAction('generate-cards')}>
                  <CreditCard className="h-4 w-4 mr-2" />
                  Generar Tarjetas
                </Button>
                <Button variant="outline" className="justify-start" onClick={() => handleQuickAction('send-notifications')}>
                  <Bell className="h-4 w-4 mr-2" />
                  Notificaciones
                </Button>
                <Button variant="outline" className="justify-start" onClick={() => handleQuickAction('attendance-report')}>
                  <BarChart3 className="h-4 w-4 mr-2" />
                  Reporte Asistencia
                </Button>
                <Button variant="outline" className="justify-start" onClick={() => handleQuickAction('backup-data')}>
                  <Download className="h-4 w-4 mr-2" />
                  Respaldar Datos
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Users Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Usuarios ({filteredUsers.length})</CardTitle>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm" onClick={() => getUsers({ page: 1, limit: usersPerPage })}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Actualizar
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedUsers.length === currentUsers.length && currentUsers.length > 0}
                        onCheckedChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Contacto</TableHead>
                    <TableHead>Rol</TableHead>
                    <TableHead>Membresía</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Último Check-in</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentUsers.map((user) => (
                    <TableRow key={user.id} className="hover:bg-gray-50">
                      <TableCell>
                        <Checkbox
                          checked={selectedUsers.includes(user.id)}
                          onCheckedChange={() => handleSelectUser(user.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <Avatar>
                            <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${user.first_name} ${user.last_name}`} />
                            <AvatarFallback>
                              {user.first_name[0]}{user.last_name[0]}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium text-gray-900">
                              {user.first_name} {user.last_name}
                            </p>
                            <p className="text-sm text-gray-500">ID: {user.id}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="flex items-center space-x-1">
                            <Mail className="h-3 w-3 text-gray-400" />
                            <p className="text-sm text-gray-900">{user.email}</p>
                          </div>
                          <div className="flex items-center space-x-1 mt-1">
                            <Phone className="h-3 w-3 text-gray-400" />
                            <p className="text-sm text-gray-500">{user.phone}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getRoleBadgeVariant(user.role)}>
                          {getRoleText(user.role)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{user.user_type}</p>
                          <p className="text-sm text-gray-500">{user.membership_type}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusBadgeVariant(user.status)}>
                          {getStatusText(user.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {user.last_checkin || 'Nunca'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button variant="ghost" size="sm" onClick={() => handleViewUser(user)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {finalTotalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
                  <div className="text-sm text-gray-700">
                    Mostrando {indexOfFirstUser + 1} a {Math.min(indexOfLastUser, filteredUsers.length)} de {filteredUsers.length} usuarios
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(Math.max(currentPage - 1, 1))}
                      disabled={currentPage === 1 || loading}
                    >
                      Anterior
                    </Button>
                    <span className="text-sm text-gray-700">
                      Página {currentPage} de {finalTotalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(Math.min(currentPage + 1, finalTotalPages))}
                      disabled={currentPage === finalTotalPages || loading}
                    >
                      Siguiente
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          {/* Analytics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Membership Growth */}
            <Card>
              <CardHeader>
                <CardTitle>Crecimiento de Membresías</CardTitle>
                <CardDescription>Nuevos miembros vs cancelaciones por mes</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={membershipGrowthData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="nuevos" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} name="Nuevos" />
                    <Area type="monotone" dataKey="cancelados" stackId="2" stroke="#EF4444" fill="#EF4444" fillOpacity={0.6} name="Cancelados" />
                    <Legend />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Membership Type Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Distribución por Tipo de Membresía</CardTitle>
                <CardDescription>Porcentaje de usuarios por tipo de membresía</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={membershipTypeDistribution}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}%`}
                    >
                      {membershipTypeDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
            </TabsContent>

            <TabsContent value="checkins" className="mt-0 space-y-6">
          {/* Check-ins Analytics */}
          <Card>
            <CardHeader>
              <CardTitle>Análisis de Check-ins</CardTitle>
              <CardDescription>Patrones de asistencia durante la semana</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={attendanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="checkins" fill="#3B82F6" name="Check-ins" />
                  <Bar dataKey="checkouts" fill="#10B981" name="Check-outs" />
                  <Legend />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Recent Check-ins */}
          <Card>
            <CardHeader>
              <CardTitle>Check-ins Recientes</CardTitle>
              <CardDescription>Últimos usuarios que han ingresado al gimnasio</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Avatar>
                        <AvatarFallback>U{i}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">Usuario {i}</p>
                        <p className="text-sm text-gray-500">Membresía Mensual</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{new Date().toLocaleTimeString()}</p>
                      <Badge variant="outline">Check-in</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports" className="space-y-6">
          {/* Reports Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="h-5 w-5 mr-2 text-blue-600" />
                  Reporte de Membresías
                </CardTitle>
                <CardDescription>Estado actual de todas las membresías</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Generar Reporte
                </Button>
              </CardContent>
            </Card>

            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2 text-green-600" />
                  Análisis de Asistencia
                </CardTitle>
                <CardDescription>Patrones de uso del gimnasio</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Generar Reporte
                </Button>
              </CardContent>
            </Card>

            <Card className="cursor-pointer hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <DollarSign className="h-5 w-5 mr-2 text-purple-600" />
                  Reporte Financiero
                </CardTitle>
                <CardDescription>Ingresos por membresías y servicios</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Generar Reporte
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* User Details Dialog */}
      <Dialog open={showUserDetailsDialog} onOpenChange={setShowUserDetailsDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Detalles del Usuario</DialogTitle>
            <DialogDescription>
              Información completa y historial del usuario seleccionado.
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 py-4">
              {/* User Info */}
              <div className="lg:col-span-1 space-y-4">
                <div className="text-center">
                  <Avatar className="w-24 h-24 mx-auto mb-4">
                    <AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${selectedUser.first_name} ${selectedUser.last_name}`} />
                    <AvatarFallback className="text-2xl">
                      {selectedUser.first_name[0]}{selectedUser.last_name[0]}
                    </AvatarFallback>
                  </Avatar>
                  <h3 className="text-xl font-bold">{selectedUser.first_name} {selectedUser.last_name}</h3>
                  <p className="text-gray-500">ID: {selectedUser.id}</p>
                  <Badge variant={getStatusBadgeVariant(selectedUser.status)} className="mt-2">
                    {getStatusText(selectedUser.status)}
                  </Badge>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Mail className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">{selectedUser.email}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Phone className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">{selectedUser.phone}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Shield className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">{getRoleText(selectedUser.role)}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CreditCard className="h-4 w-4 text-gray-400" />
                    <span className="text-sm">{selectedUser.user_type}</span>
                  </div>
                </div>
              </div>

              {/* User Activity */}
              <div className="lg:col-span-2 space-y-4">
                <Tabs defaultValue="activity">
                  <TabsList>
                    <TabsTrigger value="activity">Actividad</TabsTrigger>
                    <TabsTrigger value="payments">Pagos</TabsTrigger>
                    <TabsTrigger value="classes">Clases</TabsTrigger>
                  </TabsList>
                  <TabsContent value="activity" className="space-y-4">
                    <div className="space-y-3">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                          <div className="p-2 bg-blue-100 rounded-full">
                            <UserCheck className="h-4 w-4 text-blue-600" />
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-medium">Check-in al gimnasio</p>
                            <p className="text-xs text-gray-500">Hace {i} horas</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                  <TabsContent value="payments" className="space-y-4">
                    <div className="space-y-3">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className="p-2 bg-green-100 rounded-full">
                              <DollarSign className="h-4 w-4 text-green-600" />
                            </div>
                            <div>
                              <p className="text-sm font-medium">Pago de membresía</p>
                              <p className="text-xs text-gray-500">{new Date().toLocaleDateString()}</p>
                            </div>
                          </div>
                          <Badge variant="default">$85.00</Badge>
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                  <TabsContent value="classes" className="space-y-4">
                    <div className="space-y-3">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className="p-2 bg-purple-100 rounded-full">
                              <Calendar className="h-4 w-4 text-purple-600" />
                            </div>
                            <div>
                              <p className="text-sm font-medium">Clase de Yoga</p>
                              <p className="text-xs text-gray-500">Mañana 7:00 AM</p>
                            </div>
                          </div>
                          <Badge variant="outline">Inscrito</Badge>
                        </div>
                      ))}
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUserDetailsDialog(false)}>
              Cerrar
            </Button>
            <Button>
              <Edit className="h-4 w-4 mr-2" />
              Editar Usuario
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default UsersPage