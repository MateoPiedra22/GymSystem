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
    const estado = searchParams.get('estado')
    const desde = searchParams.get('desde')
    const hasta = searchParams.get('hasta')
    
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    let url = `${BACKEND_URL}/api/pagos?skip=${skip}&limit=${limit}`
    if (usuario_id) url += `&usuario_id=${usuario_id}`
    if (estado) url += `&estado=${estado}`
    if (desde) url += `&desde=${desde}`
    if (hasta) url += `&hasta=${hasta}`
    
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
    console.error('Error fetching pagos:', error)
    
    // Retornar datos de fallback
    return NextResponse.json([
      {
        id: "1",
        usuario_id: "2",
        monto: 150.00,
        monto_final: 150.00,
        fecha_pago: "2024-12-01T10:00:00Z",
        fecha_vencimiento: "2024-12-01T00:00:00Z",
        metodo_pago: "TARJETA_CREDITO",
        concepto: "MEMBRESIA",
        estado: "PAGADO",
        notas: "Pago mensual"
      },
      {
        id: "2",
        usuario_id: "2",
        monto: 50.00,
        monto_final: 50.00,
        fecha_pago: "2024-12-15T14:30:00Z",
        fecha_vencimiento: "2024-12-15T00:00:00Z",
        metodo_pago: "EFECTIVO",
        concepto: "CLASE_ESPECIAL",
        estado: "PAGADO",
        notas: "Clase personalizada"
      }
    ])
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    const response = await fetch(`${BACKEND_URL}/api/pagos`, {
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
    console.error('Error creating pago:', error)
    return NextResponse.json(
      { error: 'Error al registrar pago' },
      { status: 500 }
    )
  }
} 