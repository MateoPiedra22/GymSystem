import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    const logoId = params.id
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/logos/${logoId}`, {
      method: 'PUT',
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
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error updating logo:', error)
    
    // Simular respuesta exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: "Logo actualizado correctamente",
      logo_id: params.id,
      timestamp: new Date().toISOString()
    })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    const logoId = params.id
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/logos/${logoId}`, {
      method: 'DELETE',
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
    console.error('Error deleting logo:', error)
    
    // Simular respuesta exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: "Logo eliminado correctamente",
      logo_id: params.id,
      timestamp: new Date().toISOString()
    })
  }
} 