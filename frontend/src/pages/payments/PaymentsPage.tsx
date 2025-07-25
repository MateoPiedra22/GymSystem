import { useState, useEffect } from 'react'
import { usePaymentStore } from '../../store/paymentStore'
import { cn } from '../../utils/cn'
import {
  Search,
  Filter,
  Download,
  Plus,
  Eye,
  Edit,
  MoreHorizontal,
  DollarSign,
  Calendar,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  FileText,
  CreditCard,
  CheckCircle,
  XCircle,
  AlertCircle,
  Settings,
  ChevronLeft,
  ChevronRight,
  Calculator,
  Printer,
  Share2,
  RotateCcw,
  Activity,
  Send,
  MoreVertical,
  BarChart3,
  Upload,
  Target
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback } from '../../components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'

import { Checkbox } from '../../components/ui/checkbox'

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
  Legend,
  LineChart,
  Line
} from 'recharts'

// Mock data for charts and analytics
const revenueData = [
  { month: 'Ene', revenue: 45000, target: 50000, payments: 120 },
  { month: 'Feb', revenue: 52000, target: 50000, payments: 135 },
  { month: 'Mar', revenue: 48000, target: 50000, payments: 128 },
  { month: 'Abr', revenue: 61000, target: 55000, payments: 142 },
  { month: 'May', revenue: 55000, target: 55000, payments: 138 }
]

const paymentMethodData = [
  { name: 'Tarjeta de Crédito', value: 45, color: '#3b82f6' },
  { name: 'Efectivo', value: 30, color: '#10b981' },
  { name: 'Transferencia', value: 20, color: '#f59e0b' },
  { name: 'Débito Automático', value: 5, color: '#ef4444' }
]

const membershipRevenueData = [
  { type: 'Premium Mensual', revenue: 180000, count: 45 },
  { type: 'Básico Estudiante', revenue: 120000, count: 80 },
  { type: 'Funcional Semanal', revenue: 95000, count: 35 },
  { type: 'Diaria', revenue: 45000, count: 150 }
]

const paymentTrendsData = [
  { day: 'Lun', completed: 25, pending: 8, overdue: 3 },
  { day: 'Mar', completed: 32, pending: 12, overdue: 2 },
  { day: 'Mié', completed: 28, pending: 15, overdue: 5 },
  { day: 'Jue', completed: 35, pending: 10, overdue: 4 },
  { day: 'Vie', completed: 42, pending: 18, overdue: 6 },
  { day: 'Sáb', completed: 38, pending: 22, overdue: 8 },
  { day: 'Dom', completed: 20, pending: 14, overdue: 3 }
]

interface Payment {
  id: number
  user_id: number
  user_name?: string
  amount: number
  status: string
  payment_method: string
  payment_type: string
  membership_type?: string
  due_date?: string
  payment_date?: string
  invoice_number?: string
  reference_id?: string
}

const membershipTypes = ['Todos', 'Premium Mensual', 'Básico Estudiante', 'Funcional Semanal', 'Diaria']
const statusOptions = ['Todos', 'paid', 'pending', 'overdue', 'cancelled']
const paymentMethods = ['Todos', 'Efectivo', 'Tarjeta de Crédito', 'Transferencia', 'Débito Automático']

