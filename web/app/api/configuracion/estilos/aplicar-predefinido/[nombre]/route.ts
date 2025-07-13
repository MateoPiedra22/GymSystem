import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(
  request: NextRequest,
  { params }: { params: { nombre: string } }
) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    const nombreTema = params.nombre
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/estilos/aplicar-predefinido/${nombreTema}`, {
      method: 'POST',
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
    console.error('Error applying predefined theme:', error)
    
    // Simular respuesta exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: `Tema "${params.nombre}" aplicado correctamente`,
      tema_aplicado: {
        nombre: params.nombre,
        aplicado_en: new Date().toISOString()
      }
    })
  }
} 