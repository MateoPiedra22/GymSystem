import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const page = searchParams.get('page') || '1'
    const limit = searchParams.get('limit') || '10'
    const search = searchParams.get('search')
    const departamento = searchParams.get('departamento')
    const cargo = searchParams.get('cargo')
    const estado = searchParams.get('estado')

    // Construir query parameters
    const queryParams = new URLSearchParams({
      page,
      limit,
      ...(search && { search }),
      ...(departamento && { departamento }),
      ...(cargo && { cargo }),
      ...(estado && { estado })
    })

    const response = await fetch(`${BACKEND_URL}/api/empleados?${queryParams}`, {
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching empleados:', error)
    
    // Datos de fallback para desarrollo
    return NextResponse.json({
      items: [
        {
          id: '1',
          nombre: 'Ana',
          apellido: 'García',
          email: 'ana.garcia@gym.com',
          telefono: '+51 987 654 321',
          telefono_emergencia: '+51 987 654 322',
          direccion: 'Av. Principal 123, Lima',
          fecha_nacimiento: '1990-05-15',
          dni: '12345678',
          numero_seguro_social: 'NSS123456789',
          cargo: 'Instructora',
          departamento: 'Entrenamiento',
          fecha_ingreso: '2023-01-15',
          tipo_contrato: 'Tiempo Completo',
          salario_base: 2500.00,
          comisiones_porcentaje: 5.0,
          bonos_meta: 200.00,
          horario_entrada: '08:00',
          horario_salida: '17:00',
          dias_trabajo: 'Lunes a Viernes',
          notas: 'Especialista en yoga y pilates',
          banco: 'Banco de Crédito',
          numero_cuenta: '1234567890123456',
          tipo_cuenta: 'Ahorros',
          certificaciones: ['Yoga Alliance', 'Pilates Mat'],
          estado: 'Activo'
        },
        {
          id: '2',
          nombre: 'Carlos',
          apellido: 'López',
          email: 'carlos.lopez@gym.com',
          telefono: '+51 987 654 323',
          telefono_emergencia: '+51 987 654 324',
          direccion: 'Calle Secundaria 456, Lima',
          fecha_nacimiento: '1985-08-20',
          dni: '87654321',
          numero_seguro_social: 'NSS987654321',
          cargo: 'Entrenador',
          departamento: 'Entrenamiento',
          fecha_ingreso: '2023-03-01',
          tipo_contrato: 'Tiempo Completo',
          salario_base: 2800.00,
          comisiones_porcentaje: 7.0,
          bonos_meta: 300.00,
          horario_entrada: '06:00',
          horario_salida: '15:00',
          dias_trabajo: 'Lunes a Sábado',
          notas: 'Especialista en CrossFit y fuerza',
          banco: 'BBVA',
          numero_cuenta: '6543210987654321',
          tipo_cuenta: 'Corriente',
          certificaciones: ['CrossFit Level 2', 'NSCA-CPT'],
          estado: 'Activo'
        }
      ],
      page: 1,
      limit: 10,
      total: 2,
      pages: 1
    })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/empleados`, {
      method: 'POST',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
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
    console.error('Error creating empleado:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  }
} 