import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Eye, EyeOff, Dumbbell, User, Users } from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../utils/cn'

type LoginMode = 'dueno' | 'profesor'

const duenoSchema = z.object({
  password: z.string().min(1, 'Contraseña es requerida'),
})

const profesorSchema = z.object({
  profesorId: z.string().min(1, 'Selecciona un profesor'),
  password: z.string().min(1, 'Contraseña es requerida'),
})

type DuenoForm = z.infer<typeof duenoSchema>
type ProfesorForm = z.infer<typeof profesorSchema>

// Mock professors list
const mockProfessors = [
  { id: 'prof1', name: 'Carlos Rodríguez', specialty: 'Entrenamiento Funcional' },
  { id: 'prof2', name: 'María González', specialty: 'Yoga y Pilates' },
  { id: 'prof3', name: 'Luis Martínez', specialty: 'Musculación' },
  { id: 'prof4', name: 'Ana López', specialty: 'Cardio y Aeróbicos' },
]

export function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [loginMode, setLoginMode] = useState<LoginMode>('dueno')
  const navigate = useNavigate()
  const { login, loading, error, clearError } = useAuthStore()

  const duenoForm = useForm<DuenoForm>({
    resolver: zodResolver(duenoSchema),
    defaultValues: { password: '' }
  })

  const profesorForm = useForm<ProfesorForm>({
    resolver: zodResolver(profesorSchema),
    defaultValues: { profesorId: '', password: '' }
  })



  const handleDuenoLogin = async (data: DuenoForm) => {
    try {
      clearError()
      await login({
        email: 'Zurka', // Gym owner username
        password: data.password
      })
      navigate('/dashboard')
    } catch (error) {
      console.error('Login error:', error)
    }
  }

  const handleProfesorLogin = async (data: ProfesorForm) => {
    try {
      clearError()
      await login({
        email: `profesor_${data.profesorId}`, // Special identifier for trainer
        password: data.password
      })
      navigate('/dashboard')
    } catch (error) {
      console.error('Login error:', error)
    }
  }



  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="max-w-4xl w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-blue-600 p-3 rounded-full">
              <Dumbbell className="h-8 w-8 text-white" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Zurka Gym System
          </h2>
          <p className="text-gray-600">
            Sistema de Administración para Dueños y Profesores
          </p>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="space-y-6">
            <h3 className="text-xl font-semibold text-center text-gray-900 mb-8">
              Iniciar Sesión
            </h3>
            
            {/* Login Mode Selector */}
            <div className="flex justify-center space-x-4 mb-8">
              <button
                type="button"
                onClick={() => setLoginMode('dueno')}
                className={cn(
                  "flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors",
                  loginMode === 'dueno'
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                )}
              >
                <User className="h-4 w-4" />
                <span>Dueño</span>
              </button>
              <button
                type="button"
                onClick={() => setLoginMode('profesor')}
                className={cn(
                  "flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors",
                  loginMode === 'profesor'
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                )}
              >
                <Users className="h-4 w-4" />
                <span>Profesor</span>
              </button>

            </div>

            {/* Dueño Login Form */}
            {loginMode === 'dueno' && (
              <form onSubmit={duenoForm.handleSubmit(handleDuenoLogin)} className="space-y-6">
                <div className="text-center text-sm text-gray-600 mb-4">
                  Acceso para el propietario del gimnasio Zurka
                </div>
                
                <div>
                  <label htmlFor="dueno-password" className="block text-sm font-medium text-gray-700 mb-2">
                    Contraseña de Zurka
                  </label>
                  <div className="relative">
                    <input
                      {...duenoForm.register('password')}
                      type={showPassword ? 'text' : 'password'}
                      id="dueno-password"
                      placeholder="Contraseña por defecto: 0000"
                      className={cn(
                        "w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                        (duenoForm.formState.errors.password || error) && "border-red-500 focus:ring-red-500 focus:border-red-500"
                      )}
                      disabled={loading}
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => setShowPassword(!showPassword)}
                      disabled={loading}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4 text-gray-400" />
                      ) : (
                        <Eye className="h-4 w-4 text-gray-400" />
                      )}
                    </button>
                  </div>
                  {duenoForm.formState.errors.password && (
                    <p className="mt-1 text-sm text-red-600">{duenoForm.formState.errors.password.message}</p>
                  )}
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={loading}
                >
                  {loading ? 'Iniciando sesión...' : 'Acceder como Dueño'}
                </Button>
              </form>
            )}

            {/* Profesor Login Form */}
            {loginMode === 'profesor' && (
              <form onSubmit={profesorForm.handleSubmit(handleProfesorLogin)} className="space-y-6">
                <div className="text-center text-sm text-gray-600 mb-4">
                  Acceso para profesores del gimnasio
                </div>
                
                <div>
                  <label htmlFor="profesor-select" className="block text-sm font-medium text-gray-700 mb-2">
                    Seleccionar Profesor
                  </label>
                  <Select
                    value={profesorForm.watch('profesorId')}
                    onValueChange={(value) => profesorForm.setValue('profesorId', value)}
                    disabled={loading}
                  >
                    <SelectTrigger className={cn(
                      "w-full",
                      profesorForm.formState.errors.profesorId && "border-red-500"
                    )}>
                      <SelectValue placeholder="Selecciona tu perfil de profesor" />
                    </SelectTrigger>
                    <SelectContent>
                      {mockProfessors.map((profesor) => (
                        <SelectItem key={profesor.id} value={profesor.id}>
                          <div className="flex flex-col">
                            <span className="font-medium">{profesor.name}</span>
                            <span className="text-sm text-gray-500">{profesor.specialty}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {profesorForm.formState.errors.profesorId && (
                    <p className="mt-1 text-sm text-red-600">{profesorForm.formState.errors.profesorId.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="profesor-password" className="block text-sm font-medium text-gray-700 mb-2">
                    Contraseña
                  </label>
                  <div className="relative">
                    <input
                      {...profesorForm.register('password')}
                      type={showPassword ? 'text' : 'password'}
                      id="profesor-password"
                      placeholder="Ingresa tu contraseña"
                      className={cn(
                        "w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                        (profesorForm.formState.errors.password || error) && "border-red-500 focus:ring-red-500 focus:border-red-500"
                      )}
                      disabled={loading}
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => setShowPassword(!showPassword)}
                      disabled={loading}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4 text-gray-400" />
                      ) : (
                        <Eye className="h-4 w-4 text-gray-400" />
                      )}
                    </button>
                  </div>
                  {profesorForm.formState.errors.password && (
                    <p className="mt-1 text-sm text-red-600">{profesorForm.formState.errors.password.message}</p>
                  )}
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={loading}
                >
                  {loading ? 'Iniciando sesión...' : 'Acceder como Profesor'}
                </Button>
              </form>
            )}


          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>© 2024 Zurka Gym System. Sistema de Administración.</p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage