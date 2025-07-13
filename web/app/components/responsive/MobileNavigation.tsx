'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import * as Icons from '../ui/Icons'
import { cn } from '../../utils/cn'

interface NavLink {
  href: string
  label: string
  icon: any
  exact?: boolean
}

interface MobileNavigationProps {
  navLinks: NavLink[]
  isOpen: boolean
  onClose: () => void
}

export function MobileNavigation({ navLinks, isOpen, onClose }: MobileNavigationProps) {
  const pathname = usePathname()

  const isActive = (link: NavLink) => {
    if (!pathname) return false
    if (link.exact) {
      return pathname === link.href
    }
    return pathname.startsWith(link.href) && link.href !== '/'
  }

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Drawer móvil */}
      <div className={cn(
        "fixed top-0 left-0 h-full w-64 bg-white shadow-xl transform transition-transform duration-300 ease-in-out z-50 lg:hidden",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Header del drawer */}
        <div className="flex items-center justify-between p-4 border-b bg-blue-600 text-white">
          <h2 className="text-lg font-semibold">Sistema Gimnasio</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Icons.X className="w-5 h-5 text-white" />
          </button>
        </div>
        
        {/* Lista de navegación */}
        <nav className="py-4">
          <ul className="space-y-1">
            {navLinks.map((link) => {
              const active = isActive(link)
              return (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    onClick={onClose}
                    className={cn(
                      "flex items-center px-4 py-3 mx-2 rounded-lg transition-colors duration-200",
                      active
                        ? "bg-blue-50 text-blue-700 border-r-4 border-blue-700"
                        : "text-gray-700 hover:bg-gray-100"
                    )}
                  >
                    <link.icon 
                      className={cn(
                        "mr-3",
                        active ? "text-blue-700" : "text-gray-600",
                        "w-5 h-5"
                      )}
                    />
                    <span className="font-medium">{link.label}</span>
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
        
        {/* Footer del drawer */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-gray-50">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <Icons.Users className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                Usuario Admin
              </p>
              <p className="text-xs text-gray-500 truncate">
                admin@gimnasio.com
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

// Componente de navegación bottom para móviles
interface BottomNavigationProps {
  navLinks: NavLink[]
  maxItems?: number
}

export function BottomNavigation({ navLinks, maxItems = 5 }: BottomNavigationProps) {
  const pathname = usePathname()
  const [showMore, setShowMore] = useState(false)
  
  const isActive = (link: NavLink) => {
    if (!pathname) return false
    if (link.exact) {
      return pathname === link.href
    }
    return pathname.startsWith(link.href) && link.href !== '/'
  }

  const mainLinks = navLinks.slice(0, maxItems - 1)
  const moreLinks = navLinks.slice(maxItems - 1)
  
  return (
    <>
      {/* Overlay para menú "más" */}
      {showMore && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-25 z-40"
          onClick={() => setShowMore(false)}
        />
      )}
      
      {/* Bottom navigation bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-30 lg:hidden">
        <div className="grid grid-cols-5 h-16">
          {/* Enlaces principales */}
          {mainLinks.map((link) => {
            const active = isActive(link)
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "flex flex-col items-center justify-center space-y-1 transition-colors",
                  active ? "text-blue-600" : "text-gray-600"
                )}
              >
                <link.icon 
                  className={cn(
                    active ? "text-blue-600" : "text-gray-600",
                    "w-4 h-4"
                  )}
                />
                <span className="text-xs font-medium truncate w-full text-center">
                  {link.label}
                </span>
              </Link>
            )
          })}
          
          {/* Botón "Más" */}
          {moreLinks.length > 0 && (
            <button
              onClick={() => setShowMore(!showMore)}
              className="flex flex-col items-center justify-center space-y-1 text-gray-600"
            >
              <Icons.Menu className="w-4 h-4" />
              <span className="text-xs font-medium">Más</span>
            </button>
          )}
        </div>
        
        {/* Menú desplegable "Más" */}
        {showMore && moreLinks.length > 0 && (
          <div className="absolute bottom-full left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
            <div className="py-2">
              {moreLinks.map((link) => {
                const active = isActive(link)
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setShowMore(false)}
                    className={cn(
                      "flex items-center px-4 py-3 transition-colors",
                      active ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50"
                    )}
                  >
                    <link.icon 
                      className={cn(
                        "mr-3",
                        active ? "text-blue-700" : "text-gray-600",
                        "w-5 h-5"
                      )}
                    />
                    <span className="font-medium">{link.label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </>
  )
}

// Componente de tab bar horizontal para tablets
interface TabNavigationProps {
  navLinks: NavLink[]
}

export function TabNavigation({ navLinks }: TabNavigationProps) {
  const pathname = usePathname()
  
  const isActive = (link: NavLink) => {
    if (!pathname) return false
    if (link.exact) {
      return pathname === link.href
    }
    return pathname.startsWith(link.href) && link.href !== '/'
  }

  return (
    <div className="hidden md:block lg:hidden border-b border-gray-200 bg-white">
      <div className="flex space-x-8 px-4">
        {navLinks.map((link) => {
          const active = isActive(link)
          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center space-x-2 py-4 border-b-2 font-medium text-sm transition-colors",
                active
                  ? "border-blue-600 text-blue-700"
                  : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
              )}
            >
              <link.icon 
                className={cn(
                  active ? "text-blue-700" : "text-gray-600",
                  "w-5 h-5"
                )}
              />
              <span>{link.label}</span>
            </Link>
          )
        })}
      </div>
    </div>
  )
} 