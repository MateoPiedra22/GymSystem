import { NextRequest, NextResponse } from 'next/server';

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

interface MultimediaResponse {
  multimedia: Array<{
    id: string;
    nombre: string;
    descripcion?: string;
    tipo: string;
    categoria: string;
    archivo_url: string;
    thumbnail_url?: string;
    formato: string;
    tamaño_mb: number;
    duracion_segundos?: number;
    dimensiones?: { width: number; height: number };
    orden: number;
    es_principal: boolean;
    etiquetas: string[];
    nivel_dificultad?: string;
    es_premium: boolean;
    estado: string;
    fecha_subida: string;
    estadisticas: {
      vistas: number;
      descargas: number;
      me_gusta: number;
      reportes: number;
    };
  }>;
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
}

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { searchParams } = new URL(req.url);
    const pagina = searchParams.get('pagina') || '1';
    const por_pagina = searchParams.get('por_pagina') || '20';
    const tipo = searchParams.get('tipo');
    const categoria = searchParams.get('categoria');
    const estado = searchParams.get('estado');

    // Construir query parameters para el backend
    const queryParams = new URLSearchParams({
      pagina,
      por_pagina,
      ...(tipo && { tipo }),
      ...(categoria && { categoria }),
      ...(estado && { estado })
    });

    // Llamada al backend FastAPI
    const backendUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/multimedia/rutinas/${params.id}?${queryParams}`;
    
    const response = await fetch(backendUrl, {
      headers: {
        'Authorization': req.headers.get('Authorization') || '',
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);
      
      return NextResponse.json(
        { error: `Error del servidor: ${response.status}` },
        { status: response.status }
      );
    }

    const data: MultimediaResponse = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error en API multimedia rutinas:', error);
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    );
  }
} 