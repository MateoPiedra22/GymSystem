import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const page = searchParams.get('page') || '1'
    const limit = searchParams.get('limit') || '10'
    const search = searchParams.get('search')
    const activo = searchParams.get('activo')
    const visible_web = searchParams.get('visible_web')

    // Construir query parameters
    const queryParams = new URLSearchParams({
      page,
      limit,
      ...(search && { search }),
      ...(activo && { activo }),
      ...(visible_web && { visible_web })
    })

    const response = await fetch(`${BACKEND_URL}/api/tipos-cuota?${queryParams}`, {
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching tipos-cuota:', error)
    
    // Datos de fallback para desarrollo
    return NextResponse.json({
      items: [
        {
          id: '1',
          codigo: 'PREMIUM_MEN',
          nombre: 'Premium Mensual',
          descripcion: 'Membresía premium con acceso completo a todas las instalaciones y clases',
          duracion_dias: 30,
          precio: 89.99,
          precio_promocional: 79.99,
          incluye_clases: true,
          limite_clases_mes: null,
          acceso_24h: true,
          incluye_evaluacion: true,
          incluye_rutina: true,
          invitados_mes: 2,
          edad_minima: 16,
          edad_maxima: null,
          horario_restringido: false,
          horario_inicio: null,
          horario_fin: null,
          beneficios: ['Acceso 24h', 'Clases ilimitadas', 'Evaluación física', 'Rutina personalizada'],
          activo: true,
          visible_web: true,
          requiere_aprobacion: false,
          renovacion_automatica: true,
          dias_aviso_vencimiento: 7,
          orden_visualizacion: 1
        },
        {
          id: '2',
          codigo: 'BASICO_MEN',
          nombre: 'Básico Mensual',
          descripcion: 'Membresía básica con acceso a instalaciones principales',
          duracion_dias: 30,
          precio: 59.99,
          precio_promocional: null,
          incluye_clases: true,
          limite_clases_mes: 8,
          acceso_24h: false,
          incluye_evaluacion: false,
          incluye_rutina: false,
          invitados_mes: 0,
          edad_minima: 16,
          edad_maxima: null,
          horario_restringido: true,
          horario_inicio: '06:00',
          horario_fin: '22:00',
          beneficios: ['Acceso a instalaciones', '8 clases por mes'],
          activo: true,
          visible_web: true,
          requiere_aprobacion: false,
          renovacion_automatica: true,
          dias_aviso_vencimiento: 5,
          orden_visualizacion: 2
        }
      ],
      page: 1,
      limit: 10,
      total: 2,
      pages: 1
    })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/tipos-cuota`, {
      method: 'POST',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error creating tipo-cuota:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
} 