'use client'

import { useState, useEffect, ReactNode } from 'react'
import { cn } from '../../utils/cn'

// Breakpoints estándar para la aplicación
export const Breakpoints = {
  sm: 640,   // móviles grandes
  md: 768,   // tablets
  lg: 1024,  // laptops pequeñas
  xl: 1280,  // desktops
  '2xl': 1536 // pantallas grandes
} as const

export type BreakpointKey = keyof typeof Breakpoints
export type DeviceType = 'mobile' | 'tablet' | 'desktop'

// Hook para detectar el tamaño de pantalla actual
export function useResponsive() {
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 })
  const [deviceType, setDeviceType] = useState<DeviceType>('desktop')
  const [currentBreakpoint, setCurrentBreakpoint] = useState<BreakpointKey>('lg')

  useEffect(() => {
    function handleResize() {
      const width = window.innerWidth
      const height = window.innerHeight
      
      setWindowSize({ width, height })

      // Determinar tipo de dispositivo
      if (width < Breakpoints.md) {
        setDeviceType('mobile')
        setCurrentBreakpoint(width < Breakpoints.sm ? 'sm' : 'sm')
      } else if (width < Breakpoints.lg) {
        setDeviceType('tablet')
        setCurrentBreakpoint('md')
      } else {
        setDeviceType('desktop')
        if (width < Breakpoints.xl) {
          setCurrentBreakpoint('lg')
        } else if (width < Breakpoints['2xl']) {
          setCurrentBreakpoint('xl')
        } else {
          setCurrentBreakpoint('2xl')
        }
      }
    }

    // Establecer tamaño inicial
    handleResize()

    // Agregar listener
    window.addEventListener('resize', handleResize)

    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return {
    windowSize,
    deviceType,
    currentBreakpoint,
    isMobile: deviceType === 'mobile',
    isTablet: deviceType === 'tablet',
    isDesktop: deviceType === 'desktop',
    width: windowSize.width,
    height: windowSize.height
  }
}

// Componente para renderizado condicional según el tamaño de pantalla
interface ResponsiveProps {
  children: ReactNode
  showOn?: DeviceType[]
  hideOn?: DeviceType[]
  className?: string
}

export function Responsive({ children, showOn, hideOn, className }: ResponsiveProps) {
  const { deviceType } = useResponsive()

  // Si se especifica showOn, solo mostrar en esos dispositivos
  if (showOn && !showOn.includes(deviceType)) {
    return null
  }

  // Si se especifica hideOn, ocultar en esos dispositivos
  if (hideOn && hideOn.includes(deviceType)) {
    return null
  }

  return <div className={className}>{children}</div>
}

// Componente Grid responsivo con diferentes layouts
interface ResponsiveGridProps {
  children: ReactNode
  className?: string
  cols?: {
    mobile?: number
    tablet?: number
    desktop?: number
  }
  gap?: {
    mobile?: string
    tablet?: string
    desktop?: string
  }
}

export function ResponsiveGrid({ 
  children, 
  className, 
  cols = { mobile: 1, tablet: 2, desktop: 3 },
  gap = { mobile: 'gap-4', tablet: 'gap-6', desktop: 'gap-8' }
}: ResponsiveGridProps) {
  const { deviceType } = useResponsive()

  const getGridClasses = () => {
    const baseClasses = 'grid'
    
    // Columnas según dispositivo
    let colClasses = ''
    if (deviceType === 'mobile') {
      colClasses = `grid-cols-${cols.mobile || 1}`
    } else if (deviceType === 'tablet') {
      colClasses = `grid-cols-${cols.tablet || 2}`
    } else {
      colClasses = `grid-cols-${cols.desktop || 3}`
    }

    // Gap según dispositivo
    let gapClasses = ''
    if (deviceType === 'mobile') {
      gapClasses = gap.mobile || 'gap-4'
    } else if (deviceType === 'tablet') {
      gapClasses = gap.tablet || 'gap-6'
    } else {
      gapClasses = gap.desktop || 'gap-8'
    }

    return cn(baseClasses, colClasses, gapClasses, className)
  }

  return (
    <div className={getGridClasses()}>
      {children}
    </div>
  )
}

// Componente para manejar tablas responsivas
interface ResponsiveTableProps {
  children: ReactNode
  className?: string
  stackOnMobile?: boolean
}

export function ResponsiveTable({ 
  children, 
  className, 
  stackOnMobile = true 
}: ResponsiveTableProps) {
  const { isMobile } = useResponsive()

  if (isMobile && stackOnMobile) {
    return (
      <div className={cn('space-y-4', className)}>
        {children}
      </div>
    )
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <div className="min-w-full">
        {children}
      </div>
    </div>
  )
}

// Componente para contenedores con padding responsivo
interface ResponsiveContainerProps {
  children: ReactNode
  className?: string
  padding?: {
    mobile?: string
    tablet?: string
    desktop?: string
  }
  maxWidth?: boolean
}

export function ResponsiveContainer({ 
  children, 
  className,
  padding = { mobile: 'px-4', tablet: 'px-6', desktop: 'px-8' },
  maxWidth = true
}: ResponsiveContainerProps) {
  const { deviceType } = useResponsive()

  const getPaddingClasses = () => {
    if (deviceType === 'mobile') {
      return padding.mobile || 'px-4'
    } else if (deviceType === 'tablet') {
      return padding.tablet || 'px-6'
    } else {
      return padding.desktop || 'px-8'
    }
  }

  const containerClasses = cn(
    getPaddingClasses(),
    maxWidth && 'mx-auto max-w-7xl',
    className
  )

  return (
    <div className={containerClasses}>
      {children}
    </div>
  )
}

// Componente para navegación adaptativa
interface ResponsiveNavProps {
  children: ReactNode
  mobileComponent?: ReactNode
  tabletComponent?: ReactNode
  desktopComponent?: ReactNode
  className?: string
}

export function ResponsiveNav({ 
  children, 
  mobileComponent, 
  tabletComponent, 
  desktopComponent, 
  className 
}: ResponsiveNavProps) {
  const { deviceType } = useResponsive()

  if (deviceType === 'mobile' && mobileComponent) {
    return <div className={className}>{mobileComponent}</div>
  }

  if (deviceType === 'tablet' && tabletComponent) {
    return <div className={className}>{tabletComponent}</div>
  }

  if (deviceType === 'desktop' && desktopComponent) {
    return <div className={className}>{desktopComponent}</div>
  }

  // Fallback al contenido por defecto
  return <div className={className}>{children}</div>
}

// Componente para manejo de espaciado responsivo
interface ResponsiveSpacingProps {
  children: ReactNode
  className?: string
  spacing?: {
    mobile?: string
    tablet?: string
    desktop?: string
  }
}

export function ResponsiveSpacing({ 
  children, 
  className,
  spacing = { mobile: 'space-y-4', tablet: 'space-y-6', desktop: 'space-y-8' }
}: ResponsiveSpacingProps) {
  const { deviceType } = useResponsive()

  const getSpacingClasses = () => {
    if (deviceType === 'mobile') {
      return spacing.mobile || 'space-y-4'
    } else if (deviceType === 'tablet') {
      return spacing.tablet || 'space-y-6'
    } else {
      return spacing.desktop || 'space-y-8'
    }
  }

  return (
    <div className={cn(getSpacingClasses(), className)}>
      {children}
    </div>
  )
}

// Utilidades para clases CSS responsivas
export const ResponsiveClasses = {
  // Paddings responsivos
  padding: {
    sm: 'px-4 py-2 sm:px-6 sm:py-3 lg:px-8 lg:py-4',
    md: 'px-6 py-3 sm:px-8 sm:py-4 lg:px-12 lg:py-6',
    lg: 'px-8 py-4 sm:px-12 sm:py-6 lg:px-16 lg:py-8'
  },
  
  // Grids responsivos comunes
  grid: {
    cards: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6 lg:gap-8',
    kpis: 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4 lg:gap-6',
    charts: 'grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8',
    form: 'grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6'
  },
  
  // Texto responsivo
  text: {
    title: 'text-2xl sm:text-3xl lg:text-4xl font-bold',
    subtitle: 'text-lg sm:text-xl lg:text-2xl font-semibold',
    body: 'text-sm sm:text-base',
    caption: 'text-xs sm:text-sm'
  },
  
  // Espaciado responsivo
  spacing: {
    section: 'space-y-6 sm:space-y-8 lg:space-y-12',
    content: 'space-y-4 sm:space-y-6 lg:space-y-8',
    items: 'space-y-2 sm:space-y-3 lg:space-y-4'
  }
}

export default { useResponsive, Responsive, ResponsiveGrid, ResponsiveTable, ResponsiveContainer, ResponsiveNav, ResponsiveSpacing, ResponsiveClasses } 