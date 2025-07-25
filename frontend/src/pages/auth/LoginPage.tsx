import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Eye, EyeOff, Dumbbell, User, Users, ArrowLeft } from 'lucide-react'
import { Button } from '../../components/ui/button'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../utils/cn'

type LoginStep = 'role-selection' | 'owner-login' | 'trainer-selection' | 'trainer-login'

const ownerLoginSchema = z.object({
  password: z.string().min(1, 'Contraseña es requerida'),
})

const trainerLoginSchema = z.object({
  password: z.string().min(1, 'Contraseña es requerida'),
})

type OwnerLoginForm = z.infer<typeof ownerLoginSchema>
type TrainerLoginForm = z.infer<typeof trainerLoginSchema>

// Mock trainers data - this should come from API in real implementation
const mockTrainers = [
  {
    id: 1,
    first_name: 'Carlos',
    last_name: 'Rodriguez',
    specialties: ['Musculación', 'CrossFit'],
    profile_picture: 'https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20fitness%20trainer%20headshot%20male%20athletic%20confident&image_size=square'
  },
  {
    id: 2,
    first_name: 'Maria',
    last_name: 'Gonzalez',
    specialties: ['Yoga', 'Pilates'],
    profile_picture: 'https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20female%20yoga%20instructor%20headshot%20serene%20confident&image_size=square'
  },
  {
    id: 3,
    first_name: 'Diego',
    last_name: 'Martinez',
    specialties: ['Funcional', 'HIIT'],
    profile_picture: 'https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20fitness%20coach%20male%20energetic%20athletic&image_size=square'
  }
]

