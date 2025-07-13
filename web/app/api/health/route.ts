// /web/app/api/health/route.ts
import { NextResponse } from 'next/server';
import { NextRequest } from 'next/server';

// Forzar renderizado dinámico
export const dynamic = 'force-dynamic'

interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  version: string;
  environment: string;
  checks: {
    database: HealthCheck;
    redis: HealthCheck;
    api: HealthCheck;
    disk: HealthCheck;
    memory: HealthCheck;
  };
  response_time: number;
}

interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time?: number;
  error?: string;
  details?: any;
}

async function checkDatabase(): Promise<HealthCheck> {
  const startTime = Date.now();
  
  try {
    // Verificar conectividad con la base de datos del backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(5000), // 5 segundos timeout
    });

    const responseTime = Date.now() - startTime;
    
    if (!response.ok) {
      return {
        status: 'unhealthy',
        response_time: responseTime,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = await response.json();
    
    // Verificar que la respuesta incluya información de la base de datos
    if (data.database && data.database.status === 'healthy') {
      return {
        status: 'healthy',
        response_time: responseTime,
        details: data.database,
      };
    } else {
      return {
        status: 'degraded',
        response_time: responseTime,
        error: 'Database check failed in backend response',
        details: data.database,
      };
    }
  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      status: 'unhealthy',
      response_time: responseTime,
      error: error instanceof Error ? error.message : 'Unknown database error',
    };
  }
}

async function checkRedis(): Promise<HealthCheck> {
  const startTime = Date.now();
  
  try {
    // Verificar Redis a través del backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(3000), // 3 segundos timeout
    });

    const responseTime = Date.now() - startTime;
    
    if (!response.ok) {
      return {
        status: 'unhealthy',
        response_time: responseTime,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = await response.json();
    
    if (data.redis && data.redis.status === 'healthy') {
      return {
        status: 'healthy',
        response_time: responseTime,
        details: data.redis,
      };
    } else {
      return {
        status: 'degraded',
        response_time: responseTime,
        error: 'Redis check failed in backend response',
        details: data.redis,
      };
    }
  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      status: 'unhealthy',
      response_time: responseTime,
      error: error instanceof Error ? error.message : 'Unknown Redis error',
    };
  }
}

async function checkAPI(): Promise<HealthCheck> {
  const startTime = Date.now();
  
  try {
    // Verificar conectividad general con el backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(3000), // 3 segundos timeout
    });

    const responseTime = Date.now() - startTime;
    
    if (!response.ok) {
      return {
        status: 'unhealthy',
        response_time: responseTime,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = await response.json();
    
    return {
      status: 'healthy',
      response_time: responseTime,
      details: {
        status: data.status,
        version: data.version,
        uptime: data.uptime,
      },
    };
  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      status: 'unhealthy',
      response_time: responseTime,
      error: error instanceof Error ? error.message : 'Unknown API error',
    };
  }
}

function checkDisk(): HealthCheck {
  try {
    // En Next.js, no tenemos acceso directo al sistema de archivos del servidor
    // pero podemos verificar que podemos escribir en el directorio temporal
    const tempDir = process.env.TEMP || process.env.TMP || '/tmp';
    
    // Verificar que el directorio temporal existe y es accesible
    const fs = require('fs');
    const path = require('path');
    
    if (fs.existsSync(tempDir) && fs.statSync(tempDir).isDirectory()) {
      // Verificar permisos de escritura
      const testFile = path.join(tempDir, `health-check-${Date.now()}.tmp`);
      
      try {
        fs.writeFileSync(testFile, 'health check test');
        fs.unlinkSync(testFile);
        
        return {
          status: 'healthy',
          details: {
            temp_directory: tempDir,
            writable: true,
          },
        };
      } catch (writeError) {
        return {
          status: 'degraded',
          error: 'Cannot write to temp directory',
          details: {
            temp_directory: tempDir,
            writable: false,
          },
        };
      }
    } else {
      return {
        status: 'degraded',
        error: 'Temp directory not accessible',
        details: {
          temp_directory: tempDir,
          exists: false,
        },
      };
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown disk error',
    };
  }
}

