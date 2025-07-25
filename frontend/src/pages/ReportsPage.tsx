import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Button } from '../components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Badge } from '../components/ui/badge'
import {
  TrendingUp,
  TrendingDown,
  Users,
  DollarSign,
  Calendar,
  Activity,
  Download,
  Filter,
  RefreshCw
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts'

// Mock data for charts
const monthlyRevenue = [
  { month: 'Ene', revenue: 45000, members: 120 },
  { month: 'Feb', revenue: 52000, members: 135 },
  { month: 'Mar', revenue: 48000, members: 128 },
  { month: 'Abr', revenue: 61000, members: 152 },
  { month: 'May', revenue: 55000, members: 145 },
  { month: 'Jun', revenue: 67000, members: 168 }
]

const membershipTypes = [
  { name: 'Básica', value: 45, color: '#3B82F6' },
  { name: 'Premium', value: 30, color: '#10B981' },
  { name: 'VIP', value: 15, color: '#F59E0B' },
  { name: 'Estudiante', value: 10, color: '#EF4444' }
]

const classAttendance = [
  { day: 'Lun', morning: 25, afternoon: 35, evening: 45 },
  { day: 'Mar', morning: 30, afternoon: 40, evening: 50 },
  { day: 'Mié', morning: 28, afternoon: 38, evening: 48 },
  { day: 'Jue', morning: 32, afternoon: 42, evening: 52 },
  { day: 'Vie', morning: 35, afternoon: 45, evening: 55 },
  { day: 'Sáb', morning: 40, afternoon: 30, evening: 25 },
  { day: 'Dom', morning: 20, afternoon: 25, evening: 15 }
]

const equipmentUsage = [
  { equipment: 'Caminadoras', usage: 85 },
  { equipment: 'Pesas', usage: 92 },
  { equipment: 'Bicicletas', usage: 78 },
  { equipment: 'Máquinas', usage: 65 },
  { equipment: 'Funcional', usage: 88 }
]

export default function ReportsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState('month')
  const [selectedReport, setSelectedReport] = useState('overview')

  const kpiCards = [
    {
      title: 'Ingresos Totales',
      value: '$67,000',
      change: '+12.5%',
      trend: 'up',
      icon: DollarSign,
      color: 'text-green-600'
    },
    {
      title: 'Nuevos Miembros',
      value: '23',
      change: '+8.2%',
      trend: 'up',
      icon: Users,
      color: 'text-blue-600'
    },
    {
      title: 'Clases Impartidas',
      value: '156',
      change: '+5.1%',
      trend: 'up',
      icon: Calendar,
      color: 'text-purple-600'
    },
    {
      title: 'Tasa de Retención',
      value: '94.2%',
      change: '-2.1%',
      trend: 'down',
      icon: Activity,
      color: 'text-orange-600'
    }
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reportes y Análisis</h1>
          <p className="text-gray-600 mt-1">Análisis detallado del rendimiento del gimnasio</p>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
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

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((kpi, index) => {
          const Icon = kpi.icon
          return (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{kpi.title}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-2">{kpi.value}</p>
                    <div className="flex items-center mt-2">
                      {kpi.trend === 'up' ? (
                        <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                      )}
                      <span className={`text-sm font-medium ${
                        kpi.trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {kpi.change}
                      </span>
                      <span className="text-sm text-gray-500 ml-1">vs mes anterior</span>
                    </div>
                  </div>
                  <div className={`p-3 rounded-full bg-gray-50`}>
                    <Icon className={`h-6 w-6 ${kpi.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Main Reports */}
      <Tabs value={selectedReport} onValueChange={setSelectedReport}>
        <TabsList>
          <TabsTrigger value="overview">Resumen General</TabsTrigger>
          <TabsTrigger value="financial">Financiero</TabsTrigger>
          <TabsTrigger value="members">Miembros</TabsTrigger>
          <TabsTrigger value="operations">Operaciones</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Revenue Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Ingresos Mensuales</CardTitle>
                <CardDescription>Evolución de ingresos y nuevos miembros</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={monthlyRevenue}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="revenue" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.1} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Membership Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Distribución de Membresías</CardTitle>
                <CardDescription>Tipos de membresía más populares</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={membershipTypes}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}%`}
                    >
                      {membershipTypes.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Class Attendance */}
          <Card>
            <CardHeader>
              <CardTitle>Asistencia a Clases por Horario</CardTitle>
              <CardDescription>Distribución de asistencia durante la semana</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={classAttendance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="morning" stackId="a" fill="#F59E0B" name="Mañana" />
                  <Bar dataKey="afternoon" stackId="a" fill="#3B82F6" name="Tarde" />
                  <Bar dataKey="evening" stackId="a" fill="#10B981" name="Noche" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="financial" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Análisis Financiero Detallado</CardTitle>
                <CardDescription>Ingresos, gastos y rentabilidad</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={monthlyRevenue}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="revenue" stroke="#10B981" strokeWidth={3} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Métricas Financieras</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                  <span className="text-sm font-medium">Ingresos Totales</span>
                  <span className="font-bold text-green-600">$328,000</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                  <span className="text-sm font-medium">Gastos Totales</span>
                  <span className="font-bold text-red-600">$89,500</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                  <span className="text-sm font-medium">Ganancia Neta</span>
                  <span className="font-bold text-blue-600">$238,500</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                  <span className="text-sm font-medium">Margen de Ganancia</span>
                  <span className="font-bold text-purple-600">72.7%</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="members" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Crecimiento de Miembros</CardTitle>
                <CardDescription>Nuevos miembros vs cancelaciones</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={monthlyRevenue}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="members" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Estadísticas de Miembros</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Total Activos</span>
                    <Badge variant="secondary">168</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Nuevos este mes</span>
                    <Badge className="bg-green-100 text-green-800">23</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Cancelaciones</span>
                    <Badge className="bg-red-100 text-red-800">5</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Tasa de Retención</span>
                    <Badge className="bg-blue-100 text-blue-800">94.2%</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="operations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Uso de Equipamiento</CardTitle>
              <CardDescription>Porcentaje de uso por tipo de equipo</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {equipmentUsage.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{item.equipment}</span>
                    <div className="flex items-center space-x-3">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${item.usage}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-12">{item.usage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}