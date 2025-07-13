import React, { useState } from 'react';

interface MobileNavigationProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
}

export function MobileNavigation({ 
  children, 
  className = '',
  title = 'Navegación'
}: MobileNavigationProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={`md:hidden ${className}`}>
      {/* Botón de menú */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-center w-10 h-10 rounded-md bg-gray-100 hover:bg-gray-200 transition-colors"
      >
        <svg 
          className="w-6 h-6" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          {isOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Menú desplegable */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
          <div className="px-4 py-2">
            <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
            <nav className="space-y-1">
              {children}
            </nav>
          </div>
        </div>
      )}
    </div>
  );
} 