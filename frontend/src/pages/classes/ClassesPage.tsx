import { useState, useEffect } from 'react'
import { 
  Calendar, Clock, Users, MapPin, Eye, Edit, MoreHorizontal,
  Search, Filter, Download, Plus, TrendingUp, TrendingDown,
  XCircle,
  UserPlus, Bell, Star,
  Percent,
  FileText, Copy,
  ChevronLeft, ChevronRight, ChevronDown, ChevronUp
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Badge } from '../../components/ui/badge'
import { Avatar, AvatarFallback } from '../../components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'

import { Checkbox } from '../../components/ui/checkbox'

import { 
  AreaChart, Area, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { useClassStore } from '../../store/classStore'

import { cn } from '../../utils/cn'

// Mock data for charts
const attendanceData = [
  { month: 'Ene', attendance: 85, capacity: 100 },
  { month: 'Feb', attendance: 92, capacity: 100 },
  { month: 'Mar', attendance: 78, capacity: 100 },
  { month: 'Abr', attendance: 88, capacity: 100 },
  { month: 'May', attendance: 95, capacity: 100 },
  { month: 'Jun', attendance: 82, capacity: 100 }
]

const categoryData = [
  { name: 'Yoga', value: 35, color: '#8B5CF6' },
  { name: 'Cardio', value: 25, color: '#06B6D4' },
  { name: 'Fuerza', value: 20, color: '#10B981' },
  { name: 'Pilates', value: 15, color: '#F59E0B' },
  { name: 'Otros', value: 5, color: '#EF4444' }
]

const timeSlotData = [
  { slot: '6:00-8:00', classes: 12, attendance: 85 },
  { slot: '8:00-10:00', classes: 18, attendance: 92 },
  { slot: '10:00-12:00', classes: 15, attendance: 78 },
  { slot: '12:00-14:00', classes: 8, attendance: 65 },
  { slot: '14:00-16:00', classes: 10, attendance: 70 },
  { slot: '16:00-18:00', classes: 20, attendance: 95 },
  { slot: '18:00-20:00', classes: 25, attendance: 98 },
  { slot: '20:00-22:00', classes: 15, attendance: 88 }
]

const popularClasses = [
  { id: 1, name: 'Yoga Matutino', instructor: 'Ana García', attendance: 98, rating: 4.9 },
  { id: 2, name: 'HIIT Intensivo', instructor: 'Carlos López', attendance: 95, rating: 4.8 },
  { id: 3, name: 'Pilates Avanzado', instructor: 'María Rodríguez', attendance: 92, rating: 4.7 },
  { id: 4, name: 'Spinning', instructor: 'Juan Martínez', attendance: 90, rating: 4.6 },
  { id: 5, name: 'Zumba', instructor: 'Laura Sánchez', attendance: 88, rating: 4.5 }
]

// Using GymClass interface from types

export default function ClassesPage() {
  const { classes, loading, error, getClasses } = useClassStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('Todas')
  const [selectedDifficulty, setSelectedDifficulty] = useState('Todas')
  const [selectedStatus, setSelectedStatus] = useState('Todos')
  const [selectedTimeSlot, setSelectedTimeSlot] = useState('Todos')
  const [selectedDate, setSelectedDate] = useState('')
  const [viewMode, setViewMode] = useState<'list' | 'calendar' | 'grid'>('list')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(10)
  const [selectedClasses, setSelectedClasses] = useState<number[]>([])
  const [showFilters, setShowFilters] = useState(false)

  useEffect(() => {
    getClasses()
  }, [getClasses])

  // Filter and search logic
  const filteredClasses = classes.filter(classSession => {
    const instructorName = `${classSession.instructor?.first_name || ''} ${classSession.instructor?.last_name || ''}`.toLowerCase()
    const matchesSearch = classSession.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         instructorName.includes(searchTerm.toLowerCase()) ||
                         classSession.category.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'Todas' || classSession.category === selectedCategory
    const matchesDifficulty = selectedDifficulty === 'Todas' || classSession.difficulty_level === selectedDifficulty
    const matchesStatus = selectedStatus === 'Todos' || classSession.is_active
    
    return matchesSearch && matchesCategory && matchesDifficulty && matchesStatus
  })

  // Pagination
  const totalPages = Math.ceil(filteredClasses.length / itemsPerPage)
  const indexOfLastClass = currentPage * itemsPerPage
  const indexOfFirstClass = indexOfLastClass - itemsPerPage
  const currentClasses = filteredClasses.slice(indexOfFirstClass, indexOfLastClass)

  // Selection handlers
  const handleSelectClass = (classId: number) => {
    setSelectedClasses(prev => 
      prev.includes(classId) 
        ? prev.filter(id => id !== classId)
        : [...prev, classId]
    )
  }

  const handleSelectAll = () => {
    setSelectedClasses(
      selectedClasses.length === currentClasses.length 
        ? [] 
        : currentClasses.map(c => c.id)
    )
  }

  // Utility functions

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800'
      case 'advanced': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount)
  }



  const getOccupancyPercentage = (enrolled: number, capacity: number) => {
    return Math.round((enrolled / capacity) * 100)
  }

  // Calculate statistics
  const totalClasses = classes.length
  const classesToday = 0 // GymClass doesn't have date property, would need ClassSchedule
  const totalEnrollments = 0 // GymClass doesn't have enrolled property, would need ClassSchedule
  const averageAttendance = 0 // Would need enrollment data from ClassSchedule

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <XCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error al cargar las clases</h3>
        <p className="text-gray-500 mb-4">{error}</p>
        <Button onClick={() => getClasses()}>Reintentar</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestión de Clases</h1>
          <p className="text-gray-600">Administra horarios, instructores y reservas</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Exportar
          </Button>
          <Button variant="outline" size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Horarios
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Nueva Clase
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Resumen</TabsTrigger>
          <TabsTrigger value="classes">Clases</TabsTrigger>
          <TabsTrigger value="analytics">Análisis</TabsTrigger>
          <TabsTrigger value="schedule">Horarios</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Clases</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalClasses}</div>
                <p className="text-xs text-muted-foreground">
                  <TrendingUp className="h-3 w-3 inline mr-1" />
                  +12% desde el mes pasado
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Clases Hoy</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{classesToday}</div>
                <p className="text-xs text-muted-foreground">
                  <TrendingUp className="h-3 w-3 inline mr-1" />
                  +5% vs ayer
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Inscripciones</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{totalEnrollments}</div>
                <p className="text-xs text-muted-foreground">
                  <TrendingUp className="h-3 w-3 inline mr-1" />
                  +8% desde el mes pasado
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Asistencia Promedio</CardTitle>
                <Percent className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{averageAttendance}%</div>
                <p className="text-xs text-muted-foreground">
                  <TrendingDown className="h-3 w-3 inline mr-1" />
                  -2% desde el mes pasado
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Tendencia de Asistencia</CardTitle>
                <CardDescription>Asistencia vs capacidad por mes</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={attendanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="attendance" stackId="1" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.6} />
                    <Area type="monotone" dataKey="capacity" stackId="2" stroke="#E5E7EB" fill="#E5E7EB" fillOpacity={0.3} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Distribución por Categoría</CardTitle>
                <CardDescription>Clases por tipo de actividad</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }: { name: string; percent: number }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Popular Classes */}
          <Card>
            <CardHeader>
              <CardTitle>Clases Más Populares</CardTitle>
              <CardDescription>Basado en asistencia y calificaciones</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {popularClasses.map((classItem, index) => (
                  <div key={classItem.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-purple-100 text-purple-600 rounded-full font-semibold">
                        {index + 1}
                      </div>
                      <div>
                        <h4 className="font-medium">{classItem.name}</h4>
                        <p className="text-sm text-gray-500">{classItem.instructor}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm font-medium">{classItem.attendance}% asistencia</p>
                        <div className="flex items-center">
                          <Star className="h-4 w-4 text-yellow-400 fill-current" />
                          <span className="text-sm text-gray-600 ml-1">{classItem.rating}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="classes" className="space-y-6">
          {/* Search and Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      placeholder="Buscar clases, instructores o categorías..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowFilters(!showFilters)}
                  >
                    <Filter className="h-4 w-4 mr-2" />
                    Filtros
                    {showFilters ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
                  </Button>
                  <Select value={viewMode} onValueChange={(value: 'list' | 'calendar' | 'grid') => setViewMode(value)}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="list">Lista</SelectItem>
                      <SelectItem value="grid">Cuadrícula</SelectItem>
                      <SelectItem value="calendar">Calendario</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {showFilters && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mt-4 pt-4 border-t">
                  <div>
                    <Label htmlFor="date">Fecha</Label>
                    <Input
                      id="date"
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="category">Categoría</Label>
                    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Todas">Todas</SelectItem>
                        <SelectItem value="Yoga">Yoga</SelectItem>
                        <SelectItem value="Cardio">Cardio</SelectItem>
                        <SelectItem value="Fuerza">Fuerza</SelectItem>
                        <SelectItem value="Pilates">Pilates</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="difficulty">Dificultad</Label>
                    <Select value={selectedDifficulty} onValueChange={setSelectedDifficulty}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Todas">Todas</SelectItem>
                        <SelectItem value="beginner">Principiante</SelectItem>
                        <SelectItem value="intermediate">Intermedio</SelectItem>
                        <SelectItem value="advanced">Avanzado</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="status">Estado</Label>
                    <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Todos">Todos</SelectItem>
                        <SelectItem value="scheduled">Programada</SelectItem>
                        <SelectItem value="in_progress">En Progreso</SelectItem>
                        <SelectItem value="completed">Completada</SelectItem>
                        <SelectItem value="cancelled">Cancelada</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="timeSlot">Horario</Label>
                    <Select value={selectedTimeSlot} onValueChange={setSelectedTimeSlot}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Todos">Todos</SelectItem>
                        <SelectItem value="Mañana">Mañana</SelectItem>
                        <SelectItem value="Tarde">Tarde</SelectItem>
                        <SelectItem value="Noche">Noche</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm">
              <UserPlus className="h-4 w-4 mr-2" />
              Inscripción Rápida
            </Button>
            <Button variant="outline" size="sm">
              <Bell className="h-4 w-4 mr-2" />
              Enviar Recordatorios
            </Button>
            <Button variant="outline" size="sm">
              <Copy className="h-4 w-4 mr-2" />
              Duplicar Horario
            </Button>
            <Button variant="outline" size="sm">
              <FileText className="h-4 w-4 mr-2" />
              Generar Reporte
            </Button>
          </div>

          {/* Classes Table */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Clases ({filteredClasses.length})</CardTitle>
                {selectedClasses.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      {selectedClasses.length} seleccionadas
                    </span>
                    <Button variant="outline" size="sm">
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
                        checked={selectedClasses.length === currentClasses.length && currentClasses.length > 0}
                        onCheckedChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Clase</TableHead>
                    <TableHead>Instructor</TableHead>
                    <TableHead>Fecha & Hora</TableHead>
                    <TableHead>Ubicación</TableHead>
                    <TableHead>Ocupación</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Precio</TableHead>
                    <TableHead>Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentClasses.map((classSession) => {
                    const occupancyPercentage = getOccupancyPercentage(classSession.current_enrollment, classSession.max_capacity)
                    const instructorName = `${classSession.instructor?.first_name || ''} ${classSession.instructor?.last_name || ''}`.trim()
                    const instructorInitials = instructorName.split(' ').map(n => n[0]).join('').toUpperCase()
                    return (
                      <TableRow key={classSession.id}>
                        <TableCell>
                          <Checkbox
                            checked={selectedClasses.includes(classSession.id)}
                            onCheckedChange={() => handleSelectClass(classSession.id)}
                          />
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{classSession.name}</p>
                            <p className="text-sm text-gray-500">{classSession.category}</p>
                            <Badge variant="secondary" className={getDifficultyColor(classSession.difficulty_level)}>
                              {classSession.difficulty_level === 'beginner' ? 'Principiante' : 
                               classSession.difficulty_level === 'intermediate' ? 'Intermedio' : 'Avanzado'}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Avatar className="h-8 w-8">
                              <AvatarFallback>{instructorInitials}</AvatarFallback>
                            </Avatar>
                            <span className="text-sm">{instructorName}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="text-sm">No programada</p>
                            <p className="text-sm text-gray-500">
                              {classSession.duration_minutes} min
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <MapPin className="h-4 w-4 text-gray-400" />
                            <span className="text-sm">{classSession.room}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="flex items-center space-x-2">
                              <Users className="h-4 w-4 text-gray-400" />
                              <span className="text-sm font-medium">
                                {classSession.current_enrollment}/{classSession.max_capacity}
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                              <div
                                className={cn(
                                  "h-2 rounded-full",
                                  occupancyPercentage >= 90 ? "bg-red-500" :
                                  occupancyPercentage >= 70 ? "bg-yellow-500" : "bg-green-500"
                                )}
                                style={{ width: `${occupancyPercentage}%` }}
                              ></div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Badge className={classSession.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                              {classSession.is_active ? 'Activa' : 'Inactiva'}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          {formatCurrency(classSession.price)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
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
                    )
                  })}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-gray-700">
                    Mostrando {indexOfFirstClass + 1} a {Math.min(indexOfLastClass, filteredClasses.length)} de {filteredClasses.length} clases
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(Math.max(currentPage - 1, 1))}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Anterior
                    </Button>
                    <span className="text-sm text-gray-700">
                      Página {currentPage} de {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(Math.min(currentPage + 1, totalPages))}
                      disabled={currentPage === totalPages}
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
          {/* Time Slot Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Análisis por Horarios</CardTitle>
              <CardDescription>Distribución de clases y asistencia por franja horaria</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={timeSlotData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="slot" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="classes" fill="#8B5CF6" name="Número de Clases" />
                  <Bar yAxisId="right" dataKey="attendance" fill="#06B6D4" name="% Asistencia" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Additional Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Métricas de Rendimiento</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Tasa de Cancelación</span>
                  <span className="text-sm text-red-600">3.2%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Tiempo Promedio de Reserva</span>
                  <span className="text-sm text-green-600">2.5 días</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Satisfacción Promedio</span>
                  <span className="text-sm text-blue-600">4.7/5</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Clases con Lista de Espera</span>
                  <span className="text-sm text-orange-600">15%</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tendencias Semanales</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'].map((day, index) => {
                    const percentage = [85, 92, 78, 88, 95, 82, 65][index]
                    return (
                      <div key={day} className="flex items-center justify-between">
                        <span className="text-sm font-medium">{day}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-purple-600 h-2 rounded-full"
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600">{percentage}%</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="schedule" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Gestión de Horarios</CardTitle>
              <CardDescription>Configura y administra los horarios de clases</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Calendar className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Vista de Calendario</h3>
                <p className="text-gray-500 mb-4">Aquí se mostraría un calendario interactivo para gestionar horarios</p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Crear Horario
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}