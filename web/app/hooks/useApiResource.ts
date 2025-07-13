'use client'

import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../utils/api'

// Tipos optimizados
export interface ApiResourceOptions {
  endpoint: string
  params?: Record<string, any>
  enabled?: boolean
  refetchInterval?: number
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
  staleTime?: number
  gcTime?: number
  retryCount?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pages: number
  per_page: number
  has_next: boolean
  has_prev: boolean
}

export interface UseApiResourceReturn<T> {
  data: T | null
  loading: boolean
  error: string | null
  isStale: boolean
  isFetching: boolean
  refetch: () => Promise<void>
  refresh: () => Promise<void>
}

// Hook optimizado con React Query
export function useApiResource<T = any>(
  options: ApiResourceOptions
): UseApiResourceReturn<T> {
  const queryClient = useQueryClient()
  
  // Generar clave única para la query
  const queryKey = useMemo(() => [
    'api-resource',
    options.endpoint,
    options.params || {}
  ], [options.endpoint, options.params])

  // Función de fetch optimizada
  const queryFn = useCallback(async (): Promise<T> => {
    try {
      // Construir URL con parámetros
      let url = options.endpoint
      if (options.params && Object.keys(options.params).length > 0) {
        const searchParams = new URLSearchParams()
        Object.entries(options.params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            searchParams.append(key, String(value))
          }
        })
        url += `?${searchParams.toString()}`
      }

      const response = await api.get(url)
      const result = response.data
      
      // Callback de éxito
      if (options.onSuccess) {
        options.onSuccess(result)
      }
      
      return result
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Error desconocido')
      
      // Callback de error
      if (options.onError) {
        options.onError(err)
      }
      
      throw err
    }
  }, [options.endpoint, options.params, options.onSuccess, options.onError])

  // Configurar query con React Query
  const query = useQuery({
    queryKey,
    queryFn,
    enabled: options.enabled !== false,
    refetchInterval: options.refetchInterval,
    staleTime: options.staleTime || 5 * 60 * 1000, // 5 minutos por defecto
    gcTime: options.gcTime || 10 * 60 * 1000, // 10 minutos por defecto
    retry: options.retryCount || 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    refetchOnWindowFocus: false,
    refetchOnReconnect: 'always',
  })

  // Función de refetch optimizada
  const refetch = useCallback(async () => {
    await query.refetch()
  }, [query])

  // Función de refresh que invalida cache
  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey })
  }, [queryClient, queryKey])

  return {
    data: query.data || null,
    loading: query.isLoading,
    error: query.error?.message || null,
    isStale: query.isStale,
    isFetching: query.isFetching,
    refetch,
    refresh,
  }
}

// Hook especializado para recursos paginados con React Query
export function usePaginatedResource<T = any>(
  endpoint: string,
  initialParams: Record<string, any> = {}
) {
  const [params, setParams] = useState({
    page: 1,
    per_page: 20,
    ...initialParams,
  })

  const queryClient = useQueryClient()
  
  const queryKey = useMemo(() => [
    'paginated-resource',
    endpoint,
    params
  ], [endpoint, params])

  const queryFn = useCallback(async (): Promise<PaginatedResponse<T>> => {
    const url = `${endpoint}?${new URLSearchParams(
      Object.entries(params).reduce((acc, [key, value]) => {
        if (value !== undefined && value !== null) {
          acc[key] = String(value)
        }
        return acc
      }, {} as Record<string, string>)
    ).toString()}`

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`)
    }

    return await response.json()
  }, [endpoint, params])

  const query = useQuery({
    queryKey,
    queryFn,
    staleTime: 2 * 60 * 1000, // 2 minutos para listas
    gcTime: 5 * 60 * 1000, // 5 minutos para listas
    retry: 3,
    refetchOnWindowFocus: false,
  })

  // Prefetch de páginas adyacentes
  const prefetchAdjacentPages = useCallback((currentPage: number, totalPages: number) => {
    const pagesToPrefetch = []
    
    // Prefetch página anterior
    if (currentPage > 1) {
      pagesToPrefetch.push(currentPage - 1)
    }
    
    // Prefetch página siguiente
    if (currentPage < totalPages) {
      pagesToPrefetch.push(currentPage + 1)
    }

    pagesToPrefetch.forEach(page => {
      const prefetchParams = { ...params, page }
      const prefetchKey = ['paginated-resource', endpoint, prefetchParams]
      
      queryClient.prefetchQuery({
        queryKey: prefetchKey,
        queryFn: async () => {
          const url = `${endpoint}?${new URLSearchParams(
            Object.entries(prefetchParams).reduce((acc, [key, value]) => {
              if (value !== undefined && value !== null) {
                acc[key] = String(value)
              }
              return acc
            }, {} as Record<string, string>)
          ).toString()}`

          const response = await fetch(url, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json',
            },
          })

          if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`)
          }

          return await response.json()
        },
        staleTime: 2 * 60 * 1000,
      })
    })
  }, [endpoint, params, queryClient])

  // Callbacks optimizados
  const goToPage = useCallback((page: number) => {
    setParams(prev => ({ ...prev, page }))
  }, [])

  const setFilters = useCallback((filters: Record<string, any>) => {
    setParams(prev => ({ ...prev, ...filters, page: 1 }))
  }, [])

  const setPageSize = useCallback((per_page: number) => {
    setParams(prev => ({ ...prev, per_page, page: 1 }))
  }, [])

  // Prefetch cuando cambian los datos
  const paginationData = query.data ? {
    total: query.data.total,
    page: query.data.page,
    pages: query.data.pages,
    per_page: query.data.per_page,
    has_next: query.data.has_next,
    has_prev: query.data.has_prev,
  } : null

  // Ejecutar prefetch
  if (paginationData) {
    prefetchAdjacentPages(paginationData.page, paginationData.pages)
  }

  return {
    data: query.data?.items || [],
    pagination: paginationData,
    loading: query.isLoading,
    error: query.error?.message || null,
    isStale: query.isStale,
    isFetching: query.isFetching,
    params,
    goToPage,
    setFilters,
    setPageSize,
    refetch: query.refetch,
  }
}

