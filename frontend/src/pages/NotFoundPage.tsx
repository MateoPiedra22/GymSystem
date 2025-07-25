import { Link } from 'react-router-dom'
import { Home, ArrowLeft, Search, HelpCircle } from 'lucide-react'
import { Button } from '../components/ui/button'

export function NotFoundPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          {/* 404 Illustration */}
          <div className="mx-auto w-32 h-32 mb-8">
            <img
              src="https://trae-api-us.mchost.guru/api/ide/v1/text_to_image?prompt=404%20error%20page%20illustration%20modern%20minimalist&image_size=square"
              alt="404 Error"
              className="w-full h-full object-cover rounded-lg"
            />
          </div>
          
          {/* Error Message */}
          <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
          <h2 className="text-2xl font-semibold text-gray-700 mb-4">
            Página no encontrada
          </h2>
          <p className="text-gray-600 mb-8 max-w-md mx-auto">
            Lo sentimos, la página que estás buscando no existe o ha sido movida. 
            Verifica la URL o regresa al inicio.
          </p>
          
          {/* Action Buttons */}
          <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center">
            <Link to="/">
              <Button className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700">
                <Home className="h-4 w-4 mr-2" />
                Ir al Inicio
              </Button>
            </Link>
            <Button 
              variant="outline" 
              onClick={() => window.history.back()}
              className="w-full sm:w-auto"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Volver Atrás
            </Button>
          </div>
          
          {/* Help Section */}
          <div className="mt-12 pt-8 border-t border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              ¿Necesitas ayuda?
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-md mx-auto">
              <Link 
                to="/dashboard" 
                className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <Search className="h-4 w-4 mr-2" />
                Buscar en Dashboard
              </Link>
              <a 
                href="mailto:soporte@fitlifegym.com" 
                className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <HelpCircle className="h-4 w-4 mr-2" />
                Contactar Soporte
              </a>
            </div>
          </div>
          
          {/* Quick Links */}
          <div className="mt-8">
            <p className="text-sm text-gray-500 mb-4">Enlaces rápidos:</p>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <Link to="/users" className="text-indigo-600 hover:text-indigo-500">
                Usuarios
              </Link>
              <Link to="/payments" className="text-indigo-600 hover:text-indigo-500">
                Pagos
              </Link>
              <Link to="/classes" className="text-indigo-600 hover:text-indigo-500">
                Clases
              </Link>
              <Link to="/routines" className="text-indigo-600 hover:text-indigo-500">
                Rutinas
              </Link>
              <Link to="/employees" className="text-indigo-600 hover:text-indigo-500">
                Empleados
              </Link>
              <Link to="/community" className="text-indigo-600 hover:text-indigo-500">
                Comunidad
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage