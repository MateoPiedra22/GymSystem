'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Modal } from '../ui/Modal';
import { FileUpload } from '../ui/FileUpload';

interface MultimediaItem {
  id: string;
  nombre: string;
  descripcion?: string;
  tipo: 'imagen' | 'video' | 'gif' | 'audio' | 'documento';
  categoria: string;
  archivo_url: string;
  thumbnail_url?: string;
  formato: string;
  tamaño_mb: number;
  duracion_segundos?: number;
  dimensiones?: { width: number; height: number };
  orden: number;
  es_principal: boolean;
  etiquetas: string[];
  nivel_dificultad?: string;
  es_premium: boolean;
  estado: string;
  fecha_subida: string;
  estadisticas: {
    vistas: number;
    descargas: number;
    me_gusta: number;
    reportes: number;
  };
}

interface Anotacion {
  id: string;
  titulo?: string;
  texto: string;
  tipo_anotacion: string;
  tiempo_inicio?: number;
  tiempo_fin?: number;
  posicion_x?: number;
  posicion_y?: number;
  color: string;
  mostrar_automaticamente: boolean;
  es_interactiva: boolean;
}

interface MultimediaViewerProps {
  ejercicioId: string;
  multimedia: MultimediaItem[];
  onUpload?: (file: File, metadata: any) => void;
  onDelete?: (multimediaId: string) => void;
  onUpdate?: (multimediaId: string, updates: any) => void;
  readOnly?: boolean;
  showUpload?: boolean;
}

// Función para obtener color de categoría
const getCategoriaColor = (categoria: string): string => {
  const colors = {
    'demostracion': 'bg-blue-100 text-blue-800',
    'tutorial': 'bg-green-100 text-green-800',
    'tecnica': 'bg-purple-100 text-purple-800',
    'variacion': 'bg-orange-100 text-orange-800',
    'seguridad': 'bg-red-100 text-red-800',
    'motivacional': 'bg-yellow-100 text-yellow-800',
    'progreso': 'bg-indigo-100 text-indigo-800'
  };
  return colors[categoria as keyof typeof colors] || 'bg-gray-100 text-gray-800';
};

// Función para formatear tamaño de archivo
const formatFileSize = (mb: number): string => {
  return mb < 1 ? `${(mb * 1024).toFixed(0)} KB` : `${mb.toFixed(1)} MB`;
};

