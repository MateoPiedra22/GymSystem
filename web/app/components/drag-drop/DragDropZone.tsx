import React, { useState, useRef, useCallback } from 'react';

interface DragDropZoneProps {
  onDrop: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // en MB
  className?: string;
  children?: React.ReactNode;
  disabled?: boolean;
}

export function DragDropZone({ 
  onDrop, 
  accept = '*/*', 
  multiple = false, 
  maxSize = 10,
  className = '',
  children,
  disabled = false
}: DragDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFiles = useCallback((files: FileList): File[] => {
    const validFiles: File[] = [];
    const errors: string[] = [];

    Array.from(files).forEach((file) => {
      // Validar tamaño
      if (file.size > maxSize * 1024 * 1024) {
        errors.push(`"${file.name}" es demasiado grande. Máximo ${maxSize}MB.`);
        return;
      }

      // Validar tipo
      if (accept !== '*/*') {
        const acceptedTypes = accept.split(',').map(type => type.trim());
        const fileType = file.type;
        const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
        
        const isAccepted = acceptedTypes.some(type => {
          if (type.startsWith('.')) {
            return fileExtension === type;
          }
          return fileType.match(new RegExp(type.replace('*', '.*')));
        });

        if (!isAccepted) {
          errors.push(`"${file.name}" no es un tipo de archivo permitido.`);
          return;
        }
      }

      validFiles.push(file);
    });

    if (errors.length > 0) {
      setError(errors.join('\n'));
      return [];
    }

    setError(null);
    return validFiles;
  }, [accept, maxSize]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    const validFiles = validateFiles(files);
    if (validFiles.length > 0) {
      onDrop(multiple ? validFiles : [validFiles[0]]);
    }
  }, [disabled, multiple, onDrop, validateFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const validFiles = validateFiles(files);
    if (validFiles.length > 0) {
      onDrop(multiple ? validFiles : [validFiles[0]]);
    }

    // Limpiar input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [multiple, onDrop, validateFiles]);

  const handleClick = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [disabled]);

  return (
    <div className={className}>
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
          ${isDragOver 
            ? 'border-blue-400 bg-blue-50 scale-105' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
        />
        
        {children || (
          <div className="space-y-4">
            <div className="text-4xl">📁</div>
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragOver ? 'Suelta los archivos aquí' : 'Arrastra archivos aquí o haz clic'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {accept !== '*/*' ? `Tipos permitidos: ${accept}` : 'Cualquier tipo de archivo'}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                Máximo {maxSize}MB {multiple ? 'por archivo' : ''}
              </p>
            </div>
          </div>
        )}
      </div>
      
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600 whitespace-pre-line">{error}</p>
        </div>
      )}
    </div>
  );
} 