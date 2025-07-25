# GymSystem - Sistema de Gestión de Gimnasio Modular

## 1. Descripción General del Producto

GymSystem es un sistema integral de gestión de gimnasio con arquitectura modular independiente, backend en Python y frontend web moderno con capacidades desktop a través de Tauri.

El sistema resuelve la gestión completa de gimnasios incluyendo miembros, rutinas personalizadas, clases, empleados, pagos y análisis en tiempo real, dirigido a propietarios de gimnasios, administradores y personal operativo.

Objetivo: Crear la plataforma más completa, personalizable y resiliente del mercado con mensajería automática WhatsApp y arquitectura que garantiza funcionamiento independiente de cada módulo.

## 2. Características Principales

### 2.1 Roles de Usuario

| Rol | Método de Registro | Permisos Principales |
|-----|-------------------|---------------------|
| Super Admin | Instalación inicial | Control total del sistema, configuración global, gestión de empleados |
| Administrador | Creado por Super Admin | Gestión completa del gimnasio, reportes avanzados, configuración de marca |
| Empleado/Staff | Registro por Admin | Check-in/out, ventas, atención al cliente, gestión básica de usuarios |
| Entrenador | Registro por Admin | Gestión de clases, rutinas personalizadas, seguimiento de usuarios |
| Usuario por Defecto | Acceso básico | Funcionalidades esenciales sin restricciones de rol para MVP |

### 2.2 Módulos del Sistema

Nuestro sistema modular consta de las siguientes páginas principales:

1. **Dashboard**: panel de control unificado con métricas en tiempo real, reportes integrados y accesos rápidos.
2. **Usuarios**: gestión completa de miembros, perfiles, membresías y seguimiento personalizado.
3. **Rutinas**: sistema avanzado de rutinas personalizadas con plantillas, estructuración automática y seguimiento de progreso.
4. **Ejercicios**: biblioteca completa de ejercicios con categorización, instrucciones y multimedia.
5. **Clases**: programación, reservas, gestión de horarios y seguimiento de asistencia.
6. **Empleados**: gestión de personal, horarios, roles y evaluaciones de desempeño.
7. **Pagos**: facturación, suscripciones, recordatorios automáticos y análisis financiero.
8. **Configuración**: personalización completa de marca, mensajería WhatsApp y configuración del sistema.

### 2.3 Detalles de Páginas

| Página | Módulo | Descripción de Funcionalidad |
|--------|--------|------------------------------|
| Dashboard | Panel de Métricas | Mostrar estadísticas en tiempo real: usuarios activos, ingresos del día, clases programadas, rutinas completadas |
| Dashboard | Reportes Integrados | Gráficos interactivos de rendimiento, análisis de tendencias, proyecciones financieras |
| Dashboard | Accesos Rápidos | Botones para funciones frecuentes: nuevo usuario, check-in rápido, nueva rutina, programar clase |
| Dashboard | Centro de Notificaciones | Alertas inteligentes: pagos vencidos, clases por confirmar, rutinas pendientes |
| Usuarios | Gestión de Perfiles | Crear perfiles completos con datos personales, fotos, objetivos fitness, historial médico básico |
| Usuarios | Sistema de Membresías | Gestión de tipos de membresía, renovaciones automáticas, estados activos/inactivos |
| Usuarios | Check-in/Check-out | Sistema de entrada con QR, RFID o búsqueda manual, registro de tiempo de permanencia |
| Usuarios | Seguimiento de Progreso | Métricas corporales, objetivos, logros y evolución fotográfica |
| Rutinas | Creador de Rutinas | Editor visual para crear rutinas personalizadas con drag & drop de ejercicios |
| Rutinas | Sistema de Plantillas | Biblioteca de plantillas predefinidas por objetivos: pérdida de peso,