// Función para formatear duración
const formatDuration = (seconds?: number): string => {
  if (!seconds) return '';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// Función para obtener icono de tipo
const getTipoIcon = (tipo: string): string => {
  switch (tipo) {
    case 'imagen': return '🖼️';
    case 'video': return '🎥';
    case 'gif': return '🎬';
    case 'audio': return '🎵';
    case 'documento': return '📄';
    default: return '📎';
  }
};

export function MultimediaViewer({
  ejercicioId,
  multimedia,
  onUpload,
  onDelete,
  onUpdate,
  readOnly = false,
  showUpload = true
}: MultimediaViewerProps) {
  const [selectedItem, setSelectedItem] = useState<MultimediaItem | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAnnotations, setShowAnnotations] = useState(false);
  const [anotaciones, setAnotaciones] = useState<Anotacion[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Ordenar multimedia por orden y tipo
  const sortedMultimedia = useMemo(() => {
    return [...multimedia].sort((a, b) => {
      if (a.es_principal && !b.es_principal) return -1;
      if (!a.es_principal && b.es_principal) return 1;
      return a.orden - b.orden;
    });
  }, [multimedia]);

  const multimediaImagenes = useMemo(() => 
    sortedMultimedia.filter(m => m.tipo === 'imagen' && !m.es_principal), 
    [sortedMultimedia]
  );
  const multimediaVideos = useMemo(() => 
    sortedMultimedia.filter(m => m.tipo === 'video' && !m.es_principal), 
    [sortedMultimedia]
  );
  const multimediaAudio = useMemo(() => 
    sortedMultimedia.filter(m => m.tipo === 'audio' && !m.es_principal), 
    [sortedMultimedia]
  );
  const multimediaDocumentos = useMemo(() => 
    sortedMultimedia.filter(m => m.tipo === 'documento' && !m.es_principal), 
    [sortedMultimedia]
  );

  const handleFileUpload = (file: File) => {
    setShowUploadModal(true);
  };

  const handlePlayVideo = (item: MultimediaItem) => {
    setSelectedItem(item);
    setIsPlaying(true);
  };

  return (
    <div className="space-y-6">
      {/* Header con botón de subida */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Contenido Multimedia</h3>
        {showUpload && !readOnly && (
          <Button onClick={() => setShowUploadModal(true)}>
            📤 Subir Multimedia
          </Button>
        )}
      </div>

      {/* Mensaje de error o vacío */}
      {(!multimedia || multimedia.length === 0) && (
        <div className="text-center text-gray-500 py-8">
          No hay archivos multimedia disponibles para este ejercicio.
        </div>
      )}

      {/* Multimedia principal */}
      {sortedMultimedia.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Principal item */}
          {sortedMultimedia.find(m => m.es_principal) && (
            <div className="lg:col-span-2">
              <MultimediaCard
                item={sortedMultimedia.find(m => m.es_principal)!}
                isMain={true}
                onPlay={handlePlayVideo}
                onEdit={onUpdate}
                onDelete={onDelete}
                readOnly={readOnly}
              />
            </div>
          )}
        </div>
      )}

      {/* Secciones por tipo */}
      {multimediaImagenes.length > 0 && (
        <MultimediaSection
          title="Imágenes"
          items={multimediaImagenes}
          onPlay={setSelectedItem}
          onEdit={onUpdate}
          onDelete={onDelete}
          readOnly={readOnly}
        />
      )}

      {multimediaVideos.length > 0 && (
        <MultimediaSection
          title="Videos"
          items={multimediaVideos}
          onPlay={handlePlayVideo}
          onEdit={onUpdate}
          onDelete={onDelete}
          readOnly={readOnly}
        />
      )}

      {multimediaAudio.length > 0 && (
        <MultimediaSection
          title="Audio"
          items={multimediaAudio}
          onPlay={setSelectedItem}
          onEdit={onUpdate}
          onDelete={onDelete}
          readOnly={readOnly}
        />
      )}

      {multimediaDocumentos.length > 0 && (
        <MultimediaSection
          title="Documentos"
          items={multimediaDocumentos}
          onPlay={setSelectedItem}
          onEdit={onUpdate}
          onDelete={onDelete}
          readOnly={readOnly}
        />
      )}

      {/* Modal de reproducción */}
      {selectedItem && (
        <MultimediaModal
          item={selectedItem}
          isOpen={!!selectedItem}
          onClose={() => setSelectedItem(null)}
          anotaciones={anotaciones}
          onAddAnnotation={() => {/* Implementar */}}
        />
      )}

      {/* Modal de upload */}
      {showUploadModal && (
        <UploadModal
          ejercicioId={ejercicioId}
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          onUpload={onUpload}
        />
      )}
    </div>
  );
}

// Componente para sección de multimedia
function MultimediaSection({
  title,
  items,
  onPlay,
  onEdit,
  onDelete,
  readOnly
}: {
  title: string;
  items: MultimediaItem[];
  onPlay: (item: MultimediaItem) => void;
  onEdit?: (id: string, updates: any) => void;
  onDelete?: (id: string) => void;
  readOnly: boolean;
}) {
  return (
    <div>
      <h4 className="font-medium mb-3">{title} ({items.length})</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map(item => (
          <MultimediaCard
            key={item.id}
            item={item}
            onPlay={onPlay}
            onEdit={onEdit}
            onDelete={onDelete}
            readOnly={readOnly}
          />
        ))}
      </div>
    </div>
  );
}

