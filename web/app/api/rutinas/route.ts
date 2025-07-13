import { NextRequest, NextResponse } from 'next/server';

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const pagina = searchParams.get('pagina') || '1';
    const por_pagina = searchParams.get('por_pagina') || '50';
    const busqueda = searchParams.get('busqueda');
    const nivel = searchParams.get('nivel');

    // Construir query parameters
    const queryParams = new URLSearchParams({
      pagina,
      por_pagina,
      ...(busqueda && { busqueda }),
      ...(nivel && { nivel })
    });

    // Llamada al backend FastAPI
    const backendUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/rutinas?${queryParams}`;
    
    const response = await fetch(backendUrl, {
      headers: {
        'Authorization': req.headers.get('Authorization') || 'Bearer mock-token',
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      console.error('Backend error:', response.status);
      
      // Retornar datos de fallback para desarrollo
      return NextResponse.json([
        {
          id: "1",
          nombre: "Rutina Principiante",
          descripcion: "Rutina ideal para personas que están comenzando en el gimnasio",
          nivel: "Principiante",
          duracion_estimada: 45,
          ejercicios: [
            {
              id: "1",
              nombre: "Sentadillas",
              descripcion: "Ejercicio básico para piernas",
              tipo: "Fuerza",
              dificultad: "Principiante",
              musculos_trabajados: "Cuádriceps, Glúteos",
              imagen_url: "/images/ejercicios/sentadillas.jpg"
            },
            {
              id: "2",
              nombre: "Flexiones",
              descripcion: "Ejercicio para pecho y brazos",
              tipo: "Fuerza",
              dificultad: "Principiante",
              musculos_trabajados: "Pecho, Tríceps",
              imagen_url: "/images/ejercicios/flexiones.jpg"
            },
            {
              id: "3",
              nombre: "Plancha",
              descripcion: "Ejercicio de estabilización",
              tipo: "Estabilidad",
              dificultad: "Principiante",
              musculos_trabajados: "Core, Hombros",
              imagen_url: "/images/ejercicios/plancha.jpg"
            }
          ]
        },
        {
          id: "2",
          nombre: "Rutina Intermedia",
          descripcion: "Rutina para personas con experiencia en el gimnasio",
          nivel: "Intermedio",
          duracion_estimada: 60,
          ejercicios: [
            {
              id: "4",
              nombre: "Press de Banca",
              descripcion: "Ejercicio compuesto para pecho",
              tipo: "Fuerza",
              dificultad: "Intermedio",
              musculos_trabajados: "Pecho, Hombros, Tríceps",
              imagen_url: "/images/ejercicios/press-banca.jpg"
            },
            {
              id: "5",
              nombre: "Peso Muerto",
              descripcion: "Ejercicio fundamental para espalda",
              tipo: "Fuerza",
              dificultad: "Intermedio",
              musculos_trabajados: "Espalda, Glúteos, Isquios",
              imagen_url: "/images/ejercicios/peso-muerto.jpg"
            },
            {
              id: "6",
              nombre: "Sentadilla con Barra",
              descripcion: "Variación avanzada de sentadillas",
              tipo: "Fuerza",
              dificultad: "Intermedio",
              musculos_trabajados: "Cuádriceps, Glúteos, Core",
              imagen_url: "/images/ejercicios/sentadilla-barra.jpg"
            }
          ]
        },
        {
          id: "3",
          nombre: "Rutina Avanzada",
          descripcion: "Rutina para atletas experimentados",
          nivel: "Avanzado",
          duracion_estimada: 75,
          ejercicios: [
            {
              id: "7",
              nombre: "Clean & Jerk",
              descripcion: "Movimiento olímpico completo",
              tipo: "Potencia",
              dificultad: "Avanzado",
              musculos_trabajados: "Todo el cuerpo",
              imagen_url: "/images/ejercicios/clean-jerk.jpg"
            },
            {
              id: "8",
              nombre: "Muscle Ups",
              descripcion: "Ejercicio de calistenia avanzado",
              tipo: "Fuerza",
              dificultad: "Avanzado",
              musculos_trabajados: "Espalda, Bíceps, Hombros",
              imagen_url: "/images/ejercicios/muscle-ups.jpg"
            },
            {
              id: "9",
              nombre: "Handstand Push-ups",
              descripcion: "Flexiones en posición de pino",
              tipo: "Fuerza",
              dificultad: "Avanzado",
              musculos_trabajados: "Hombros, Tríceps, Core",
              imagen_url: "/images/ejercicios/handstand-pushups.jpg"
            }
          ]
        }
      ]);
    }

    const data = await response.json();
    
    // Si es una respuesta paginada, extraer solo los items
    const rutinas = data.items || data;
    
    return NextResponse.json(rutinas);

  } catch (error) {
    console.error('Error en API rutinas:', error);
    
    // Retornar datos de fallback en caso de error
    return NextResponse.json([
      {
        id: "1",
        nombre: "Rutina Básica",
        descripcion: "Rutina de ejemplo para desarrollo",
        nivel: "Principiante",
        duracion_estimada: 30,
        ejercicios: [
          {
            id: "1",
            nombre: "Ejercicio de Ejemplo",
            descripcion: "Descripción del ejercicio",
            tipo: "Fuerza",
            dificultad: "Principiante",
            musculos_trabajados: "Músculos principales"
          }
        ]
      }
    ]);
  }
} 