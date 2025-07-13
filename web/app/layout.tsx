/**
 * Root Layout
 * Este componente define la estructura base de la aplicación web
 */
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './styles/globals.css'
import { Providers } from './providers'
import { OfflineIndicator } from './components/OfflineIndicator'
import { Navigation, TopBar } from './components/Navigation'
import { SkipToContentLink } from './components/Accessibility'
import { AnimatedPage } from './components/Animations'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sistema de Gimnasio',
  description: 'Sistema integral de gestión para gimnasios',
  viewport: 'width=device-width, initial-scale=1',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#0f172a' }
  ]
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        <Providers>
          <SkipToContentLink />
          <OfflineIndicator showBadge={true} showBanner={true} />
          
          <div className="flex h-screen">
            <Navigation />
            <div className="flex-1 flex flex-col lg:ml-64">
              <TopBar />
              <main className="flex-1 overflow-auto p-6">
                <AnimatedPage>
                  {children}
                </AnimatedPage>
              </main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  )
}