// Componente para tarjeta de multimedia
function MultimediaCard({
  item,
  isMain = false,
  onPlay,
  onEdit,
  onDelete,
  readOnly
}: {
  item: MultimediaItem;
  isMain?: boolean;
  onPlay: (item: MultimediaItem) => void;
  onEdit?: (id: string, updates: any) => void;
  onDelete?: (id: string) => void;
  readOnly: boolean;
}) {
  const cardSize = isMain ? 'h-64' : 'h-48';

  return (
    <div className={`border rounded-lg overflow-hidden hover:shadow-lg transition-shadow ${isMain ? 'ring-2 ring-blue-500' : ''}`}>
      {/* Thumbnail/Preview */}
      <div className={`${cardSize} bg-gray-100 relative group cursor-pointer`} onClick={() => onPlay(item)}>
        {item.tipo === 'imagen' ? (
          <img 
            src={item.archivo_url} 
            alt={item.nombre}
            className="w-full h-full object-cover"
          />
        ) : item.tipo === 'video' ? (
          <div className="w-full h-full bg-black flex items-center justify-center relative">
            {item.thumbnail_url ? (
              <img 
                src={item.thumbnail_url} 
                alt={item.nombre}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-white text-4xl">🎥</div>
            )}
            <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center">
              <div className="bg-white bg-opacity-90 rounded-full p-3">
                <svg className="w-6 h-6 text-gray-800" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14zm0 1A8 8 0 1 1 8 0a8 8 0 0 1 0 16z"/>
                  <path d="M6.271 5.055a.5.5 0 0 1 .52.038L11 7.055a.5.5 0 0 1 0 .89L6.791 9.907a.5.5 0 0 1-.791-.39V5.5a.5.5 0 0 1 .271-.445z"/>
                </svg>
              </div>
            </div>
            {item.duracion_segundos && (
              <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                {Math.floor(item.duracion_segundos / 60)}:{(item.duracion_segundos % 60).toString().padStart(2, '0')}
              </div>
            )}
          </div>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <div className="text-4xl mb-2">{getTipoIcon(item.tipo)}</div>
              <div className="text-sm text-gray-600">{item.formato.toUpperCase()}</div>
            </div>
          </div>
        )}

        {/* Overlay con acciones */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
          <Button variant="outline" size="sm" className="bg-white">
            {item.tipo === 'video' ? '▶️' : '👁️'} Ver
          </Button>
        </div>

        {/* Badges */}
        <div className="absolute top-2 left-2 flex flex-wrap gap-1">
          {item.es_principal && (
            <Badge variant="default" className="text-xs">Principal</Badge>
          )}
          {item.es_premium && (
            <Badge variant="secondary" className="text-xs">Premium</Badge>
          )}
        </div>
      </div>

      {/* Información */}
      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h5 className="font-medium text-sm truncate flex-1 mr-2">{item.nombre}</h5>
          {!readOnly && (
            <div className="flex gap-1">
              <Button variant="outline" size="sm" onClick={() => onEdit?.(item.id, {})}>
                ✏️
              </Button>
              <Button variant="outline" size="sm" onClick={() => onDelete?.(item.id)}>
                🗑️
              </Button>
            </div>
          )}
        </div>

        {item.descripcion && (
          <p className="text-xs text-gray-600 mb-2 line-clamp-2">{item.descripcion}</p>
        )}

        <div className="flex flex-wrap gap-1 mb-2">
          <Badge className={`text-xs ${getCategoriaColor(item.categoria)}`}>
            {item.categoria}
          </Badge>
          {item.nivel_dificultad && (
            <Badge variant="outline" className="text-xs">
              {item.nivel_dificultad}
            </Badge>
          )}
        </div>

        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>{formatFileSize(item.tamaño_mb)}</span>
          <div className="flex gap-2">
            <span>👁️ {item.estadisticas.vistas}</span>
            <span>👍 {item.estadisticas.me_gusta}</span>
          </div>
        </div>

        {item.etiquetas.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {item.etiquetas.slice(0, 3).map((tag, index) => (
              <span key={index} className="text-xs bg-gray-100 text-gray-600 px-1 py-0.5 rounded">
                #{tag}
              </span>
            ))}
            {item.etiquetas.length > 3 && (
              <span className="text-xs text-gray-500">+{item.etiquetas.length - 3}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Modal para reproducción de multimedia
function MultimediaModal({
  item,
  isOpen,
  onClose,
  anotaciones,
  onAddAnnotation
}: {
  item: MultimediaItem;
  isOpen: boolean;
  onClose: () => void;
  anotaciones: Anotacion[];
  onAddAnnotation: () => void;
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">{item.nombre}</h3>
          <Button variant="outline" onClick={onClose}>✕</Button>
        </div>

        {/* Reproductor */}
        <div className="mb-4">
          {item.tipo === 'video' ? (
            <video 
              controls 
              className="w-full rounded-lg"
              src={item.archivo_url}
            >
              Tu navegador no soporta el elemento video.
            </video>
          ) : item.tipo === 'imagen' ? (
            <img 
              src={item.archivo_url} 
              alt={item.nombre}
              className="w-full rounded-lg"
            />
          ) : item.tipo === 'audio' ? (
            <audio controls className="w-full">
              <source src={item.archivo_url} type={`audio/${item.formato}`} />
              Tu navegador no soporta el elemento audio.
            </audio>
          ) : (
            <div className="bg-gray-100 p-8 rounded-lg text-center">
              <div className="text-4xl mb-2">{getTipoIcon(item.tipo)}</div>
              <p className="text-gray-600 mb-4">Documento {item.formato.toUpperCase()}</p>
              <Button onClick={() => window.open(item.archivo_url, '_blank')}>
                📄 Abrir Documento
              </Button>
            </div>
          )}
        </div>

        {/* Información detallada */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium mb-2">Información</h4>
            <div className="space-y-1 text-sm">
              <p><span className="font-medium">Formato:</span> {item.formato.toUpperCase()}</p>
              <p><span className="font-medium">Tamaño:</span> {formatFileSize(item.tamaño_mb)}</p>
              {item.duracion_segundos && (
                <p><span className="font-medium">Duración:</span> {formatDuration(item.duracion_segundos)}</p>
              )}
              {item.dimensiones && (
                <p><span className="font-medium">Resolución:</span> {item.dimensiones.width}x{item.dimensiones.height}</p>
              )}
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-2">Estadísticas</h4>
            <div className="space-y-1 text-sm">
              <p><span className="font-medium">Vistas:</span> {item.estadisticas.vistas}</p>
              <p><span className="font-medium">Descargas:</span> {item.estadisticas.descargas}</p>
              <p><span className="font-medium">Me gusta:</span> {item.estadisticas.me_gusta}</p>
              <p><span className="font-medium">Reportes:</span> {item.estadisticas.reportes}</p>
            </div>
          </div>
        </div>

        {item.descripcion && (
          <div className="mt-4">
            <h4 className="font-medium mb-2">Descripción</h4>
            <p className="text-sm text-gray-600">{item.descripcion}</p>
          </div>
        )}

        {item.etiquetas.length > 0 && (
          <div className="mt-4">
            <h4 className="font-medium mb-2">Etiquetas</h4>
            <div className="flex flex-wrap gap-1">
              {item.etiquetas.map((tag, index) => (
                <span key={index} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}

// Modal de upload
function UploadModal({
  ejercicioId,
  isOpen,
  onClose,
  onUpload
}: {
  ejercicioId: string;
  isOpen: boolean;
  onClose: () => void;
  onUpload?: (file: File, metadata: any) => void;
}) {
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    tipo: 'imagen',
    categoria: 'demostracion',
    orden: 1,
    es_principal: false,
    etiquetas: '',
    nivel_dificultad: '',
    es_premium: false
  });

  const handleFileSelect = (file: File) => {
    if (!formData.nombre) {
      setFormData(prev => ({
        ...prev,
        nombre: file.name.split('.')[0]
      }));
    }
  };

  const handleSubmit = (file: File) => {
    onUpload?.(file, formData);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4">Subir Multimedia</h3>

        <div className="space-y-4">
          {/* Campos del formulario */}
          <div>
            <label className="block text-sm font-medium mb-1">Nombre</label>
            <input
              type="text"
              value={formData.nombre}
              onChange={(e) => setFormData(prev => ({ ...prev, nombre: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="Nombre del archivo"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Descripción</label>
            <textarea
              value={formData.descripcion}
              onChange={(e) => setFormData(prev => ({ ...prev, descripcion: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              rows={3}
              placeholder="Descripción opcional"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Tipo</label>
              <select
                value={formData.tipo}
                onChange={(e) => setFormData(prev => ({ ...prev, tipo: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="imagen">Imagen</option>
                <option value="video">Video</option>
                <option value="gif">GIF</option>
                <option value="audio">Audio</option>
                <option value="documento">Documento</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Categoría</label>
              <select
                value={formData.categoria}
                onChange={(e) => setFormData(prev => ({ ...prev, categoria: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="demostracion">Demostración</option>
                <option value="tutorial">Tutorial</option>
                <option value="tecnica">Técnica</option>
                <option value="variacion">Variación</option>
                <option value="seguridad">Seguridad</option>
                <option value="motivacional">Motivacional</option>
                <option value="progreso">Progreso</option>
              </select>
            </div>
          </div>

          {/* Upload area */}
          <FileUpload
            accept={getAcceptString(formData.tipo)}
            onFileSelect={handleFileSelect}
            onUploadComplete={(file) => handleSubmit(file)}
            maxSize={getMaxSize(formData.tipo)}
          />

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>Cancelar</Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}

// Funciones auxiliares
function getAcceptString(tipo: string): string {
  const accepts = {
    'imagen': 'image/*',
    'video': 'video/*',
    'gif': 'image/gif',
    'audio': 'audio/*',
    'documento': '.pdf,.txt,.doc,.docx'
  };
  return accepts[tipo as keyof typeof accepts] || '*/*';
}

function getMaxSize(tipo: string): number {
  const sizes = {
    'imagen': 10,
    'video': 500,
    'gif': 20,
    'audio': 50,
    'documento': 20
  };
  return sizes[tipo as keyof typeof sizes] || 10;
} 