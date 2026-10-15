import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { skillsApi, Skill } from '../api/client';

export function SkillDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [skill, setSkill] = useState<Skill | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const fetchSkill = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const response = await skillsApi.get(parseInt(id));
        setSkill(response.data);
      } catch (err: unknown) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          setError('Skill not found');
        } else {
          setError('Failed to load skill');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchSkill();
  }, [id]);

  const handleExport = async (format: 'markdown' | 'json') => {
    if (!id) return;
    setExporting(true);
    try {
      const response = await skillsApi.export(parseInt(id), format);
      const blob = new Blob([response.data.content], {
        type: format === 'markdown' ? 'text/markdown' : 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${skill?.slug || 'skill'}.${format === 'markdown' ? 'md' : 'json'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      alert('Export failed');
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async () => {
    if (!id || !skill) return;
    if (!confirm(`Delete "${skill.name}"? This action cannot be undone.`)) return;
    try {
      await skillsApi.delete(parseInt(id));
      navigate('/skills');
    } catch (err) {
      alert('Failed to delete skill');
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  if (error || !skill) {
    return (
      <div className="card">
        <div className="card-body empty-state">
          <div className="empty-state-icon">⚠️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">{error || 'Skill not found'}</h3>
          <Link to="/skills" className="btn btn-primary">Back to Skills</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link to="/skills" className="text-sm text-gray-500 hover:underline mb-2 inline-block">
            ← Back to Skills
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{skill.name}</h1>
          <p className="text-gray-500 mt-1">{skill.slug}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/skills/${skill.id}/edit`} className="btn btn-outline">Edit</Link>
          <button onClick={() => handleExport('markdown')} disabled={exporting} className="btn btn-outline">
            Export MD
          </button>
          <button onClick={() => handleExport('json')} disabled={exporting} className="btn btn-outline">
            Export JSON
          </button>
          <button onClick={handleDelete} className="btn btn-outline text-red-600 border-red-200 hover:bg-red-50">
            Delete
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold">Description</h2>
            </div>
            <div className="card-body">
              {skill.description ? (
                <div className="prose prose-sm max-w-none">{skill.description}</div>
              ) : (
                <p className="text-gray-500 italic">No description provided</p>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold">Content</h2>
            </div>
            <div className="card-body">
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm font-mono whitespace-pre-wrap">
                {skill.content}
              </pre>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold">Metadata</h2>
            </div>
            <div className="card-body space-y-4">
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm text-gray-500">Version</dt>
                  <dd className="font-mono text-lg font-medium">{skill.version}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Author ID</dt>
                  <dd className="font-mono">{skill.author_id}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Created</dt>
                  <dd>{new Date(skill.created_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Updated</dt>
                  <dd>{new Date(skill.updated_at).toLocaleString()}</dd>
                </div>
              </dl>

              {skill.platform_targets.length > 0 && (
                <div>
                  <dt className="text-sm text-gray-500 mb-2 block">Platform Targets</dt>
                  <div className="flex flex-wrap gap-1">
                    {skill.platform_targets.map((platform) => (
                      <span key={platform} className="badge badge-primary">{platform}</span>
                    ))}
                  </div>
                </div>
              )}

              {skill.tags.length > 0 && (
                <div>
                  <dt className="text-sm text-gray-500 mb-2 block">Tags</dt>
                  <div className="flex flex-wrap gap-1">
                    {skill.tags.map((tag) => (
                      <span key={tag} className="badge badge-secondary">{tag}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold">Actions</h2>
            </div>
            <div className="card-body space-y-3">
              <Link to={`/skills/${skill.id}/edit`} className="btn btn-primary w-full">
                Edit Skill
              </Link>
              <button onClick={() => handleExport('markdown')} disabled={exporting} className="btn btn-outline w-full">
                Export as Markdown
              </button>
              <button onClick={() => handleExport('json')} disabled={exporting} className="btn btn-outline w-full">
                Export as JSON
              </button>
              <button onClick={handleDelete} className="btn btn-outline text-red-600 border-red-200 hover:bg-red-50 w-full">
                Delete Skill
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}