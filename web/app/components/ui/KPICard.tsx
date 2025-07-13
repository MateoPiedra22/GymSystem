import React from 'react';

interface KPICardProps {
  id: string;
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  suffix?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export function KPICard({ 
  id,
  label, 
  value, 
  icon, 
  suffix = '',
  trend,
  className = '' 
}: KPICardProps) {
  return (
    <div className={`bg-white rounded-lg border p-6 hover:shadow-md transition-shadow ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {value}{suffix}
          </p>
          {trend && (
            <div className="flex items-center mt-2">
              <span className={`text-sm font-medium ${
                trend.isPositive ? 'text-green-600' : 'text-red-600'
              }`}>
                {trend.isPositive ? '+' : ''}{trend.value}%
              </span>
              <svg 
                className={`ml-1 h-4 w-4 ${
                  trend.isPositive ? 'text-green-600' : 'text-red-600'
                }`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                {trend.isPositive ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6" />
                )}
              </svg>
            </div>
          )}
        </div>
        {icon && (
          <div className="text-gray-400 ml-4">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
} 