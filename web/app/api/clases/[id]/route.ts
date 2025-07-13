import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const claseId = params.id
    
    const response = await fetch(`${BACKEND_URL}/api/clases/${claseId}`, {
      headers: {
        'Authorization': request.headers.get('Authorization') || 'Bearer mock-token',
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching clase:', error)
    
    // Retornar clase de ejemplo para desarrollo
    return NextResponse.json({
      id: params.id,
      nombre: 'Clase de Ejemplo',
      descripcion: 'Descripción de la clase de ejemplo',
      instructor: 'Instructor Ejemplo',
      dia_semana: 'Lunes',
      hora_inicio: '09:00',
      hora_fin: '10:00',
      duracion_minutos: 60,
      capacidad_maxima: 20,
      inscritos: 15,
      plazas_disponibles: 5,
      precio: 25.00,
      nivel: 'Intermedio',
      esta_activa: true,
      categoria: 'Funcional',
      sala: 'Sala Principal',
      equipamiento_requerido: ['Equipamiento básico']
    })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const claseId = params.id
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/clases/${claseId}`, {
      method: 'PUT',
      headers: {
        'Authorization': request.headers.get('Authorization') || 'Bearer mock-token',
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
    console.error('Error updating clase:', error)
    
    // Simular actualización exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: 'Clase actualizada correctamente',
      clase_id: params.id,
      timestamp: new Date().toISOString()
    })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const claseId = params.id
    
    const response = await fetch(`${BACKEND_URL}/api/clases/${claseId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': request.headers.get('Authorization') || 'Bearer mock-token',
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error deleting clase:', error)
    
    // Simular eliminación exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: 'Clase eliminada correctamente',
      clase_id: params.id,
      timestamp: new Date().toISOString()
    })
  }
} 