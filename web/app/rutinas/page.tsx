'use client'
export const dynamic = 'force-dynamic'

/**
 * Página de gestión de rutinas con soporte multimedia
 */
import { useState, useEffect } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Alert } from '../components/ui/Alert';
import { MultimediaViewer } from '../components/multimedia/MultimediaViewer';
import { useMultimediaEjercicios } from '../hooks/useMultimedia';

interface Ejercicio {
  id: string;
  nombre: string;
  descripcion?: string;
  tipo: string;
  dificultad: string;
  musculos_trabajados?: string;
  imagen_url?: string;
  video_url?: string;
}

interface Rutina {
  id: string;
  nombre: string;
  descripcion?: string;
  nivel: string;
  duracion_estimada?: number;
  ejercicios: Ejercicio[];
}

export default function RutinasPage() {
  const [rutinas, setRutinas] = useState<Rutina[]>([]);
  const [selectedRutina, setSelectedRutina] = useState<Rutina | null>(null);
  const [selectedEjercicio, setSelectedEjercicio] = useState<Ejercicio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Hook para multimedia del ejercicio seleccionado
  const {
    multimedia,
    loading: multimediaLoading,
    error: multimediaError,
    uploadMultimedia,
    updateMultimedia,
    deleteMultimedia,
    refreshMultimedia
  } = useMultimediaEjercicios(selectedEjercicio?.id || '');

  // Cargar rutinas
  useEffect(() => {
    loadRutinas();
  }, []);

  const loadRutinas = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/rutinas');
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setRutinas(data);
      
      // Seleccionar primera rutina por defecto
      if (data.length > 0) {
        setSelectedRutina(data[0]);
        if (data[0].ejercicios.length > 0) {
          setSelectedEjercicio(data[0].ejercicios[0]);
        }
      }
      
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Error cargando rutinas';
      setError(errorMsg);
      console.error('Error cargando rutinas:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadMultimedia = async (file: File, metadata: any) => {
    if (!selectedEjercicio) return;
    
    const success = await uploadMultimedia(file, {
      ...metadata,
      ejercicio_id: selectedEjercicio.id
    });
    
    if (success) {
      await refreshMultimedia();
    }
  };

  const handleUpdateMultimedia = async (multimediaId: string, updates: any) => {
    const success = await updateMultimedia(multimediaId, updates);
    if (success) {
      await refreshMultimedia();
    }
  };

  const handleDeleteMultimedia = async (multimediaId: string) => {
    const success = await deleteMultimedia(multimediaId);
    if (success) {
      await refreshMultimedia();
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <LoadingSpinner />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="page-header">
          <h1 className="page-title">
            🏋️ Gestión de Rutinas
          </h1>
          <p className="page-subtitle">
            Administra las rutinas de entrenamiento y su contenido multimedia
          </p>
        </div>

        {/* Alertas */}
        {error && (
          <Alert variant="destructive">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 text-sm underline"
            >
              Cerrar
            </button>
          </Alert>
        )}

        {multimediaError && (
          <Alert variant="destructive">
            Error multimedia: {multimediaError}
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Lista de rutinas */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Rutinas Disponibles</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {rutinas.map((rutina) => (
                    <div
                      key={rutina.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedRutina?.id === rutina.id
                          ? 'bg-blue-50 border-blue-200'
                          : 'hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        setSelectedRutina(rutina);
                        if (rutina.ejercicios.length > 0) {
                          setSelectedEjercicio(rutina.ejercicios[0]);
                        }
                      }}
                    >
                      <h4 className="font-medium">{rutina.nombre}</h4>
                      <p className="text-sm text-gray-600">{rutina.descripcion}</p>
                      <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>Nivel: {rutina.nivel}</span>
                        <span>{rutina.ejercicios.length} ejercicios</span>
                      </div>
                    </div>
                  ))}
                </div>

                {rutinas.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <p>No hay rutinas disponibles</p>
                    <Button className="mt-4" onClick={loadRutinas}>
                      🔄 Recargar
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Detalles y multimedia */}
          <div className="lg:col-span-2">
            {selectedRutina ? (
              <div className="space-y-6">
                {/* Información de la rutina */}
                <Card>
                  <CardHeader>
                    <CardTitle>{selectedRutina.nombre}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div>
                        <span className="text-sm font-medium">Nivel:</span>
                        <p className="text-sm text-gray-600">{selectedRutina.nivel}</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium">Duración:</span>
                        <p className="text-sm text-gray-600">
                          {selectedRutina.duracion_estimada 
                            ? `${selectedRutina.duracion_estimada} min` 
                            : 'No especificada'
                          }
                        </p>
                      </div>
                      <div>
                        <span className="text-sm font-medium">Ejercicios:</span>
                        <p className="text-sm text-gray-600">{selectedRutina.ejercicios.length}</p>
                      </div>
                    </div>
                    
                    {selectedRutina.descripcion && (
                      <p className="text-gray-700">{selectedRutina.descripcion}</p>
                    )}
                  </CardContent>
                </Card>

                {/* Lista de ejercicios */}
                <Card>
                  <CardHeader>
                    <CardTitle>Ejercicios de la Rutina</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {selectedRutina.ejercicios.map((ejercicio) => (
                        <div
                          key={ejercicio.id}
                          className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                            selectedEjercicio?.id === ejercicio.id
                              ? 'bg-green-50 border-green-200'
                              : 'hover:bg-gray-50'
                          }`}
                          onClick={() => setSelectedEjercicio(ejercicio)}
                        >
                          <h5 className="font-medium">{ejercicio.nombre}</h5>
                          <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>{ejercicio.tipo}</span>
                            <span>{ejercicio.dificultad}</span>
                          </div>
                          {ejercicio.musculos_trabajados && (
                            <p className="text-xs text-gray-600 mt-1">
                              {ejercicio.musculos_trabajados}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Multimedia del ejercicio seleccionado */}
                {selectedEjercicio && (
                  <Card>
                    <CardHeader>
                      <CardTitle>
                        Multimedia - {selectedEjercicio.nombre}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {multimediaLoading ? (
                        <LoadingSpinner />
                      ) : (
                        <MultimediaViewer
                          ejercicioId={selectedEjercicio.id}
                          multimedia={multimedia}
                          onUpload={handleUploadMultimedia}
                          onUpdate={handleUpdateMultimedia}
                          onDelete={handleDeleteMultimedia}
                          showUpload={true}
                        />
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <Card>
                <CardContent className="flex items-center justify-center h-64">
                  <div className="text-center text-gray-500">
                    <p className="text-lg mb-2">🏋️</p>
                    <p>Selecciona una rutina para ver sus detalles y multimedia</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
