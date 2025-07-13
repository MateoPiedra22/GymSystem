import React from 'react';

interface ResponsiveDataTableProps {
  children: React.ReactNode;
  className?: string;
  striped?: boolean;
  hover?: boolean;
}

export function ResponsiveDataTable({ 
  children, 
  className = '',
  striped = true,
  hover = true
}: ResponsiveDataTableProps) {
  return (
    <div className={`overflow-x-auto shadow ring-1 ring-black ring-opacity-5 md:rounded-lg ${className}`}>
      <table className="min-w-full divide-y divide-gray-300">
        <thead className="bg-gray-50">
          {React.Children.map(children, child => {
            if (React.isValidElement(child) && child.type === 'thead') {
              return child;
            }
            return null;
          })}
        </thead>
        <tbody className={`divide-y divide-gray-200 bg-white ${
          striped ? '[&_tr:nth-child(even)]:bg-gray-50' : ''
        } ${
          hover ? '[&_tr:hover]:bg-gray-100' : ''
        }`}>
          {React.Children.map(children, child => {
            if (React.isValidElement(child) && child.type === 'tbody') {
              return child;
            }
            return null;
          })}
        </tbody>
      </table>
    </div>
  );
} 