import { useState, useEffect } from 'react'

export interface Asistencia {
  id: string
  usuario: {
    id: string
    nombre: string
    apellido: string
  }
  fecha_hora_entrada: string
  fecha_hora_salida?: string | null
  clase?: {
    id: string
    nombre: string
  } | null
}

// Datos simulados de asistencias
const asistenciasSimuladas: Asistencia[] = [
  {
    id: '1',
    usuario: { id: '1', nombre: 'Ana', apellido: 'García' },
    clase: { id: '1', nombre: 'Yoga Matutino' },
    fecha_hora_entrada: '2024-12-10T08:00:00',
    fecha_hora_salida: '2024-12-10T09:30:00'
  },
  {
    id: '2',
    usuario: { id: '2', nombre: 'Carlos', apellido: 'López' },
    clase: { id: '2', nombre: 'CrossFit' },
    fecha_hora_entrada: '2024-12-10T18:00:00',
    fecha_hora_salida: null
  },
  {
    id: '3',
    usuario: { id: '3', nombre: 'María', apellido: 'Rodríguez' },
    clase: null,
    fecha_hora_entrada: '2024-12-10T16:30:00',
    fecha_hora_salida: '2024-12-10T18:00:00'
  }
]

// Hook básico para obtener asistencias
export function useAsistencias() {
  const [asistencias, setAsistencias] = useState<Asistencia[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Simular carga de datos
    setTimeout(() => {
      setAsistencias(asistenciasSimuladas)
      setLoading(false)
    }, 1000)
  }, [])

  return { asistencias, loading, error }
} 