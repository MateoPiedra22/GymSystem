/**
 * Suite de Pruebas Automatizadas para la Aplicación Web
 * Pruebas de componentes, hooks, y funcionalidades
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { jest } from '@jest/globals'

// Mock Next.js router
const mockPush = jest.fn()
const mockBack = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    back: mockBack,
    refresh: jest.fn(),
  }),
  usePathname: () => '/test-path',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock API calls
const mockApiClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}

jest.mock('../app/utils/api-client', () => ({
  apiClient: mockApiClient
}))

// Importar componentes a probar
import { Button } from '../app/components/ui/Button'
import { Input } from '../app/components/ui/Input'
import { Card } from '../app/components/ui/Card'
import { Badge } from '../app/components/ui/Badge'
import { Modal } from '../app/components/ui/Modal'
import { useResponsive } from '../app/components/responsive/ResponsiveWrapper'
import { ResponsiveDataTable } from '../app/components/responsive/ResponsiveDataTable'

// Test utilities
const renderWithProviders = (component: React.ReactElement) => {
  return render(component)
}

describe('🧪 Componentes UI Básicos', () => {
  describe('Button Component', () => {
    test('renderiza correctamente con texto', () => {
      render(<Button>Click me</Button>)
      expect(screen.getByRole('button')).toHaveTextContent('Click me')
    })

    test('maneja eventos onClick', async () => {
      const handleClick = jest.fn()
      render(<Button onClick={handleClick}>Click me</Button>)
      
      await userEvent.click(screen.getByRole('button'))
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    test('aplica variantes correctamente', () => {
      render(<Button variant="destructive">Delete</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-destructive')
    })

    test('maneja estado disabled', () => {
      render(<Button disabled>Disabled</Button>)
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    test('muestra loading state', () => {
      render(<Button loading>Loading</Button>)
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })
  })

  describe('Input Component', () => {
    test('renderiza con label', () => {
      render(<Input label="Email" />)
      expect(screen.getByLabelText('Email')).toBeInTheDocument()
    })

    test('maneja cambios de valor', async () => {
      const handleChange = jest.fn()
      render(<Input onChange={handleChange} />)
      
      const input = screen.getByRole('textbox')
      await userEvent.type(input, 'test value')
      
      expect(handleChange).toHaveBeenCalled()
    })

    test('muestra errores de validación', () => {
      render(<Input error="Campo requerido" />)
      expect(screen.getByText('Campo requerido')).toBeInTheDocument()
    })

    test('aplica estilos de error', () => {
      render(<Input error="Error" />)
      const input = screen.getByRole('textbox')
      expect(input).toHaveClass('border-destructive')
    })
  })

  describe('Card Component', () => {
    test('renderiza contenido correctamente', () => {
      render(
        <Card>
          <Card.Header>
            <Card.Title>Test Title</Card.Title>
          </Card.Header>
          <Card.Content>
            <p>Test content</p>
          </Card.Content>
        </Card>
      )
      
      expect(screen.getByText('Test Title')).toBeInTheDocument()
      expect(screen.getByText('Test content')).toBeInTheDocument()
    })
  })

  describe('Badge Component', () => {
    test('renderiza con variantes', () => {
      render(<Badge variant="success">Active</Badge>)
      const badge = screen.getByText('Active')
      expect(badge).toHaveClass('bg-green-500')
    })
  })

  describe('Modal Component', () => {
    test('se abre y cierra correctamente', async () => {
      const handleClose = jest.fn()
      const { rerender } = render(
        <Modal isOpen={false} onClose={handleClose}>
          <p>Modal content</p>
        </Modal>
      )
      
      expect(screen.queryByText('Modal content')).not.toBeInTheDocument()
      
      rerender(
        <Modal isOpen={true} onClose={handleClose}>
          <p>Modal content</p>
        </Modal>
      )
      
      expect(screen.getByText('Modal content')).toBeInTheDocument()
    })

    test('cierra al hacer click en backdrop', async () => {
      const handleClose = jest.fn()
      render(
        <Modal isOpen={true} onClose={handleClose} closeOnBackdrop={true}>
          <p>Modal content</p>
        </Modal>
      )
      
      const backdrop = screen.getByTestId('modal-backdrop')
      await userEvent.click(backdrop)
      
      expect(handleClose).toHaveBeenCalled()
    })
  })
})

describe('📱 Responsive Functionality', () => {
  // Mock window.innerWidth
  const mockInnerWidth = (width: number) => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: width,
    })
    window.dispatchEvent(new Event('resize'))
  }

  describe('useResponsive Hook', () => {
    test('detecta dispositivo móvil', () => {
      let hookResult: any
      
      function TestComponent() {
        hookResult = useResponsive()
        return <div>Test</div>
      }
      
      act(() => {
        mockInnerWidth(600) // Móvil
      })
      
      render(<TestComponent />)
      
      expect(hookResult.isMobile).toBe(true)
      expect(hookResult.deviceType).toBe('mobile')
    })

    test('detecta tablet', () => {
      let hookResult: any
      
      function TestComponent() {
        hookResult = useResponsive()
        return <div>Test</div>
      }
      
      act(() => {
        mockInnerWidth(800) // Tablet
      })
      
      render(<TestComponent />)
      
      expect(hookResult.isTablet).toBe(true)
      expect(hookResult.deviceType).toBe('tablet')
    })

    test('detecta desktop', () => {
      let hookResult: any
      
      function TestComponent() {
        hookResult = useResponsive()
        return <div>Test</div>
      }
      
      act(() => {
        mockInnerWidth(1200) // Desktop
      })
      
      render(<TestComponent />)
      
      expect(hookResult.isDesktop).toBe(true)
      expect(hookResult.deviceType).toBe('desktop')
    })
  })
})

describe('📊 Data Table Functionality', () => {
  const sampleData = [
    { id: 1, name: 'John Doe', email: 'john@example.com', status: 'active' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'inactive' },
    { id: 3, name: 'Bob Johnson', email: 'bob@example.com', status: 'active' },
  ]

  const sampleColumns = [
    { key: 'name', label: 'Name', sortable: true, priority: 1 },
    { key: 'email', label: 'Email', priority: 2 },
    { key: 'status', label: 'Status', priority: 1 },
  ]

  test('renderiza datos correctamente', () => {
    render(
      <ResponsiveDataTable 
        data={sampleData} 
        columns={sampleColumns}
      />
    )
    
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('jane@example.com')).toBeInTheDocument()
  })

  test('funciona la búsqueda', async () => {
    render(
      <ResponsiveDataTable 
        data={sampleData} 
        columns={sampleColumns}
        searchable={true}
      />
    )
    
    const searchInput = screen.getByPlaceholderText('Buscar...')
    await userEvent.type(searchInput, 'John')
    
    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument()
  })

  test('funciona el ordenamiento', async () => {
    render(
      <ResponsiveDataTable 
        data={sampleData} 
        columns={sampleColumns}
        sortable={true}
      />
    )
    
    const nameHeader = screen.getByText('Name')
    await userEvent.click(nameHeader)
    
    // Verificar que el ordenamiento se aplicó
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('Bob Johnson') // Primer dato después del header
  })

  test('maneja estado vacío', () => {
    render(
      <ResponsiveDataTable 
        data={[]} 
        columns={sampleColumns}
        emptyMessage="No data found"
      />
    )
    
    expect(screen.getByText('No data found')).toBeInTheDocument()
  })

  test('maneja estado de carga', () => {
    render(
      <ResponsiveDataTable 
        data={sampleData} 
        columns={sampleColumns}
        loading={true}
      />
    )
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })
})

describe('🔗 API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('maneja respuestas exitosas de API', async () => {
    mockApiClient.get.mockResolvedValue({
      data: { message: 'Success' },
      status: 200
    })

    // Test component que usa API
    function TestAPIComponent() {
      const [data, setData] = React.useState(null)
      
      React.useEffect(() => {
        mockApiClient.get('/api/test').then(response => {
          setData(response.data)
        })
      }, [])
      
      return <div>{data ? data.message : 'Loading...'}</div>
    }
    
    render(<TestAPIComponent />)
    
    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument()
    })
  })

  test('maneja errores de API', async () => {
    mockApiClient.get.mockRejectedValue(new Error('Network error'))

    function TestErrorComponent() {
      const [error, setError] = React.useState(null)
      
      React.useEffect(() => {
        mockApiClient.get('/api/test').catch(err => {
          setError(err.message)
        })
      }, [])
      
      return <div>{error || 'Loading...'}</div>
    }
    
    render(<TestErrorComponent />)
    
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })
})

describe('🎯 Performance Tests', () => {
  test('componente renderiza en tiempo aceptable', () => {
    const startTime = performance.now()
    
    render(
      <ResponsiveDataTable 
        data={Array.from({ length: 100 }, (_, i) => ({
          id: i,
          name: `User ${i}`,
          email: `user${i}@example.com`
        }))} 
        columns={[
          { key: 'name', label: 'Name' },
          { key: 'email', label: 'Email' }
        ]}
      />
    )
    
    const endTime = performance.now()
    const renderTime = endTime - startTime
    
    expect(renderTime).toBeLessThan(100) // Menos de 100ms
  })

  test('búsqueda es eficiente con grandes datasets', async () => {
    const largeData = Array.from({ length: 1000 }, (_, i) => ({
      id: i,
      name: `User ${i}`,
      email: `user${i}@example.com`
    }))
    
    render(
      <ResponsiveDataTable 
        data={largeData} 
        columns={[
          { key: 'name', label: 'Name' },
          { key: 'email', label: 'Email' }
        ]}
        searchable={true}
      />
    )
    
    const searchInput = screen.getByPlaceholderText('Buscar...')
    
    const startTime = performance.now()
    await userEvent.type(searchInput, 'User 500')
    const endTime = performance.now()
    
    const searchTime = endTime - startTime
    expect(searchTime).toBeLessThan(50) // Menos de 50ms
  })
})

describe('♿ Accessibility Tests', () => {
  test('botones tienen etiquetas accesibles', () => {
    render(<Button aria-label="Save document">💾</Button>)
    
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-label', 'Save document')
  })

  test('inputs tienen labels asociados', () => {
    render(<Input label="Email Address" id="email" />)
    
    const input = screen.getByLabelText('Email Address')
    expect(input).toHaveAttribute('id', 'email')
  })

  test('modal maneja focus correctamente', () => {
    render(
      <Modal isOpen={true} onClose={jest.fn()}>
        <button>First button</button>
        <button>Second button</button>
      </Modal>
    )
    
    const firstButton = screen.getByText('First button')
    expect(firstButton).toHaveFocus()
  })

  test('navegación por teclado funciona', async () => {
    render(
      <div>
        <Button>Button 1</Button>
        <Button>Button 2</Button>
        <Button>Button 3</Button>
      </div>
    )
    
    const button1 = screen.getByText('Button 1')
    const button2 = screen.getByText('Button 2')
    
    button1.focus()
    expect(button1).toHaveFocus()
    
    await userEvent.tab()
    expect(button2).toHaveFocus()
  })
})

describe('🔒 Security Tests', () => {
  test('previene XSS en contenido dinámico', () => {
    const maliciousContent = '<script>alert("XSS")</script>'
    
    render(
      <Card>
        <Card.Content>
          <p>{maliciousContent}</p>
        </Card.Content>
      </Card>
    )
    
    // El contenido debe ser escapado
    expect(screen.getByText(maliciousContent)).toBeInTheDocument()
    expect(document.querySelector('script')).toBeNull()
  })

  test('valida inputs de formulario', async () => {
    function TestForm() {
      const [error, setError] = React.useState('')
      
      const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        const formData = new FormData(e.target as HTMLFormElement)
        const email = formData.get('email') as string
        
        if (!email.includes('@')) {
          setError('Email inválido')
        }
      }
      
      return (
        <form onSubmit={handleSubmit}>
          <Input name="email" />
          <Button type="submit">Submit</Button>
          {error && <p role="alert">{error}</p>}
        </form>
      )
    }
    
    render(<TestForm />)
    
    const input = screen.getByRole('textbox')
    const button = screen.getByRole('button')
    
    await userEvent.type(input, 'invalid-email')
    await userEvent.click(button)
    
    expect(screen.getByRole('alert')).toHaveTextContent('Email inválido')
  })
})

// Test runner utilities
export const runUITests = () => {
  // Ejecutar solo pruebas de UI
  return jest.runCLI({ testNamePattern: 'Componentes UI' }, [__dirname])
}

export const runPerformanceTests = () => {
  // Ejecutar solo pruebas de rendimiento
  return jest.runCLI({ testNamePattern: 'Performance Tests' }, [__dirname])
}

export const runAccessibilityTests = () => {
  // Ejecutar solo pruebas de accesibilidad
  return jest.runCLI({ testNamePattern: 'Accessibility Tests' }, [__dirname])
}

export const runAllTests = () => {
  // Ejecutar todas las pruebas
  return jest.runCLI({}, [__dirname])
} 