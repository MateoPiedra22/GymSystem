'use client';

import { useState, useEffect, useCallback } from 'react';

interface MultimediaItem {
  id: string;
  nombre: string;
  descripcion?: string;
  tipo: 'imagen' | 'video' | 'gif' | 'audio' | 'documento';
  categoria: string;
  archivo_url: string;
  thumbnail_url?: string;
  formato: string;
  tamaño_mb: number;
  duracion_segundos?: number;
  dimensiones?: { width: number; height: number };
  orden: number;
  es_principal: boolean;
  etiquetas: string[];
  nivel_dificultad?: string;
  es_premium: boolean;
  estado: string;
  fecha_subida: string;
  estadisticas: {
    vistas: number;
    descargas: number;
    me_gusta: number;
    reportes: number;
  };
}

interface MultimediaListResponse {
  multimedia: MultimediaItem[];
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
}

interface UseMultimediaOptions {
  ejercicioId?: string;
  rutinaId?: string;
  autoLoad?: boolean;
}

interface UseMultimediaReturn {
  multimedia: MultimediaItem[];
  loading: boolean;
  error: string | null;
  total: number;
  pagina: number;
  totalPaginas: number;
  // Funciones de gestión
  loadMultimedia: (page?: number) => Promise<void>;
  uploadMultimedia: (file: File, metadata: any) => Promise<boolean>;
  updateMultimedia: (id: string, updates: any) => Promise<boolean>;
  deleteMultimedia: (id: string) => Promise<boolean>;
  setAsPrincipal: (id: string) => Promise<boolean>;
  // Filtros
  filtros: {
    tipo?: string;
    categoria?: string;
    estado?: string;
  };
  setFiltros: (filtros: any) => void;
  // Utilidades
  refreshMultimedia: () => Promise<void>;
  clearError: () => void;
}

