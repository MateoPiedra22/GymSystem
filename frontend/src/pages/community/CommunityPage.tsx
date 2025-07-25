import { useState, useEffect, useCallback } from 'react'
import {
  Search,
  Filter,
  Plus,
  Heart,
  MessageCircle,
  Share2,
  Users,
  TrendingUp,
  Calendar,
  Trophy,
  Activity,
  Image,
  Video,
  FileText,
  MoreHorizontal,
  Eye,
  Star,
  Zap,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { cn } from '../../utils/cn'
// import { useCommunityStore } from '../../store/communityStore' // Store not available yet
// import { debounce } from '../../utils/debounce' // File not available

interface Post {
  id: number
  user: {
    id: number
    name: string
    avatar_url?: string
    role: 'member' | 'trainer' | 'admin'
    verified: boolean
  }
  content: string
  type: 'text' | 'image' | 'video' | 'achievement' | 'workout' | 'event'
  media_url?: string
  workout_data?: {
    exercise: string
    sets: number
    reps: number
    weight: number
  }
  achievement_data?: {
    title: string
    description: string
    badge_url: string
  }
  event_data?: {
    title: string
    date: string
    location: string
    participants: number
  }
  likes_count: number
  comments_count: number
  shares_count: number
  is_liked: boolean
  created_at: string
  tags: string[]
}

interface Challenge {
  id: number
  title: string
  description: string
  type: 'fitness' | 'nutrition' | 'mindfulness' | 'social'
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  duration_days: number
  participants_count: number
  reward_points: number
  start_date: string
  end_date: string
  image_url: string
  is_joined: boolean
  progress?: number
}

// Mock data removed - now using real communityStore data

const postTypes = ['Todos', 'text', 'image', 'video', 'achievement', 'workout', 'event']
const challengeTypes = ['Todos', 'fitness', 'nutrition', 'mindfulness', 'social']
const difficulties = ['Todos', 'beginner', 'intermediate', 'advanced']

export function CommunityPage() {
  // Temporary state until communityStore is created
  const [posts] = useState<Post[]>([])
  const [challenges] = useState<Challenge[]>([])
  // Stats will come from communityStore when implemented
  const stats = {
    total_members: 0,
    active_today: 0,
    posts_today: 0,
    challenges_active: 0,
    total_achievements: 0,
    engagement_rate: 0
  }
  const [loading] = useState(false)
  const [error] = useState<string | null>(null)
  
  const [filteredPosts, setFilteredPosts] = useState<Post[]>([])
  const [activeTab, setActiveTab] = useState<'feed' | 'challenges' | 'leaderboard'>('feed')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPostType, setSelectedPostType] = useState('Todos')
  const [selectedChallengeType, setSelectedChallengeType] = useState('Todos')
  const [selectedDifficulty, setSelectedDifficulty] = useState('Todos')
  const [showFilters, setShowFilters] = useState(false)

  // Simple debounce function
  const debounce = (func: (...args: any[]) => void, delay: number) => {
    let timeoutId: NodeJS.Timeout
    return (...args: any[]) => {
      clearTimeout(timeoutId)
      timeoutId = setTimeout(() => func(...args), delay)
    }
  }

  // Temporary placeholder functions until communityStore is created
  const handleSearch = useCallback(
    debounce((term: string) => {
      // TODO: Implement search when communityStore is available
      console.log('Search term:', term)
    }, 300),
    []
  )

  // Filter posts based on search and filters
  useEffect(() => {
    if (!posts) {
      setFilteredPosts([])
      return
    }

    let filtered = posts

    // Post type filter
    if (selectedPostType !== 'Todos') {
      filtered = filtered.filter(post => post.type === selectedPostType)
    }

    setFilteredPosts(filtered)
  }, [posts, selectedPostType])

  const handleLikePost = (postId: number) => {
    // TODO: Implement like functionality when communityStore is available
    console.log('Like post:', postId)
  }

  const handleJoinChallenge = (challengeId: number) => {
    // TODO: Implement join challenge when communityStore is available
    console.log('Join challenge:', challengeId)
  }

  const getPostTypeText = (type: string) => {
    switch (type) {
      case 'text':
        return 'Texto'
      case 'image':
        return 'Imagen'
      case 'video':
        return 'Video'
      case 'achievement':
        return 'Logro'
      case 'workout':
        return 'Entrenamiento'
      case 'event':
        return 'Evento'
      default:
        return 'Todos'
    }
  }

  const getChallengeTypeText = (type: string) => {
    switch (type) {
      case 'fitness':
        return 'Fitness'
      case 'nutrition':
        return 'Nutrición'
      case 'mindfulness':
        return 'Mindfulness'
      case 'social':
        return 'Social'
      default:
        return 'Todos'
    }
  }

  const getDifficultyText = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'Principiante'
      case 'intermediate':
        return 'Intermedio'
      case 'advanced':
        return 'Avanzado'
      default:
        return 'Todos'
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-100 text-green-800'
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800'
      case 'advanced':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
    
    if (diffInHours < 1) {
      return 'Hace unos minutos'
    } else if (diffInHours < 24) {
      return `Hace ${diffInHours}h`
    } else {
      return date.toLocaleDateString('es-AR')
    }
  }

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase()
  }

  const getPostIcon = (type: string) => {
    switch (type) {
      case 'image':
        return <Image className="h-4 w-4" />
      case 'video':
        return <Video className="h-4 w-4" />
      case 'achievement':
        return <Trophy className="h-4 w-4" />
      case 'workout':
        return <Activity className="h-4 w-4" />
      case 'event':
        return <Calendar className="h-4 w-4" />
      default:
        return <FileText className="h-4 w-4" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Comunidad</h1>
          <p className="text-gray-600">Conecta, comparte y motívate con otros miembros</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Users className="h-4 w-4 mr-2" />
            Miembros
          </Button>
          <Button className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="h-4 w-4 mr-2" />
            Nueva Publicación
          </Button>
        </div>
      </div>

      {/* Loading and Error States */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Cargando contenido...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Miembros Totales</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_members}</p>
            </div>
            <div className="bg-indigo-500 p-2 rounded-lg">
              <Users className="h-5 w-5 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Activos Hoy</p>
              <p className="text-2xl font-bold text-gray-900">{stats.active_today}</p>
            </div>
            <div className="bg-green-500 p-2 rounded-lg">
              <Activity className="h-5 w-5 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Publicaciones Hoy</p>
              <p className="text-2xl font-bold text-gray-900">{stats.posts_today}</p>
            </div>
            <div className="bg-blue-500 p-2 rounded-lg">
              <MessageCircle className="h-5 w-5 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Engagement</p>
              <p className="text-2xl font-bold text-gray-900">{stats.engagement_rate}%</p>
            </div>
            <div className="bg-purple-500 p-2 rounded-lg">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('feed')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm",
                activeTab === 'feed'
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              Feed
            </button>
            <button
              onClick={() => setActiveTab('challenges')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm",
                activeTab === 'challenges'
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              Desafíos
            </button>
            <button
              onClick={() => setActiveTab('leaderboard')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm",
                activeTab === 'leaderboard'
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              Ranking
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'feed' && (
            <div className="space-y-6">
              {/* Search and Filters */}
              <div className="flex items-center space-x-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Buscar publicaciones, usuarios o etiquetas..."
                    value={searchTerm}
                    onChange={(e) => {
                      setSearchTerm(e.target.value)
                      handleSearch(e.target.value)
                    }}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
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

              {/* Filters */}
              {showFilters && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tipo de Publicación
                    </label>
                    <select
                      value={selectedPostType}
                      onChange={(e) => setSelectedPostType(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {postTypes.map(type => (
                        <option key={type} value={type}>
                          {getPostTypeText(type)}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Posts Feed */}
              <div className="space-y-6">
                {filteredPosts.map((post) => (
                  <div key={post.id} className="bg-white border border-gray-200 rounded-lg p-6">
                    {/* Post Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                          {post.user.avatar_url ? (
                            <img
                              src={post.user.avatar_url}
                              alt={post.user.name}
                              className="w-full h-full object-cover rounded-full"
                            />
                          ) : (
                            <span className="text-indigo-600 font-medium text-sm">
                              {getInitials(post.user.name)}
                            </span>
                          )}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <p className="font-medium text-gray-900">{post.user.name}</p>
                            {post.user.verified && (
                              <div className="bg-blue-500 p-1 rounded-full">
                                <Star className="h-3 w-3 text-white" />
                              </div>
                            )}
                            {post.user.role === 'trainer' && (
                              <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                                Entrenador
                              </span>
                            )}
                          </div>
                          <div className="flex items-center space-x-2 text-sm text-gray-500">
                            {getPostIcon(post.type)}
                            <span>{formatDate(post.created_at)}</span>
                          </div>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* Post Content */}
                    <div className="mb-4">
                      <p className="text-gray-900 whitespace-pre-wrap">{post.content}</p>
                    </div>

                    {/* Post Media/Special Content */}
                    {post.type === 'image' && post.media_url && (
                      <div className="mb-4">
                        <img
                          src={post.media_url}
                          alt="Post image"
                          className="w-full h-64 object-cover rounded-lg"
                        />
                      </div>
                    )}

                    {post.type === 'achievement' && post.achievement_data && (
                      <div className="mb-4 p-4 bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <img
                            src={post.achievement_data.badge_url}
                            alt="Achievement badge"
                            className="w-12 h-12 object-cover rounded-full"
                          />
                          <div>
                            <h4 className="font-semibold text-yellow-800">{post.achievement_data.title}</h4>
                            <p className="text-sm text-yellow-700">{post.achievement_data.description}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {post.type === 'workout' && post.workout_data && (
                      <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold text-blue-800">{post.workout_data.exercise}</h4>
                            <p className="text-sm text-blue-700">
                              {post.workout_data.sets} series × {post.workout_data.reps} repeticiones
                              {post.workout_data.weight > 0 && ` × ${post.workout_data.weight}kg`}
                            </p>
                          </div>
                          <Activity className="h-8 w-8 text-blue-500" />
                        </div>
                      </div>
                    )}

                    {/* Tags */}
                    {post.tags.length > 0 && (
                      <div className="mb-4">
                        <div className="flex flex-wrap gap-2">
                          {post.tags.map((tag, index) => (
                            <span key={index} className="inline-flex px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Post Actions */}
                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                      <div className="flex items-center space-x-6">
                        <button
                          onClick={() => handleLikePost(post.id)}
                          className={cn(
                            "flex items-center space-x-2 text-sm",
                            post.is_liked ? "text-red-600" : "text-gray-500 hover:text-red-600"
                          )}
                        >
                          <Heart className={cn("h-4 w-4", post.is_liked && "fill-current")} />
                          <span>{post.likes_count}</span>
                        </button>
                        <button className="flex items-center space-x-2 text-sm text-gray-500 hover:text-blue-600">
                          <MessageCircle className="h-4 w-4" />
                          <span>{post.comments_count}</span>
                        </button>
                        <button className="flex items-center space-x-2 text-sm text-gray-500 hover:text-green-600">
                          <Share2 className="h-4 w-4" />
                          <span>{post.shares_count}</span>
                        </button>
                      </div>
                      <div className="flex items-center space-x-2 text-xs text-gray-500">
                        <Eye className="h-3 w-3" />
                        <span>{post.likes_count + post.comments_count * 2} vistas</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'challenges' && (
            <div className="space-y-6">
              {/* Challenge Filters */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de Desafío
                  </label>
                  <select
                    value={selectedChallengeType}
                    onChange={(e) => setSelectedChallengeType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {challengeTypes.map(type => (
                      <option key={type} value={type}>
                        {getChallengeTypeText(type)}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dificultad
                  </label>
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    {difficulties.map(difficulty => (
                      <option key={difficulty} value={difficulty}>
                        {getDifficultyText(difficulty)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Challenges Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {challenges.map((challenge) => (
                  <div key={challenge.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                    <img
                      src={challenge.image_url}
                      alt={challenge.title}
                      className="w-full h-48 object-cover"
                    />
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-3">
                        <h3 className="font-semibold text-gray-900">{challenge.title}</h3>
                        <span className={cn(
                          "inline-flex px-2 py-1 text-xs font-semibold rounded-full",
                          getDifficultyColor(challenge.difficulty)
                        )}>
                          {getDifficultyText(challenge.difficulty)}
                        </span>
                      </div>
                      
                      <p className="text-sm text-gray-600 mb-4">{challenge.description}</p>
                      
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">Duración:</span>
                          <span className="font-medium">{challenge.duration_days} días</span>
                        </div>
                        
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">Participantes:</span>
                          <span className="font-medium">{challenge.participants_count}</span>
                        </div>
                        
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-500">Recompensa:</span>
                          <div className="flex items-center space-x-1">
                            <Zap className="h-3 w-3 text-yellow-500" />
                            <span className="font-medium">{challenge.reward_points} pts</span>
                          </div>
                        </div>
                        
                        {challenge.is_joined && challenge.progress !== undefined && (
                          <div>
                            <div className="flex items-center justify-between text-sm mb-1">
                              <span className="text-gray-500">Progreso:</span>
                              <span className="font-medium">{challenge.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${challenge.progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                        
                        <Button
                          onClick={() => handleJoinChallenge(challenge.id)}
                          className={cn(
                            "w-full",
                            challenge.is_joined
                              ? "bg-green-600 hover:bg-green-700"
                              : "bg-indigo-600 hover:bg-indigo-700"
                          )}
                        >
                          {challenge.is_joined ? 'Participando' : 'Unirse al Desafío'}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'leaderboard' && (
            <div className="space-y-6">
              <div className="text-center py-12">
                <Trophy className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Ranking de la Comunidad</h3>
                <p className="text-gray-600">Próximamente: Tabla de clasificación con puntos, logros y estadísticas de miembros</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CommunityPage