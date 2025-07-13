'use client';

import React, { useRef, useState } from 'react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // en MB
  className?: string;
  disabled?: boolean;
  children?: React.ReactNode;
}

export function FileUpload({ 
  onFileSelect, 
  accept = '*/*', 
  multiple = false, 
  maxSize = 10,
  className = '',
  disabled = false,
  children 
}: FileUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = (file: File) => {
    setError(null);
    
    // Validar tamaño
    if (file.size > maxSize * 1024 * 1024) {
      setError(`El archivo es demasiado grande. Máximo ${maxSize}MB.`);
      return;
    }

    onFileSelect(file);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className={className}>
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
          ${dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleChange}
          className="hidden"
          disabled={disabled}
        />
        
        {children || (
          <div>
            <div className="text-4xl mb-2">📁</div>
            <p className="text-sm text-gray-600">
              Arrastra un archivo aquí o haz clic para seleccionar
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Máximo {maxSize}MB
            </p>
          </div>
        )}
      </div>
      
      {error && (
        <p className="text-red-600 text-sm mt-2">{error}</p>
      )}
    </div>
  );
}

interface LogoUploadProps {
  onUploadSuccess: (logo: any) => void;
  onError?: (error: string) => void;
  className?: string;
}

export function LogoUpload({ onUploadSuccess, onError, className }: LogoUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFileSelect = (file: File) => {
    // Crear preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Subir archivo
    uploadLogo(file);
  };

  const uploadLogo = async (file: File) => {
    try {
      setUploading(true);
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('nombre', file.name.split('.')[0]);
      formData.append('descripcion', `Logo subido desde interfaz web`);
      formData.append('es_principal', 'false');

      const response = await fetch('/api/configuracion/logos/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Error al subir el logo');
      }

      const logo = await response.json();
      onUploadSuccess(logo);
      setPreview(null);
      
    } catch (error) {
      onError?.(error instanceof Error ? error.message : 'Error desconocido');
      setPreview(null);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className={className}>
      <FileUpload
        accept="image/png,image/jpeg,image/jpg,image/svg+xml"
        maxSize={5}
        onFileSelect={handleFileSelect}
        disabled={uploading}
        className="mb-4"
      >
        <div className="space-y-4">
          {preview ? (
            <div className="flex flex-col items-center">
              <img 
                src={preview} 
                alt="Vista previa" 
                className="w-20 h-20 object-contain border rounded"
              />
              <div className="text-sm text-gray-600">
                {uploading ? 'Subiendo...' : 'Vista previa'}
              </div>
            </div>
          ) : (
            <>
              <div className="text-4xl">🖼️</div>
              <div className="text-sm text-gray-600">
                Subir Logo del Sistema
              </div>
              <div className="text-xs text-gray-500">
                PNG, JPG, SVG • Máximo 5MB
              </div>
            </>
          )}
          
          {uploading && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
            </div>
          )}
        </div>
      </FileUpload>
    </div>
  );
} 