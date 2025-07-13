import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

export function Button({ 
  children, 
  variant = 'default', 
  size = 'default', 
  className = '', 
  onClick,
  disabled = false,
  type = 'button'
}: ButtonProps) {
  const getVariantStyles = () => {
    switch (variant) {
      case 'destructive':
        return 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 dark:bg-red-600 dark:hover:bg-red-700';
      case 'outline':
        return 'border border-gray-300 bg-transparent text-gray-700 hover:bg-gray-50 focus:ring-gray-500 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800';
      case 'secondary':
        return 'bg-gray-100 text-gray-900 hover:bg-gray-200 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600';
      case 'ghost':
        return 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500 dark:text-gray-300 dark:hover:bg-gray-800';
      case 'link':
        return 'text-blue-600 underline-offset-4 hover:underline focus:ring-blue-500 dark:text-blue-400';
      default:
        return 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 dark:bg-blue-600 dark:hover:bg-blue-700';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'h-8 px-3 text-xs';
      case 'lg':
        return 'h-12 px-8 text-base';
      case 'icon':
        return 'h-10 w-10 p-0';
      default:
        return 'h-10 px-4 py-2 text-sm';
    }
  };

  return (
    <button
      type={type}
      className={`
        inline-flex items-center justify-center rounded-md font-medium transition-colors
        focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50
        ${getVariantStyles()} ${getSizeStyles()} ${className}
      `}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
} 