function checkMemory(): HealthCheck {
  try {
    // En Node.js, podemos obtener información básica de memoria
    const memUsage = process.memoryUsage();
    const memUsageMB = {
      rss: Math.round(memUsage.rss / 1024 / 1024),
      heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
      heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
      external: Math.round(memUsage.external / 1024 / 1024),
    };

    // Verificar si el uso de memoria está en niveles saludables
    const heapUsagePercent = (memUsage.heapUsed / memUsage.heapTotal) * 100;
    
    if (heapUsagePercent > 90) {
      return {
        status: 'unhealthy',
        error: 'High memory usage',
        details: {
          ...memUsageMB,
          heap_usage_percent: Math.round(heapUsagePercent),
        },
      };
    } else if (heapUsagePercent > 75) {
      return {
        status: 'degraded',
        details: {
          ...memUsageMB,
          heap_usage_percent: Math.round(heapUsagePercent),
        },
      };
    } else {
      return {
        status: 'healthy',
        details: {
          ...memUsageMB,
          heap_usage_percent: Math.round(heapUsagePercent),
        },
      };
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown memory error',
    };
  }
}

function determineOverallStatus(checks: HealthCheckResult['checks']): 'healthy' | 'degraded' | 'unhealthy' {
  const statuses = Object.values(checks).map(check => check.status);
  
  if (statuses.every(status => status === 'healthy')) {
    return 'healthy';
  } else if (statuses.some(status => status === 'unhealthy')) {
    return 'unhealthy';
  } else {
    return 'degraded';
  }
}

export async function GET(request: NextRequest) {
  const startTime = Date.now();
  
  try {
    // Ejecutar todas las verificaciones en paralelo
    const [databaseCheck, redisCheck, apiCheck] = await Promise.allSettled([
      checkDatabase(),
      checkRedis(),
      checkAPI(),
    ]);

    // Verificaciones locales (síncronas)
    const diskCheck = checkDisk();
    const memoryCheck = checkMemory();

    // Construir resultado
    const checks = {
      database: databaseCheck.status === 'fulfilled' ? databaseCheck.value : {
        status: 'unhealthy' as const,
        error: databaseCheck.reason?.message || 'Database check failed',
      },
      redis: redisCheck.status === 'fulfilled' ? redisCheck.value : {
        status: 'unhealthy' as const,
        error: redisCheck.reason?.message || 'Redis check failed',
      },
      api: apiCheck.status === 'fulfilled' ? apiCheck.value : {
        status: 'unhealthy' as const,
        error: apiCheck.reason?.message || 'API check failed',
      },
      disk: diskCheck,
      memory: memoryCheck,
    };

    const overallStatus = determineOverallStatus(checks);
    const responseTime = Date.now() - startTime;

    const healthResult: HealthCheckResult = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      checks,
      response_time: responseTime,
    };

    // Determinar código de estado HTTP
    let statusCode = 200;
    if (overallStatus === 'unhealthy') {
      statusCode = 503; // Service Unavailable
    } else if (overallStatus === 'degraded') {
      statusCode = 200; // OK pero con advertencias
    }

    return NextResponse.json(healthResult, { status: statusCode });

  } catch (error) {
    const responseTime = Date.now() - startTime;
    
    const errorResult: HealthCheckResult = {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      checks: {
        database: { status: 'unhealthy', error: 'Health check failed' },
        redis: { status: 'unhealthy', error: 'Health check failed' },
        api: { status: 'unhealthy', error: 'Health check failed' },
        disk: { status: 'unhealthy', error: 'Health check failed' },
        memory: { status: 'unhealthy', error: 'Health check failed' },
      },
      response_time: responseTime,
    };

    return NextResponse.json(errorResult, { status: 503 });
  }
}

// Endpoint adicional para health check simple (para load balancers)
export async function HEAD() {
  try {
    // Verificación rápida de conectividad con el backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(2000), // 2 segundos timeout
    });

    if (response.ok) {
      return new NextResponse(null, { status: 200 });
    } else {
      return new NextResponse(null, { status: 503 });
    }
  } catch (error) {
    return new NextResponse(null, { status: 503 });
  }
} 