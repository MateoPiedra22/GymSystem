#!/usr/bin/env node
/**
 * Health Check Script para el Frontend Web
 * Verifica el estado del servidor Next.js y servicios externos
 */

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuración
const config = {
    port: process.env.PORT || 3000,
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 5000,
    retries: 3,
    retryDelay: 1000
};

// Logger mejorado
class Logger {
    static log(message, level = 'INFO') {
        const timestamp = new Date().toISOString();
        const colors = {
            INFO: '\x1b[36m',    // Cyan
            WARNING: '\x1b[33m', // Yellow
            ERROR: '\x1b[31m',   // Red
            SUCCESS: '\x1b[32m'  // Green
        };
        const reset = '\x1b[0m';
        const color = colors[level] || colors.INFO;
        // Logging disabled in production
    }
}

// Cliente HTTP mejorado con retry
class HttpClient {
    static async makeRequest(url, options = {}, retries = config.retries) {
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                return await this._makeSingleRequest(url, options);
            } catch (error) {
                if (attempt === retries) {
                    throw error;
                }
                Logger.log(`Intento ${attempt} falló, reintentando en ${config.retryDelay}ms...`, 'WARNING');
                await this._delay(config.retryDelay);
            }
        }
    }

    static _makeSingleRequest(url, options = {}) {
        return new Promise((resolve, reject) => {
            const urlObj = new URL(url);
            const isHttps = urlObj.protocol === 'https:';
            const client = isHttps ? https : http;
            
            const requestOptions = {
                hostname: urlObj.hostname,
                port: urlObj.port || (isHttps ? 443 : 80),
                path: urlObj.pathname + urlObj.search,
                method: 'GET',
                timeout: config.timeout,
                ...options
            };
            
            const req = client.request(requestOptions, (res) => {
                let data = '';
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    resolve({
                        statusCode: res.statusCode,
                        headers: res.headers,
                        data: data
                    });
                });
            });
            
            req.on('error', (error) => {
                reject(error);
            });
            
            req.on('timeout', () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });
            
            req.end();
        });
    }

    static _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Verificador de servicios
class ServiceChecker {
    static async checkNextJsServer() {
        try {
            const response = await HttpClient.makeRequest(`http://localhost:${config.port}`);
            
            if (response.statusCode === 200) {
                Logger.log('✅ Next.js Server: OK', 'SUCCESS');
                return { success: true, details: { statusCode: response.statusCode } };
            } else {
                Logger.log(`❌ Next.js Server: ERROR - Status ${response.statusCode}`, 'ERROR');
                return { success: false, details: { statusCode: response.statusCode } };
            }
        } catch (error) {
            Logger.log(`❌ Next.js Server: ERROR - ${error.message}`, 'ERROR');
            return { success: false, details: { error: error.message } };
        }
    }

    static async checkApiServer() {
        try {
            const response = await HttpClient.makeRequest(`${config.apiUrl}/health`);
            
            if (response.statusCode === 200) {
                Logger.log('✅ API Server: OK', 'SUCCESS');
                return { success: true, details: { statusCode: response.statusCode } };
            } else {
                Logger.log(`❌ API Server: ERROR - Status ${response.statusCode}`, 'ERROR');
                return { success: false, details: { statusCode: response.statusCode } };
            }
        } catch (error) {
            Logger.log(`❌ API Server: ERROR - ${error.message}`, 'ERROR');
            return { success: false, details: { error: error.message } };
        }
    }

    static async checkStaticFiles() {
        try {
            const response = await HttpClient.makeRequest(`http://localhost:${config.port}/favicon.ico`);
            
            if (response.statusCode === 200 || response.statusCode === 404) {
                Logger.log('✅ Static Files: OK', 'SUCCESS');
                return { success: true, details: { statusCode: response.statusCode } };
            } else {
                Logger.log(`❌ Static Files: ERROR - Status ${response.statusCode}`, 'ERROR');
                return { success: false, details: { statusCode: response.statusCode } };
            }
        } catch (error) {
            Logger.log(`❌ Static Files: ERROR - ${error.message}`, 'ERROR');
            return { success: false, details: { error: error.message } };
        }
    }
}

// Verificador de sistema
class SystemChecker {
    static async checkEnvironment() {
        try {
            const requiredEnvVars = [
                'NODE_ENV',
                'NEXT_PUBLIC_API_URL'
            ];
            
            const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
            
            if (missingVars.length === 0) {
                Logger.log('✅ Environment Variables: OK', 'SUCCESS');
                return { success: true, details: { vars: requiredEnvVars } };
            } else {
                Logger.log(`❌ Environment Variables: ERROR - Missing: ${missingVars.join(', ')}`, 'ERROR');
                return { success: false, details: { missing: missingVars } };
            }
        } catch (error) {
            Logger.log(`❌ Environment Variables: ERROR - ${error.message}`, 'ERROR');
            return { success: false, details: { error: error.message } };
        }
    }

    static async checkMemoryUsage() {
        try {
            const memUsage = process.memoryUsage();
            const memUsageMB = {
                rss: Math.round(memUsage.rss / 1024 / 1024),
                heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
                heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
                external: Math.round(memUsage.external / 1024 / 1024)
            };
            
            // Considerar saludable si el heap usado es menor a 500MB
            if (memUsageMB.heapUsed < 500) {
                Logger.log(`✅ Memory Usage: OK (${memUsageMB.heapUsed}MB used)`, 'SUCCESS');
                return { success: true, details: memUsageMB };
            } else {
                Logger.log(`⚠️ Memory Usage: HIGH (${memUsageMB.heapUsed}MB used)`, 'WARNING');
                return { success: false, details: memUsageMB };
            }
        } catch (error) {
            Logger.log(`❌ Memory Usage: ERROR - ${error.message}`, 'ERROR');
            return { success: false, details: { error: error.message } };
        }
    }

