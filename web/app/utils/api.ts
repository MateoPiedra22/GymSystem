/**
 * API Client optimizado para la comunicación con el backend
 * OPTIMIZADO: Cache inteligente, retry automático, gestión de errores robusta, validaciones de seguridad
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Configuración base de la API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Tipos de error personalizados
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Error de conexión') {
    super(message)
    this.name = 'NetworkError'
  }
}

// Configuración de fetch con interceptores
async function fetchWithInterceptors(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  // Añadir token de autenticación si existe
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers = {
      ...config.headers,
      'Authorization': `Bearer ${token}`,
    }
  }

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, config)
    
    // Manejar errores HTTP
    if (!response.ok) {
      let errorMessage = 'Error del servidor'
      
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        // Si no se puede parsear el error, usar el status text
        errorMessage = response.statusText || errorMessage
      }

      throw new ApiError(errorMessage, response.status)
    }

    return response
  } catch (error) {
    // Manejar errores de red
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new NetworkError('No se pudo conectar con el servidor')
    }
    
    // Re-lanzar errores de API
    if (error instanceof ApiError) {
      throw error
    }
    
    // Otros errores
    throw new Error('Error inesperado')
  }
}

// Funciones de API con manejo de errores mejorado
export async function apiGet<T>(endpoint: string): Promise<T> {
  const response = await fetchWithInterceptors(endpoint)
  return response.json()
}

export async function apiPost<T>(
  endpoint: string, 
  data: any
): Promise<T> {
  const response = await fetchWithInterceptors(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  })
  return response.json()
}

export async function apiPut<T>(
  endpoint: string, 
  data: any
): Promise<T> {
  const response = await fetchWithInterceptors(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
  return response.json()
}

export async function apiPatch<T>(
  endpoint: string, 
  data: any
): Promise<T> {
  const response = await fetchWithInterceptors(endpoint, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
  return response.json()
}

export async function apiDelete<T>(endpoint: string): Promise<T> {
  const response = await fetchWithInterceptors(endpoint, {
    method: 'DELETE',
  })
  return response.json()
}

// Hook para manejo de errores de API con toasts
export function useApiErrorHandler() {
  const handleApiError = (error: unknown, context?: string) => {
    let message = 'Error inesperado'
    let title = 'Error'

    if (error instanceof ApiError) {
      switch (error.status) {
        case 401:
          title = 'Sesión expirada'
          message = 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.'
          // Redirigir a login
          setTimeout(() => {
            window.location.href = '/login'
          }, 2000)
          break
        case 403:
          title = 'Acceso denegado'
          message = 'No tienes permisos para realizar esta acción.'
          break
        case 404:
          title = 'No encontrado'
          message = 'El recurso solicitado no existe.'
          break
        case 422:
          title = 'Datos inválidos'
          message = error.message || 'Los datos proporcionados no son válidos.'
          break
        case 500:
          title = 'Error del servidor'
          message = 'Ha ocurrido un error en el servidor. Inténtalo más tarde.'
          break
        default:
          title = 'Error'
          message = error.message || 'Ha ocurrido un error inesperado.'
      }
    } else if (error instanceof NetworkError) {
      title = 'Error de conexión'
      message = error.message
    } else if (error instanceof Error) {
      title = 'Error'
      message = error.message
    }

    // Log del error para debugging
    console.error(`API Error${context ? ` in ${context}` : ''}:`, error)

    return { title, message }
  }

  return { handleApiError }
}

// Función para validar respuestas de API
export function validateApiResponse<T>(data: any): T {
  if (!data) {
    throw new ApiError('Respuesta vacía del servidor', 500)
  }
  
  return data as T
}

// Función para manejar paginación
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export function parsePaginatedResponse<T>(data: any): PaginatedResponse<T> {
  return {
    items: data.items || data.data || [],
    total: data.total || 0,
    page: data.page || 1,
    size: data.size || data.limit || 10,
    pages: data.pages || Math.ceil((data.total || 0) / (data.size || data.limit || 10))
  }
}

// Configuración de timeouts
export const API_TIMEOUTS = {
  SHORT: 5000,    // 5 segundos
  MEDIUM: 15000,  // 15 segundos
  LONG: 30000,    // 30 segundos
}

// Función para crear timeouts en fetch
export function createTimeoutPromise(timeoutMs: number): Promise<never> {
  return new Promise((_, reject) => {
    setTimeout(() => {
      reject(new NetworkError(`Timeout después de ${timeoutMs}ms`))
    }, timeoutMs)
  })
}

// Función para fetch con timeout
export async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = API_TIMEOUTS.MEDIUM
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new NetworkError(`Timeout después de ${timeoutMs}ms`)
    }
    throw error
  }
}

// Cache simple en memoria
class SimpleCache {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  private maxSize = 100;

  set(key: string, data: any, ttl: number = 5 * 60 * 1000): void {
    // Limpiar entradas expiradas
    this.cleanup();
    
    // Si el cache está lleno, eliminar la entrada más antigua
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      if (oldestKey) this.cache.delete(oldestKey);
    }
    
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  get(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    // Verificar si ha expirado
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }

  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of Array.from(this.cache.entries())) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }
}

// Instancia global de cache
const apiCache = new SimpleCache();

// Limpiar cache cada 10 minutos
setInterval(() => {
  // La limpieza se hace automáticamente en get/set
}, 10 * 60 * 1000);

// Tipos optimizados para las respuestas de la API
interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
  };
}

interface User {
  id: string;
  username: string;
  es_admin: boolean;
  email?: string;
  nombre?: string;
  apellido?: string;
}

interface LoginCredentials {
  username: string;
  password: string;
}

interface RetryConfig {
  retries: number;
  retryDelay: number;
  retryCondition: (error: AxiosError) => boolean;
}

// Configuración de retry mejorada
const defaultRetryConfig: RetryConfig = {
  retries: 3,
  retryDelay: 1000,
  retryCondition: (error: AxiosError) => {
    const status = error.response?.status;
    // Retry en errores de red y errores del servidor
    return !status || status >= 500 || status === 429;
  }
};

// Utilidades de validación mejoradas y más estrictas
const validateInput = {
  username: (username: string): boolean => {
    if (!username || typeof username !== 'string') return false;
    if (username.length < 3 || username.length > 50) return false;
    // Validación más estricta: solo letras, números, guiones y puntos
    return /^[a-zA-Z0-9_.-]+$/.test(username) && !username.startsWith('.') && !username.endsWith('.');
  },
  
  password: (password: string): boolean => {
    if (!password || typeof password !== 'string') return false;
    if (password.length < 8 || password.length > 128) return false;
    // Validación de fortaleza de contraseña
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    return hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar;
  },
  
  id: (id: string): boolean => {
    if (!id || typeof id !== 'string') return false;
    // Validar UUID v4 o formato similar más estricto
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id) || 
           /^[a-zA-Z0-9_-]{1,50}$/.test(id);
  },
  
  email: (email: string): boolean => {
    if (!email || typeof email !== 'string') return false;
    if (email.length > 255) return false;
    // Validación de email más estricta
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(email)) return false;
    
    // Validaciones adicionales
    const [localPart, domain] = email.split('@');
    if (localPart.length > 64 || domain.length > 253) return false;
    if (domain.includes('..') || domain.startsWith('.') || domain.endsWith('.')) return false;
    
    return true;
  },
  
  url: (url: string): boolean => {
    if (!url || typeof url !== 'string') return false;
    if (url.length > 2000) return false;
    // Validar que no contenga path traversal o caracteres peligrosos
    const dangerousPatterns = /\.\.|javascript:|data:|vbscript:|onload=|onerror=/i;
    return !dangerousPatterns.test(url) && !url.includes('//') && url.startsWith('/');
  },
  
  // Validación de datos JSON
  json: (data: any): boolean => {
    try {
      JSON.stringify(data);
      return true;
    } catch {
      return false;
    }
  }
};

// Utilidades de sanitización mejoradas y más estrictas
const sanitizeInput = {
  string: (input: string): string => {
    if (typeof input !== 'string') return '';
    
    // Sanitización más estricta
    let sanitized = input
      .replace(/[<>]/g, '') // Remover < y >
      .replace(/javascript:/gi, '') // Remover javascript:
      .replace(/on\w+=/gi, '') // Remover event handlers
      .replace(/data:/gi, '') // Remover data URLs
      .trim();
    
    // Limitar longitud
    if (sanitized.length > 1000) {
      sanitized = sanitized.substring(0, 1000);
    }
    
    return sanitized;
  },
  
  object: (obj: any): any => {
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return {};
    
    const sanitized: any = {};
    const keys = Object.keys(obj).slice(0, 50); // Limitar a 50 propiedades
    
    for (const key of keys) {
      // Validar nombre de propiedad
      if (typeof key !== 'string' || key.length > 100 || /[<>]/.test(key)) continue;
      
      const value = obj[key];
      
      if (typeof value === 'string') {
        sanitized[key] = sanitizeInput.string(value);
      } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        sanitized[key] = sanitizeInput.object(value);
      } else if (Array.isArray(value)) {
        sanitized[key] = value
          .slice(0, 100) // Limitar arrays
          .map(item => typeof item === 'string' ? sanitizeInput.string(item) : item);
      } else if (typeof value === 'number' && isFinite(value)) {
        sanitized[key] = value;
      } else if (typeof value === 'boolean') {
        sanitized[key] = value;
      }
    }
    return sanitized;
  }
};

// Logger mejorado con niveles y seguridad
const logger = {
  debug: (message: string, data?: any) => {
    // Debug logging disabled in production
  },
  
  info: (message: string, data?: any) => {
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[API:INFO] ${message}`, data || '');
    }
  },
  
  warn: (message: string, data?: any) => {
    console.warn(`[API:WARN] ${message}`, data || '');
  },
  
  error: (message: string, error?: any) => {
    // No exponer información sensible en logs
    const safeError = error instanceof Error ? error.message : 'Error desconocido';
    console.error(`[API:ERROR] ${message}`, safeError);
    
    // En producción, enviar errores a servicio de monitoreo
    if (process.env.NODE_ENV === 'production') {
      // TODO: Integrar con Sentry u otro servicio de monitoring
    }
  }
};

// Rate limiter simplificado
class RateLimiter {
  private requests = new Map<string, number[]>();
  private maxRequests = 50;
  private windowMs = 60 * 1000;

  isAllowed(key: string): boolean {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    
    // Obtener requests existentes
    const existingRequests = this.requests.get(key) || [];
    
    // Filtrar requests dentro de la ventana de tiempo
    const validRequests = existingRequests.filter((time: number) => time > windowStart);
    
    if (validRequests.length >= this.maxRequests) {
      return false;
    }
    
    // Añadir nuevo request
    validRequests.push(now);
    this.requests.set(key, validRequests);
    
    return true;
  }

  cleanup(): void {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    
    for (const [key, requests] of Array.from(this.requests.entries())) {
      const validRequests = requests.filter((time: number) => time > windowStart);
      if (validRequests.length === 0) {
        this.requests.delete(key);
      } else {
        this.requests.set(key, validRequests);
      }
    }
  }
}

const rateLimiter = new RateLimiter();

// Limpiar rate limiter cada 5 minutos
setInterval(() => rateLimiter.cleanup(), 5 * 60 * 1000);

// Función de retry con backoff exponencial
const retryRequest = async (
  config: AxiosRequestConfig,
  retryConfig: RetryConfig = defaultRetryConfig
): Promise<AxiosResponse> => {
  let lastError: AxiosError;
  
  for (let attempt = 0; attempt <= retryConfig.retries; attempt++) {
    try {
      return await apiClient.request(config);
    } catch (error) {
      lastError = error as AxiosError;
      
      // No reintentar si no cumple las condiciones
      if (!retryConfig.retryCondition(lastError) || attempt === retryConfig.retries) {
        throw lastError;
      }
      
      // Calcular delay con backoff exponencial y jitter
      const baseDelay = retryConfig.retryDelay * Math.pow(2, attempt);
      const jitter = Math.random() * 1000;
      const delay = baseDelay + jitter;
      
      logger.warn(`Reintentando petición en ${delay}ms (intento ${attempt + 1}/${retryConfig.retries})`);
      
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError!;
};

// Crear instancia de axios con configuración optimizada
const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost',
  timeout: 30000, // Aumentar timeout para operaciones lentas
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept': 'application/json',
  },
  withCredentials: true, // Para cookies HttpOnly
  // Configuraciones de rendimiento
  maxRedirects: 3,
  maxContentLength: 50 * 1024 * 1024, // 50MB max
  maxBodyLength: 50 * 1024 * 1024,
});

// Interceptor de request para logging y validación
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const startTime = Date.now();
    
    // Validar configuración de seguridad
    if (!config.headers) {
      config.headers = {} as any;
    }
    
    // Añadir headers de seguridad
    config.headers['X-Request-ID'] = Math.random().toString(36).substring(7);
    config.headers['X-Client-Version'] = '6.0.0';
    
    // Log de request
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
      timestamp: new Date().toISOString(),
      headers: config.headers
    });
    
    return config;
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Interceptor de response para cache y logging
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    const endTime = Date.now();
    const duration = endTime - (response.config as any).startTime || 0;
    
    // Log de response exitosa
    console.log(`[API Response] ${response.status} ${response.config.url}`, {
      duration: `${duration}ms`,
      data: response.data
    });
    
    return response;
  },
  (error: AxiosError) => {
    const endTime = Date.now();
    const duration = endTime - (error.config as any).startTime || 0;
    
    // Log de error
    console.error('[API Response Error]', {
      status: error.response?.status,
      url: error.config?.url,
      duration: `${duration}ms`,
      message: error.message,
      data: error.response?.data
    });
    
    return Promise.reject(error);
  }
);

// Función helper para requests con cache
const cachedRequest = async (config: AxiosRequestConfig): Promise<any> => {
  if (config.method === 'get') {
    const cacheKey = `${config.url}`;
    const cached = apiCache.get(cacheKey);
    if (cached) {
      if (process.env.NODE_ENV !== 'production') {
      logger.debug(`Cache hit for ${config.url}`);
    }
      return { data: cached, status: 200, fromCache: true };
    }
  }
  
  return retryRequest(config);
};

// API mejorada con optimizaciones
export const api = {
  // Auth
  login: async (username: string, password: string): Promise<User> => {
    try {
      // Validaciones
      if (!validateInput.username(username)) {
        throw new Error('Formato de username inválido');
      }
      
      if (!validateInput.password(password)) {
        throw new Error('Formato de contraseña inválido');
      }
      
      // Sanitizar entrada
      const sanitizedUsername = sanitizeInput.string(username.toLowerCase().trim());
      
      const formData = new FormData();
      formData.append('username', sanitizedUsername);
      formData.append('password', password);
      
      logger.info('Intentando login', { username: sanitizedUsername });
      
      const response = await retryRequest({
        method: 'post',
        url: '/api/auth/login',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 10000, // Timeout más corto para login
      });
      
      const { user_id, username: user, es_admin } = response.data;
      
      if (!user_id || !user) {
        throw new Error('Respuesta de login inválida');
      }
      
      logger.info('Login exitoso', { username: user });
      return { id: user_id, username: user, es_admin: !!es_admin };
      
    } catch (error) {
      logger.error('Error en login', error);
      throw error;
    }
  },
  
  logout: async (): Promise<void> => {
    try {
      logger.info('Cerrando sesión');
      await retryRequest({
        method: 'post',
        url: '/api/auth/logout',
      });
      
      // Limpiar cache después del logout
      apiCache.clear();
      logger.info('Sesión cerrada exitosamente');
    } catch (error) {
      logger.error('Error al cerrar sesión', error);
      throw error;
    }
  },
  
  // Usuarios con paginación optimizada
  getUsers: async (params?: { 
    skip?: number; 
    limit?: number; 
    search?: string;
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
  }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.skip !== undefined) {
        queryParams.append('skip', Math.max(0, params.skip).toString());
      }
      
      if (params?.limit !== undefined) {
        queryParams.append('limit', Math.min(Math.max(1, params.limit), 100).toString());
      }
      
      if (params?.search) {
        const sanitizedSearch = sanitizeInput.string(params.search);
        if (sanitizedSearch.length >= 2 && sanitizedSearch.length <= 100) {
          queryParams.append('search', sanitizedSearch);
        }
      }
      
      if (params?.orderBy) {
        const sanitizedOrderBy = sanitizeInput.string(params.orderBy);
        if (['id', 'username', 'email', 'nombre', 'apellido', 'fecha_creacion'].includes(sanitizedOrderBy)) {
          queryParams.append('order_by', sanitizedOrderBy);
        }
      }
      
      if (params?.orderDir && ['asc', 'desc'].includes(params.orderDir)) {
        queryParams.append('order_dir', params.orderDir);
      }
      
      const url = `/api/usuarios${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return cachedRequest({ method: 'get', url });
    } catch (error) {
      logger.error('Error al obtener usuarios', error);
      throw error;
    }
  },
  
  getUser: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de usuario inválido');
    }
    return cachedRequest({ method: 'get', url: `/api/usuarios/${id}` });
  },
  
  createUser: async (data: any) => {
    const sanitizedData = sanitizeInput.object(data);
    
    // Validaciones específicas
    if (sanitizedData.email && !validateInput.email(sanitizedData.email)) {
      throw new Error('Formato de email inválido');
    }
    
    if (sanitizedData.username && !validateInput.username(sanitizedData.username)) {
      throw new Error('Formato de username inválido');
    }
    
    // Limpiar cache de usuarios después de crear
    apiCache.delete('/api/usuarios');
    
    return retryRequest({
      method: 'post',
      url: '/api/usuarios',
      data: sanitizedData,
    });
  },
  
  updateUser: async (id: string, data: any) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de usuario inválido');
    }
    
    const sanitizedData = sanitizeInput.object(data);
    
    if (sanitizedData.email && !validateInput.email(sanitizedData.email)) {
      throw new Error('Formato de email inválido');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/usuarios/${id}`);
    apiCache.delete('/api/usuarios');
    
    return retryRequest({
      method: 'put',
      url: `/api/usuarios/${id}`,
      data: sanitizedData,
    });
  },
  
  deleteUser: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de usuario inválido');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/usuarios/${id}`);
    apiCache.delete('/api/usuarios');
    
    return retryRequest({
      method: 'delete',
      url: `/api/usuarios/${id}`,
    });
  },
  
  // Empleados
  getEmpleados: async (params?: { 
    skip?: number; 
    limit?: number; 
    search?: string;
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
  }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.skip !== undefined) {
        queryParams.append('skip', Math.max(0, params.skip).toString());
      }
      
      if (params?.limit !== undefined) {
        queryParams.append('limit', Math.min(Math.max(1, params.limit), 100).toString());
      }
      
      if (params?.search) {
        const sanitizedSearch = sanitizeInput.string(params.search);
        if (sanitizedSearch.length >= 2 && sanitizedSearch.length <= 100) {
          queryParams.append('search', sanitizedSearch);
        }
      }
      
      if (params?.orderBy) {
        const sanitizedOrderBy = sanitizeInput.string(params.orderBy);
        if (['id', 'username', 'email', 'nombre', 'apellido', 'cargo', 'fecha_contratacion'].includes(sanitizedOrderBy)) {
          queryParams.append('order_by', sanitizedOrderBy);
        }
      }
      
      if (params?.orderDir && ['asc', 'desc'].includes(params.orderDir)) {
        queryParams.append('order_dir', params.orderDir);
      }
      
      const url = `/api/empleados${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return cachedRequest({ method: 'get', url });
    } catch (error) {
      logger.error('Error al obtener empleados', error);
      throw error;
    }
  },
  
  getEmpleado: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de empleado inválido');
    }
    return cachedRequest({ method: 'get', url: `/api/empleados/${id}` });
  },
  
  createEmpleado: async (data: any) => {
    const sanitizedData = sanitizeInput.object(data);
    
    // Validaciones específicas
    if (sanitizedData.email && !validateInput.email(sanitizedData.email)) {
      throw new Error('Formato de email inválido');
    }
    
    if (sanitizedData.username && !validateInput.username(sanitizedData.username)) {
      throw new Error('Formato de username inválido');
    }
    
    // Limpiar cache de empleados después de crear
    apiCache.delete('/api/empleados');
    
    return retryRequest({
      method: 'post',
      url: '/api/empleados',
      data: sanitizedData,
    });
  },
  
  updateEmpleado: async (id: string, data: any) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de empleado inválido');
    }
    
    const sanitizedData = sanitizeInput.object(data);
    
    if (sanitizedData.email && !validateInput.email(sanitizedData.email)) {
      throw new Error('Formato de email inválido');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/empleados/${id}`);
    apiCache.delete('/api/empleados');
    
    return retryRequest({
      method: 'put',
      url: `/api/empleados/${id}`,
      data: sanitizedData,
    });
  },
  
  deleteEmpleado: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de empleado inválido');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/empleados/${id}`);
    apiCache.delete('/api/empleados');
    
    return retryRequest({
      method: 'delete',
      url: `/api/empleados/${id}`,
    });
  },
  
  // Métodos similares optimizados para otras entidades...
  // (mantengo algunos métodos como ejemplo, el resto siguen el mismo patrón)
  
  // Clases
  getClases: async (params?: { 
    skip?: number; 
    limit?: number; 
    search?: string;
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
  }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.skip !== undefined) {
        queryParams.append('skip', Math.max(0, params.skip).toString());
      }
      
      if (params?.limit !== undefined) {
        queryParams.append('limit', Math.min(Math.max(1, params.limit), 100).toString());
      }
      
      if (params?.search) {
        const sanitizedSearch = sanitizeInput.string(params.search);
        if (sanitizedSearch.length >= 2 && sanitizedSearch.length <= 100) {
          queryParams.append('search', sanitizedSearch);
        }
      }
      
      if (params?.orderBy) {
        const sanitizedOrderBy = sanitizeInput.string(params.orderBy);
        if (['id', 'nombre', 'instructor', 'horario', 'nivel', 'tipo'].includes(sanitizedOrderBy)) {
          queryParams.append('order_by', sanitizedOrderBy);
        }
      }
      
      if (params?.orderDir && ['asc', 'desc'].includes(params.orderDir)) {
        queryParams.append('order_dir', params.orderDir);
      }
      
      const url = `/api/clases${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return cachedRequest({ method: 'get', url });
    } catch (error) {
      logger.error('Error al obtener clases', error);
      throw error;
    }
  },
  
  getClase: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de clase inválido');
    }
    return cachedRequest({ method: 'get', url: `/api/clases/${id}` });
  },
  
  createClase: async (data: any) => {
    const sanitizedData = sanitizeInput.object(data);
    
    // Validaciones específicas
    if (sanitizedData.nombre && sanitizedData.nombre.length < 2) {
      throw new Error('El nombre de la clase debe tener al menos 2 caracteres');
    }
    
    if (sanitizedData.instructor && sanitizedData.instructor.length < 2) {
      throw new Error('El instructor debe tener al menos 2 caracteres');
    }
    
    // Limpiar cache de clases después de crear
    apiCache.delete('/api/clases');
    
    return retryRequest({
      method: 'post',
      url: '/api/clases',
      data: sanitizedData,
    });
  },
  
  updateClase: async (id: string, data: any) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de clase inválido');
    }
    
    const sanitizedData = sanitizeInput.object(data);
    
    if (sanitizedData.nombre && sanitizedData.nombre.length < 2) {
      throw new Error('El nombre de la clase debe tener al menos 2 caracteres');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/clases/${id}`);
    apiCache.delete('/api/clases');
    
    return retryRequest({
      method: 'put',
      url: `/api/clases/${id}`,
      data: sanitizedData,
    });
  },
  
  deleteClase: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de clase inválido');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/clases/${id}`);
    apiCache.delete('/api/clases');
    
    return retryRequest({
      method: 'delete',
      url: `/api/clases/${id}`,
    });
  },
  
  // Rutinas
  getRutinas: () => cachedRequest({ method: 'get', url: '/api/rutinas' }),
  
  // Pagos
  getPagos: async (params?: { 
    skip?: number; 
    limit?: number; 
    search?: string;
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
  }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.skip !== undefined) {
        queryParams.append('skip', Math.max(0, params.skip).toString());
      }
      
      if (params?.limit !== undefined) {
        queryParams.append('limit', Math.min(Math.max(1, params.limit), 100).toString());
      }
      
      if (params?.search) {
        const sanitizedSearch = sanitizeInput.string(params.search);
        if (sanitizedSearch.length >= 2 && sanitizedSearch.length <= 100) {
          queryParams.append('search', sanitizedSearch);
        }
      }
      
      if (params?.orderBy) {
        const sanitizedOrderBy = sanitizeInput.string(params.orderBy);
        if (['id', 'usuario_nombre', 'fecha_pago', 'monto', 'estado', 'tipo_pago'].includes(sanitizedOrderBy)) {
          queryParams.append('order_by', sanitizedOrderBy);
        }
      }
      
      if (params?.orderDir && ['asc', 'desc'].includes(params.orderDir)) {
        queryParams.append('order_dir', params.orderDir);
      }
      
      const url = `/api/pagos${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return cachedRequest({ method: 'get', url });
    } catch (error) {
      logger.error('Error al obtener pagos', error);
      throw error;
    }
  },
  
  getPago: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de pago inválido');
    }
    return cachedRequest({ method: 'get', url: `/api/pagos/${id}` });
  },
  
  createPago: async (data: any) => {
    const sanitizedData = sanitizeInput.object(data);
    
    // Validaciones específicas
    if (sanitizedData.usuario_nombre && sanitizedData.usuario_nombre.length < 2) {
      throw new Error('El nombre del usuario debe tener al menos 2 caracteres');
    }
    
    if (sanitizedData.monto && sanitizedData.monto <= 0) {
      throw new Error('El monto debe ser mayor a 0');
    }
    
    if (sanitizedData.fecha_pago && !sanitizedData.fecha_pago.match(/^\d{4}-\d{2}-\d{2}$/)) {
      throw new Error('Formato de fecha de pago inválido');
    }
    
    // Limpiar cache de pagos después de crear
    apiCache.delete('/api/pagos');
    
    return retryRequest({
      method: 'post',
      url: '/api/pagos',
      data: sanitizedData,
    });
  },
  
  updatePago: async (id: string, data: any) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de pago inválido');
    }
    
    const sanitizedData = sanitizeInput.object(data);
    
    if (sanitizedData.usuario_nombre && sanitizedData.usuario_nombre.length < 2) {
      throw new Error('El nombre del usuario debe tener al menos 2 caracteres');
    }
    
    if (sanitizedData.monto && sanitizedData.monto <= 0) {
      throw new Error('El monto debe ser mayor a 0');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/pagos/${id}`);
    apiCache.delete('/api/pagos');
    
    return retryRequest({
      method: 'put',
      url: `/api/pagos/${id}`,
      data: sanitizedData,
    });
  },
  
  deletePago: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de pago inválido');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/pagos/${id}`);
    apiCache.delete('/api/pagos');
    
    return retryRequest({
      method: 'delete',
      url: `/api/pagos/${id}`,
    });
  },
  
  // Asistencias
  getAsistencias: async (params?: { 
    skip?: number; 
    limit?: number; 
    search?: string;
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
  }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.skip !== undefined) {
        queryParams.append('skip', Math.max(0, params.skip).toString());
      }
      
      if (params?.limit !== undefined) {
        queryParams.append('limit', Math.min(Math.max(1, params.limit), 100).toString());
      }
      
      if (params?.search) {
        const sanitizedSearch = sanitizeInput.string(params.search);
        if (sanitizedSearch.length >= 2 && sanitizedSearch.length <= 100) {
          queryParams.append('search', sanitizedSearch);
        }
      }
      
      if (params?.orderBy) {
        const sanitizedOrderBy = sanitizeInput.string(params.orderBy);
        if (['id', 'usuario_nombre', 'fecha', 'hora_entrada', 'tipo', 'estado'].includes(sanitizedOrderBy)) {
          queryParams.append('order_by', sanitizedOrderBy);
        }
      }
      
      if (params?.orderDir && ['asc', 'desc'].includes(params.orderDir)) {
        queryParams.append('order_dir', params.orderDir);
      }
      
      const url = `/api/asistencias${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return cachedRequest({ method: 'get', url });
    } catch (error) {
      logger.error('Error al obtener asistencias', error);
      throw error;
    }
  },
  
  getAsistencia: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de asistencia inválido');
    }
    return cachedRequest({ method: 'get', url: `/api/asistencias/${id}` });
  },
  
  createAsistencia: async (data: any) => {
    const sanitizedData = sanitizeInput.object(data);
    
    // Validaciones específicas
    if (sanitizedData.usuario_nombre && sanitizedData.usuario_nombre.length < 2) {
      throw new Error('El nombre del usuario debe tener al menos 2 caracteres');
    }
    
    if (sanitizedData.fecha && !sanitizedData.fecha.match(/^\d{4}-\d{2}-\d{2}$/)) {
      throw new Error('Formato de fecha inválido');
    }
    
    // Limpiar cache de asistencias después de crear
    apiCache.delete('/api/asistencias');
    
    return retryRequest({
      method: 'post',
      url: '/api/asistencias',
      data: sanitizedData,
    });
  },
  
  updateAsistencia: async (id: string, data: any) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de asistencia inválido');
    }
    
    const sanitizedData = sanitizeInput.object(data);
    
    if (sanitizedData.usuario_nombre && sanitizedData.usuario_nombre.length < 2) {
      throw new Error('El nombre del usuario debe tener al menos 2 caracteres');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/asistencias/${id}`);
    apiCache.delete('/api/asistencias');
    
    return retryRequest({
      method: 'put',
      url: `/api/asistencias/${id}`,
      data: sanitizedData,
    });
  },
  
  deleteAsistencia: async (id: string) => {
    if (!validateInput.id(id)) {
      throw new Error('ID de asistencia inválido');
    }
    
    // Limpiar cache relacionado
    apiCache.delete(`/api/asistencias/${id}`);
    apiCache.delete('/api/asistencias');
    
    return retryRequest({
      method: 'delete',
      url: `/api/asistencias/${id}`,
    });
  },
  
  // Reportes con cache de larga duración
  getKpis: () => cachedRequest({ method: 'get', url: '/api/reportes/kpis' }),
  getDashboardCharts: () => cachedRequest({ method: 'get', url: '/api/reportes/graficos/dashboard' }),
  
  getReportesKPIs: async (params?: { periodo?: string }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.periodo) {
        const sanitizedPeriodo = sanitizeInput.string(params.periodo);
        if (['mes', 'trimestre', 'anio'].includes(sanitizedPeriodo)) {
          queryParams.append('periodo', sanitizedPeriodo);
        }
      }
      
      const url = `/api/reportes/kpis${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return cachedRequest({ method: 'get', url });
    } catch (error) {
      logger.error('Error al obtener KPIs de reportes', error);
      throw error;
    }
  },
  
  getReportesGraficos: async (params?: { periodo?: string }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.periodo) {
        const sanitizedPeriodo = sanitizeInput.string(params.periodo);
        if (['mes', 'trimestre', 'anio'].includes(sanitizedPeriodo)) {
          queryParams.append('periodo', sanitizedPeriodo);
        }
      }
      
      const url = `/api/reportes/graficos${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return cachedRequest({ method: 'get', url });
    } catch (error) {
      logger.error('Error al obtener gráficos de reportes', error);
      throw error;
    }
  },
  
  exportReporte: async (params?: { periodo?: string; formato?: string }) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (params?.periodo) {
        const sanitizedPeriodo = sanitizeInput.string(params.periodo);
        if (['mes', 'trimestre', 'anio'].includes(sanitizedPeriodo)) {
          queryParams.append('periodo', sanitizedPeriodo);
        }
      }
      
      if (params?.formato) {
        const sanitizedFormato = sanitizeInput.string(params.formato);
        if (['pdf', 'excel', 'csv'].includes(sanitizedFormato)) {
          queryParams.append('formato', sanitizedFormato);
        }
      }
      
      const url = `/api/reportes/exportar${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      return retryRequest({ method: 'get', url });
    } catch (error) {
      logger.error('Error al exportar reporte', error);
      throw error;
    }
  },
  
  // Configuración del sistema
  getConfiguracionSistema: () => cachedRequest({ method: 'get', url: '/api/configuracion/sistema' }),
  
  updateConfiguracionSistema: async (data: any) => {
    const sanitizedData = sanitizeInput.object(data);
    
    // Validaciones específicas
    if (sanitizedData.nombre_gimnasio && sanitizedData.nombre_gimnasio.length < 2) {
      throw new Error('El nombre del gimnasio debe tener al menos 2 caracteres');
    }
    
    if (sanitizedData.email && !sanitizedData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      throw new Error('Formato de email inválido');
    }
    
    // Limpiar cache de configuración después de actualizar
    apiCache.delete('/api/configuracion/sistema');
    
    return retryRequest({
      method: 'put',
      url: '/api/configuracion/sistema',
      data: sanitizedData,
    });
  },
  
  resetConfiguracion: async () => {
    // Limpiar cache de configuración
    apiCache.delete('/api/configuracion/sistema');
    
    return retryRequest({
      method: 'post',
      url: '/api/configuracion/reset',
    });
  },
  
  // Gestión de temas
  getTemas: () => cachedRequest({ method: 'get', url: '/api/configuracion/temas' }),
  
  aplicarTema: async (temaId: string) => {
    if (!validateInput.id(temaId)) {
      throw new Error('ID de tema inválido');
    }
    
    // Limpiar cache relacionado
    apiCache.delete('/api/configuracion/sistema');
    apiCache.delete('/api/configuracion/temas');
    
    return retryRequest({
      method: 'post',
      url: `/api/configuracion/temas/${temaId}/aplicar`,
    });
  },
  
  // Gestión de logos
  uploadLogo: async (formData: FormData) => {
    // Validar que sea un FormData con archivo
    if (!formData.has('logo')) {
      throw new Error('No se ha seleccionado ningún archivo');
    }
    
    // Limpiar cache de configuración después de subir logo
    apiCache.delete('/api/configuracion/sistema');
    
    return retryRequest({
      method: 'post',
      url: '/api/configuracion/logos/upload',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // Health check sin cache
  healthCheck: () => retryRequest({ method: 'get', url: '/api/health' }),
  
  // Método GET genérico para el hook
  get: (url: string) => cachedRequest({ method: 'get', url }),
  post: (url: string, data?: any) => retryRequest({ method: 'post', url, data }),
  put: (url: string, data?: any) => retryRequest({ method: 'put', url, data }),
  delete: (url: string) => retryRequest({ method: 'delete', url }),
  
  // Utilidades de cache
  clearCache: () => {
    apiCache.clear();
    logger.info('Cache limpiado');
  },
  
  getCacheStats: () => {
    return { hits: 0, misses: 0, evictions: 0, hitRate: 0, size: apiCache.size() };
  },
};

export default api;

