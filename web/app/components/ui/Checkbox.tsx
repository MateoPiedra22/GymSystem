import React from 'react';

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function Checkbox({ 
  label, 
  error, 
  helperText, 
  className = '', 
  id,
  ...props 
}: CheckboxProps) {
  const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="space-y-1">
      <div className="flex items-center">
        <input
          id={checkboxId}
          type="checkbox"
          className={`
            h-4 w-4 rounded border-gray-300 text-blue-600
            focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
            disabled:opacity-50 disabled:cursor-not-allowed
            ${error ? 'border-red-300 focus:ring-red-500' : ''}
            ${className}
          `}
          {...props}
        />
        {label && (
          <label htmlFor={checkboxId} className="ml-2 block text-sm text-gray-700">
            {label}
          </label>
        )}
      </div>
      
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
      
      {helperText && !error && (
        <p className="text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
} 