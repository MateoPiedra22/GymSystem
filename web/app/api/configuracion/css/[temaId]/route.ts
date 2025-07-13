import { NextRequest, NextResponse } from 'next/server'

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(
  request: NextRequest,
  { params }: { params: { temaId: string } }
) {
  try {
    const token = request.headers.get('Authorization') || 'Bearer mock-token'
    const temaId = params.temaId
    
    const response = await fetch(`${BACKEND_URL}/api/configuracion/css/${temaId}`, {
      method: 'GET',
      headers: {
        'Authorization': token,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }

    const css = await response.text()
    return new NextResponse(css, {
      headers: {
        'Content-Type': 'text/css',
      },
    })
  } catch (error) {
    console.error('Error generating CSS:', error)
    
    // Retornar CSS de fallback para desarrollo
    const fallbackCSS = `
      :root {
        --primary: #3B82F6;
        --secondary: #10B981;
        --accent: #F59E0B;
        --danger: #EF4444;
        --background: #FFFFFF;
        --surface: #F9FAFB;
        --border: #E5E7EB;
        --text: #1F2937;
        --border-radius: 0.5rem;
        --transition: 300ms;
      }
      
      .gym-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        transition: all var(--transition) ease;
      }
      
      .gym-card:hover {
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        transform: translateY(-2px);
      }
      
      .page-header {
        margin-bottom: 2rem;
      }
      
      .page-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 0.5rem;
      }
      
      .page-subtitle {
        color: #6B7280;
        font-size: 1.125rem;
      }
    `
    
    return new NextResponse(fallbackCSS, {
      headers: {
        'Content-Type': 'text/css',
      },
    })
  }
} 