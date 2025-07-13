import React from 'react';

interface FadeInProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}

export function FadeIn({ 
  children, 
  delay = 0, 
  duration = 300, 
  className = '' 
}: FadeInProps) {
  return (
    <div 
      className={`animate-fade-in ${className}`}
      style={{
        animationDelay: `${delay}ms`,
        animationDuration: `${duration}ms`
      }}
    >
      {children}
    </div>
  );
}

interface SlideInProps {
  children: React.ReactNode;
  direction?: 'left' | 'right' | 'up' | 'down';
  delay?: number;
  duration?: number;
  className?: string;
}

export function SlideIn({ 
  children, 
  direction = 'up', 
  delay = 0, 
  duration = 300, 
  className = '' 
}: SlideInProps) {
  const getDirectionClass = () => {
    switch (direction) {
      case 'left': return 'animate-slide-in-left';
      case 'right': return 'animate-slide-in-right';
      case 'down': return 'animate-slide-in-down';
      default: return 'animate-slide-in-up';
    }
  };

  return (
    <div 
      className={`${getDirectionClass()} ${className}`}
      style={{
        animationDelay: `${delay}ms`,
        animationDuration: `${duration}ms`
      }}
    >
      {children}
    </div>
  );
}

interface ScaleInProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}

export function ScaleIn({ 
  children, 
  delay = 0, 
  duration = 300, 
  className = '' 
}: ScaleInProps) {
  return (
    <div 
      className={`animate-scale-in ${className}`}
      style={{
        animationDelay: `${delay}ms`,
        animationDuration: `${duration}ms`
      }}
    >
      {children}
    </div>
  );
}

interface StaggerContainerProps {
  children: React.ReactNode;
  staggerDelay?: number;
  className?: string;
}

export function StaggerContainer({ 
  children, 
  staggerDelay = 100, 
  className = '' 
}: StaggerContainerProps) {
  const childrenArray = React.Children.toArray(children);
  
  return (
    <div className={className}>
      {childrenArray.map((child, index) => (
        <div
          key={index}
          style={{ animationDelay: `${index * staggerDelay}ms` }}
          className="animate-fade-in"
        >
          {child}
        </div>
      ))}
    </div>
  );
} 