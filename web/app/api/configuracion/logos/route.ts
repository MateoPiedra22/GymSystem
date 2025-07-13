import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/logos`, {
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
    console.error('Error fetching logos config:', error)
    
    // Retornar datos de fallback para desarrollo
    return NextResponse.json([
      {
        id: "1",
        nombre: "Logo Principal",
        descripcion: "Logo oficial del gimnasio",
        archivo_path: "logo-principal.png",
        tipo_archivo: "image/png",
        tamaño_kb: 45,
        dimensiones: { width: 200, height: 80 },
        es_principal: true,
        activo: true,
        creado_en: new Date().toISOString()
      },
      {
        id: "2",
        nombre: "Logo Alternativo",
        descripcion: "Logo alternativo para uso en fondos oscuros",
        archivo_path: "logo-alternativo.png",
        tipo_archivo: "image/png",
        tamaño_kb: 38,
        dimensiones: { width: 180, height: 72 },
        es_principal: false,
        activo: true,
        creado_en: new Date().toISOString()
      },
      {
        id: "3",
        nombre: "Logo Compacto",
        descripcion: "Versión compacta del logo para espacios pequeños",
        archivo_path: "logo-compacto.png",
        tipo_archivo: "image/png",
        tamaño_kb: 25,
        dimensiones: { width: 120, height: 48 },
        es_principal: false,
        activo: true,
        creado_en: new Date().toISOString()
      }
    ])
  }
}

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
      id: "new-logo-id",
      nombre: "Nuevo Logo",
      descripcion: "Logo subido recientemente",
      archivo_path: "nuevo-logo.png",
      tipo_archivo: "image/png",
      tamaño_kb: 50,
      dimensiones: { width: 200, height: 80 },
      es_principal: false,
      activo: true,
      creado_en: new Date().toISOString()
    })
  }
} 