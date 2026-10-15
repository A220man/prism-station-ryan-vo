import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { skillsApi, Skill } from '../api/client';

export function SkillsList() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  const fetchSkills = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await skillsApi.list({ skip: page * limit, limit, search: search || undefined });
      setSkills(response.data.items);
      setTotal(response.data.total);
    } catch (err) {
      setError('Failed to load skills');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, [page, search]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchSkills();
  };

  const totalPages = Math.ceil(total / limit);

  if (loading && skills.length === 0) {
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Skills</h1>
          <p className="text-gray-500 mt-1">Manage your AI agent skills</p>
        </div>
        <Link to="/skills/new" className="btn btn-primary">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Skill
        </Link>
      </div>

      <form onSubmit={handleSearch} className="card">
        <div className="card-body">
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search skills..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="form-input"
              />
            </div>
            <button type="submit" className="btn btn-primary">
              Search
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="card border-red-200">
          <div className="card-body text-red-600">{error}</div>
        </div>
      )}

      {skills.length === 0 && !loading && !error ? (
        <div className="card">
          <div className="card-body empty-state">
            <div className="empty-state-icon">📦</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No skills found</h3>
            <p className="text-gray-500 mb-4">Get started by creating your first skill</p>
            <Link to="/skills/new" className="btn btn-primary">Create Skill</Link>
          </div>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Version</th>
                    <th>Platforms</th>
                    <th>Tags</th>
                    <th>Updated</th>
                    <th className="w-24">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {skills.map((skill) => (
                    <tr key={skill.id}>
                      <td>
                        <Link to={`/skills/${skill.id}`} className="font-medium text-blue-600 hover:underline">
                          {skill.name}
                        </Link>
                        <div className="text-sm text-gray-500">{skill.slug}</div>
                      </td>
                      <td className="font-mono text-sm">{skill.version}</td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {skill.platform_targets.map((platform) => (
                            <span key={platform} className="badge badge-primary">{platform}</span>
                          ))}
                          {skill.platform_targets.length === 0 && (
                            <span className="badge badge-secondary">Any</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {skill.tags.slice(0, 3).map((tag) => (
                            <span key={tag} className="badge badge-secondary">{tag}</span>
                          ))}
                          {skill.tags.length > 3 && (
                            <span className="badge badge-secondary">+{skill.tags.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td className="text-sm text-gray-500">
                        {new Date(skill.updated_at).toLocaleDateString()}
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <Link to={`/skills/${skill.id}/edit`} className="btn btn-ghost btn-sm">Edit</Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 0}
                className="btn btn-outline btn-sm"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page + 1} of {totalPages} ({total} total)
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= totalPages - 1}
                className="btn btn-outline btn-sm"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}