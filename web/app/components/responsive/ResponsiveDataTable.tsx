'use client'

import { useState, useMemo } from 'react'
import { useResponsive } from './ResponsiveWrapper'
import { Icons } from '../ui/Icons'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Badge } from '../ui/Badge'
import { cn } from '../../utils/cn'

interface Column {
  key: string
  label: string
  sortable?: boolean
  width?: string
  className?: string
  render?: (value: any, row: any, index: number) => React.ReactNode
  mobileRender?: (value: any, row: any, index: number) => React.ReactNode
  hideOnMobile?: boolean
  priority?: number // 1 = alta prioridad, 3 = baja prioridad
}

interface ResponsiveDataTableProps {
  data: any[]
  columns: Column[]
  keyField?: string
  searchable?: boolean
  searchPlaceholder?: string
  sortable?: boolean
  loading?: boolean
  emptyMessage?: string
  className?: string
  onRowClick?: (row: any, index: number) => void
  showPagination?: boolean
  itemsPerPage?: number
}

// Hook personalizado para manejo de datos
function useTableData(
  data: any[],
  searchTerm: string,
  sortConfig: { key: string; direction: 'asc' | 'desc' } | null,
  currentPage: number,
  itemsPerPage: number,
  showPagination: boolean
) {
  // Filtrar datos por búsqueda
  const filteredData = useMemo(() => {
    if (!searchTerm) return data

    return data.filter(row =>
      Object.values(row).some(value =>
        String(value).toLowerCase().includes(searchTerm.toLowerCase())
      )
    )
  }, [data, searchTerm])

  // Ordenar datos
  const sortedData = useMemo(() => {
    if (!sortConfig) return filteredData

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortConfig.key]
      const bValue = b[sortConfig.key]

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1
      }
      return 0
    })
  }, [filteredData, sortConfig])

  // Paginar datos
  const paginatedData = useMemo(() => {
    if (!showPagination) return sortedData

    const startIndex = (currentPage - 1) * itemsPerPage
    return sortedData.slice(startIndex, startIndex + itemsPerPage)
  }, [sortedData, currentPage, itemsPerPage, showPagination])

  return { filteredData, sortedData, paginatedData }
}

// Componente para la barra de búsqueda
function SearchBar({ 
  searchable, 
  searchTerm, 
  setSearchTerm, 
  searchPlaceholder, 
  resultCount 
}: {
  searchable: boolean
  searchTerm: string
  setSearchTerm: (term: string) => void
  searchPlaceholder: string
  resultCount: number
}) {
  if (!searchable) return null

  return (
    <div className="flex items-center space-x-4">
      <div className="flex-1 max-w-md">
        <Input
          type="search"
          placeholder={searchPlaceholder}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full"
        />
      </div>
      <div className="text-sm text-gray-600">
        {resultCount} resultado{resultCount !== 1 ? 's' : ''}
      </div>
    </div>
  )
}

// Componente para el estado de carga
function LoadingState() {
  return (
    <div className="flex items-center justify-center py-12">
      <Icons.Status.Loading size="lg" className="animate-spin text-blue-600" />
    </div>
  )
}

// Componente para el estado vacío
function EmptyState({ 
  emptyMessage, 
  searchTerm, 
  onClearSearch 
}: {
  emptyMessage: string
  searchTerm: string
  onClearSearch: () => void
}) {
  return (
    <div className="text-center py-12">
      <div className="text-gray-500 text-lg font-medium">
        {emptyMessage}
      </div>
      {searchTerm && (
        <button
          onClick={onClearSearch}
          className="mt-2 text-blue-600 hover:text-blue-700 text-sm"
        >
          Limpiar búsqueda
        </button>
      )}
    </div>
  )
}

