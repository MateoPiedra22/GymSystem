import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/estilos/predefinidos`, {
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
    console.error('Error fetching predefined styles:', error)
    
    // Retornar datos de fallback para desarrollo
    return NextResponse.json([
      {
        nombre: "Tema Clásico",
        datos: {
          nombre_tema: "Tema Clásico",
          descripcion: "Tema profesional con colores sobrios y elegantes",
          colores_primarios: {
            primary: "#1F2937",
            secondary: "#374151",
            accent: "#6B7280",
            danger: "#DC2626"
          },
          colores_secundarios: {
            background: "#FFFFFF",
            surface: "#F9FAFB",
            border: "#E5E7EB",
            text: "#111827"
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
            border_radius: "0.375rem",
            shadow_small: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
            shadow_medium: "0 4px 6px -1px rgb(0 0 0 / 0.1)"
          },
          animaciones: {
            transition_fast: "150ms",
            transition_normal: "300ms",
            transition_slow: "500ms"
          },
          es_predeterminado: false,
          activo: true
        }
      },
      {
        nombre: "Tema Moderno",
        datos: {
          nombre_tema: "Tema Moderno",
          descripcion: "Tema con colores vibrantes y diseño contemporáneo",
          colores_primarios: {
            primary: "#3B82F6",
            secondary: "#10B981",
            accent: "#F59E0B",
            danger: "#EF4444"
          },
          colores_secundarios: {
            background: "#FFFFFF",
            surface: "#F8FAFC",
            border: "#E2E8F0",
            text: "#1E293B"
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
            shadow_small: "0 1px 3px 0 rgb(0 0 0 / 0.1)",
            shadow_medium: "0 10px 15px -3px rgb(0 0 0 / 0.1)"
          },
          animaciones: {
            transition_fast: "150ms",
            transition_normal: "300ms",
            transition_slow: "500ms"
          },
          es_predeterminado: true,
          activo: true
        }
      },
      {
        nombre: "Tema Oscuro",
        datos: {
          nombre_tema: "Tema Oscuro",
          descripcion: "Tema oscuro para reducir la fatiga visual",
          colores_primarios: {
            primary: "#60A5FA",
            secondary: "#34D399",
            accent: "#FBBF24",
            danger: "#F87171"
          },
          colores_secundarios: {
            background: "#111827",
            surface: "#1F2937",
            border: "#374151",
            text: "#F9FAFB"
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
            shadow_small: "0 1px 3px 0 rgb(0 0 0 / 0.3)",
            shadow_medium: "0 10px 15px -3px rgb(0 0 0 / 0.3)"
          },
          animaciones: {
            transition_fast: "150ms",
            transition_normal: "300ms",
            transition_slow: "500ms"
          },
          es_predeterminado: false,
          activo: true
        }
      },
      {
        nombre: "Tema Deportivo",
        datos: {
          nombre_tema: "Tema Deportivo",
          descripcion: "Tema energético inspirado en el deporte",
          colores_primarios: {
            primary: "#EF4444",
            secondary: "#10B981",
            accent: "#F59E0B",
            danger: "#DC2626"
          },
          colores_secundarios: {
            background: "#FFFFFF",
            surface: "#FEF2F2",
            border: "#FECACA",
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
            border_radius: "0.75rem",
            shadow_small: "0 1px 3px 0 rgb(239 68 68 / 0.1)",
            shadow_medium: "0 10px 15px -3px rgb(239 68 68 / 0.1)"
          },
          animaciones: {
            transition_fast: "150ms",
            transition_normal: "300ms",
            transition_slow: "500ms"
          },
          es_predeterminado: false,
          activo: true
        }
      }
    ])
  }
} 