    static async checkDiskSpace() {
        try {
            const buildDir = path.join(process.cwd(), '.next');
            
            if (fs.existsSync(buildDir)) {
                const stats = fs.statSync(buildDir);
                const sizeMB = Math.round(stats.size / 1024 / 1024);
                
                if (sizeMB < 1000) { // Menos de 1GB
                    Logger.log(`✅ Disk Space: OK (${sizeMB}MB build size)`, 'SUCCESS');
                    return { success: true, details: { buildSize: sizeMB } };
                } else {
                    Logger.log(`⚠️ Disk Space: HIGH (${sizeMB}MB build size)`, 'WARNING');
                    return { success: false, details: { buildSize: sizeMB } };
                }
            } else {
                Logger.log('⚠️ Disk Space: No build directory found', 'WARNING');
                return { success: false, details: { error: 'No build directory' } };
            }
        } catch (error) {
            Logger.log(`❌ Disk Space: ERROR - ${error.message}`, 'ERROR');
            return { success: false, details: { error: error.message } };
        }
    }

    static async checkNodeVersion() {
        try {
            const version = process.version;
            const majorVersion = parseInt(version.slice(1).split('.')[0]);
            
            if (majorVersion >= 18) {
                Logger.log(`✅ Node Version: OK (${version})`, 'SUCCESS');
                return { success: true, details: { version } };
            } else {
                Logger.log(`❌ Node Version: ERROR - ${version} (requires 18+)`, 'ERROR');
                return { success: false, details: { version, required: '18+' } };
            }
        } catch (error) {
            Logger.log(`❌ Node Version: ERROR - ${error.message}`, 'ERROR');
            return { success: false, details: { error: error.message } };
        }
    }
}

// Verificador de rendimiento
class PerformanceChecker {
    static async checkResponseTime() {
        try {
            const startTime = Date.now();
            const response = await HttpClient.makeRequest(`http://localhost:${config.port}`);
            const responseTime = Date.now() - startTime;
            
            if (responseTime < 1000) { // Menos de 1 segundo
                Logger.log(`✅ Response Time: OK (${responseTime}ms)`, 'SUCCESS');
                return { success: true, details: { responseTime } };
            } else {
                Logger.log(`⚠️ Response Time: SLOW (${responseTime}ms)`, 'WARNING');
                return { success: false, details: { responseTime } };
            }
        } catch (error) {
            Logger.log(`❌ Response Time: ERROR - ${error.message}`, 'ERROR');
            return { success: false, details: { error: error.message } };
        }
    }
}

// Generador de reportes
class ReportGenerator {
    static generateReport(results) {
        const successfulChecks = results.filter(r => r.success).length;
        const totalChecks = results.length;
        const failedChecks = results.filter(r => !r.success);
        
        Logger.log(`📊 Resumen: ${successfulChecks}/${totalChecks} checks exitosos`);
        
        if (failedChecks.length > 0) {
            Logger.log('❌ Checks fallidos:', 'ERROR');
            failedChecks.forEach(check => {
                Logger.log(`  - ${check.name}: ${JSON.stringify(check.details)}`, 'ERROR');
            });
        }
        
        return {
            total: totalChecks,
            successful: successfulChecks,
            failed: failedChecks.length,
            results
        };
    }
}

async function main() {
    Logger.log('🔍 Iniciando health check del frontend...');
    
    const checks = [
        { name: 'Next.js Server', func: ServiceChecker.checkNextJsServer },
        { name: 'API Server', func: ServiceChecker.checkApiServer },
        { name: 'Static Files', func: ServiceChecker.checkStaticFiles },
        { name: 'Environment Variables', func: SystemChecker.checkEnvironment },
        { name: 'Memory Usage', func: SystemChecker.checkMemoryUsage },
        { name: 'Disk Space', func: SystemChecker.checkDiskSpace },
        { name: 'Node Version', func: SystemChecker.checkNodeVersion },
        { name: 'Response Time', func: PerformanceChecker.checkResponseTime }
    ];
    
    const results = [];
    
    for (const check of checks) {
        try {
            const result = await check.func();
            results.push({ name: check.name, success: result.success, details: result.details });
        } catch (error) {
            Logger.log(`❌ Error en check ${check.name}: ${error.message}`, 'ERROR');
            results.push({ name: check.name, success: false, details: { error: error.message } });
        }
    }
    
    const report = ReportGenerator.generateReport(results);
    
    if (report.successful === report.total) {
        Logger.log('✅ Todos los servicios están funcionando correctamente', 'SUCCESS');
        process.exit(0);
    } else {
        Logger.log(`❌ ${report.failed} servicios tienen problemas`, 'ERROR');
        process.exit(1);
    }
}

// Manejar señales de terminación
process.on('SIGTERM', () => {
    Logger.log('Recibida señal SIGTERM, terminando...');
    process.exit(0);
});

process.on('SIGINT', () => {
    Logger.log('Recibida señal SIGINT, terminando...');
    process.exit(0);
});

// Ejecutar health check
if (require.main === module) {
    main().catch(error => {
        Logger.log(`❌ Health check falló: ${error.message}`, 'ERROR');
        process.exit(1);
    });
}

module.exports = {
    ServiceChecker,
    SystemChecker,
    PerformanceChecker,
    ReportGenerator,
    HttpClient,
    Logger
}; 