export function useMultimedia({
  ejercicioId,
  rutinaId,
  autoLoad = true
}: UseMultimediaOptions = {}): UseMultimediaReturn {
  const [multimedia, setMultimedia] = useState<MultimediaItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(0);
  const [filtros, setFiltros] = useState({});

  // Función para obtener multimedia
  const loadMultimedia = useCallback(async (page: number = 1) => {
    if (!ejercicioId && !rutinaId) return;

    setLoading(true);
    setError(null);

    try {
      const baseUrl = ejercicioId 
        ? `/api/multimedia/ejercicios/${ejercicioId}`
        : `/api/multimedia/rutinas/${rutinaId}`;
      
      // Construir query parameters
      const params = new URLSearchParams({
        pagina: page.toString(),
        por_pagina: '20',
        ...filtros
      });

      const response = await fetch(`${baseUrl}?${params.toString()}`);
      
      if (!response.ok) {
        let errorMsg = `Error ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) errorMsg = errorData.error;
        } catch {}
        throw new Error(errorMsg);
      }

      const data: MultimediaListResponse = await response.json();
      
      setMultimedia(data.multimedia);
      setTotal(data.total);
      setPagina(data.pagina);
      setTotalPaginas(data.total_paginas);
      
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error desconocido';
      setError(errorMsg);
      console.error('Error cargando multimedia:', err);
    } finally {
      setLoading(false);
    }
  }, [ejercicioId, rutinaId, filtros]);

  // Función para subir multimedia
  const uploadMultimedia = useCallback(async (file: File, metadata: any): Promise<boolean> => {
    if (!ejercicioId && !rutinaId) {
      setError('No hay ejercicio o rutina especificado');
      return false;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // Agregar metadatos
      Object.keys(metadata).forEach(key => {
        if (metadata[key] !== undefined && metadata[key] !== null) {
          formData.append(key, metadata[key].toString());
        }
      });

      const uploadUrl = ejercicioId 
        ? `/api/multimedia/ejercicios/${ejercicioId}/upload`
        : `/api/multimedia/rutinas/${rutinaId}/upload`;

      const response = await fetch(uploadUrl, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        let errorMsg = 'Error al subir archivo';
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) errorMsg = errorData.error;
        } catch {}
        throw new Error(errorMsg);
      }

      // Recargar lista después de subir
      await loadMultimedia(pagina);
      return true;

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error subiendo archivo';
      setError(errorMsg);
      console.error('Error subiendo multimedia:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [ejercicioId, rutinaId, loadMultimedia, pagina]);

  // Función para actualizar multimedia
  const updateMultimedia = useCallback(async (id: string, updates: any): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/multimedia/ejercicios/multimedia/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        let errorMsg = 'Error al actualizar multimedia';
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) errorMsg = errorData.error;
        } catch {}
        throw new Error(errorMsg);
      }

      // Actualizar el item en la lista local
      setMultimedia(prev => prev.map(item => 
        item.id === id ? { ...item, ...updates } : item
      ));

      return true;

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error actualizando multimedia';
      setError(errorMsg);
      console.error('Error actualizando multimedia:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // Función para eliminar multimedia
  const deleteMultimedia = useCallback(async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/multimedia/ejercicios/multimedia/${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        let errorMsg = 'Error al eliminar multimedia';
        try {
          const errorData = await response.json();
          if (errorData && errorData.error) errorMsg = errorData.error;
        } catch {}
        throw new Error(errorMsg);
      }

      // Remover de la lista local
      setMultimedia(prev => prev.filter(item => item.id !== id));
      setTotal(prev => prev - 1);

      return true;

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error eliminando multimedia';
      setError(errorMsg);
      console.error('Error eliminando multimedia:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // Función para establecer como principal
  const setAsPrincipal = useCallback(async (id: string): Promise<boolean> => {
    return updateMultimedia(id, { es_principal: true });
  }, [updateMultimedia]);

  // Función para refrescar
  const refreshMultimedia = useCallback(async () => {
    await loadMultimedia(pagina);
  }, [loadMultimedia, pagina]);

  // Función para limpiar error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Cargar multimedia al montar o cambiar dependencias
  useEffect(() => {
    if (autoLoad && (ejercicioId || rutinaId)) {
      loadMultimedia(1);
    }
  }, [ejercicioId, rutinaId, autoLoad, loadMultimedia]);

  // Recargar cuando cambien los filtros
  useEffect(() => {
    if (ejercicioId || rutinaId) {
      loadMultimedia(1);
    }
  }, [filtros, loadMultimedia, ejercicioId, rutinaId]);

  return {
    multimedia,
    loading,
    error,
    total,
    pagina,
    totalPaginas,
    loadMultimedia,
    uploadMultimedia,
    updateMultimedia,
    deleteMultimedia,
    setAsPrincipal,
    filtros,
    setFiltros,
    refreshMultimedia,
    clearError
  };
}

// Hook específico para ejercicios
export function useMultimediaEjercicios(ejercicioId: string) {
  return useMultimedia({ ejercicioId });
}

// Hook específico para rutinas
export function useMultimediaRutinas(rutinaId: string) {
  return useMultimedia({ rutinaId });
}

// Hook para estadísticas de multimedia
export function useMultimediaStats(ejercicioId?: string, rutinaId?: string) {
  const [stats, setStats] = useState({
    total_archivos: 0,
    total_por_tipo: {},
    total_por_categoria: {},
    espacio_usado_mb: 0,
    archivos_mas_vistos: [],
    archivos_recientes: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    if (!ejercicioId && !rutinaId) return;

    setLoading(true);
    setError(null);

    try {
      const baseUrl = ejercicioId 
        ? `/api/multimedia/ejercicios/${ejercicioId}/stats`
        : `/api/multimedia/rutinas/${rutinaId}/stats`;

      const response = await fetch(baseUrl);
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setStats(data);
      
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error cargando estadísticas';
      setError(errorMsg);
      console.error('Error cargando estadísticas:', err);
    } finally {
      setLoading(false);
    }
  }, [ejercicioId, rutinaId]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return {
    stats,
    loading,
    error,
    refreshStats: loadStats
  };
} 