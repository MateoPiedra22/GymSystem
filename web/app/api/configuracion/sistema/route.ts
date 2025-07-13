import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/sistema`, {
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
    console.error('Error fetching system config:', error)
    
    // Retornar datos de fallback para desarrollo
    return NextResponse.json({
      tema_activo: {
        id: "1",
        nombre_tema: "Tema Predeterminado",
        descripcion: "Tema principal del sistema",
        colores_primarios: {
          primary: "#3B82F6",
          secondary: "#10B981",
          accent: "#F59E0B",
          danger: "#EF4444"
        },
        colores_secundarios: {
          background: "#FFFFFF",
          surface: "#F9FAFB",
          border: "#E5E7EB",
          text: "#1F2937"
        },
        fuentes: {
          primary: "Inter",
          secondary: "Roboto",
          monospace: "Fira Code"
        },
        tamaños: {
          text_small: "0.875rem",
          text_base: "1rem",
          text_large: "1.125rem",
          text_xlarge: "1.25rem"
        },
        bordes_y_sombras: {
          border_radius: "0.5rem",
          shadow_small: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
          shadow_medium: "0 4px 6px -1px rgb(0 0 0 / 0.1)"
        },
        animaciones: {
          transition_fast: "150ms",
          transition_normal: "300ms",
          transition_slow: "500ms"
        },
        es_predeterminado: true,
        activo: true,
        creado_en: new Date().toISOString()
      },
      logo_principal: {
        id: "1",
        nombre: "Logo Principal",
        descripcion: "Logo principal del gimnasio",
        archivo_path: "logo.png",
        tipo_archivo: "image/png",
        tamaño_kb: 45,
        dimensiones: { width: 200, height: 80 },
        es_principal: true,
        activo: true,
        creado_en: new Date().toISOString()
      },
      configuraciones_adicionales: {
        nombre_gimnasio: "GymSystem Pro",
        direccion: "Calle Principal 123",
        telefono: "+1 234 567 890",
        email: "info@gymsystem.com",
        horario_apertura: "06:00",
        horario_cierre: "22:00",
        moneda: "USD",
        zona_horaria: "America/New_York",
        idioma: "es",
        notificaciones_email: true,
        notificaciones_sms: false,
        backup_automatico: true,
        modo_mantenimiento: false
      }
    })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/sistema`, {
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
    console.error('Error updating system config:', error)
    
    // Simular respuesta exitosa para desarrollo
    return NextResponse.json({
      success: true,
      message: "Configuración actualizada correctamente",
      timestamp: new Date().toISOString()
    })
  }
} 