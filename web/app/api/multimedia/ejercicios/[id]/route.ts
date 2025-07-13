import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const { searchParams } = new URL(request.url);
    
    // Construir query parameters
    const queryParams = new URLSearchParams();
    searchParams.forEach((value, key) => {
      queryParams.append(key, value);
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
      `${BACKEND_URL}/multimedia/ejercicios/${id}?${queryParams.toString()}`,
      {
        method: 'GET',
        headers: backendHeaders
      }
    );
    
    if (!response.ok) {
      const errorData = await response.text();
      return NextResponse.json(
        { error: `Error del servidor: ${errorData}` },
        { status: response.status }
      );
    }

    let multimedia;
    try {
      multimedia = await response.json();
    } catch (e) {
      return NextResponse.json(
        { error: 'Respuesta inválida del backend (no es JSON válido)' },
        { status: 502 }
      );
    }

    if (!multimedia || typeof multimedia !== 'object' || Array.isArray(multimedia)) {
      return NextResponse.json(
        { error: 'El backend no devolvió un objeto multimedia válido.' },
        { status: 502 }
      );
    }

    return NextResponse.json(multimedia);
    
  } catch (error) {
    console.error('Error obteniendo multimedia:', error);
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    );
  }
} 