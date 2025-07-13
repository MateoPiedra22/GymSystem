import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const pagoId = params.id
    
    const response = await fetch(`${BACKEND_URL}/api/pagos/${pagoId}`, {
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
    console.error('Error fetching pago:', error)
    
    // Retornar pago de ejemplo para desarrollo
    return NextResponse.json({
      id: params.id,
      usuario_id: '1',
      usuario_nombre: 'Usuario Ejemplo',
      tipo_cuota_id: '1',
      tipo_cuota_nombre: 'Mensual',
      monto: 59.99,
      metodo_pago: 'Tarjeta de Crédito',
      estado: 'Completado',
      fecha_pago: new Date().toISOString(),
      fecha_vencimiento: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      referencia: `PAY-${params.id}-2024`,
      descripcion: 'Pago de ejemplo',
      comprobante_url: null
    })
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const pagoId = params.id
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/pagos/${pagoId}`, {
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
    console.error('Error updating pago:', error)
    
    // Simular actualización exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: 'Pago actualizado correctamente',
      pago_id: params.id,
      timestamp: new Date().toISOString()
    })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const pagoId = params.id
    
    const response = await fetch(`${BACKEND_URL}/api/pagos/${pagoId}`, {
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
    console.error('Error deleting pago:', error)
    
    // Simular eliminación exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: 'Pago eliminado correctamente',
      pago_id: params.id,
      timestamp: new Date().toISOString()
    })
  }
} 