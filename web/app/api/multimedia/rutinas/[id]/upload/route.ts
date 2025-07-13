import { NextRequest, NextResponse } from 'next/server';

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const formData = await req.formData();
    
    // Validar que hay un archivo
    const file = formData.get('file') as File;
    if (!file) {
      return NextResponse.json(
        { error: 'No se ha proporcionado ningún archivo' },
        { status: 400 }
      );
    }

    // Crear FormData para enviar al backend
    const backendFormData = new FormData();
    backendFormData.append('file', file);
    
    // Agregar metadatos del formulario
    const metadataFields = [
      'nombre', 'descripcion', 'categoria', 'etiquetas', 
      'nivel_dificultad', 'es_premium', 'orden'
    ];
    
    metadataFields.forEach(field => {
      const value = formData.get(field);
      if (value) {
        backendFormData.append(field, value.toString());
      }
    });

    // Llamada al backend FastAPI
    const backendUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/multimedia/rutinas/${params.id}/upload`;
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Authorization': req.headers.get('Authorization') || ''
      },
      body: backendFormData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend upload error:', response.status, errorData);
      
      return NextResponse.json(
        { error: errorData.detail || `Error al subir archivo: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error en upload multimedia rutina:', error);
    return NextResponse.json(
      { error: 'Error interno del servidor al procesar el archivo' },
      { status: 500 }
    );
  }
} 