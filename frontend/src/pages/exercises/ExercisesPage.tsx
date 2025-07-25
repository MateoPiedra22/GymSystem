import { useState } from 'react'
import { 
  Search, Filter, Plus, Download, MoreHorizontal, 
  Eye, Edit, Trash2, Star, Play, Image,
  Dumbbell, TrendingUp, Users,
  CheckCircle, Grid3X3, List, RefreshCw,
  Camera, Video, Tag, Award, ArrowUp, ArrowDown, Upload, Settings, Heart, Activity, Target, Zap, Flame, Copy
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { Badge } from '../../components/ui/badge'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'

import { Checkbox } from '../../components/ui/checkbox'
import { 
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { cn } from '../../utils/cn'

// Mock data for charts
const exerciseUsageData = [
  { month: 'Ene', exercises: 45, popular: 12 },
  { month: 'Feb', exercises: 52, popular: 15 },
  { month: 'Mar', exercises: 48, popular: 18 },
  { month: 'Abr', exercises: 61, popular: 22 },
  { month: 'May', exercises: 55, popular: 25 },
  { month: 'Jun', exercises: 67, popular: 28 }
]

const categoryDistribution = [
  { name: 'Fuerza', value: 35, color: '#f97316' },
  { name: 'Cardio', value: 25, color: '#3b82f6' },
  { name: 'Flexibilidad', value: 20, color: '#10b981' },
  { name: 'Funcional', value: 15, color: '#8b5cf6' },
  { name: 'Otros', value: 5, color: '#6b7280' }
]

const difficultyStats = [
  { difficulty: 'Principiante', count: 45, percentage: 35 },
  { difficulty: 'Intermedio', count: 52, percentage: 40 },
  { difficulty: 'Avanzado', count: 32, percentage: 25 }
]

const popularExercises = [
  { id: 1, name: 'Press de Banca', category: 'Fuerza', uses: 156, rating: 4.8 },
  { id: 2, name: 'Sentadillas', category: 'Fuerza', uses: 142, rating: 4.9 },
  { id: 3, name: 'Peso Muerto', category: 'Fuerza', uses: 128, rating: 4.7 },
  { id: 4, name: 'Dominadas', category: 'Fuerza', uses: 98, rating: 4.6 },
  { id: 5, name: 'Burpees', category: 'Cardio', uses: 87, rating: 4.2 }
]

// Mock exercises data
const mockExercises = [
  {
    id: 1,
    name: 'Press de Banca',
    description: 'Ejercicio fundamental para el desarrollo del pecho, hombros y tríceps',
    category: 'Fuerza',
    difficulty_level: 'intermediate',
    muscle_groups: ['Pecho', 'Hombros', 'Tríceps'],
    equipment_needed: ['Banca', 'Barra', 'Discos'],
    image_url: 'https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20gym%20bench%20press%20exercise%20demonstration&image_size=square',
    video_url: 'https://example.com/video1',
    created_by: 'Entrenador Pro',
    rating: 4.8,
    uses: 156,
    approved: true,
    created_at: '2024-01-15'
  },
  {
    id: 2,
    name: 'Sentadillas',
    description: 'Ejercicio compuesto para piernas y glúteos, fundamental en cualquier rutina',
    category: 'Fuerza',
    difficulty_level: 'beginner',
    muscle_groups: ['Cuádriceps', 'Glúteos', 'Isquiotibiales'],
    equipment_needed: ['Ninguno'],
    image_url: 'https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20gym%20squat%20exercise%20demonstration&image_size=square',
    video_url: null,
    created_by: 'Fitness Expert',
    rating: 4.9,
    uses: 142,
    approved: true,
    created_at: '2024-01-10'
  },
  {
    id: 3,
    name: 'Peso Muerto',
    description: 'Ejercicio de fuerza que trabaja múltiples grupos musculares simultáneamente',
    category: 'Fuerza',
    difficulty_level: 'advanced',
    muscle_groups: ['Espalda', 'Glúteos', 'Isquiotibiales', 'Core'],
    equipment_needed: ['Barra', 'Discos'],
    image_url: 'https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20gym%20deadlift%20exercise%20demonstration&image_size=square',
    video_url: 'https://example.com/video3',
    created_by: 'Strength Coach',
    rating: 4.7,
    uses: 128,
    approved: true,
    created_at: '2024-01-08'
  },
  {
    id: 4,
    name: 'Burpees',
    description: 'Ejercicio cardiovascular de alta intensidad que trabaja todo el cuerpo',
    category: 'Cardio',
    difficulty_level: 'intermediate',
    muscle_groups: ['Todo el cuerpo'],
    equipment_needed: ['Ninguno'],
    image_url: 'https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20gym%20burpee%20exercise%20demonstration&image_size=square',
    video_url: 'https://example.com/video4',
    created_by: 'HIIT Trainer',
    rating: 4.2,
    uses: 87,
    approved: true,
    created_at: '2024-01-05'
  },
  {
    id: 5,
    name: 'Plancha',
    description: 'Ejercicio isométrico para fortalecer el core y mejorar la estabilidad',
    category: 'Core',
    difficulty_level: 'beginner',
    muscle_groups: ['Core', 'Hombros'],
    equipment_needed: ['Ninguno'],
    image_url: 'https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20gym%20plank%20exercise%20demonstration&image_size=square',
    video_url: null,
    created_by: 'Core Specialist',
    rating: 4.5,
    uses: 95,
    approved: true,
    created_at: '2024-01-03'
  }
]

interface Exercise {
  id: number
  name: string
  description: string
  category: string
  difficulty_level: string
  muscle_groups: string[]
  equipment_needed: string[]
  image_url?: string
  video_url?: string | null
  created_by: string
  rating: number
  uses: number
  approved: boolean
  created_at: string
}

export default function ExercisesPage() {
  const [exercises] = useState<Exercise[]>(mockExercises)

  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('Todas')
  const [selectedDifficulty, setSelectedDifficulty] = useState('Todas')
  const [selectedMuscleGroup, setSelectedMuscleGroup] = useState('Todos')
  const [selectedEquipment, setSelectedEquipment] = useState('Todos')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [showFilters, setShowFilters] = useState(false)
  const [showApprovedOnly, setShowApprovedOnly] = useState(false)
  const [selectedExercises, setSelectedExercises] = useState<number[]>([])
  const [sortBy, setSortBy] = useState('name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(12)

  // Filter options
  const categories = ['Todas', 'Fuerza', 'Cardio', 'Flexibilidad', 'Core', 'Funcional', 'Rehabilitación']
  const difficulties = ['Todas', 'beginner', 'intermediate', 'advanced']
  const muscleGroups = ['Todos', 'Pecho', 'Espalda', 'Hombros', 'Brazos', 'Piernas', 'Glúteos', 'Core', 'Todo el cuerpo']
  const equipmentOptions = ['Todos', 'Ninguno', 'Mancuernas', 'Barra', 'Máquinas', 'Bandas', 'Kettlebells', 'TRX']

  // Utility functions
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800'
      case 'advanced': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getDifficultyText = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'Principiante'
      case 'intermediate': return 'Intermedio'
      case 'advanced': return 'Avanzado'
      default: return difficulty
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Fuerza': return <Dumbbell className="h-4 w-4 text-orange-500" />
      case 'Cardio': return <Heart className="h-4 w-4 text-red-500" />
      case 'Flexibilidad': return <Activity className="h-4 w-4 text-green-500" />
      case 'Core': return <Target className="h-4 w-4 text-purple-500" />
      case 'Funcional': return <Zap className="h-4 w-4 text-blue-500" />
      default: return <Dumbbell className="h-4 w-4 text-gray-500" />
    }
  }

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={cn(
          'h-3 w-3',
          i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'
        )}
      />
    ))
  }

  // Filter and sort exercises
  const filteredExercises = exercises.filter(exercise => {
    const matchesSearch = exercise.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         exercise.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         exercise.muscle_groups.some(muscle => muscle.toLowerCase().includes(searchTerm.toLowerCase()))
    const matchesCategory = selectedCategory === 'Todas' || exercise.category === selectedCategory
    const matchesDifficulty = selectedDifficulty === 'Todas' || exercise.difficulty_level === selectedDifficulty
    const matchesMuscleGroup = selectedMuscleGroup === 'Todos' || exercise.muscle_groups.includes(selectedMuscleGroup)
    const matchesEquipment = selectedEquipment === 'Todos' || exercise.equipment_needed.includes(selectedEquipment)
    const matchesApproved = !showApprovedOnly || exercise.approved

    return matchesSearch && matchesCategory && matchesDifficulty && matchesMuscleGroup && matchesEquipment && matchesApproved
  })

  // Sort exercises
  const sortedExercises = [...filteredExercises].sort((a, b) => {
    let aValue: any = a[sortBy as keyof Exercise]
    let bValue: any = b[sortBy as keyof Exercise]

    if (sortBy === 'rating' || sortBy === 'uses') {
      aValue = Number(aValue)
      bValue = Number(bValue)
    } else {
      aValue = String(aValue).toLowerCase()
      bValue = String(bValue).toLowerCase()
    }

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })

  // Pagination
  const totalPages = Math.ceil(sortedExercises.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const currentExercises = sortedExercises.slice(startIndex, startIndex + itemsPerPage)

  const handleSelectExercise = (exerciseId: number) => {
    setSelectedExercises(prev => 
      prev.includes(exerciseId) 
        ? prev.filter(id => id !== exerciseId)
        : [...prev, exerciseId]
    )
  }

  const handleSelectAll = () => {
    if (selectedExercises.length === currentExercises.length) {
      setSelectedExercises([])
    } else {
      setSelectedExercises(currentExercises.map(exercise => exercise.id))
    }
  }

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Ejercicios</h1>
          <p className="text-gray-600">Gestiona la biblioteca de ejercicios del gimnasio</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" className="flex items-center space-x-2">
            <Download className="h-4 w-4" />
            <span>Exportar</span>
          </Button>
          <Button variant="outline" className="flex items-center space-x-2">
            <Upload className="h-4 w-4" />
            <span>Importar</span>
          </Button>
          <Button className="flex items-center space-x-2 bg-orange-600 hover:bg-orange-700">
            <Plus className="h-4 w-4" />
            <span>Nuevo Ejercicio</span>
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Resumen</TabsTrigger>
          <TabsTrigger value="exercises">Ejercicios</TabsTrigger>
          <TabsTrigger value="analytics">Analíticas</TabsTrigger>
          <TabsTrigger value="library">Biblioteca</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Ejercicios</p>
                    <p className="text-2xl font-bold text-gray-900">{exercises.length}</p>
                    <p className="text-xs text-green-600 flex items-center mt-1">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      +12% este mes
                    </p>
                  </div>
                  <div className="bg-orange-500 p-3 rounded-lg">
                    <Dumbbell className="h-6 w-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Ejercicios Populares</p>
                    <p className="text-2xl font-bold text-gray-900">28</p>
                    <p className="text-xs text-blue-600 flex items-center mt-1">
                      <Flame className="h-3 w-3 mr-1" />
                      Más de 50 usos
                    </p>
                  </div>
                  <div className="bg-blue-500 p-3 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Valoración Promedio</p>
                    <p className="text-2xl font-bold text-gray-900">4.6</p>
                    <p className="text-xs text-yellow-600 flex items-center mt-1">
                      <Star className="h-3 w-3 mr-1" />
                      Excelente calidad
                    </p>
                  </div>
                  <div className="bg-yellow-500 p-3 rounded-lg">
                    <Star className="h-6 w-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Categorías</p>
                    <p className="text-2xl font-bold text-gray-900">6</p>
                    <p className="text-xs text-purple-600 flex items-center mt-1">
                      <Target className="h-3 w-3 mr-1" />
                      Bien distribuidas
                    </p>
                  </div>
                  <div className="bg-purple-500 p-3 rounded-lg">
                    <Target className="h-6 w-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Uso de Ejercicios</CardTitle>
                <CardDescription>Tendencia mensual de uso de ejercicios</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={exerciseUsageData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="exercises" stroke="#f97316" fill="#fed7aa" />
                    <Area type="monotone" dataKey="popular" stroke="#3b82f6" fill="#bfdbfe" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Distribución por Categoría</CardTitle>
                <CardDescription>Porcentaje de ejercicios por categoría</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryDistribution}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}%`}
                    >
                      {categoryDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Popular Exercises */}
          <Card>
            <CardHeader>
              <CardTitle>Ejercicios Más Populares</CardTitle>
              <CardDescription>Los ejercicios más utilizados en rutinas</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {popularExercises.map((exercise, index) => (
                  <div key={exercise.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className="bg-orange-100 text-orange-600 rounded-full w-8 h-8 flex items-center justify-center font-semibold">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{exercise.name}</p>
                        <p className="text-sm text-gray-600">{exercise.category}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <p className="text-sm font-medium text-gray-900">{exercise.uses}</p>
                        <p className="text-xs text-gray-600">usos</p>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Star className="h-4 w-4 text-yellow-400 fill-current" />
                        <span className="text-sm font-medium">{exercise.rating}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="exercises" className="space-y-6">
          {/* Search and Filters */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-4 mb-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Buscar ejercicios por nombre, descripción, músculos..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="approved-only"
                    checked={showApprovedOnly}
                    onCheckedChange={(checked) => setShowApprovedOnly(checked === true)}
                  />
                  <Label htmlFor="approved-only" className="text-sm">Solo aprobados</Label>
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowFilters(!showFilters)}
                  className={cn(showFilters && "bg-gray-50")}
                >
                  <Filter className="h-4 w-4 mr-2" />
                  Filtros
                </Button>
              </div>

              {showFilters && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
                  <div>
                    <Label className="text-sm font-medium">Categoría</Label>
                    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map(category => (
                          <SelectItem key={category} value={category}>{category}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Dificultad</Label>
                    <Select value={selectedDifficulty} onValueChange={setSelectedDifficulty}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {difficulties.map(difficulty => (
                          <SelectItem key={difficulty} value={difficulty}>
                            {difficulty === 'Todas' ? 'Todas' : getDifficultyText(difficulty)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Grupo Muscular</Label>
                    <Select value={selectedMuscleGroup} onValueChange={setSelectedMuscleGroup}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {muscleGroups.map(muscle => (
                          <SelectItem key={muscle} value={muscle}>{muscle}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Equipamiento</Label>
                    <Select value={selectedEquipment} onValueChange={setSelectedEquipment}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {equipmentOptions.map(equipment => (
                          <SelectItem key={equipment} value={equipment}>{equipment}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {selectedExercises.length > 0 && (
                <>
                  <Button variant="outline" size="sm">
                    <Copy className="h-4 w-4 mr-2" />
                    Duplicar ({selectedExercises.length})
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Exportar ({selectedExercises.length})
                  </Button>
                  <Button variant="destructive" size="sm">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Eliminar ({selectedExercises.length})
                  </Button>
                </>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Label className="text-sm">Vista:</Label>
                <div className="flex border border-gray-300 rounded-md">
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('grid')}
                    className="rounded-r-none"
                  >
                    <Grid3X3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('list')}
                    className="rounded-l-none"
                  >
                    <List className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Label className="text-sm">Ordenar:</Label>
                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="name">Nombre</SelectItem>
                    <SelectItem value="category">Categoría</SelectItem>
                    <SelectItem value="difficulty_level">Dificultad</SelectItem>
                    <SelectItem value="rating">Valoración</SelectItem>
                    <SelectItem value="uses">Uso</SelectItem>
                    <SelectItem value="created_at">Fecha</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                >
                  {sortOrder === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />}
                </Button>
              </div>
              <div className="text-sm text-gray-600">
                {filteredExercises.length} ejercicios
              </div>
            </div>
          </div>

          {/* Exercises Grid/List */}
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {currentExercises.map((exercise) => (
                <Card key={exercise.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                  <div className="relative h-48 bg-gray-100">
                    {exercise.image_url ? (
                      <img
                        src={exercise.image_url}
                        alt={exercise.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Image className="h-12 w-12 text-gray-400" />
                      </div>
                    )}
                    <div className="absolute top-2 right-2">
                      <Checkbox
                        checked={selectedExercises.includes(exercise.id)}
                        onCheckedChange={() => handleSelectExercise(exercise.id)}
                      />
                    </div>
                    <div className="absolute top-2 left-2">
                      <Badge className={getDifficultyColor(exercise.difficulty_level)}>
                        {getDifficultyText(exercise.difficulty_level)}
                      </Badge>
                    </div>
                    {exercise.video_url && (
                      <div className="absolute bottom-2 right-2">
                        <div className="bg-black bg-opacity-50 rounded-full p-1">
                          <Play className="h-4 w-4 text-white" />
                        </div>
                      </div>
                    )}
                  </div>

                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getCategoryIcon(exercise.category)}
                        <span className="text-sm font-medium text-gray-600">{exercise.category}</span>
                      </div>
                      {exercise.approved && (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{exercise.name}</h3>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">{exercise.description}</p>

                    <div className="mb-3">
                      <p className="text-xs font-medium text-gray-700 mb-1">Músculos:</p>
                      <div className="flex flex-wrap gap-1">
                        {exercise.muscle_groups.slice(0, 3).map((muscle, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {muscle}
                          </Badge>
                        ))}
                        {exercise.muscle_groups.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{exercise.muscle_groups.length - 3}
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-1">
                        {renderStars(exercise.rating)}
                        <span className="text-xs text-gray-600 ml-1">({exercise.rating})</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Users className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-600">{exercise.uses}</span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="text-xs text-gray-500">
                        Por {exercise.created_by}
                      </div>
                      <div className="flex items-center space-x-1">
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
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedExercises.length === currentExercises.length && currentExercises.length > 0}
                        onCheckedChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('name')}>
                      <div className="flex items-center space-x-1">
                        <span>Ejercicio</span>
                        {sortBy === 'name' && (
                          sortOrder === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                        )}
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('category')}>
                      <div className="flex items-center space-x-1">
                        <span>Categoría</span>
                        {sortBy === 'category' && (
                          sortOrder === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                        )}
                      </div>
                    </TableHead>
                    <TableHead>Músculos</TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('difficulty_level')}>
                      <div className="flex items-center space-x-1">
                        <span>Dificultad</span>
                        {sortBy === 'difficulty_level' && (
                          sortOrder === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                        )}
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('uses')}>
                      <div className="flex items-center space-x-1">
                        <span>Uso</span>
                        {sortBy === 'uses' && (
                          sortOrder === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                        )}
                      </div>
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('rating')}>
                      <div className="flex items-center space-x-1">
                        <span>Valoración</span>
                        {sortBy === 'rating' && (
                          sortOrder === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                        )}
                      </div>
                    </TableHead>
                    <TableHead>Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentExercises.map((exercise) => (
                    <TableRow key={exercise.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedExercises.includes(exercise.id)}
                          onCheckedChange={() => handleSelectExercise(exercise.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-3">
                          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                            {exercise.image_url ? (
                              <img
                                src={exercise.image_url}
                                alt={exercise.name}
                                className="w-full h-full object-cover rounded-lg"
                              />
                            ) : (
                              <Image className="h-6 w-6 text-gray-400" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <p className="font-medium text-gray-900">{exercise.name}</p>
                              {exercise.video_url && <Play className="h-3 w-3 text-blue-500" />}
                              {exercise.approved && <CheckCircle className="h-3 w-3 text-green-500" />}
                            </div>
                            <p className="text-sm text-gray-500 line-clamp-1">{exercise.description}</p>
                            <p className="text-xs text-gray-400">Por {exercise.created_by}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          {getCategoryIcon(exercise.category)}
                          <span className="text-sm">{exercise.category}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {exercise.muscle_groups.slice(0, 2).map((muscle, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {muscle}
                            </Badge>
                          ))}
                          {exercise.muscle_groups.length > 2 && (
                            <Badge variant="outline" className="text-xs">
                              +{exercise.muscle_groups.length - 2}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getDifficultyColor(exercise.difficulty_level)}>
                          {getDifficultyText(exercise.difficulty_level)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <Users className="h-3 w-3 text-gray-400" />
                          <span className="text-sm">{exercise.uses}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          {renderStars(exercise.rating)}
                          <span className="text-xs text-gray-600 ml-1">({exercise.rating})</span>
                        </div>
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
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Mostrando {startIndex + 1} a {Math.min(startIndex + itemsPerPage, filteredExercises.length)} de {filteredExercises.length} ejercicios
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Anterior
                </Button>
                <span className="text-sm text-gray-700">
                  Página {currentPage} de {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

            <TabsContent value="analytics" className="space-y-6 mt-0">
          {/* Analytics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Estadísticas por Dificultad</CardTitle>
                <CardDescription>Distribución de ejercicios por nivel</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={difficultyStats}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="difficulty" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#f97316" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tendencia de Creación</CardTitle>
                <CardDescription>Ejercicios creados por mes</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={exerciseUsageData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="exercises" stroke="#10b981" fill="#d1fae5" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Analytics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Ejercicios por Categoría</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {categoryDistribution.map((category) => (
                    <div key={category.name} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: category.color }}
                        />
                        <span className="text-sm font-medium">{category.name}</span>
                      </div>
                      <span className="text-sm text-gray-600">{category.value}%</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Métricas de Calidad</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Valoración promedio</span>
                    <span className="text-lg font-bold text-green-600">4.6/5</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Ejercicios con video</span>
                    <span className="text-lg font-bold text-blue-600">68%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Ejercicios aprobados</span>
                    <span className="text-lg font-bold text-purple-600">92%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Uso promedio</span>
                    <span className="text-lg font-bold text-orange-600">24</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Actividad Reciente</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="bg-green-100 p-1 rounded-full">
                      <Plus className="h-3 w-3 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Nuevo ejercicio creado</p>
                      <p className="text-xs text-gray-600">Hace 2 horas</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 p-1 rounded-full">
                      <Edit className="h-3 w-3 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Ejercicio actualizado</p>
                      <p className="text-xs text-gray-600">Hace 4 horas</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="bg-yellow-100 p-1 rounded-full">
                      <Star className="h-3 w-3 text-yellow-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Nueva valoración</p>
                      <p className="text-xs text-gray-600">Hace 6 horas</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="library" className="space-y-6">
          {/* Library Management */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Gestión de Biblioteca</CardTitle>
                <CardDescription>Herramientas para organizar y mantener la biblioteca de ejercicios</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Button variant="outline" className="h-20 flex-col">
                    <Upload className="h-6 w-6 mb-2" />
                    <span>Importar Ejercicios</span>
                  </Button>
                  <Button variant="outline" className="h-20 flex-col">
                    <Download className="h-6 w-6 mb-2" />
                    <span>Exportar Biblioteca</span>
                  </Button>
                  <Button variant="outline" className="h-20 flex-col">
                    <RefreshCw className="h-6 w-6 mb-2" />
                    <span>Sincronizar</span>
                  </Button>
                  <Button variant="outline" className="h-20 flex-col">
                    <Settings className="h-6 w-6 mb-2" />
                    <span>Configuración</span>
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Estado de la Biblioteca</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Total de ejercicios</span>
                    <span className="font-semibold">{exercises.length}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Con imágenes</span>
                    <span className="font-semibold text-green-600">85%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Con videos</span>
                    <span className="font-semibold text-blue-600">68%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Aprobados</span>
                    <span className="font-semibold text-purple-600">92%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Última actualización</span>
                    <span className="text-xs text-gray-600">Hace 2 horas</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button variant="outline" className="h-16 flex-col">
              <Camera className="h-5 w-5 mb-1" />
              <span className="text-sm">Añadir Imágenes</span>
            </Button>
            <Button variant="outline" className="h-16 flex-col">
              <Video className="h-5 w-5 mb-1" />
              <span className="text-sm">Añadir Videos</span>
            </Button>
            <Button variant="outline" className="h-16 flex-col">
              <Tag className="h-5 w-5 mb-1" />
              <span className="text-sm">Gestionar Etiquetas</span>
            </Button>
            <Button variant="outline" className="h-16 flex-col">
              <Award className="h-5 w-5 mb-1" />
              <span className="text-sm">Revisar Calidad</span>
            </Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}