import React from 'react';

interface ChartWrapperProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  height?: number;
}

export function ChartWrapper({ 
  title, 
  children, 
  className = '',
  height = 300 
}: ChartWrapperProps) {
  return (
    <div className={`bg-white rounded-lg border p-6 ${className}`}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      <div style={{ height: `${height}px` }}>
        {children}
      </div>
    </div>
  );
} 