// Hook para mutaciones optimizado
export function useApiMutation<TData = any, TVariables = any>() {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async ({
      url,
      method,
      data,
    }: {
      url: string
      method: 'POST' | 'PUT' | 'DELETE' | 'PATCH'
      data?: TVariables
    }): Promise<TData> => {
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: data ? JSON.stringify(data) : undefined,
      })

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      return response.status !== 204 ? await response.json() : ({} as TData)
    },
    onSuccess: (data, variables) => {
      // Invalidar queries relacionadas automáticamente
      const baseEndpoint = variables.url.split('?')[0].split('/').slice(0, -1).join('/')
      queryClient.invalidateQueries({ 
        queryKey: ['api-resource', baseEndpoint] 
      })
      queryClient.invalidateQueries({ 
        queryKey: ['paginated-resource', baseEndpoint] 
      })
    },
    retry: (failureCount, error) => {
      // No retry para errores de validación (4xx)
      if (error instanceof Error && error.message.includes('4')) {
        return false
      }
      return failureCount < 2
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  })

  const mutate = useCallback(async (
    url: string,
    options: {
      method: 'POST' | 'PUT' | 'DELETE' | 'PATCH'
      data?: TVariables
      onSuccess?: (data: TData) => void
      onError?: (error: Error) => void
    }
  ): Promise<TData | null> => {
    try {
      const result = await mutation.mutateAsync({
        url,
        method: options.method,
        data: options.data,
      })
      
      if (options.onSuccess) {
        options.onSuccess(result)
      }
      
      return result
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Error desconocido')
      
      if (options.onError) {
        options.onError(err)
      }
      
      throw err
    }
  }, [mutation])

  return {
    mutate,
    loading: mutation.isPending,
    error: mutation.error?.message || null,
  }
}

// Hook para invalidar cache de forma inteligente
export function useApiCache() {
  const queryClient = useQueryClient()

  const invalidateEndpoint = useCallback((endpoint: string) => {
    queryClient.invalidateQueries({ 
      queryKey: ['api-resource', endpoint] 
    })
    queryClient.invalidateQueries({ 
      queryKey: ['paginated-resource', endpoint] 
    })
  }, [queryClient])

  const invalidateAll = useCallback(() => {
    queryClient.invalidateQueries()
  }, [queryClient])

  const clearCache = useCallback(() => {
    queryClient.clear()
  }, [queryClient])

  const getCachedData = useCallback(<T>(endpoint: string, params?: Record<string, any>) => {
    const queryKey = ['api-resource', endpoint, params || {}]
    return queryClient.getQueryData<T>(queryKey)
  }, [queryClient])

  return {
    invalidateEndpoint,
    invalidateAll,
    clearCache,
    getCachedData,
  }
} 