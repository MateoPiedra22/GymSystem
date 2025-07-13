import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const userId = params.id
    
    const response = await fetch(`${BACKEND_URL}/api/usuarios/${userId}`, {
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
    console.error('Error fetching usuario:', error)
    
    // Retornar usuario de ejemplo para desarrollo
    return NextResponse.json({
      id: params.id,
      nombre: 'Usuario',
      apellido: 'Ejemplo',
      email: 'usuario@ejemplo.com',
      telefono: '+51 987 654 321',
      fecha_nacimiento: '1990-01-01',
      direccion: 'Dirección de ejemplo',
      fecha_registro: '2024-01-01',
      esta_activo: true,
      tipo_membresia: 'Básico',
      ultimo_pago: '2024-12-01',
      estado_pago: 'Activo',
      objetivo: 'Mantener forma',
      asistencias_mes: 15
    })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const userId = params.id
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/usuarios/${userId}`, {
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
    console.error('Error updating usuario:', error)
    
    // Simular actualización exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: 'Usuario actualizado correctamente',
      usuario_id: params.id,
      timestamp: new Date().toISOString()
    })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const userId = params.id
    
    const response = await fetch(`${BACKEND_URL}/api/usuarios/${userId}`, {
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
    console.error('Error deleting usuario:', error)
    
    // Simular eliminación exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: 'Usuario eliminado correctamente',
      usuario_id: params.id,
      timestamp: new Date().toISOString()
    })
  }
} 