export function PaymentsPage() {
  const {
    payments,
    loading,
    error,
    paymentPagination,
    paymentFilters,
    getPayments,
    paymentStats
  } = usePaymentStore()
  
  const [filteredPayments, setFilteredPayments] = useState<Payment[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedMembershipType, setSelectedMembershipType] = useState('Todos')
  const [selectedStatus, setSelectedStatus] = useState('Todos')
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('Todos')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedPayments, setSelectedPayments] = useState<number[]>([])
  const [paymentsPerPage] = useState(10)
  const [dateRange, setDateRange] = useState('month')
  const [activeTab, setActiveTab] = useState('overview')


  // Load payments on component mount
  useEffect(() => {
    getPayments({ page: 1, limit: paymentsPerPage })
  }, [])

  // Filter payments based on search and filters
  useEffect(() => {
    if (!payments) {
      setFilteredPayments([])
      return
    }

    let filtered = payments

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(payment =>
        ((payment as Payment).user_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        ((payment as Payment).invoice_number || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        ((payment as Payment).membership_type || payment.payment_type || '').toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Membership type filter
    if (selectedMembershipType !== 'Todos') {
      filtered = filtered.filter(payment => ((payment as Payment).membership_type || payment.payment_type) === selectedMembershipType)
    }

    // Status filter
    if (selectedStatus !== 'Todos') {
      filtered = filtered.filter(payment => payment.status === selectedStatus)
    }

    // Payment method filter
    if (selectedPaymentMethod !== 'Todos') {
      filtered = filtered.filter(payment => payment.payment_method === selectedPaymentMethod)
    }

    setFilteredPayments(filtered)
  }, [payments, searchTerm, selectedMembershipType, selectedStatus, selectedPaymentMethod])

  // Calculate pagination
  const indexOfLastPayment = paymentPagination.page * paymentsPerPage
  const indexOfFirstPayment = indexOfLastPayment - paymentsPerPage
  const currentPayments = filteredPayments.slice(indexOfFirstPayment, indexOfLastPayment)

  const handleSelectPayment = (paymentId: number) => {
    setSelectedPayments(prev =>
      prev.includes(paymentId)
        ? prev.filter(id => id !== paymentId)
        : [...prev, paymentId]
    )
  }

  const handleSelectAll = () => {
    if (selectedPayments.length === currentPayments.length) {
      setSelectedPayments([])
    } else {
      setSelectedPayments(currentPayments.map(payment => payment.id))
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'paid':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'overdue':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'paid':
        return 'Pagado'
      case 'pending':
        return 'Pendiente'
      case 'overdue':
        return 'Vencido'
      case 'cancelled':
        return 'Cancelado'
      default:
        return 'Desconocido'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'bg-green-100 text-green-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'overdue':
        return 'bg-red-100 text-red-800'
      case 'cancelled':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-AR')
  }

  const calculateStats = () => {
    const totalRevenue = paymentStats?.total_revenue || 0
    const monthlyRevenue = (paymentStats as any)?.monthly_revenue || 0
    const pendingPayments = (paymentStats as any)?.pending_payments || 0
    const overduePayments = (paymentStats as any)?.overdue_payments || 0
    const revenueGrowth = (paymentStats as any)?.revenue_growth || 0
    const paymentSuccessRate = filteredPayments.length > 0 ? 
      (filteredPayments.filter(p => p.status === 'paid').length / filteredPayments.length) * 100 : 0
    
    return {
      totalRevenue,
      monthlyRevenue,
      pendingPayments,
      overduePayments,
      revenueGrowth,
      paymentSuccessRate
    }
  }

  const stats = calculateStats()

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Gestión de Pagos
          </h1>
          <p className="text-gray-600 mt-2">Administra cuotas, facturación y análisis financiero integral</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm" className="hover:bg-blue-50">
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
          <Button variant="outline" size="sm" className="hover:bg-green-50">
            <Upload className="h-4 w-4 mr-2" />
            Importar
          </Button>
          <Button variant="outline" size="sm" className="hover:bg-yellow-50">
            <Send className="h-4 w-4 mr-2" />
            Recordatorios
          </Button>
          <Button className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white shadow-lg">
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Pago
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
          <span className="ml-2 text-gray-600">Cargando pagos...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
              <span className="text-red-700">Error al cargar los pagos: {error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">
            <BarChart3 className="h-4 w-4 mr-2" />
            <span>Resumen</span>
          </TabsTrigger>
          <TabsTrigger value="payments">
            <CreditCard className="h-4 w-4 mr-2" />
            <span>Pagos</span>
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="h-4 w-4 mr-2" />
            <span>Análisis</span>
          </TabsTrigger>
          <TabsTrigger value="reports">
            <FileText className="h-4 w-4 mr-2" />
            <span>Reportes</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Quick Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="bg-gradient-to-br from-green-500 to-emerald-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-100 text-sm font-medium">Ingresos Totales</p>
                    <p className="text-2xl font-bold">{formatCurrency(stats.totalRevenue)}</p>
                  </div>
                  <div className="bg-white/20 p-3 rounded-lg">
                    <DollarSign className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 flex items-center">
                  <TrendingUp className="h-4 w-4 mr-1" />
                  <span className="text-sm font-medium">+{stats.revenueGrowth}%</span>
                  <span className="text-green-100 text-sm ml-1">vs mes anterior</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-blue-500 to-cyan-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm font-medium">Ingresos Mensuales</p>
                    <p className="text-2xl font-bold">{formatCurrency(stats.monthlyRevenue)}</p>
                  </div>
                  <div className="bg-white/20 p-3 rounded-lg">
                    <Calendar className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 flex items-center">
                  <Target className="h-4 w-4 mr-1" />
                  <span className="text-sm font-medium">Meta: {formatCurrency(55000)}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-yellow-500 to-orange-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-yellow-100 text-sm font-medium">Pagos Pendientes</p>
                    <p className="text-2xl font-bold">{stats.pendingPayments}</p>
                  </div>
                  <div className="bg-white/20 p-3 rounded-lg">
                    <Clock className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 flex items-center">
                  <AlertCircle className="h-4 w-4 mr-1" />
                  <span className="text-sm font-medium">Requieren atención</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-red-500 to-pink-600 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-red-100 text-sm font-medium">Pagos Vencidos</p>
                    <p className="text-2xl font-bold">{stats.overduePayments}</p>
                  </div>
                  <div className="bg-white/20 p-3 rounded-lg">
                    <AlertTriangle className="h-6 w-6" />
                  </div>
                </div>
                <div className="mt-4 flex items-center">
                  <TrendingDown className="h-4 w-4 mr-1" />
                  <span className="text-sm font-medium">Acción urgente</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Revenue Trend Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  <span>Tendencia de Ingresos</span>
                </CardTitle>
                <CardDescription>Evolución mensual de ingresos y objetivos</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                    <Area type="monotone" dataKey="revenue" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                    <Area type="monotone" dataKey="target" stroke="#6b7280" fill="#6b7280" fillOpacity={0.1} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Payment Methods Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-blue-600" />
                  <span>Métodos de Pago</span>
                </CardTitle>
                <CardDescription>Distribución por tipo de pago</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={paymentMethodData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }: { name: string; percent: number }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {paymentMethodData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-purple-600" />
                <span>Acciones Rápidas</span>
              </CardTitle>
              <CardDescription>Herramientas de gestión financiera</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Button variant="outline" className="justify-start h-auto p-4 hover:bg-blue-50">
                  <div className="flex flex-col items-start space-y-2">
                    <Send className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="font-medium">Enviar Recordatorios</p>
                      <p className="text-sm text-gray-500">Notificar pagos pendientes</p>
                    </div>
                  </div>
                </Button>
                <Button variant="outline" className="justify-start h-auto p-4 hover:bg-green-50">
                  <div className="flex flex-col items-start space-y-2">
                    <FileText className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium">Generar Facturas</p>
                      <p className="text-sm text-gray-500">Crear facturas masivas</p>
                    </div>
                  </div>
                </Button>
                <Button variant="outline" className="justify-start h-auto p-4 hover:bg-purple-50">
                  <div className="flex flex-col items-start space-y-2">
                    <CreditCard className="h-5 w-5 text-purple-600" />
                    <div>
                      <p className="font-medium">Procesar Pagos</p>
                      <p className="text-sm text-gray-500">Gestión de cobros</p>
                    </div>
                  </div>
                </Button>
                <Button variant="outline" className="justify-start h-auto p-4 hover:bg-orange-50">
                  <div className="flex flex-col items-start space-y-2">
                    <Download className="h-5 w-5 text-orange-600" />
                    <div>
                      <p className="font-medium">Reporte Financiero</p>
                      <p className="text-sm text-gray-500">Análisis detallado</p>
                    </div>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments" className="space-y-6">
          {/* Search and Filters */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-4 mb-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    type="text"
                    placeholder="Buscar por usuario, factura o tipo de membresía..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <Select value={dateRange} onValueChange={setDateRange}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="week">Esta Semana</SelectItem>
                    <SelectItem value="month">Este Mes</SelectItem>
                    <SelectItem value="quarter">Este Trimestre</SelectItem>
                    <SelectItem value="year">Este Año</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className={cn(showFilters && "bg-gray-50")}
                >
                  <Filter className="h-4 w-4 mr-2" />
                  Filtros
                </Button>
              </div>

              {/* Filters */}
              {showFilters && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                  <div>
                    <Label className="text-sm font-medium text-gray-700 mb-2">
                      Tipo de Membresía
                    </Label>
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
                  <div>
                    <Label className="text-sm font-medium text-gray-700 mb-2">
                      Estado
                    </Label>
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
                  <div>
                    <Label className="text-sm font-medium text-gray-700 mb-2">
                      Método de Pago
                    </Label>
                    <Select value={selectedPaymentMethod} onValueChange={setSelectedPaymentMethod}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {paymentMethods.map(method => (
                          <SelectItem key={method} value={method}>{method}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payments Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <CreditCard className="h-5 w-5 text-blue-600" />
                    <span>Pagos ({filteredPayments.length})</span>
                  </CardTitle>
                  <CardDescription>Gestión completa de pagos y facturación</CardDescription>
                </div>
                {selectedPayments.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary">
                      {selectedPayments.length} seleccionados
                    </Badge>
                    <Button variant="outline" size="sm">
                      <MoreVertical className="h-4 w-4 mr-2" />
                      Acciones en lote
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedPayments.length === currentPayments.length && currentPayments.length > 0}
                        onCheckedChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Factura</TableHead>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Membresía</TableHead>
                    <TableHead>Monto</TableHead>
                    <TableHead>Vencimiento</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Método</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentPayments.map((payment) => (
                    <TableRow key={payment.id} className="hover:bg-gray-50">
                      <TableCell>
                        <Checkbox
                          checked={selectedPayments.includes(payment.id)}
                          onCheckedChange={() => handleSelectPayment(payment.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium text-gray-900">
                            {payment.invoice_number || payment.reference_id || `INV-${payment.id}`}
                          </p>
                          <p className="text-sm text-gray-500">ID: {payment.id}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-blue-100 text-blue-600">
                              {(payment.user_name || `U${payment.user_id}`).charAt(0)}
                            </AvatarFallback>
                          </Avatar>
                          <p className="text-sm text-gray-900">
                            {payment.user_name || `Usuario ${payment.user_id}`}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {payment.membership_type || payment.payment_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <p className="font-medium text-gray-900">{formatCurrency(payment.amount)}</p>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="text-sm text-gray-900">
                            {payment.due_date ? formatDate(payment.due_date) : 'N/A'}
                          </p>
                          {payment.payment_date && (
                            <p className="text-sm text-gray-500">
                              Pagado: {formatDate(payment.payment_date)}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(payment.status)}
                          <Badge className={cn(getStatusColor(payment.status))}>
                            {getStatusText(payment.status)}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{payment.payment_method}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <Button variant="ghost" size="sm">
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
              {paymentPagination.totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
                  <div className="text-sm text-gray-700">
                    Mostrando {indexOfFirstPayment + 1} a {Math.min(indexOfLastPayment, filteredPayments.length)} de {filteredPayments.length} pagos
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newPage = Math.max(paymentPagination.page - 1, 1)
                        getPayments({ ...paymentFilters, page: newPage, limit: paymentsPerPage })
                      }}
                      disabled={paymentPagination.page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Anterior
                    </Button>
                    <span className="text-sm text-gray-700">
                      Página {paymentPagination.page} de {paymentPagination.totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newPage = Math.min(paymentPagination.page + 1, paymentPagination.totalPages)
                        getPayments({ ...paymentFilters, page: newPage, limit: paymentsPerPage })
                      }}
                      disabled={paymentPagination.page === paymentPagination.totalPages}
                    >
                      Siguiente
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Revenue by Membership Type */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-green-600" />
                  <span>Ingresos por Membresía</span>
                </CardTitle>
                <CardDescription>Análisis de rentabilidad por tipo</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={membershipRevenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                    <Bar dataKey="revenue" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Payment Trends */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-blue-600" />
                  <span>Tendencias de Pago</span>
                </CardTitle>
                <CardDescription>Patrones semanales de pagos</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={paymentTrendsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="completed" stroke="#10b981" name="Completados" />
                    <Line type="monotone" dataKey="pending" stroke="#f59e0b" name="Pendientes" />
                    <Line type="monotone" dataKey="overdue" stroke="#ef4444" name="Vencidos" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Additional Analytics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Tasa de Éxito</CardTitle>
                <CardDescription>Porcentaje de pagos completados</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">
                  {stats.paymentSuccessRate.toFixed(1)}%
                </div>
                <p className="text-sm text-gray-500 mt-2">Excelente rendimiento</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Tiempo Promedio</CardTitle>
                <CardDescription>Días para completar pago</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">2.3</div>
                <p className="text-sm text-gray-500 mt-2">Días promedio</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Valor Promedio</CardTitle>
                <CardDescription>Monto promedio por pago</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-purple-600">
                  {formatCurrency(stats.totalRevenue / Math.max(filteredPayments.length, 1))}
                </div>
                <p className="text-sm text-gray-500 mt-2">Por transacción</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="reports" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <span>Reporte Mensual</span>
                </CardTitle>
                <CardDescription>Resumen financiero del mes</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Generar PDF
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Calculator className="h-5 w-5 text-green-600" />
                  <span>Estado de Cuenta</span>
                </CardTitle>
                <CardDescription>Detalle de pagos por usuario</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full" variant="outline">
                  <Printer className="h-4 w-4 mr-2" />
                  Imprimir
                </Button>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <RotateCcw className="h-5 w-5 text-purple-600" />
                  <span>Historial Completo</span>
                </CardTitle>
                <CardDescription>Todos los movimientos</CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full" variant="outline">
                  <Share2 className="h-4 w-4 mr-2" />
                  Exportar Excel
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Report Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Configurar Reporte Personalizado</CardTitle>
              <CardDescription>Crea reportes específicos según tus necesidades</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="report-type">Tipo de Reporte</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="financial">Financiero</SelectItem>
                      <SelectItem value="membership">Por Membresía</SelectItem>
                      <SelectItem value="overdue">Pagos Vencidos</SelectItem>
                      <SelectItem value="methods">Métodos de Pago</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="date-range">Rango de Fechas</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar período" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="last-week">Última Semana</SelectItem>
                      <SelectItem value="last-month">Último Mes</SelectItem>
                      <SelectItem value="last-quarter">Último Trimestre</SelectItem>
                      <SelectItem value="custom">Personalizado</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex space-x-2">
                <Button className="flex-1">
                  <FileText className="h-4 w-4 mr-2" />
                  Generar Reporte
                </Button>
                <Button variant="outline">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default PaymentsPage