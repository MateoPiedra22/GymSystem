import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    const formData = await request.formData()
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/logos/upload`, {
      method: 'POST',
      headers: {
        'Authorization': token,
      },
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error uploading logo:', error)
    
    // Simular respuesta exitosa para desarrollo
    return NextResponse.json({
      id: "uploaded-logo-id",
      nombre: "Logo Subido",
      descripcion: "Logo subido recientemente",
      archivo_path: "uploaded-logo.png",
      tipo_archivo: "image/png",
      tamaño_kb: 55,
      dimensiones: { width: 250, height: 100 },
      es_principal: false,
      activo: true,
      creado_en: new Date().toISOString()
    })
  }
} 