export function LoginPage() {
  const [currentStep, setCurrentStep] = useState<LoginStep>('role-selection')
  const [selectedTrainer, setSelectedTrainer] = useState<typeof mockTrainers[0] | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()
  const { login, loading, error, clearError } = useAuthStore()

  const ownerForm = useForm<OwnerLoginForm>({
    resolver: zodResolver(ownerLoginSchema),
  })

  const trainerForm = useForm<TrainerLoginForm>({
    resolver: zodResolver(trainerLoginSchema),
  })

  const handleOwnerLogin = async (data: OwnerLoginForm) => {
    try {
      clearError()
      await login({ 
        role: 'owner', 
        password: data.password 
      })
      navigate('/dashboard')
    } catch (error) {
      console.error('Owner login error:', error)
    }
  }

  const handleTrainerLogin = async (data: TrainerLoginForm) => {
    if (!selectedTrainer) return
    
    try {
      clearError()
      await login({ 
        role: 'trainer', 
        password: data.password,
        trainer_id: selectedTrainer.id
      })
      navigate('/dashboard')
    } catch (error) {
      console.error('Trainer login error:', error)
    }
  }

  const handleTrainerSelect = (trainer: typeof mockTrainers[0]) => {
    setSelectedTrainer(trainer)
    setCurrentStep('trainer-login')
  }

  const handleBack = () => {
    if (currentStep === 'trainer-login') {
      setCurrentStep('trainer-selection')
      setSelectedTrainer(null)
      trainerForm.reset()
    } else if (currentStep === 'trainer-selection' || currentStep === 'owner-login') {
      setCurrentStep('role-selection')
      ownerForm.reset()
      trainerForm.reset()
    }
    clearError()
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
          {/* Back Button */}
          {currentStep !== 'role-selection' && (
            <button
              onClick={handleBack}
              className="flex items-center text-blue-600 hover:text-blue-700 mb-6 transition-colors"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Volver
            </button>
          )}

          {/* Role Selection */}
          {currentStep === 'role-selection' && (
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-center text-gray-900 mb-8">
                Selecciona tu tipo de acceso
              </h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                {/* Owner Card */}
                <div 
                  onClick={() => setCurrentStep('owner-login')}
                  className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white cursor-pointer hover:from-blue-600 hover:to-blue-700 transition-all duration-200 transform hover:scale-105 shadow-lg"
                >
                  <div className="text-center">
                    <div className="bg-white/20 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                      <User className="h-8 w-8" />
                    </div>
                    <h4 className="text-xl font-bold mb-2">Dueño</h4>
                    <p className="text-blue-100 text-sm">
                      Acceso completo al sistema con contraseña maestra
                    </p>
                  </div>
                </div>

                {/* Trainer Card */}
                <div 
                  onClick={() => setCurrentStep('trainer-selection')}
                  className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 text-white cursor-pointer hover:from-green-600 hover:to-green-700 transition-all duration-200 transform hover:scale-105 shadow-lg"
                >
                  <div className="text-center">
                    <div className="bg-white/20 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                      <Users className="h-8 w-8" />
                    </div>
                    <h4 className="text-xl font-bold mb-2">Profesor</h4>
                    <p className="text-green-100 text-sm">
                      Acceso operativo con selección de perfil individual
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Owner Login */}
          {currentStep === 'owner-login' && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full p-3 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                  <User className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Acceso de Dueño
                </h3>
                <p className="text-gray-600">
                  Ingresa la contraseña maestra para acceder al sistema completo
                </p>
              </div>

              <form onSubmit={ownerForm.handleSubmit(handleOwnerLogin)} className="space-y-6">
                <div>
                  <label htmlFor="owner-password" className="block text-sm font-medium text-gray-700 mb-2">
                    Contraseña Maestra
                  </label>
                  <div className="relative">
                    <input
                      {...ownerForm.register('password')}
                      type={showPassword ? 'text' : 'password'}
                      id="owner-password"
                      placeholder="Ingresa la contraseña maestra"
                      className={cn(
                        "w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                        (ownerForm.formState.errors.password || error) && "border-red-500 focus:ring-red-500 focus:border-red-500"
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
                  {ownerForm.formState.errors.password && (
                    <p className="mt-1 text-sm text-red-600">{ownerForm.formState.errors.password.message}</p>
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

              {/* Demo Info */}
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <h4 className="text-sm font-medium text-blue-800 mb-2">💡 Información de acceso:</h4>
                <div className="text-xs text-blue-700 space-y-1">
                  <p><strong>Contraseña maestra:</strong> 0000</p>
                  <p className="text-blue-600 italic">Ver README.md para cambiar la contraseña maestra</p>
                </div>
              </div>
            </div>
          )}

          {/* Trainer Selection */}
          {currentStep === 'trainer-selection' && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="bg-green-100 rounded-full p-3 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                  <Users className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Selecciona tu Perfil de Profesor
                </h3>
                <p className="text-gray-600">
                  Elige tu perfil de la lista de profesores disponibles
                </p>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mockTrainers.map((trainer) => (
                  <div
                    key={trainer.id}
                    onClick={() => handleTrainerSelect(trainer)}
                    className="bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-green-500 hover:shadow-md transition-all duration-200 transform hover:scale-105"
                  >
                    <div className="text-center">
                      <img
                        src={trainer.profile_picture}
                        alt={`${trainer.first_name} ${trainer.last_name}`}
                        className="w-16 h-16 rounded-full mx-auto mb-3 object-cover"
                      />
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {trainer.first_name} {trainer.last_name}
                      </h4>
                      <div className="flex flex-wrap justify-center gap-1">
                        {trainer.specialties.map((specialty, index) => (
                          <span
                            key={index}
                            className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full"
                          >
                            {specialty}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trainer Login */}
          {currentStep === 'trainer-login' && selectedTrainer && (
            <div className="space-y-6">
              <div className="text-center">
                <img
                  src={selectedTrainer.profile_picture}
                  alt={`${selectedTrainer.first_name} ${selectedTrainer.last_name}`}
                  className="w-20 h-20 rounded-full mx-auto mb-4 object-cover"
                />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {selectedTrainer.first_name} {selectedTrainer.last_name}
                </h3>
                <div className="flex justify-center gap-2 mb-4">
                  {selectedTrainer.specialties.map((specialty, index) => (
                    <span
                      key={index}
                      className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full"
                    >
                      {specialty}
                    </span>
                  ))}
                </div>
                <p className="text-gray-600">
                  Ingresa tu contraseña para acceder al sistema
                </p>
              </div>

              <form onSubmit={trainerForm.handleSubmit(handleTrainerLogin)} className="space-y-6">
                <div>
                  <label htmlFor="trainer-password" className="block text-sm font-medium text-gray-700 mb-2">
                    Contraseña
                  </label>
                  <div className="relative">
                    <input
                      {...trainerForm.register('password')}
                      type={showPassword ? 'text' : 'password'}
                      id="trainer-password"
                      placeholder="Ingresa tu contraseña"
                      className={cn(
                        "w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500",
                        (trainerForm.formState.errors.password || error) && "border-red-500 focus:ring-red-500 focus:border-red-500"
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
                  {trainerForm.formState.errors.password && (
                    <p className="mt-1 text-sm text-red-600">{trainerForm.formState.errors.password.message}</p>
                  )}
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={loading}
                >
                  {loading ? 'Iniciando sesión...' : 'Acceder como Profesor'}
                </Button>
              </form>

              {/* Demo Info */}
              <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
                <h4 className="text-sm font-medium text-green-800 mb-2">💡 Información de acceso:</h4>
                <div className="text-xs text-green-700 space-y-1">
                  <p><strong>Contraseña de prueba:</strong> password</p>
                  <p className="text-green-600 italic">Las contraseñas se gestionan desde el módulo de Usuarios</p>
                </div>
              </div>
            </div>
          )}
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