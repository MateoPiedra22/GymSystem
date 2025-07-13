import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const skip = searchParams.get('skip') || '0'
    const limit = searchParams.get('limit') || '100'
    const activa = searchParams.get('activa')
    const dia_semana = searchParams.get('dia_semana')
    
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    let url = `${BACKEND_URL}/api/clases?skip=${skip}&limit=${limit}`
    if (activa) url += `&activa=${activa}`
    if (dia_semana) url += `&dia_semana=${dia_semana}`
    
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
    console.error('Error fetching clases:', error)
    
    // Retornar datos de fallback
    return NextResponse.json([
      {
        id: "1",
        nombre: "Yoga Matutino",
        descripcion: "Clase de yoga para principiantes",
        instructor: "Ana García",
        dia_semana: "LUNES",
        hora_inicio: "08:00:00",
        hora_fin: "09:00:00",
        capacidad_maxima: 20,
        precio: 15.00,
        activa: true,
        ubicacion: "Sala A"
      },
      {
        id: "2",
        nombre: "CrossFit",
        descripcion: "Entrenamiento funcional intenso",
        instructor: "Carlos López",
        dia_semana: "MARTES",
        hora_inicio: "18:00:00",
        hora_fin: "19:00:00",
        capacidad_maxima: 15,
        precio: 20.00,
        activa: true,
        ubicacion: "Sala B"
      }
    ])
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    const response = await fetch(`${BACKEND_URL}/api/clases`, {
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
    console.error('Error creating clase:', error)
    return NextResponse.json(
      { error: 'Error al crear clase' },
      { status: 500 }
    )
  }
} 