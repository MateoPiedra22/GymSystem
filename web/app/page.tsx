'use client'
export const dynamic = 'force-dynamic'
/**
 * Página principal del Dashboard Ultra Moderno y Profesional
 * Muestra información clave del gimnasio con diseño profesional y armónico
 */

import React from 'react'
import { DashboardLayout } from './components/DashboardLayout'
import { DashboardOverview } from './components/DashboardOverview'

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header principal mejorado */}
        <div className="page-header">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title">
                🏋️ Dashboard Principal
              </h1>
              <p className="page-subtitle">
                Resumen general del estado del gimnasio y sistema P2P
              </p>
            </div>
            
            <div className="hidden md:flex items-center space-x-4 text-white/80">
              <div className="text-center">
                <div className="text-2xl font-bold" id="system-status">100%</div>
                <div className="text-sm">Sistema Activo</div>
              </div>
              <div className="w-px h-12 bg-white/20"></div>
              <div className="text-center">
                <div className="text-2xl font-bold" id="system-health">✅</div>
                <div className="text-sm">Todo Funcional</div>
              </div>
            </div>
          </div>
        </div>

        {/* Contenido del dashboard modernizado */}
        <DashboardOverview />

        {/* Información adicional del sistema */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="gym-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="mr-2">🔄</span>
              Estado del Sistema
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Backend API</span>
                <span className="gym-badge-success">Operativo</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Base de Datos</span>
                <span className="gym-badge-success">Conectada</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Cache Redis</span>
                <span className="gym-badge-success">Activo</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Frontend</span>
                <span className="gym-badge-success">Funcionando</span>
              </div>
            </div>
          </div>

          <div className="gym-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="mr-2">⚡</span>
              Rendimiento
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Velocidad de carga</span>
                <span className="gym-badge-success">Excelente</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Uso de memoria</span>
                <span className="gym-badge-info">Optimizado</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Conectividad</span>
                <span className="gym-badge-success">Estable</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Sincronización</span>
                <span className="gym-badge-success">En tiempo real</span>
              </div>
            </div>
          </div>

          <div className="gym-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <span className="mr-2">🎯</span>
              Acciones Rápidas
            </h3>
            <div className="space-y-3">
              <button className="w-full gym-btn-primary">
                <span className="mr-2">👤</span>
                Nuevo Usuario
              </button>
              <button className="w-full gym-btn-secondary">
                <span className="mr-2">📅</span>
                Nueva Clase
              </button>
              <button className="w-full gym-btn-accent">
                <span className="mr-2">💰</span>
                Registrar Pago
              </button>
              <button className="w-full gym-btn-success">
                <span className="mr-2">📊</span>
                Ver Reportes
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
