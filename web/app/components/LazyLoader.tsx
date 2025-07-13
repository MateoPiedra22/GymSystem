import React, { Suspense, lazy } from 'react';
import { LoadingSpinner } from './ui/LoadingSpinner';

interface LazyLoaderProps {
  component: () => Promise<{ default: React.ComponentType<any> }>;
  fallback?: React.ReactNode;
  props?: any;
}

export function LazyLoader({ 
  component, 
  fallback = <LoadingSpinner />,
  props = {}
}: LazyLoaderProps) {
  const LazyComponent = lazy(component);

  return (
    <Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </Suspense>
  );
} 