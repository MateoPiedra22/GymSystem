import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Button } from '../../components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Badge } from '../../components/ui/badge'
import {
  Users,
  DollarSign,
  Calendar,
  Activity,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  UserPlus,
  UserCheck,
  Dumbbell,
  Target,
  Heart,
  Bell,
  MessageSquare,
  RefreshCw,
  BarChart3,
  CheckCircle,
  AlertTriangle,
  Info,
  Filter,
  Download,
  Zap
} from 'lucide-react'
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
import { useDashboardStore } from '../../store'

// Mock data for enhanced dashboard
const revenueData = [
  { month: 'Ene', revenue: 45000, expenses: 25000, members: 120 },
  { month: 'Feb', revenue: 52000, expenses: 28000, members: 135 },
  { month: 'Mar', revenue: 48000, expenses: 26000, members: 128 },
  { month: 'Abr', revenue: 61000, expenses: 32000, members: 152 },
  { month: 'May', revenue: 55000, expenses: 29000, members: 145 },
  { month: 'Jun', revenue: 67000, expenses: 35000, members: 168 }
]

const attendanceData = [
  { day: 'Lun', morning: 25, afternoon: 35, evening: 45 },
  { day: 'Mar', morning: 30, afternoon: 40, evening: 50 },
  { day: 'Mié', morning: 28, afternoon: 38, evening: 48 },
  { day: 'Jue', morning: 32, afternoon: 42, evening: 52 },
  { day: 'Vie', morning: 35, afternoon: 45, evening: 55 },
  { day: 'Sáb', morning: 40, afternoon: 30, evening: 25 },
  { day: 'Dom', morning: 20, afternoon: 25, evening: 15 }
]

const membershipDistribution = [
  { name: 'Básica', value: 45, color: '#3B82F6' },
  { name: 'Premium', value: 30, color: '#10B981' },
  { name: 'VIP', value: 15, color: '#F59E0B' },
  { name: 'Estudiante', value: 10, color: '#EF4444' }
]

const equipmentUsage = [
  { equipment: 'Caminadoras', usage: 85, capacity: 100 },
  { equipment: 'Pesas', usage: 92, capacity: 100 },
  { equipment: 'Bicicletas', usage: 78, capacity: 100 },
  { equipment: 'Máquinas', usage: 65, capacity: 100 },
  { equipment: 'Funcional', usage: 88, capacity: 100 }
]

const notifications = [
  { id: 1, type: 'success', title: 'Nuevo miembro registrado', message: 'Juan Pérez se ha unido al gimnasio', time: '5 min' },
  { id: 2, type: 'warning', title: 'Pago pendiente', message: '3 miembros tienen pagos vencidos', time: '15 min' },
  { id: 3, type: 'info', title: 'Clase cancelada', message: 'Yoga de las 18:00 ha sido cancelada', time: '30 min' },
  { id: 4, type: 'error', title: 'Equipo fuera de servicio', message: 'Caminadora #3 requiere mantenimiento', time: '1 h' }
]

const quickActions = [
  { name: 'Nuevo Miembro', action: 'new-member', icon: UserPlus, color: 'bg-blue-600 hover:bg-blue-700' },
  { name: 'Check-in Rápido', action: 'quick-checkin', icon: UserCheck, color: 'bg-green-600 hover:bg-green-700' },
  { name: 'Nueva Rutina', action: 'new-routine', icon: Dumbbell, color: 'bg-purple-600 hover:bg-purple-700' },
  { name: 'Programar Clase', action: 'schedule-class', icon: Calendar, color: 'bg-orange-600 hover:bg-orange-700' },
  { name: 'Mensaje Masivo', action: 'mass-message', icon: MessageSquare, color: 'bg-indigo-600 hover:bg-indigo-700' },
  { name: 'Generar Reporte', action: 'generate-report', icon: BarChart3, color: 'bg-pink-600 hover:bg-pink-700' }
]

