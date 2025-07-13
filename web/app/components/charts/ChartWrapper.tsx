/**
 * Componente ChartWrapper - Renderiza diferentes tipos de gráficos interactivos
 * Soporta múltiples librerías y tipos de visualización
 */
'use client'

import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale
} from 'chart.js'
import { Bar, Line, Doughnut, Pie, Radar, PolarArea } from 'react-chartjs-2'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

// Registrar todos los componentes de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale
)

// Tipos de gráficos soportados
export type ChartType = 
  | 'bar' 
  | 'line' 
  | 'area' 
  | 'doughnut' 
  | 'pie' 
  | 'horizontal_bar'
  | 'multi_line'
  | 'grouped_bar'
  | 'stacked_bar'
  | 'radar'
  | 'polar'

// Configuración de colores predefinidos
const CHART_COLORS = {
  primary: '#3B82F6',
  secondary: '#10B981', 
  accent: '#F59E0B',
  danger: '#EF4444',
  purple: '#8B5CF6',
  pink: '#EC4899',
  indigo: '#6366F1',
  teal: '#14B8A6',
  orange: '#F97316',
  gray: '#6B7280'
}

const COLOR_PALETTE = Object.values(CHART_COLORS)

interface ChartData {
  labels?: string[]
  datasets?: any[]
  [key: string]: any
}

interface ChartWrapperProps {
  type: ChartType
  data: any
  title?: string
  subtitle?: string
  height?: number
  className?: string
  showLegend?: boolean
  showTooltips?: boolean
  animated?: boolean
  responsive?: boolean
  onClick?: (element: any, chart: any) => void
}

