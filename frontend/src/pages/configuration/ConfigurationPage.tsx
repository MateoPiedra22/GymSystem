import { useState, useEffect } from 'react'
import {
  Building,
  Bell,
  Shield,
  CreditCard,
  Mail,
  Smartphone,
  Globe,
  Save,
  RefreshCw,
  Eye,
  EyeOff,
  X,
  AlertTriangle,
  Loader2,
  Upload,
  Calendar
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { cn } from '../../utils/cn'
import { useConfigStore } from '../../store'

// Using types from config.ts - no need for local interfaces

// Mock data removed - now using real configStore data

const timezones = [
  'America/Argentina/Buenos_Aires',
  'America/New_York',
  'America/Los_Angeles',
  'Europe/Madrid',
  'Europe/London'
]

const currencies = ['ARS', 'USD', 'EUR', 'GBP']
const languages = [{ code: 'es', name: 'Español' }, { code: 'en', name: 'English' }]

export function ConfigurationPage() {
  const {
    systemConfig,
    brandConfig,
    notificationConfig,
    loading,
    error,
    getSystemConfig,
    getBrandConfig,
    getNotificationConfig,
    updateSystemConfig,
    updateBrandConfig,
    updateNotificationConfig,
    clearError
  } = useConfigStore()
  
  // Local state for form data
  const [localSystemConfig, setLocalSystemConfig] = useState<any>(null)
  const [localBrandConfig, setLocalBrandConfig] = useState<any>(null)
  
  // Update local state when store data changes
  useEffect(() => {
    if (systemConfig) {
      setLocalSystemConfig(systemConfig)
    }
  }, [systemConfig])
  
  useEffect(() => {
    if (brandConfig) {
      setLocalBrandConfig(brandConfig)
    }
  }, [brandConfig])
  
  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'security' | 'payments' | 'integrations'>('general')
  const [showSecrets, setShowSecrets] = useState<{ [key: string]: boolean }>({})
  const [hasChanges, setHasChanges] = useState(false)
  
  // Load configuration data on component mount
  useEffect(() => {
    getSystemConfig()
    getBrandConfig()
    getNotificationConfig()
  }, [])

  const handleSaveSettings = async () => {
    try {
      if (activeTab === 'general' && localSystemConfig) {
        await updateSystemConfig(localSystemConfig)
        if (localBrandConfig) {
          await updateBrandConfig(localBrandConfig)
        }
      } else if (activeTab === 'notifications' && notificationConfig) {
        await updateNotificationConfig(notificationConfig)
      }
      // Add other tabs as needed
      setHasChanges(false)
    } catch (error) {
      console.error('Error saving settings:', error)
    }
  }

  const toggleSecret = (key: string) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const maskSecret = (value: string, show: boolean) => {
    if (show || !value) return value
    return '•'.repeat(Math.min(value.length, 20))
  }

  const getDayName = (day: string) => {
    const days: { [key: string]: string } = {
      monday: 'Lunes',
      tuesday: 'Martes',
      wednesday: 'Miércoles',
      thursday: 'Jueves',
      friday: 'Viernes',
      saturday: 'Sábado',
      sunday: 'Domingo'
    }
    return days[day] || day
  }

  // Show loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
          <span className="text-gray-600">Cargando configuración...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-400 mr-2" />
            <span className="text-red-800">Error al cargar la configuración: {error}</span>
            <button
              onClick={clearError}
              className="ml-auto text-red-600 hover:text-red-800"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Configuración</h1>
          <p className="text-gray-600">Administra la configuración del gimnasio y sistema</p>
        </div>
        <div className="flex items-center space-x-3">
          {hasChanges && (
            <div className="flex items-center space-x-2 text-amber-600 bg-amber-50 px-3 py-2 rounded-md">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">Cambios sin guardar</span>
            </div>
          )}
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Restablecer
          </Button>
          <Button 
            onClick={handleSaveSettings}
            className="bg-indigo-600 hover:bg-indigo-700"
            disabled={!hasChanges}
          >
            <Save className="h-4 w-4 mr-2" />
            Guardar Cambios
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('general')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2",
                activeTab === 'general'
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              <Building className="h-4 w-4" />
              <span>General</span>
            </button>
            <button
              onClick={() => setActiveTab('notifications')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2",
                activeTab === 'notifications'
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              <Bell className="h-4 w-4" />
              <span>Notificaciones</span>
            </button>
            <button
              onClick={() => setActiveTab('security')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2",
                activeTab === 'security'
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              <Shield className="h-4 w-4" />
              <span>Seguridad</span>
            </button>
            <button
              onClick={() => setActiveTab('payments')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2",
                activeTab === 'payments'
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              <CreditCard className="h-4 w-4" />
              <span>Pagos</span>
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2",
                activeTab === 'integrations'
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              <Globe className="h-4 w-4" />
              <span>Integraciones</span>
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'general' && (
            <div className="space-y-8">
              {/* Basic Information */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Información Básica</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Nombre del Gimnasio
                    </label>
                    <input
                      type="text"
                      value={localSystemConfig?.gymName || ''}
                      onChange={(e) => {
                        setLocalSystemConfig((prev: any) => ({ ...prev, gymName: e.target.value }))
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Teléfono
                    </label>
                    <input
                      type="tel"
                      value={localSystemConfig?.phone || ''}
                      onChange={(e) => {
                        setLocalSystemConfig((prev: any) => ({ ...prev, phone: e.target.value }))
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={localSystemConfig?.email || ''}
                      onChange={(e) => {
                        setLocalSystemConfig((prev: any) => ({ ...prev, email: e.target.value }))
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sitio Web
                    </label>
                    <input
                      type="url"
                      value={localSystemConfig?.website || ''}
                      onChange={(e) => {
                        setLocalSystemConfig((prev: any) => ({ ...prev, website: e.target.value }))
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Descripción
                    </label>
                    <textarea
                      value={localSystemConfig?.gymDescription || ''}
                      onChange={(e) => {
                        setLocalSystemConfig((prev: any) => ({ ...prev, gymDescription: e.target.value }))
                        setHasChanges(true)
                      }}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Dirección
                    </label>
                    <input
                      type="text"
                      value={localSystemConfig?.address || ''}
                      onChange={(e) => {
                        setLocalSystemConfig((prev: any) => ({ ...prev, address: e.target.value }))
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
              </div>

              {/* Logo and Branding */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Logo y Marca</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Logo del Gimnasio
                    </label>
                    <div className="flex items-center space-x-4">
                      <img
                        src={localBrandConfig?.logoUrl || '/placeholder-logo.png'}
                        alt="Logo"
                        className="w-16 h-16 object-cover rounded-lg border border-gray-300"
                      />
                      <Button variant="outline" size="sm">
                        <Upload className="h-4 w-4 mr-2" />
                        Cambiar Logo
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Color Primario
                      </label>
                      <div className="flex items-center space-x-3">
                        <input
                          type="color"
                          value={localBrandConfig?.primaryColor || '#6366f1'}
                          onChange={(e) => {
                            setLocalBrandConfig((prev: any) => ({ ...prev, primaryColor: e.target.value }))
                            setHasChanges(true)
                          }}
                          className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                        />
                        <input
                          type="text"
                          value={localBrandConfig?.primaryColor || '#6366f1'}
                          onChange={(e) => {
                            setLocalBrandConfig((prev: any) => ({ ...prev, primaryColor: e.target.value }))
                            setHasChanges(true)
                          }}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Color Secundario
                      </label>
                      <div className="flex items-center space-x-3">
                        <input
                          type="color"
                          value={localBrandConfig?.secondaryColor || '#f59e0b'}
                          onChange={(e) => {
                            setLocalBrandConfig((prev: any) => ({ ...prev, secondaryColor: e.target.value }))
                            setHasChanges(true)
                          }}
                          className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                        />
                        <input
                          type="text"
                          value={localBrandConfig?.secondaryColor || '#f59e0b'}
                          onChange={(e) => {
                            setLocalBrandConfig((prev: any) => ({ ...prev, secondaryColor: e.target.value }))
                            setHasChanges(true)
                          }}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Regional Settings */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuración Regional</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Zona Horaria
                    </label>
                    <select
                      value={systemConfig?.timezone || 'America/Argentina/Buenos_Aires'}
                      onChange={() => {
                            setHasChanges(true)
                          }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {timezones.map(tz => (
                        <option key={tz} value={tz}>{tz}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Moneda
                    </label>
                    <select
                      value={systemConfig?.currency || 'ARS'}
                      onChange={() => {
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {currencies.map(currency => (
                        <option key={currency} value={currency}>{currency}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Idioma
                    </label>
                    <select
                      value={systemConfig?.language || 'es'}
                      onChange={() => {
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {languages.map(lang => (
                        <option key={lang.code} value={lang.code}>{lang.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Operating Hours */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Horarios de Funcionamiento</h3>
                <div className="space-y-4">
                  {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map((day) => {
                    const hours = systemConfig?.businessHours?.[day as keyof typeof systemConfig.businessHours] || { isOpen: true, openTime: '06:00', closeTime: '22:00' }
                    return (
                      <div key={day} className="flex items-center space-x-4">
                        <div className="w-24">
                          <span className="text-sm font-medium text-gray-700">{getDayName(day)}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={hours.isOpen}
                            onChange={() => {
                              setHasChanges(true)
                            }}
                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="text-sm text-gray-600">Abierto</span>
                        </div>
                        {hours.isOpen && (
                          <>
                            <input
                              type="time"
                              value={hours.openTime || '06:00'}
                              onChange={() => {
                                setHasChanges(true)
                              }}
                              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                            <span className="text-gray-500">a</span>
                            <input
                              type="time"
                              value={hours.closeTime || '22:00'}
                              onChange={() => {
                                setHasChanges(true)
                              }}
                              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                          </>
                        )}
                        {!hours.isOpen && (
                          <span className="text-sm text-gray-500 italic">Cerrado</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuración de Notificaciones</h3>
                <div className="space-y-6">
                  {[
                    { key: 'emailNotifications', label: 'Notificaciones por Email' },
                    { key: 'smsNotifications', label: 'Notificaciones por SMS' },
                    { key: 'pushNotifications', label: 'Notificaciones Push' },
                    { key: 'marketingEmails', label: 'Emails de Marketing' },
                    { key: 'classReminders', label: 'Recordatorios de Clases' },
                    { key: 'paymentReminders', label: 'Recordatorios de Pago' },
                    { key: 'membershipExpiry', label: 'Vencimiento de Membresías' },
                    { key: 'newMemberWelcome', label: 'Bienvenida a Nuevos Miembros' }
                  ].map(({ key, label }) => {
                    const value = notificationConfig?.[key as keyof typeof notificationConfig] || false
                    
                    return (
                      <div key={key} className="flex items-center justify-between py-3 border-b border-gray-200 last:border-b-0">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">{label}</h4>
                        </div>
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={Boolean(value)}
                            onChange={() => {
                              setHasChanges(true)
                            }}
                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuración de Seguridad</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Días para expiración de contraseña
                    </label>
                    <input
                      type="number"
                      value={90}
                      onChange={() => {
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Máximo intentos de login
                    </label>
                    <input
                      type="number"
                      value={5}
                      onChange={() => {
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Timeout de sesión (minutos)
                    </label>
                    <input
                      type="number"
                      value={30}
                      onChange={() => {
                        setHasChanges(true)
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>
                
                <div className="space-y-4 mt-6">
                  {[
                    { key: 'twoFactorAuth', label: 'Autenticación de dos factores' },
                    { key: 'requirePasswordChange', label: 'Requerir cambio de contraseña' },
                    { key: 'allowMultipleSessions', label: 'Permitir múltiples sesiones' }
                  ].map(({ key, label }) => (
                    <div key={key} className="flex items-center justify-between py-3 border-b border-gray-200 last:border-b-0">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">{label}</h4>
                      </div>
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={Boolean(systemConfig?.[key as keyof typeof systemConfig])}
                          onChange={() => {
                            setHasChanges(true)
                          }}
                          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'payments' && (
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Métodos de Pago</h3>
                <div className="space-y-6">
                  {/* Stripe */}
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-md font-medium text-gray-900">Stripe</h4>
                      <input
                        type="checkbox"
                        checked={systemConfig?.integrations?.paymentGateway?.provider === 'stripe' || false}
                        onChange={() => {
                          setHasChanges(true)
                        }}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>
                    {systemConfig?.integrations?.paymentGateway?.provider === 'stripe' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Clave Pública
                          </label>
                          <input
                            type="text"
                            value={systemConfig?.integrations?.paymentGateway?.publicKey || ''}
                            onChange={() => {
                              setHasChanges(true)
                            }}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Clave Secreta
                          </label>
                          <div className="relative">
                            <input
                              type={showSecrets['stripe_secret'] ? 'text' : 'password'}
                              value={maskSecret(systemConfig?.integrations?.paymentGateway?.publicKey || '', showSecrets['stripe_secret'])}
                              onChange={() => {
                                setHasChanges(true)
                              }}
                              className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                            <button
                              type="button"
                              onClick={() => toggleSecret('stripe_secret')}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center"
                            >
                              {showSecrets['stripe_secret'] ? (
                                <EyeOff className="h-4 w-4 text-gray-400" />
                              ) : (
                                <Eye className="h-4 w-4 text-gray-400" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* MercadoPago */}
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-md font-medium text-gray-900">MercadoPago</h4>
                      <input
                        type="checkbox"
                        checked={systemConfig?.integrations?.paymentGateway?.provider === 'paypal' || false}
                        onChange={() => {
                          setHasChanges(true)
                        }}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>
                    {systemConfig?.integrations?.paymentGateway?.provider === 'paypal' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Clave Pública
                          </label>
                          <input
                            type="text"
                            value={systemConfig?.integrations?.paymentGateway?.publicKey || ''}
                            onChange={() => {
                              setHasChanges(true)
                            }}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Access Token
                          </label>
                          <div className="relative">
                            <input
                              type={showSecrets['mp_token'] ? 'text' : 'password'}
                              value={maskSecret(systemConfig?.integrations?.paymentGateway?.publicKey || '', showSecrets['mp_token'])}
                              onChange={() => {
                                setHasChanges(true)
                              }}
                              className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                            <button
                              type="button"
                              onClick={() => toggleSecret('mp_token')}
                              className="absolute inset-y-0 right-0 pr-3 flex items-center"
                            >
                              {showSecrets['mp_token'] ? (
                                <EyeOff className="h-4 w-4 text-gray-400" />
                              ) : (
                                <Eye className="h-4 w-4 text-gray-400" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Other Payment Methods */}
                  <div className="space-y-4">
                    {[
                      { key: 'cash_payments', label: 'Pagos en Efectivo' },
                      { key: 'bank_transfer', label: 'Transferencia Bancaria' }
                    ].map(({ key, label }) => (
                      <div key={key} className="flex items-center justify-between py-3 border-b border-gray-200 last:border-b-0">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">{label}</h4>
                        </div>
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={Boolean(systemConfig?.[key as keyof typeof systemConfig])}
                            onChange={() => {
                              setHasChanges(true)
                            }}
                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Payment Policies */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Recargo por mora (%)
                      </label>
                      <input
                        type="number"
                        value={0}
                        onChange={() => {
                          setHasChanges(true)
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Período de gracia (días)
                      </label>
                      <input
                        type="number"
                        value={0}
                        onChange={() => {
                          setHasChanges(true)
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Integraciones Externas</h3>
                <div className="space-y-6">
                  {/* WhatsApp */}
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <Smartphone className="h-5 w-5 text-green-600" />
                        <h4 className="text-md font-medium text-gray-900">WhatsApp Business</h4>
                      </div>
                      <input
                        type="checkbox"
                        checked={systemConfig?.integrations?.socialMedia?.facebook ? true : false}
                        onChange={() => {
                          setHasChanges(true)
                        }}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>
                    {systemConfig?.integrations?.socialMedia?.facebook && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Token de API
                          </label>
                          <input
                            type="text"
                            value={systemConfig?.integrations?.smsService?.fromNumber || ''}
                            onChange={() => {
                              setHasChanges(true)
                            }}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Número de Teléfono
                          </label>
                          <input
                            type="tel"
                            value={systemConfig?.phone || ''}
                            onChange={() => {
                              setHasChanges(true)
                            }}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Instagram */}
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-5 h-5 bg-gradient-to-r from-purple-500 to-pink-500 rounded" />
                        <h4 className="text-md font-medium text-gray-900">Instagram</h4>
                      </div>
                      <input
                        type="checkbox"
                        checked={systemConfig?.integrations?.socialMedia?.instagram ? true : false}
                        onChange={() => {
                          setHasChanges(true)
                        }}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>
                    {systemConfig?.integrations?.socialMedia?.instagram && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Access Token
                        </label>
                        <input
                          type="text"
                          value={systemConfig?.integrations?.socialMedia?.instagram || ''}
                          onChange={() => {
                            setHasChanges(true)
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    )}
                  </div>

                  {/* Google Calendar */}
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <Calendar className="h-5 w-5 text-blue-600" />
                        <h4 className="text-md font-medium text-gray-900">Google Calendar</h4>
                      </div>
                      <input
                        type="checkbox"
                        checked={systemConfig?.integrations?.calendarSync?.isActive || false}
                        onChange={() => {
                          setHasChanges(true)
                        }}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>
                    {systemConfig?.integrations?.calendarSync?.isActive && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Calendar ID
                        </label>
                        <input
                          type="text"
                          value={systemConfig?.integrations?.calendarSync?.provider || ''}
                          onChange={() => {
                            setHasChanges(true)
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                      </div>
                    )}
                  </div>

                  {/* Mailchimp */}
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <Mail className="h-5 w-5 text-yellow-600" />
                        <h4 className="text-md font-medium text-gray-900">Mailchimp</h4>
                      </div>
                      <input
                        type="checkbox"
                        checked={systemConfig?.integrations?.emailService?.isActive || false}
                        onChange={() => {
                          setHasChanges(true)
                        }}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>
                    {systemConfig?.integrations?.emailService?.isActive && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          API Key
                        </label>
                        <div className="relative">
                          <input
                            type={showSecrets['mailchimp_key'] ? 'text' : 'password'}
                            value={maskSecret(systemConfig?.integrations?.emailService?.username || '', showSecrets['mailchimp_key'])}
                            onChange={() => {
                              setHasChanges(true)
                            }}
                            className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          />
                          <button
                            type="button"
                            onClick={() => toggleSecret('mailchimp_key')}
                            className="absolute inset-y-0 right-0 pr-3 flex items-center"
                          >
                            {showSecrets['mailchimp_key'] ? (
                              <EyeOff className="h-4 w-4 text-gray-400" />
                            ) : (
                              <Eye className="h-4 w-4 text-gray-400" />
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ConfigurationPage