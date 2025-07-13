'use client'

import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-4 w-4';
      case 'lg':
        return 'h-8 w-8';
      default:
        return 'h-6 w-6';
    }
  };

  return (
    <div className={`animate-spin rounded-full border-2 border-gray-200 border-t-blue-600 dark:border-gray-700 dark:border-t-blue-400 ${getSizeClasses()} ${className}`} />
  );
}

export function TableLoader() {
  return (
    <div className="flex items-center justify-center py-8">
      <LoadingSpinner size="lg" />
    </div>
  )
}

export function SkeletonTable() {
  return (
    <div className="animate-pulse">
      <div className="h-10 bg-gray-200 rounded-t-lg mb-2" />
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-16 bg-gray-100 mb-1" />
      ))}
    </div>
  )
}

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <LoadingSpinner size="lg" />
    </div>
  )
}
