import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    
    // Obtener FormData de la petición
    const formData = await request.formData();
    
    // Crear nueva FormData para el backend
    const backendFormData = new FormData();
    
    // Transferir todos los campos del formulario
    formData.forEach((value, key) => {
      backendFormData.append(key, value);
    });
    
    // Obtener headers de autorización
    const headersList = headers();
    const authorization = headersList.get('authorization');
    
    // Construir headers para el backend
    const backendHeaders: HeadersInit = {};
    if (authorization) {
      backendHeaders['Authorization'] = authorization;
    }
    
    // Hacer petición al backend
    const response = await fetch(
      `${BACKEND_URL}/multimedia/ejercicios/${id}/upload`,
      {
        method: 'POST',
        headers: backendHeaders,
        body: backendFormData
      }
    );
    
    if (!response.ok) {
      const errorData = await response.text();
      return NextResponse.json(
        { error: `Error del servidor: ${errorData}` },
        { status: response.status }
      );
    }

    let result;
    try {
      result = await response.json();
    } catch (e) {
      return NextResponse.json(
        { error: 'Respuesta inválida del backend (no es JSON válido)' },
        { status: 502 }
      );
    }

    if (!result || typeof result !== 'object') {
      return NextResponse.json(
        { error: 'El backend no devolvió un objeto multimedia válido.' },
        { status: 502 }
      );
    }

    return NextResponse.json(result);
    
  } catch (error) {
    console.error('Error en upload de multimedia:', error);
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    );
  }
} 