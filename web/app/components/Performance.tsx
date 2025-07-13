'use client';

import React, { Suspense, lazy, useMemo, useCallback, useState, useEffect } from 'react';
import { LoadingSpinner } from './ui/LoadingSpinner';

// Componente de carga diferida con fallback
interface LazyComponentProps {
  component: () => Promise<{ default: React.ComponentType<any> }>;
  fallback?: React.ReactNode;
  props?: any;
}

export const LazyComponent: React.FC<LazyComponentProps> = ({ 
  component, 
  fallback = <LoadingSpinner />, 
  props = {} 
}) => {
  const LazyLoadedComponent = useMemo(() => lazy(component), [component]);
  
  return (
    <Suspense fallback={fallback}>
      <LazyLoadedComponent {...props} />
    </Suspense>
  );
};

// Hook para virtualización de listas
interface UseVirtualizationProps {
  items: any[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

export const useVirtualization = ({ 
  items, 
  itemHeight, 
  containerHeight, 
  overscan = 5 
}: UseVirtualizationProps) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const visibleRange = useMemo(() => {
    const start = Math.floor(scrollTop / itemHeight);
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const end = Math.min(start + visibleCount + overscan, items.length);
    
    return {
      start: Math.max(0, start - overscan),
      end,
      offsetY: start * itemHeight
    };
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length]);
  
  const visibleItems = useMemo(() => {
    return items.slice(visibleRange.start, visibleRange.end);
  }, [items, visibleRange.start, visibleRange.end]);
  
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);
  
  return {
    visibleItems,
    visibleRange,
    handleScroll,
    totalHeight: items.length * itemHeight
  };
};

// Componente de lista virtualizada
interface VirtualizedListProps {
  items: any[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: any, index: number) => React.ReactNode;
  overscan?: number;
}

export const VirtualizedList: React.FC<VirtualizedListProps> = ({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5
}) => {
  const { visibleItems, visibleRange, handleScroll, totalHeight } = useVirtualization({
    items,
    itemHeight,
    containerHeight,
    overscan
  });
  
  return (
    <div 
      style={{ 
        height: containerHeight, 
        overflow: 'auto',
        position: 'relative'
      }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${visibleRange.offsetY}px)` }}>
          {visibleItems.map((item, index) => (
            <div key={visibleRange.start + index} style={{ height: itemHeight }}>
              {renderItem(item, visibleRange.start + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Hook para caching de datos
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export const useDataCache = <T>(key: string, ttl: number = 5 * 60 * 1000) => {
  const [cache, setCache] = useState<Map<string, CacheEntry<T>>>(new Map());
  
  const get = useCallback((cacheKey: string): T | null => {
    const entry = cache.get(cacheKey);
    if (!entry) return null;
    
    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      cache.delete(cacheKey);
      setCache(new Map(cache));
      return null;
    }
    
    return entry.data;
  }, [cache]);
  
  const set = useCallback((cacheKey: string, data: T, customTtl?: number) => {
    const newCache = new Map(cache);
    newCache.set(cacheKey, {
      data,
      timestamp: Date.now(),
      ttl: customTtl || ttl
    });
    setCache(newCache);
  }, [cache, ttl]);
  
  const clear = useCallback(() => {
    setCache(new Map());
  }, []);
  
  const remove = useCallback((cacheKey: string) => {
    const newCache = new Map(cache);
    newCache.delete(cacheKey);
    setCache(newCache);
  }, [cache]);
  
  return { get, set, clear, remove };
};

// Componente de imagen optimizada con lazy loading
interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  placeholder?: string;
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  className,
  placeholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5YWFhYSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkxvYWRpbmcuLi48L3RleHQ+PC9zdmc+'
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  
  const handleLoad = useCallback(() => {
    setIsLoaded(true);
  }, []);
  
  const handleError = useCallback(() => {
    setHasError(true);
  }, []);
  
  return (
    <div className={`relative overflow-hidden ${className || ''}`}>
      <img
        src={hasError ? placeholder : src}
        alt={alt}
        width={width}
        height={height}
        className={`transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        }`}
        onLoad={handleLoad}
        onError={handleError}
        loading="lazy"
      />
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800">
          <LoadingSpinner size="sm" />
        </div>
      )}
    </div>
  );
};

// Hook para debounce
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return debouncedValue;
};

// Hook para throttle
export const useThrottle = <T>(value: T, delay: number): T => {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastRun = React.useRef<number>(Date.now());
  
  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRun.current >= delay) {
        setThrottledValue(value);
        lastRun.current = Date.now();
      }
    }, delay - (Date.now() - lastRun.current));
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return throttledValue;
};

// Componente de memoización inteligente
export const MemoizedComponent = React.memo(({ 
  children, 
  dependencies 
}: { 
  children: React.ReactNode; 
  dependencies: any[] 
}) => {
  return <>{children}</>;
}, (prevProps, nextProps) => {
  return JSON.stringify(prevProps.dependencies) === JSON.stringify(nextProps.dependencies);
});

// Hook para intersection observer (lazy loading)
export const useIntersectionObserver = (
  options: IntersectionObserverInit = {}
) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [ref, setRef] = useState<HTMLElement | null>(null);
  
  useEffect(() => {
    if (!ref) return;
    
    const observer = new IntersectionObserver(([entry]) => {
      setIsIntersecting(entry.isIntersecting);
    }, options);
    
    observer.observe(ref);
    
    return () => {
      observer.disconnect();
    };
  }, [ref, options]);
  
  return [setRef, isIntersecting] as const;
};

// Componente de carga progresiva
interface ProgressiveLoadingProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  delay?: number;
}

export const ProgressiveLoading: React.FC<ProgressiveLoadingProps> = ({
  children,
  fallback = <LoadingSpinner />,
  delay = 100
}) => {
  const [shouldShow, setShouldShow] = useState(false);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setShouldShow(true);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [delay]);
  
  if (!shouldShow) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
}; 