// Componente para renderizado móvil
function MobileCardView({ 
  data, 
  columns, 
  keyField, 
  onRowClick 
}: {
  data: any[]
  columns: Column[]
  keyField: string
  onRowClick?: (row: any, index: number) => void
}) {
  return (
    <div className="space-y-3">
      {data.map((row, index) => (
        <div
          key={row[keyField] || index}
          className={cn(
            "bg-white border border-gray-200 rounded-lg p-4 space-y-3 shadow-sm",
            onRowClick && "cursor-pointer hover:shadow-md transition-shadow"
          )}
          onClick={onRowClick ? () => onRowClick(row, index) : undefined}
        >
          {columns.map(column => {
            const value = row[column.key]
            
            if (column.hideOnMobile) return null

            return (
              <div key={column.key} className="flex justify-between items-start">
                <span className="text-sm font-medium text-gray-600 flex-shrink-0">
                  {column.label}:
                </span>
                <span className="text-sm text-gray-900 ml-2 text-right">
                  {column.mobileRender ? column.mobileRender(value, row, index) : 
                   column.render ? column.render(value, row, index) : 
                   String(value)}
                </span>
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

// Componente para la tabla tradicional
function TableView({ 
  data, 
  columns, 
  keyField, 
  sortConfig, 
  onSort, 
  sortable, 
  onRowClick 
}: {
  data: any[]
  columns: Column[]
  keyField: string
  sortConfig: { key: string; direction: 'asc' | 'desc' } | null
  onSort: (columnKey: string) => void
  sortable: boolean
  onRowClick?: (row: any, index: number) => void
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map(column => (
                <th
                  key={column.key}
                  className={cn(
                    "px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    column.sortable && sortable && "cursor-pointer hover:bg-gray-100",
                    column.className
                  )}
                  style={{ width: column.width }}
                  onClick={() => column.sortable && onSort(column.key)}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.label}</span>
                    {column.sortable && sortable && (
                      <div className="flex flex-col">
                        <Icons.Analytics.TrendUp 
                          size="xs" 
                          className={cn(
                            "transition-colors",
                            sortConfig?.key === column.key && sortConfig.direction === 'asc'
                              ? "text-blue-600" 
                              : "text-gray-400"
                          )}
                        />
                        <Icons.Analytics.TrendDown 
                          size="xs" 
                          className={cn(
                            "transition-colors -mt-1",
                            sortConfig?.key === column.key && sortConfig.direction === 'desc'
                              ? "text-blue-600" 
                              : "text-gray-400"
                          )}
                        />
                      </div>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, index) => (
              <tr
                key={row[keyField] || index}
                className={cn(
                  "hover:bg-gray-50 transition-colors",
                  onRowClick && "cursor-pointer"
                )}
                onClick={onRowClick ? () => onRowClick(row, index) : undefined}
              >
                {columns.map(column => {
                  const value = row[column.key]
                  return (
                    <td
                      key={column.key}
                      className={cn("px-6 py-4 whitespace-nowrap text-sm", column.className)}
                    >
                      {column.render ? column.render(value, row, index) : String(value)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Componente para paginación
function Pagination({ 
  currentPage, 
  totalPages, 
  totalItems, 
  itemsPerPage, 
  onPageChange 
}: {
  currentPage: number
  totalPages: number
  totalItems: number
  itemsPerPage: number
  onPageChange: (page: number) => void
}) {
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-white border border-gray-200 rounded-lg">
      <div className="text-sm text-gray-700">
        Mostrando {((currentPage - 1) * itemsPerPage) + 1} a{' '}
        {Math.min(currentPage * itemsPerPage, totalItems)} de{' '}
        {totalItems} resultados
      </div>
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
        >
          Anterior
        </Button>
        <span className="text-sm font-medium">
          Página {currentPage} de {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
        >
          Siguiente
        </Button>
      </div>
    </div>
  )
}

export function ResponsiveDataTable({
  data,
  columns,
  keyField = 'id',
  searchable = true,
  searchPlaceholder = 'Buscar...',
  sortable = true,
  loading = false,
  emptyMessage = 'No hay datos disponibles',
  className,
  onRowClick,
  showPagination = false,
  itemsPerPage = 10
}: ResponsiveDataTableProps) {
  const { isMobile, isTablet } = useResponsive()
  const [searchTerm, setSearchTerm] = useState('')
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  // Usar hook personalizado para manejo de datos
  const { sortedData, paginatedData } = useTableData(
    data,
    searchTerm,
    sortConfig,
    currentPage,
    itemsPerPage,
    showPagination
  )

  // Manejar ordenamiento
  const handleSort = (columnKey: string) => {
    if (!sortable) return

    setSortConfig(prevConfig => {
      if (prevConfig?.key === columnKey) {
        if (prevConfig.direction === 'asc') {
          return { key: columnKey, direction: 'desc' }
        } else {
          return null // Quitar ordenamiento
        }
      } else {
        return { key: columnKey, direction: 'asc' }
      }
    })
  }

  // Obtener columnas visibles según el dispositivo
  const visibleColumns = useMemo(() => {
    if (!isMobile && !isTablet) return columns

    // En móviles, mostrar solo columnas de alta prioridad
    if (isMobile) {
      return columns.filter(col => !col.hideOnMobile && (col.priority ?? 1) <= 2)
    }

    // En tablets, mostrar columnas de prioridad media y alta
    if (isTablet) {
      return columns.filter(col => (col.priority ?? 1) <= 3)
    }

    return columns
  }, [columns, isMobile, isTablet])

  const totalPages = Math.ceil(sortedData.length / itemsPerPage)

  return (
    <div className={cn("space-y-4", className)}>
      {/* Barra de búsqueda */}
      <SearchBar
        searchable={searchable}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        searchPlaceholder={searchPlaceholder}
        resultCount={sortedData.length}
      />

      {/* Estado de carga */}
      {loading && <LoadingState />}

      {/* Estado vacío */}
      {!loading && paginatedData.length === 0 && (
        <EmptyState
          emptyMessage={emptyMessage}
          searchTerm={searchTerm}
          onClearSearch={() => setSearchTerm('')}
        />
      )}

      {/* Contenido principal */}
      {!loading && paginatedData.length > 0 && (
        <>
          {isMobile ? (
            <MobileCardView
              data={paginatedData}
              columns={visibleColumns}
              keyField={keyField}
              onRowClick={onRowClick}
            />
          ) : (
            <TableView
              data={paginatedData}
              columns={visibleColumns}
              keyField={keyField}
              sortConfig={sortConfig}
              onSort={handleSort}
              sortable={sortable}
              onRowClick={onRowClick}
            />
          )}

          {/* Paginación */}
          {showPagination && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={sortedData.length}
              itemsPerPage={itemsPerPage}
              onPageChange={setCurrentPage}
            />
          )}
        </>
      )}
    </div>
  )
}

// Componente de ejemplo de uso
export function ExampleUsage() {
  const sampleData = [
    { id: 1, nombre: 'Juan Pérez', email: 'juan@email.com', estado: 'activo', fechaRegistro: '2024-01-15' },
    { id: 2, nombre: 'María García', email: 'maria@email.com', estado: 'inactivo', fechaRegistro: '2024-01-10' },
    { id: 3, nombre: 'Carlos López', email: 'carlos@email.com', estado: 'activo', fechaRegistro: '2024-01-20' },
  ]

  const columns: Column[] = [
    {
      key: 'nombre',
      label: 'Nombre',
      sortable: true,
      priority: 1,
      render: (value) => <span className="font-medium">{value}</span>
    },
    {
      key: 'email',
      label: 'Email',
      priority: 2,
      hideOnMobile: false,
      className: 'text-gray-600'
    },
    {
      key: 'estado',
      label: 'Estado',
      priority: 1,
      render: (value) => (
        <Badge variant={value === 'activo' ? 'success' : 'secondary'}>
          {value}
        </Badge>
      ),
             mobileRender: (value) => (
         <Badge variant={value === 'activo' ? 'success' : 'secondary'}>
           {value}
         </Badge>
       )
    },
    {
      key: 'fechaRegistro',
      label: 'Fecha Registro',
      priority: 3,
      hideOnMobile: true,
      sortable: true
    }
  ]

  return (
    <ResponsiveDataTable
      data={sampleData}
      columns={columns}
      searchable={true}
      sortable={true}
      showPagination={true}
      itemsPerPage={5}
      onRowClick={(row) => {
        // Handle row click
      }}
    />
  )
} 