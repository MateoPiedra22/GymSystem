/** @type {import('next').NextConfig} */
const nextConfig = {
  // Configuración para standalone mode optimizada
  output: 'standalone',
  
  // Configuración de imágenes optimizada
  images: {
    domains: ['localhost', '127.0.0.1'],
    unoptimized: true,
  },
  
  // Configuración de headers de seguridad mejorada
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          }
        ]
      }
    ]
  },
  
  // Configuración de variables de entorno seguras
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost/api',
  },
  
  // Configuración de compilación optimizada
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
  
  // Configuración de webpack optimizada
  webpack: (config, { isServer, dev }) => {
    // Configuración específica para cliente
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        url: false,
        zlib: false,
        http: false,
        https: false,
        assert: false,
        os: false,
        path: false
      }
    }
    
    return config
  },
  
  // Configuración de seguridad adicional
  poweredByHeader: false,
  compress: true,
  
  // Configuración de TypeScript
  typescript: {
    ignoreBuildErrors: true,
  },
  
  // Configuración de ESLint
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Configuración de transpilación
  transpilePackages: ['@tanstack/react-query', 'recharts'],
}

module.exports = nextConfig