export function ChartWrapper({
  type,
  data,
  title,
  subtitle,
  height = 300,
  className = '',
  showLegend = true,
  showTooltips = true,
  animated = true,
  responsive = true,
  onClick
}: ChartWrapperProps) {
  
  // Función para preparar datos según el tipo de gráfico
  const prepareChartData = (): ChartData => {
    if (!data || !Array.isArray(data)) {
      return { labels: [], datasets: [] }
    }

    switch (type) {
      case 'bar':
      case 'horizontal_bar':
        return prepareBarData()
      
      case 'line':
      case 'area':
        return prepareLineData()
      
      case 'multi_line':
        return prepareMultiLineData()
      
      case 'doughnut':
      case 'pie':
        return preparePieData()
      
      case 'grouped_bar':
        return prepareGroupedBarData()
      
      case 'stacked_bar':
        return prepareStackedBarData()
      
      case 'radar':
        return prepareRadarData()
      
      case 'polar':
        return preparePolarData()
      
      default:
        return prepareBarData()
    }
  }

  const prepareBarData = (): ChartData => {
    const firstKey = Object.keys(data[0]).find(key => key !== 'label' && typeof data[0][key] === 'number')
    const labelKey = Object.keys(data[0]).find(key => typeof data[0][key] === 'string') || 'label'
    
    return {
      labels: data.map((item: any) => item[labelKey]),
      datasets: [{
        label: title || 'Datos',
        data: data.map((item: any) => item[firstKey!]),
        backgroundColor: type === 'horizontal_bar' 
          ? data.map((_: any, index: number) => `${COLOR_PALETTE[index % COLOR_PALETTE.length]}80`)
          : `${CHART_COLORS.primary}80`,
        borderColor: type === 'horizontal_bar'
          ? data.map((_: any, index: number) => COLOR_PALETTE[index % COLOR_PALETTE.length])
          : CHART_COLORS.primary,
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false,
      }]
    }
  }

  const prepareLineData = (): ChartData => {
    const firstKey = Object.keys(data[0]).find(key => key !== 'label' && typeof data[0][key] === 'number')
    const labelKey = Object.keys(data[0]).find(key => typeof data[0][key] === 'string') || 'label'
    
    return {
      labels: data.map((item: any) => item[labelKey]),
      datasets: [{
        label: title || 'Datos',
        data: data.map((item: any) => item[firstKey!]),
        borderColor: CHART_COLORS.primary,
        backgroundColor: type === 'area' ? `${CHART_COLORS.primary}20` : 'transparent',
        borderWidth: 3,
        pointBackgroundColor: CHART_COLORS.primary,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        fill: type === 'area',
        tension: 0.4
      }]
    }
  }

  const prepareMultiLineData = (): ChartData => {
    const labelKey = Object.keys(data[0]).find(key => typeof data[0][key] === 'string') || 'mes'
    const numericKeys = Object.keys(data[0]).filter(key => key !== labelKey && typeof data[0][key] === 'number')
    
    return {
      labels: data.map((item: any) => item[labelKey]),
      datasets: numericKeys.map((key, index) => ({
        label: key.charAt(0).toUpperCase() + key.slice(1),
        data: data.map((item: any) => item[key]),
        borderColor: COLOR_PALETTE[index % COLOR_PALETTE.length],
        backgroundColor: `${COLOR_PALETTE[index % COLOR_PALETTE.length]}20`,
        borderWidth: 3,
        pointBackgroundColor: COLOR_PALETTE[index % COLOR_PALETTE.length],
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        tension: 0.4
      }))
    }
  }

  const preparePieData = (): ChartData => {
    const firstKey = Object.keys(data[0]).find(key => key !== 'label' && typeof data[0][key] === 'number')
    const labelKey = Object.keys(data[0]).find(key => typeof data[0][key] === 'string') || 'label'
    
    return {
      labels: data.map((item: any) => item[labelKey]),
      datasets: [{
        data: data.map((item: any) => item[firstKey!]),
        backgroundColor: data.map((_: any, index: number) => COLOR_PALETTE[index % COLOR_PALETTE.length]),
        borderColor: '#ffffff',
        borderWidth: 3,
        hoverBorderWidth: 5
      }]
    }
  }

  const prepareGroupedBarData = (): ChartData => {
    const labelKey = Object.keys(data[0]).find(key => typeof data[0][key] === 'string') || 'tipo'
    const numericKeys = Object.keys(data[0]).filter(key => key !== labelKey && typeof data[0][key] === 'number')
    
    return {
      labels: data.map((item: any) => item[labelKey]),
      datasets: numericKeys.map((key, index) => ({
        label: key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' '),
        data: data.map((item: any) => item[key]),
        backgroundColor: `${COLOR_PALETTE[index % COLOR_PALETTE.length]}80`,
        borderColor: COLOR_PALETTE[index % COLOR_PALETTE.length],
        borderWidth: 2,
        borderRadius: 4
      }))
    }
  }

  const prepareStackedBarData = (): ChartData => {
    return prepareGroupedBarData() // Misma estructura, diferente configuración de opciones
  }

  const prepareRadarData = (): ChartData => {
    const numericKeys = Object.keys(data[0]).filter(key => typeof data[0][key] === 'number')
    
    return {
      labels: numericKeys.map(key => key.charAt(0).toUpperCase() + key.slice(1).replace('_', ' ')),
      datasets: [{
        label: title || 'Métricas',
        data: numericKeys.map(key => data[0][key]),
        backgroundColor: `${CHART_COLORS.primary}30`,
        borderColor: CHART_COLORS.primary,
        borderWidth: 3,
        pointBackgroundColor: CHART_COLORS.primary,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2
      }]
    }
  }

  const preparePolarData = (): ChartData => {
    const firstKey = Object.keys(data[0]).find(key => key !== 'label' && typeof data[0][key] === 'number')
    const labelKey = Object.keys(data[0]).find(key => typeof data[0][key] === 'string') || 'label'
    
    return {
      labels: data.map((item: any) => item[labelKey]),
      datasets: [{
        data: data.map((item: any) => item[firstKey!]),
        backgroundColor: data.map((_: any, index: number) => `${COLOR_PALETTE[index % COLOR_PALETTE.length]}60`),
        borderColor: data.map((_: any, index: number) => COLOR_PALETTE[index % COLOR_PALETTE.length]),
        borderWidth: 2
      }]
    }
  }

  // Configuración común para todos los gráficos
  const getChartOptions = () => {
    const baseOptions = {
      responsive,
      maintainAspectRatio: false,
      animation: animated,
      plugins: {
        legend: {
          display: showLegend,
          position: 'top' as const,
          labels: {
            padding: 20,
            usePointStyle: true,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          enabled: showTooltips,
          mode: 'index' as const,
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#ffffff',
          bodyColor: '#ffffff',
          borderColor: 'rgba(255, 255, 255, 0.2)',
          borderWidth: 1
        }
      },
      onClick: onClick || undefined
    }

    // Configuraciones específicas por tipo
    if (type === 'horizontal_bar') {
      return {
        ...baseOptions,
        indexAxis: 'y' as const,
        scales: {
          x: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          },
          y: {
            grid: {
              display: false
            }
          }
        }
      }
    }

    if (type === 'bar' || type === 'grouped_bar') {
      return {
        ...baseOptions,
        scales: {
          x: {
            grid: {
              display: false
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          }
        }
      }
    }

    if (type === 'stacked_bar') {
      return {
        ...baseOptions,
        scales: {
          x: {
            stacked: true,
            grid: {
              display: false
            }
          },
          y: {
            stacked: true,
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          }
        }
      }
    }

    if (type === 'line' || type === 'area' || type === 'multi_line') {
      return {
        ...baseOptions,
        scales: {
          x: {
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            }
          }
        },
        elements: {
          point: {
            hoverRadius: 8
          }
        }
      }
    }

    if (type === 'radar') {
      return {
        ...baseOptions,
        scales: {
          r: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            },
            pointLabels: {
              font: {
                size: 12
              }
            }
          }
        }
      }
    }

    return baseOptions
  }

  // Renderizar el componente de gráfico apropiado
  const renderChart = () => {
    const chartData = prepareChartData()
    const options = getChartOptions() as any

    // Asegurar que datasets existe y tiene el tipo correcto
    const safeChartData = {
      ...chartData,
      datasets: chartData.datasets || []
    }

    switch (type) {
      case 'bar':
      case 'horizontal_bar':
      case 'grouped_bar':
      case 'stacked_bar':
        return <Bar data={safeChartData} options={options} />
      
      case 'line':
      case 'area':
      case 'multi_line':
        return <Line data={safeChartData} options={options} />
      
      case 'doughnut':
        return <Doughnut data={safeChartData} options={options} />
      
      case 'pie':
        return <Pie data={safeChartData} options={options} />
      
      case 'radar':
        return <Radar data={safeChartData} options={options} />
      
      case 'polar':
        return <PolarArea data={safeChartData} options={options} />
      
      default:
        return <Bar data={safeChartData} options={options} />
    }
  }

  // Calcular tendencia si es aplicable
  const getTrend = () => {
    if (!data || data.length < 2) return null
    
    const firstKey = Object.keys(data[0]).find(key => typeof data[0][key] === 'number')
    if (!firstKey) return null
    
    const firstValue = data[0][firstKey]
    const lastValue = data[data.length - 1][firstKey]
    const change = ((lastValue - firstValue) / firstValue) * 100
    
    if (Math.abs(change) < 1) return { direction: 'stable', value: 0 }
    return {
      direction: change > 0 ? 'up' : 'down',
      value: Math.abs(change)
    }
  }

  const trend = getTrend()

  return (
    <div className={`gym-card ${className}`}>
      {(title || subtitle) && (
        <div className="mb-6">
          {title && (
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                {title}
              </h3>
              {trend && (
                <div className={`flex items-center space-x-1 text-sm ${
                  trend.direction === 'up' ? 'text-green-600' :
                  trend.direction === 'down' ? 'text-red-600' : 'text-gray-500'
                }`}>
                  {trend.direction === 'up' && <TrendingUp size={16} />}
                  {trend.direction === 'down' && <TrendingDown size={16} />}
                  {trend.direction === 'stable' && <Minus size={16} />}
                  <span>{trend.value.toFixed(1)}%</span>
                </div>
              )}
            </div>
          )}
          {subtitle && (
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {subtitle}
            </p>
          )}
        </div>
      )}
      
      <div style={{ height: `${height}px` }}>
        {renderChart()}
      </div>
    </div>
  )
} 