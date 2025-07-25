import { useState, useEffect, useCallback } from 'react'
import {
  Search,
  Filter,
  Plus,
  Download,
  Users,
  UserCheck,
  Calendar,
  Phone,
  Mail,
  Star,
  Eye,
  Edit,
  MoreHorizontal,
  DollarSign,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { cn } from '../../utils/cn'
import { useEmployeeStore } from '../../store'
import { Employee } from '../../types'
import { debounce } from 'lodash'

// Using Employee type from types/employee.ts

// Mock data removed - now using real store data

const roles = ['Todos', 'admin', 'owner', 'trainer', 'member']
const departments = ['Todos', 'Entrenamiento', 'Administración', 'Mantenimiento', 'Gerencia']
const statusOptions = ['Todos', 'active', 'inactive', 'suspended', 'pending']

export function EmployeesPage() {
  const {
    employees,
    loading,
    error,
    employeePagination,
    getEmployees,
    employeeStats
  } = useEmployeeStore()
  
  const [filteredEmployees, setFilteredEmployees] = useState<Employee[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRole, setSelectedRole] = useState('Todos')
  const [selectedDepartment, setSelectedDepartment] = useState('Todos')
  const [selectedStatus, setSelectedStatus] = useState('Todos')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedEmployees, setSelectedEmployees] = useState<number[]>([])
  const [employeesPerPage] = useState(10)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list')

  // Load employees on component mount
  useEffect(() => {
    getEmployees()
  }, [])

  // Search with debounce
  const handleSearch = useCallback(
    debounce((term: string) => {
      if (term.trim()) {
        getEmployees({ search: term })
      } else {
        getEmployees()
      }
    }, 300),
    [getEmployees]
  )

  // Handle page change
  const handlePageChange = (page: number) => {
    if (searchTerm.trim()) {
      getEmployees({ search: searchTerm, page, limit: employeesPerPage })
    } else {
      getEmployees({ page, limit: employeesPerPage })
    }
  }

  // Filter employees based on search and filters
  useEffect(() => {
    if (!employees) {
      setFilteredEmployees([])
      return
    }

    let filtered = employees

    // Role filter
    if (selectedRole !== 'Todos') {
      filtered = filtered.filter(employee => employee.role === selectedRole)
    }

    // Department filter
    if (selectedDepartment !== 'Todos') {
      filtered = filtered.filter(employee => employee.department === selectedDepartment)
    }

    // Status filter
    if (selectedStatus !== 'Todos') {
      filtered = filtered.filter(employee => employee.status === selectedStatus)
    }

    setFilteredEmployees(filtered)
  }, [employees, selectedRole, selectedDepartment, selectedStatus])

  // Pagination - use store data or local filtered data
  const finalTotalPages = employeePagination.totalPages || Math.ceil(filteredEmployees.length / employeesPerPage)
  const currentPage = employeePagination.page || 1
  const indexOfLastEmployee = currentPage * employeesPerPage
  const indexOfFirstEmployee = indexOfLastEmployee - employeesPerPage
  const currentEmployees = searchTerm.trim() ? 
    (employees || []) : 
    filteredEmployees.slice(indexOfFirstEmployee, indexOfLastEmployee)

  const handleSelectEmployee = (employeeId: number) => {
    setSelectedEmployees(prev =>
      prev.includes(employeeId)
        ? prev.filter(id => id !== employeeId)
        : [...prev, employeeId]
    )
  }

  const handleSelectAll = () => {
    if (selectedEmployees.length === currentEmployees.length) {
      setSelectedEmployees([])
    } else {
      setSelectedEmployees(currentEmployees.map(employee => employee.id))
    }
  }

  const getRoleText = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrador'
      case 'owner':
        return 'Propietario'
      case 'trainer':
        return 'Entrenador'
      case 'member':
        return 'Miembro'
      default:
        return 'Desconocido'
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-100 text-purple-800'
      case 'owner':
        return 'bg-yellow-100 text-yellow-800'
      case 'trainer':
        return 'bg-blue-100 text-blue-800'
      case 'member':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Activo'
      case 'inactive':
        return 'Inactivo'
      case 'suspended':
        return 'Suspendido'
      case 'pending':
        return 'Pendiente'
      default:
        return 'Desconocido'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'inactive':
        return 'bg-gray-100 text-gray-800'
      case 'suspended':
        return 'bg-red-100 text-red-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
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

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={cn(
          "h-3 w-3",
          i < Math.floor(rating) ? "text-yellow-400 fill-current" : "text-gray-300"
        )}
      />
    ))
  }

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestión de Empleados</h1>
          <p className="text-gray-600">Administra el personal, horarios y rendimiento del equipo</p>
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
          <Button className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Empleado
          </Button>
        </div>
      </div>

      {/* Loading and Error States */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Cargando empleados...</span>
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
              <p className="text-sm font-medium text-gray-600">Total Empleados</p>
              <p className="text-2xl font-bold text-gray-900">{employeeStats?.total_employees || 0}</p>
            </div>
            <div className="bg-indigo-500 p-2 rounded-lg">
              <Users className="h-5 w-5 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Empleados Activos</p>
              <p className="text-2xl font-bold text-gray-900">{employeeStats?.active_employees || 0}</p>
            </div>
            <div className="bg-green-500 p-2 rounded-lg">
              <UserCheck className="h-5 w-5 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Rendimiento Promedio</p>
              <p className="text-2xl font-bold text-gray-900">{employeeStats?.avg_performance || 0}</p>
            </div>
            <div className="bg-yellow-500 p-2 rounded-lg">
              <Star className="h-5 w-5 text-white" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Nómina Total</p>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(employeeStats?.total_payroll || 0)}</p>
            </div>
            <div className="bg-purple-500 p-2 rounded-lg">
              <DollarSign className="h-5 w-5 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar empleados por nombre, email, teléfono o especialización..."
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rol
              </label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {roles.map(role => (
                  <option key={role} value={role}>
                    {role === 'Todos' ? 'Todos' : getRoleText(role)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Departamento
              </label>
              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {departments.map(department => (
                  <option key={department} value={department}>{department}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Estado
              </label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {statusOptions.map(status => (
                  <option key={status} value={status}>
                    {status === 'Todos' ? 'Todos' : getStatusText(status)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* View Mode Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-700">Vista:</span>
          <div className="flex border border-gray-300 rounded-md">
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="rounded-r-none"
            >
              Lista
            </Button>
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="rounded-l-none"
            >
              Tarjetas
            </Button>
          </div>
        </div>
        <div className="text-sm text-gray-600">
          {filteredEmployees.length} empleados encontrados
        </div>
      </div>

      {/* Employees Grid/List */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {currentEmployees.map((employee) => (
            <div key={employee.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                    {employee.profile_picture ? (
                      <img
                        src={employee.profile_picture}
                        alt={`${employee.first_name} ${employee.last_name}`}
                        className="w-full h-full object-cover rounded-full"
                      />
                    ) : (
                      <span className="text-indigo-600 font-medium">
                        {getInitials(employee.first_name, employee.last_name)}
                      </span>
                    )}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {employee.first_name} {employee.last_name}
                    </h3>
                    <p className="text-sm text-gray-600">{employee.role}</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={selectedEmployees.includes(employee.id)}
                  onChange={() => handleSelectEmployee(employee.id)}
                  className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className={cn(
                    "inline-flex px-2 py-1 text-xs font-semibold rounded-full",
                    getRoleColor(employee.role)
                  )}>
                    {getRoleText(employee.role)}
                  </span>
                  <span className={cn(
                     "inline-flex px-2 py-1 text-xs font-semibold rounded-full",
                     getStatusColor(employee.status)
                   )}>
                     {getStatusText(employee.status)}
                   </span>
                </div>

                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Mail className="h-4 w-4" />
                  <span>{employee.email}</span>
                </div>

                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Phone className="h-4 w-4" />
                  <span>{employee.phone}</span>
                </div>

                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Calendar className="h-4 w-4" />
                  <span>Desde {formatDate(employee.hire_date)}</span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    {renderStars(employee.performance_rating || 0)}
                    <span className="text-xs text-gray-600 ml-1">({employee.performance_rating || 0})</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {formatCurrency(employee.salary || 0)}
                  </span>
                </div>



                <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                  <div className="text-xs text-gray-500">
                    {employee.department}
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
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                Empleados ({filteredEmployees.length})
              </h3>
              {selectedEmployees.length > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">
                    {selectedEmployees.length} seleccionados
                  </span>
                  <Button variant="outline" size="sm">
                    Acciones en lote
                  </Button>
                </div>
              )}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedEmployees.length === currentEmployees.length && currentEmployees.length > 0}
                      onChange={handleSelectAll}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Empleado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contacto
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Departamento
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rendimiento
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Salario
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {currentEmployees.map((employee) => (
                  <tr key={employee.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <input
                        type="checkbox"
                        checked={selectedEmployees.includes(employee.id)}
                        onChange={() => handleSelectEmployee(employee.id)}
                        className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                          {employee.profile_picture ? (
                            <img
                              src={employee.profile_picture}
                              alt={`${employee.first_name} ${employee.last_name}`}
                              className="w-full h-full object-cover rounded-full"
                            />
                          ) : (
                            <span className="text-indigo-600 font-medium text-sm">
                              {getInitials(employee.first_name, employee.last_name)}
                            </span>
                          )}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">
                            {employee.first_name} {employee.last_name}
                          </p>
                          <p className="text-sm text-gray-500">{employee.role}</p>
                          <p className="text-xs text-gray-400">Desde {formatDate(employee.hire_date)}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        "inline-flex px-2 py-1 text-xs font-semibold rounded-full",
                        getRoleColor(employee.role)
                      )}>
                        {getRoleText(employee.role)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2 text-sm text-gray-900">
                          <Mail className="h-3 w-3 text-gray-400" />
                          <span>{employee.email}</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm text-gray-500">
                          <Phone className="h-3 w-3 text-gray-400" />
                          <span>{employee.phone}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {employee.department}
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                         "inline-flex px-2 py-1 text-xs font-semibold rounded-full",
                         getStatusColor(employee.status)
                       )}>
                         {getStatusText(employee.status)}
                       </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-1">
                        {renderStars(employee.performance_rating || 0)}
                        <span className="text-xs text-gray-600 ml-1">({employee.performance_rating || 0})</span>
                      </div>

                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {formatCurrency(employee.salary || 0)}
                    </td>
                    <td className="px-6 py-4">
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
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {finalTotalPages > 1 && (
            <div className="px-6 py-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Mostrando {indexOfFirstEmployee + 1} a {Math.min(indexOfLastEmployee, searchTerm.trim() ? (employees?.length || 0) : filteredEmployees.length)} de {searchTerm.trim() ? (employees?.length || 0) : filteredEmployees.length} empleados
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1 || loading}
                  >
                    Anterior
                  </Button>
                  <span className="text-sm text-gray-700">
                    Página {currentPage} de {finalTotalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === finalTotalPages || loading}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EmployeesPage