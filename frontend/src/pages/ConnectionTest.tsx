import React, { useState, useEffect } from 'react';

interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

interface TestResponse {
  message: string;
}

const ConnectionTest: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<HealthResponse | null>(null);
  const [testStatus, setTestStatus] = useState<TestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testConnection = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Test health endpoint
      const healthResponse = await fetch('http://localhost:8000/health');
      const healthData = await healthResponse.json();
      setHealthStatus(healthData);
      
      // Test API endpoint
      const testResponse = await fetch('http://localhost:8000/api/v1/auth/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const testData = await testResponse.json();
      setTestStatus(testData);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Frontend-Backend Connection Test
        </h1>
        
        <div className="space-y-4">
          <button
            onClick={testConnection}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Testing Connection...' : 'Test Connection'}
          </button>
          
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              <strong>Error:</strong> {error}
            </div>
          )}
          
          {healthStatus && (
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              <h3 className="font-semibold mb-2">Health Check ✅</h3>
              <ul className="text-sm space-y-1">
                <li><strong>Status:</strong> {healthStatus.status}</li>
                <li><strong>Service:</strong> {healthStatus.service}</li>
                <li><strong>Version:</strong> {healthStatus.version}</li>
                <li><strong>Environment:</strong> {healthStatus.environment}</li>
              </ul>
            </div>
          )}
          
          {testStatus && (
            <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded">
              <h3 className="font-semibold mb-2">API Test ✅</h3>
              <p className="text-sm">{testStatus.message}</p>
            </div>
          )}
          
          <div className="bg-gray-100 border border-gray-300 text-gray-700 px-4 py-3 rounded">
            <h3 className="font-semibold mb-2">Connection Info</h3>
            <ul className="text-sm space-y-1">
              <li><strong>Frontend URL:</strong> http://localhost:5174</li>
              <li><strong>Backend URL:</strong> http://localhost:8000</li>
              <li><strong>API Base:</strong> http://localhost:8000/api/v1</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectionTest;