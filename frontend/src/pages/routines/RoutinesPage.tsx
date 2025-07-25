import React, { useState, useMemo } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import {
  Plus,
  Star,
  TrendingUp,
  Dumbbell,
  Play,
  Award,
  BarChart2,
  ArrowRight,
  FileText,
  Search,
  Filter,
  Edit,
  Trash2,
  Eye,
  Clock,
  Users,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, BarChart, Bar, PieChart as RechartsPieChart, Cell, Legend } from 'recharts';

const RoutinesPage: React.FC = () => {
  // State management
  const [filters, setFilters] = useState({
    search: '',
    category: 'Todas',
    difficulty: 'Todas',
    duration: 'Todas',
    isPublic: false,
    sortBy: 'name',
    sortOrder: 'asc' as 'asc' | 'desc'
  });
  
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedTab, setSelectedTab] = useState('overview');
  const routinesPerPage = 6;

  // Mock data
  const stats = {
    total_routines: 70,
    active_user_routines: 45,
    average_completion_rate: 78
  };

  const routineUsageData = [
    { month: 'Ene', routines: 65, completions: 45 },
    { month: 'Feb', routines: 70, completions: 52 },
    { month: 'Mar', routines: 68, completions: 48 },
    { month: 'Abr', routines: 75, completions: 58 },
    { month: 'May', routines: 72, completions: 55 }
  ];

  const categoryDistribution = [
    { name: 'Fuerza', value: 35, color: '#3B82F6' },
    { name: 'Cardio', value: 25, color: '#10B981' },
    { name: 'Flexibilidad', value: 20, color: '#F59E0B' },
    { name: 'Funcional', value: 20, color: '#EF4444' }
  ];

  const popularRoutines = [
    { id: 1, name: 'Fuerza Total', category: 'Fuerza', users: 156, rating: 4.8 },
    { id: 2, name: 'Cardio HIIT', category: 'Cardio', users: 142, rating: 4.7 },
    { id: 3, name: 'Yoga Flow', category: 'Flexibilidad', users: 128, rating: 4.9 }
  ];

  const difficultyStats = [
    { level: 'Principiante', count: 25, percentage: 36 },
    { level: 'Intermedio', count: 30, percentage: 43 },
    { level: 'Avanzado', count: 15, percentage: 21 }
  ];

  const mockRoutines = [
    {
      id: 1,
      name: 'Rutina de Fuerza Completa',
      description: 'Entrenamiento completo de fuerza para todo el cuerpo',
      category: 'Fuerza',
      difficulty_level: 'intermediate',
      estimated_session_duration: 60,
      goals: ['Ganar músculo', 'Aumentar fuerza'],
      is_public: true,
      created_by: 1,
      usage_count: 156,
      rating: 4.8,
      created_at: '2024-01-15'
    },
    {
      id: 2,
      name: 'HIIT Cardio Intenso',
      description: 'Entrenamiento de alta intensidad para quemar grasa',
      category: 'Cardio',
      difficulty_level: 'advanced',
      estimated_session_duration: 30,
      goals: ['Perder peso', 'Mejorar resistencia'],
      is_public: true,
      created_by: 2,
      usage_count: 142,
      rating: 4.7,
      created_at: '2024-01-20'
    },
    {
      id: 3,
      name: 'Yoga Flow Matutino',
      description: 'Secuencia de yoga para empezar el día con energía',
      category: 'Flexibilidad',
      difficulty_level: 'beginner',
      estimated_session_duration: 45,
      goals: ['Flexibilidad', 'Relajación'],
      is_public: true,
      created_by: 3,
      usage_count: 128,
      rating: 4.9,
      created_at: '2024-01-25'
    },
    {
      id: 4,
      name: 'Entrenamiento Funcional',
      description: 'Ejercicios funcionales para mejorar el rendimiento diario',
      category: 'Funcional',
      difficulty_level: 'intermediate',
      estimated_session_duration: 50,
      goals: ['Fuerza funcional', 'Coordinación'],
      is_public: false,
      created_by: 1,
      usage_count: 89,
      rating: 4.5,
      created_at: '2024-02-01'
    },
    {
      id: 5,
      name: 'Cardio Principiante',
      description: 'Rutina de cardio suave para principiantes',
      category: 'Cardio',
      difficulty_level: 'beginner',
      estimated_session_duration: 25,
      goals: ['Resistencia cardiovascular', 'Pérdida de peso'],
      is_public: true,
      created_by: 2,
      usage_count: 203,
      rating: 4.6,
      created_at: '2024-02-05'
    },
    {
      id: 6,
      name: 'Powerlifting Avanzado',
      description: 'Rutina de powerlifting para atletas experimentados',
      category: 'Fuerza',
      difficulty_level: 'advanced',
      estimated_session_duration: 90,
      goals: ['Fuerza máxima', 'Técnica'],
      is_public: true,
      created_by: 4,
      usage_count: 67,
      rating: 4.8,
      created_at: '2024-02-10'
    }
  ];

  // Helper functions
  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyLabel = (level: string) => {
    switch (level) {
      case 'beginner': return 'Principiante';
      case 'intermediate': return 'Intermedio';
      case 'advanced': return 'Avanzado';
      default: return level;
    }
  };

  const formatDuration = (minutes: number) => {
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
    }
    return `${minutes}m`;
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-3 w-3 ${
          i < Math.floor(rating) ? 'text-yellow-400 fill-current' : 'text-gray-300'
        }`}
      />
    ));
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const handleSearch = (value: string) => {
    setFilters(prev => ({ ...prev, search: value }));
    setCurrentPage(1);
  };

  const resetFilters = () => {
     setFilters({
       search: '',
       category: 'Todas',
       difficulty: 'Todas',
       duration: 'Todas',
       isPublic: false,
       sortBy: 'name',
       sortOrder: 'asc'
     });
     setCurrentPage(1);
   };

  // Filtered and paginated data
  const filteredRoutines = useMemo(() => {
    let filtered = [...mockRoutines];

    // Apply search filter
    if (filters.search) {
      filtered = filtered.filter(routine => 
        routine.name.toLowerCase().includes(filters.search.toLowerCase()) ||
        routine.description.toLowerCase().includes(filters.search.toLowerCase())
      );
    }

    // Apply category filter
    if (filters.category !== 'Todas') {
      filtered = filtered.filter(routine => routine.category === filters.category);
    }

    // Apply difficulty filter
    if (filters.difficulty !== 'Todas') {
      filtered = filtered.filter(routine => routine.difficulty_level === filters.difficulty.toLowerCase());
    }

    // Apply duration filter
    if (filters.duration !== 'Todas') {
      switch (filters.duration) {
        case 'Corta':
          filtered = filtered.filter(routine => routine.estimated_session_duration <= 30);
          break;
        case 'Media':
          filtered = filtered.filter(routine => routine.estimated_session_duration > 30 && routine.estimated_session_duration <= 60);
          break;
        case 'Larga':
          filtered = filtered.filter(routine => routine.estimated_session_duration > 60);
          break;
      }
    }

    // Apply public filter
    if (filters.isPublic) {
      filtered = filtered.filter(routine => routine.is_public);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue;
      switch (filters.sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'rating':
          aValue = a.rating;
          bValue = b.rating;
          break;
        case 'usage_count':
          aValue = a.usage_count;
          bValue = b.usage_count;
          break;
        case 'created_at':
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
          break;
        default:
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
      }

      if (filters.sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return filtered;
  }, [mockRoutines, filters]);

  const totalPages = Math.ceil(filteredRoutines.length / routinesPerPage);
  const paginatedRoutines = useMemo(() => {
    const startIndex = (currentPage - 1) * routinesPerPage;
    return filteredRoutines.slice(startIndex, startIndex + routinesPerPage);
  }, [filteredRoutines, currentPage, routinesPerPage]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestión de Rutinas</h1>
          <p className="text-gray-600">Crea, administra y asigna rutinas de entrenamiento personalizadas</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline">
            <FileText className="h-4 w-4 mr-2" />
            Exportar
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nueva Rutina
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="overview">Resumen</TabsTrigger>
          <TabsTrigger value="active">Rutinas Activas</TabsTrigger>
          <TabsTrigger value="templates">Plantillas</TabsTrigger>
          <TabsTrigger value="analytics">Análisis</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Rutinas</p>
                      <p className="text-3xl font-bold text-gray-900">{stats?.total_routines || 70}</p>
                      <p className="text-sm text-green-600 flex items-center mt-1">
                        <TrendingUp className="h-3 w-3 mr-1" />
                        +12% este mes
                      </p>
                    </div>
                    <div className="bg-blue-500 p-3 rounded-lg">
                      <Dumbbell className="h-6 w-6 text-white" />
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Rutinas Activas</p>
                      <p className="text-3xl font-bold text-gray-900">{stats?.active_user_routines || 45}</p>
                      <p className="text-sm text-green-600 flex items-center mt-1">
                        <TrendingUp className="h-3 w-3 mr-1" />
                        +8% este mes
                      </p>
                    </div>
                    <div className="bg-green-500 p-3 rounded-lg">
                      <Play className="h-6 w-6 text-white" />
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Tasa Finalización</p>
                      <p className="text-3xl font-bold text-gray-900">{stats?.average_completion_rate || 78}%</p>
                      <p className="text-sm text-green-600 flex items-center mt-1">
                        <TrendingUp className="h-3 w-3 mr-1" />
                        +5% este mes
                      </p>
                    </div>
                    <div className="bg-purple-500 p-3 rounded-lg">
                      <Award className="h-6 w-6 text-white" />
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Valoración Media</p>
                      <p className="text-3xl font-bold text-gray-900">4.6</p>
                      <div className="flex items-center mt-1">
                        {renderStars(4.6)}
                        <span className="text-sm text-gray-600 ml-1">(245 reseñas)</span>
                      </div>
                    </div>
                    <div className="bg-yellow-500 p-3 rounded-lg">
                      <Star className="h-6 w-6 text-white" />
                    </div>
                  </div>
                </Card>
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Uso de Rutinas</h3>
                    <Button variant="outline" size="sm">
                      <BarChart2 className="h-4 w-4 mr-2" />
                      Ver detalles
                    </Button>
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={routineUsageData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Area type="monotone" dataKey="routines" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
                      <Area type="monotone" dataKey="completions" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
                    </AreaChart>
                  </ResponsiveContainer>
                </Card>

                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Distribución por Categoría</h3>
                    <Button variant="outline" size="sm">
                      <BarChart2 className="h-4 w-4 mr-2" />
                      Ver detalles
                    </Button>
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <RechartsPieChart>
                      <Tooltip />
                      <RechartsPieChart data={categoryDistribution} cx="50%" cy="50%" outerRadius={80}>
                        {categoryDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </RechartsPieChart>
                      <Legend />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </Card>
              </div>

              {/* Popular Routines */}
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Rutinas Más Populares</h3>
                  <Button variant="outline" size="sm">
                    Ver todas
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </div>
                <div className="space-y-3">
                  {popularRoutines.map((routine, index) => (
                    <div key={routine.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full text-sm font-semibold">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{routine.name}</p>
                          <p className="text-sm text-gray-600">{routine.category}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-center">
                          <p className="text-sm font-medium text-gray-900">{routine.users}</p>
                          <p className="text-xs text-gray-600">usuarios</p>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Star className="h-4 w-4 text-yellow-400 fill-current" />
                          <span className="text-sm font-medium text-gray-900">{routine.rating}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </TabsContent>

        <TabsContent value="active" className="space-y-6">
              {/* Search and Filters */}
              <Card className="p-6">
                <div className="flex flex-col lg:flex-row gap-4">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                      <Input
                        placeholder="Buscar rutinas..."
                        value={filters.search}
                        onChange={(e) => handleSearch(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <Select value={filters.category} onValueChange={(value) => handleFilterChange('category', value)}>
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Categoría" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Todas">Todas</SelectItem>
                        <SelectItem value="Fuerza">Fuerza</SelectItem>
                        <SelectItem value="Cardio">Cardio</SelectItem>
                        <SelectItem value="Flexibilidad">Flexibilidad</SelectItem>
                        <SelectItem value="Funcional">Funcional</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Select value={filters.difficulty} onValueChange={(value) => handleFilterChange('difficulty', value)}>
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Dificultad" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Todas">Todas</SelectItem>
                        <SelectItem value="Principiante">Principiante</SelectItem>
                        <SelectItem value="Intermedio">Intermedio</SelectItem>
                        <SelectItem value="Avanzado">Avanzado</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Select value={filters.duration} onValueChange={(value) => handleFilterChange('duration', value)}>
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Duración" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Todas">Todas</SelectItem>
                        <SelectItem value="Corta">Corta (&lt; 30m)</SelectItem>
                        <SelectItem value="Media">Media (30-60m)</SelectItem>
                        <SelectItem value="Larga">Larga (&gt; 60m)</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Select value={filters.sortBy} onValueChange={(value) => handleFilterChange('sortBy', value)}>
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="Ordenar por" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="name">Nombre</SelectItem>
                        <SelectItem value="rating">Valoración</SelectItem>
                        <SelectItem value="usage_count">Popularidad</SelectItem>
                        <SelectItem value="created_at">Fecha</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Button variant="outline" onClick={resetFilters}>
                      <Filter className="h-4 w-4 mr-2" />
                      Limpiar
                    </Button>
                  </div>
                </div>
              </Card>

              {/* Results Summary */}
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Mostrando {paginatedRoutines.length} de {filteredRoutines.length} rutinas
                </p>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">Página {currentPage} de {totalPages}</span>
                </div>
              </div>

              {/* Routines Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {paginatedRoutines.map((routine) => (
                  <Card key={routine.id} className="p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">{routine.name}</h3>
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{routine.description}</p>
                      </div>
                      <div className="flex space-x-1 ml-2">
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <Badge variant="secondary">{routine.category}</Badge>
                        <Badge className={getDifficultyColor(routine.difficulty_level)}>
                          {getDifficultyLabel(routine.difficulty_level)}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm text-gray-600">
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span>{formatDuration(routine.estimated_session_duration)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Users className="h-4 w-4" />
                          <span>{routine.usage_count}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-1">
                          {renderStars(routine.rating)}
                          <span className="text-sm font-medium text-gray-900 ml-1">{routine.rating}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {routine.is_public && (
                            <Badge variant="outline" className="text-xs">Pública</Badge>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex flex-wrap gap-1 mt-2">
                        {routine.goals.slice(0, 2).map((goal, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {goal}
                          </Badge>
                        ))}
                        {routine.goals.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{routine.goals.length - 2} más
                          </Badge>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Anterior
                  </Button>
                  
                  <div className="flex space-x-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum;
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }
                      
                      return (
                        <Button
                          key={pageNum}
                          variant={currentPage === pageNum ? "default" : "outline"}
                          size="sm"
                          onClick={() => setCurrentPage(pageNum)}
                          className="w-10"
                        >
                          {pageNum}
                        </Button>
                      );
                    })}
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                  >
                    Siguiente
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}

              {/* Empty State */}
              {filteredRoutines.length === 0 && (
                <Card className="p-12">
                  <div className="text-center">
                    <Dumbbell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No se encontraron rutinas</h3>
                    <p className="text-gray-600 mb-4">Intenta ajustar los filtros o crear una nueva rutina</p>
                    <Button>
                      <Plus className="h-4 w-4 mr-2" />
                      Nueva Rutina
                    </Button>
                  </div>
                </Card>
              )}
            </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Estadísticas por Dificultad</h3>
              <div className="space-y-3">
                {difficultyStats.map((stat) => (
                  <div key={stat.level} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{stat.level}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${stat.percentage}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600">{stat.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Tendencias de Uso</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={routineUsageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="routines" fill="#3B82F6" />
                  <Bar dataKey="completions" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <Card className="p-6">
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Plantillas de Rutinas</h3>
              <p className="text-gray-600 mb-4">Crea y gestiona plantillas predefinidas para diferentes tipos de entrenamiento</p>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Crear Plantilla
              </Button>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RoutinesPage;