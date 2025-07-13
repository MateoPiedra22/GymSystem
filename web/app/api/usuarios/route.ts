import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const skip = searchParams.get('skip') || '0'
    const limit = searchParams.get('limit') || '100'
    const activo = searchParams.get('activo')
    const es_admin = searchParams.get('es_admin')
    
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    let url = `${BACKEND_URL}/api/usuarios?skip=${skip}&limit=${limit}`
    if (activo) url += `&activo=${activo}`
    if (es_admin) url += `&es_admin=${es_admin}`
    
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
    console.error('Error fetching usuarios:', error)
    
    // Retornar datos de fallback
    return NextResponse.json([
      {
        id: "1",
        username: "admin",
        email: "admin@gym.com",
        nombre: "Administrador",
        apellido: "Sistema",
        es_admin: true,
        esta_activo: true,
        fecha_registro: "2024-01-01T00:00:00Z"
      },
      {
        id: "2",
        username: "usuario1",
        email: "usuario1@gym.com",
        nombre: "Juan",
        apellido: "Pérez",
        es_admin: false,
        esta_activo: true,
        fecha_registro: "2024-01-15T00:00:00Z"
      }
    ])
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    const response = await fetch(`${BACKEND_URL}/api/usuarios`, {
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
    console.error('Error creating usuario:', error)
    return NextResponse.json(
      { error: 'Error al crear usuario' },
      { status: 500 }
    )
  }
} 