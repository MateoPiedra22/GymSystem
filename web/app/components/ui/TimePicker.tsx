import React from 'react';

interface TimePickerProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function TimePicker({ 
  label, 
  error, 
  helperText, 
  className = '', 
  id,
  ...props 
}: TimePickerProps) {
  const timeId = id || `time-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={timeId} className="block text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      
      <input
        id={timeId}
        type="time"
        className={`
          block w-full rounded-md border px-3 py-2 text-sm
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed
          ${error 
            ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
            : 'border-gray-300'
          }
          ${className}
        `}
        {...props}
      />
      
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
      
      {helperText && !error && (
        <p className="text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
} 