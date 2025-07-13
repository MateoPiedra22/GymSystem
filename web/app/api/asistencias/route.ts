import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const skip = searchParams.get('skip') || '0'
    const limit = searchParams.get('limit') || '100'
    const usuario_id = searchParams.get('usuario_id')
    const clase_id = searchParams.get('clase_id')
    const fecha = searchParams.get('fecha')
    
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    let url = `${BACKEND_URL}/api/asistencias?skip=${skip}&limit=${limit}`
    if (usuario_id) url += `&usuario_id=${usuario_id}`
    if (clase_id) url += `&clase_id=${clase_id}`
    if (fecha) url += `&fecha=${fecha}`
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching asistencias:', error)
    
    // Retornar datos de fallback
    return NextResponse.json([
      {
        id: "1",
        usuario_id: "2",
        clase_id: "1",
        fecha_hora_entrada: "2024-12-20T08:00:00Z",
        fecha_hora_salida: "2024-12-20T09:00:00Z",
        estado: "COMPLETADA",
        notas: "Asistencia regular"
      },
      {
        id: "2",
        usuario_id: "2",
        clase_id: "2",
        fecha_hora_entrada: "2024-12-21T10:00:00Z",
        fecha_hora_salida: "2024-12-21T11:00:00Z",
        estado: "COMPLETADA",
        notas: "Excelente rendimiento"
      }
    ])
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    const response = await fetch(`${BACKEND_URL}/api/asistencias`, {
      method: 'POST',
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data, { status: 201 })
  } catch (error) {
    console.error('Error creating asistencia:', error)
    return NextResponse.json(
      { error: 'Error al registrar asistencia' },
      { status: 500 }
    )
  }
} 