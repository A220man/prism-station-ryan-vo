import { useEffect, useState } from 'react';
import { healthApi } from '../api/client';

export function Health() {
  const [health, setHealth] = useState<{ status: string; app: string; environment: string } | null>(null);
  const [dbHealth, setDbHealth] = useState<{ status: string; database: string; error?: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const [healthRes, dbRes] = await Promise.all([
          healthApi.check(),
          healthApi.dbCheck(),
        ]);
        setHealth(healthRes.data);
        setDbHealth(dbRes.data);
      } catch (error) {
        console.error('Health check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
  }, []);

  if (loading) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">System Health</h1>
        <p className="text-gray-500 mt-1">Monitor the health of the Prism Station platform</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Application Health</h2>
          </div>
          <div className="card-body">
            {health ? (
              <dl className="space-y-4">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Status</dt>
                  <dd className={`font-medium ${health.status === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                    {health.status}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Application</dt>
                  <dd className="font-medium">{health.app}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Environment</dt>
                  <dd className="font-medium">{health.environment}</dd>
                </div>
              </dl>
            ) : (
              <p className="text-red-600">Failed to load health data</p>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Database Health</h2>
          </div>
          <div className="card-body">
            {dbHealth ? (
              <dl className="space-y-4">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Status</dt>
                  <dd className={`font-medium ${dbHealth.status === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                    {dbHealth.status}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Database</dt>
                  <dd className="font-medium">{dbHealth.database}</dd>
                </div>
                {dbHealth.error && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Error</dt>
                    <dd className="font-medium text-red-600 font-mono text-sm">{dbHealth.error}</dd>
                  </div>
                )}
              </dl>
            ) : (
              <p className="text-red-600">Failed to load database health</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}