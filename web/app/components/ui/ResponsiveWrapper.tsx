import React from 'react';

interface ResponsiveWrapperProps {
  children: React.ReactNode;
  className?: string;
  mobile?: boolean;
  tablet?: boolean;
  desktop?: boolean;
}

export function ResponsiveWrapper({ 
  children, 
  className = '',
  mobile = true,
  tablet = true,
  desktop = true
}: ResponsiveWrapperProps) {
  const getResponsiveClasses = () => {
    const classes = [];
    
    if (!mobile) classes.push('hidden');
    if (tablet) classes.push('md:block');
    if (desktop) classes.push('lg:block');
    
    return classes.join(' ');
  };

  return (
    <div className={`${getResponsiveClasses()} ${className}`}>
      {children}
    </div>
  );
} 