export function DashboardPage() {
  const [selectedPeriod, setSelectedPeriod] = useState('month')
  const [selectedKPIView, setSelectedKPIView] = useState('overview')
  const {
    loading,
    error,
    loadDashboardData
  } = useDashboardStore()

  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  // Enhanced KPI cards with more metrics
  const kpiCards = [
    {
      title: 'Miembros Activos',
      value: '168',
      change: '+12.5%',
      trend: 'up',
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      description: 'Total de miembros activos'
    },
    {
      title: 'Ingresos Mensuales',
      value: '$67,000',
      change: '+8.2%',
      trend: 'up',
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      description: 'Ingresos del mes actual'
    },
    {
      title: 'Clases Programadas',
      value: '156',
      change: '+5.1%',
      trend: 'up',
      icon: Calendar,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      description: 'Clases programadas este mes'
    },
    {
      title: 'Tasa de Asistencia',
      value: '87.3%',
      change: '-2.1%',
      trend: 'down',
      icon: Activity,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      description: 'Promedio de asistencia'
    },
    {
      title: 'Nuevos Miembros',
      value: '23',
      change: '+15.8%',
      trend: 'up',
      icon: UserPlus,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-50',
      description: 'Nuevos miembros este mes'
    },
    {
      title: 'Retención',
      value: '94.2%',
      change: '+1.3%',
      trend: 'up',
      icon: Target,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      description: 'Tasa de retención mensual'
    },
    {
      title: 'Uso de Equipos',
      value: '81.6%',
      change: '+3.7%',
      trend: 'up',
      icon: Dumbbell,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      description: 'Promedio de uso de equipos'
    },
    {
      title: 'Satisfacción',
      value: '4.8/5',
      change: '+0.2',
      trend: 'up',
      icon: Heart,
      color: 'text-pink-600',
      bgColor: 'bg-pink-50',
      description: 'Calificación promedio'
    }
  ]

  const handleQuickAction = (action: string) => {
    console.log('Quick action:', action)
    // TODO: Implement navigation to respective pages
  }

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success': return CheckCircle
      case 'warning': return AlertTriangle
      case 'error': return AlertCircle
      default: return Info
    }
  }

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success': return 'text-green-600 bg-green-50'
      case 'warning': return 'text-yellow-600 bg-yellow-50'
      case 'error': return 'text-red-600 bg-red-50'
      default: return 'text-blue-600 bg-blue-50'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertCircle className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error al cargar el dashboard</h3>
            <p className="mt-2 text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Enhanced Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Resumen completo del rendimiento del gimnasio</p>
          <div className="flex items-center space-x-4 mt-2">
            <Badge variant="outline" className="text-xs">
              Última actualización: {new Date().toLocaleTimeString()}
            </Badge>
            <Badge className="bg-green-100 text-green-800 text-xs">
              Sistema operativo
            </Badge>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="day">Hoy</SelectItem>
              <SelectItem value="week">Esta semana</SelectItem>
              <SelectItem value="month">Este mes</SelectItem>
              <SelectItem value="quarter">Trimestre</SelectItem>
              <SelectItem value="year">Este año</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filtros
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
          <Button size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
        </div>
      </div>

      {/* KPI Selection Tabs */}
      <Tabs value={selectedKPIView} onValueChange={setSelectedKPIView}>
        <TabsList>
          <TabsTrigger value="overview">Resumen</TabsTrigger>
          <TabsTrigger value="financial">Financiero</TabsTrigger>
          <TabsTrigger value="operational">Operacional</TabsTrigger>
          <TabsTrigger value="satisfaction">Satisfacción</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Main KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {kpiCards.slice(0, 4).map((kpi, index) => {
              const Icon = kpi.icon
              const TrendIcon = kpi.trend === 'up' ? TrendingUp : TrendingDown
              
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-3 rounded-xl ${kpi.bgColor}`}>
                          <Icon className={`h-6 w-6 ${kpi.color}`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-600">{kpi.title}</p>
                          <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
                          <p className="text-xs text-gray-500 mt-1">{kpi.description}</p>
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex items-center">
                      <TrendIcon className={`h-4 w-4 mr-1 ${
                        kpi.trend === 'up' ? 'text-green-500' : 'text-red-500'
                      }`} />
                      <span className={`text-sm font-medium ${
                        kpi.trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {kpi.change}
                      </span>
                      <span className="text-sm text-gray-500 ml-1">vs mes anterior</span>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
            </TabsContent>

        <TabsContent value="financial" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[kpiCards[1], kpiCards[4], kpiCards[5]].map((kpi, index) => {
              const Icon = kpi.icon
              const TrendIcon = kpi.trend === 'up' ? TrendingUp : TrendingDown
              
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-3 rounded-xl ${kpi.bgColor}`}>
                          <Icon className={`h-6 w-6 ${kpi.color}`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-600">{kpi.title}</p>
                          <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
                          <p className="text-xs text-gray-500 mt-1">{kpi.description}</p>
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex items-center">
                      <TrendIcon className={`h-4 w-4 mr-1 ${
                        kpi.trend === 'up' ? 'text-green-500' : 'text-red-500'
                      }`} />
                      <span className={`text-sm font-medium ${
                        kpi.trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {kpi.change}
                      </span>
                      <span className="text-sm text-gray-500 ml-1">vs mes anterior</span>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="operational" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[kpiCards[2], kpiCards[3], kpiCards[6]].map((kpi, index) => {
              const Icon = kpi.icon
              const TrendIcon = kpi.trend === 'up' ? TrendingUp : TrendingDown
              
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-3 rounded-xl ${kpi.bgColor}`}>
                          <Icon className={`h-6 w-6 ${kpi.color}`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-600">{kpi.title}</p>
                          <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
                          <p className="text-xs text-gray-500 mt-1">{kpi.description}</p>
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex items-center">
                      <TrendIcon className={`h-4 w-4 mr-1 ${
                        kpi.trend === 'up' ? 'text-green-500' : 'text-red-500'
                      }`} />
                      <span className={`text-sm font-medium ${
                        kpi.trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {kpi.change}
                      </span>
                      <span className="text-sm text-gray-500 ml-1">vs mes anterior</span>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="satisfaction" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[kpiCards[7]].map((kpi, index) => {
              const Icon = kpi.icon
              const TrendIcon = kpi.trend === 'up' ? TrendingUp : TrendingDown
              
              return (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-3 rounded-xl ${kpi.bgColor}`}>
                          <Icon className={`h-6 w-6 ${kpi.color}`} />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-600">{kpi.title}</p>
                          <p className="text-2xl font-bold text-gray-900">{kpi.value}</p>
                          <p className="text-xs text-gray-500 mt-1">{kpi.description}</p>
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex items-center">
                      <TrendIcon className={`h-4 w-4 mr-1 ${
                        kpi.trend === 'up' ? 'text-green-500' : 'text-red-500'
                      }`} />
                      <span className={`text-sm font-medium ${
                        kpi.trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {kpi.change}
                      </span>
                      <span className="text-sm text-gray-500 ml-1">vs mes anterior</span>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>
      </Tabs>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Quick Actions */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Zap className="h-5 w-5 mr-2 text-yellow-500" />
                Acciones Rápidas
              </CardTitle>
              <CardDescription>Accesos directos a funciones principales</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {quickActions.map((action, index) => {
                const Icon = action.icon
                return (
                  <Button
                    key={index}
                    onClick={() => handleQuickAction(action.action)}
                    className={`w-full justify-start text-white transition-all duration-200 ${action.color}`}
                    size="sm"
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {action.name}
                  </Button>
                )
              })}
            </CardContent>
          </Card>
        </div>

        {/* Notifications Center */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  <Bell className="h-5 w-5 mr-2 text-blue-500" />
                  Notificaciones
                </div>
                <Badge className="bg-red-500">{notifications.length}</Badge>
              </CardTitle>
              <CardDescription>Alertas y eventos recientes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 max-h-80 overflow-y-auto">
              {notifications.map((notification) => {
                const Icon = getNotificationIcon(notification.type)
                return (
                  <div key={notification.id} className="flex items-start space-x-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors">
                    <div className={`p-1 rounded-full ${getNotificationColor(notification.type)}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                      <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                      <p className="text-xs text-gray-400 mt-1">{notification.time}</p>
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>
        </div>

        {/* Equipment Usage */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Uso de Equipamiento</CardTitle>
              <CardDescription>Estado actual del equipamiento del gimnasio</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {equipmentUsage.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Dumbbell className="h-5 w-5 text-gray-400" />
                      <span className="text-sm font-medium">{item.equipment}</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            item.usage > 90 ? 'bg-red-500' : 
                            item.usage > 70 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${item.usage}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-12">{item.usage}%</span>
                      <Badge variant={item.usage > 90 ? 'destructive' : item.usage > 70 ? 'secondary' : 'default'}>
                        {item.usage > 90 ? 'Alto' : item.usage > 70 ? 'Medio' : 'Normal'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Análisis Financiero</CardTitle>
            <CardDescription>Ingresos vs Gastos mensuales</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, '']} />
                <Area type="monotone" dataKey="revenue" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
                <Area type="monotone" dataKey="expenses" stackId="2" stroke="#EF4444" fill="#EF4444" fillOpacity={0.6} />
                <Legend />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Attendance Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Asistencia por Horarios</CardTitle>
            <CardDescription>Distribución de asistencia durante la semana</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={attendanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="morning" stackId="a" fill="#F59E0B" name="Mañana" />
                <Bar dataKey="afternoon" stackId="a" fill="#3B82F6" name="Tarde" />
                <Bar dataKey="evening" stackId="a" fill="#10B981" name="Noche" />
                <Legend />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Membership Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Distribución de Membresías</CardTitle>
            <CardDescription>Tipos de membresía más populares</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RechartsPieChart>
                <Pie
                  data={membershipDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                >
                  {membershipDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </RechartsPieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Actividad Reciente</CardTitle>
            <CardDescription>Últimas acciones en el sistema</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                <UserPlus className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-sm font-medium">Nuevo miembro registrado</p>
                  <p className="text-xs text-gray-600">María González se unió al plan Premium</p>
                  <p className="text-xs text-gray-400">Hace 5 minutos</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <DollarSign className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm font-medium">Pago procesado</p>
                  <p className="text-xs text-gray-600">$85.00 - Membresía mensual de Carlos Ruiz</p>
                  <p className="text-xs text-gray-400">Hace 12 minutos</p>
                </div>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
                <Calendar className="h-5 w-5 text-purple-600" />
                <div>
                  <p className="text-sm font-medium">Clase programada</p>
                  <p className="text-xs text-gray-600">Yoga Avanzado - Mañana 7:00 AM</p>
                  <p className="text-xs text-gray-400">Hace 25 minutos</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default DashboardPage