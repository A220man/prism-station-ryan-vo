import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { skillsApi, SkillCreate, SkillUpdate, Skill } from '../api/client';

export function SkillForm() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = !!id;

  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [version, setVersion] = useState('1.0.0');
  const [content, setContent] = useState('');
  const [platformTargets, setPlatformTargets] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [platformInput, setPlatformInput] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState<{ type: string; message: string }[]>([]);

  const platforms = ['iOS', 'macOS', 'visionOS', 'watchOS', 'tvOS', 'linux', 'windows'];

  useEffect(() => {
    if (isEditing && id) {
      loadSkill();
    }
  }, [id, isEditing]);

  const loadSkill = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await skillsApi.get(parseInt(id));
      const skill: Skill = response.data;
      setName(skill.name);
      setSlug(skill.slug);
      setDescription(skill.description || '');
      setVersion(skill.version);
      setContent(skill.content);
      setPlatformTargets(skill.platform_targets);
      setTags(skill.tags);
    } catch (err) {
      setError('Failed to load skill');
    } finally {
      setLoading(false);
    }
  };

  const addPlatform = () => {
    if (platformInput.trim() && !platformTargets.includes(platformInput.trim())) {
      setPlatformTargets([...platformTargets, platformInput.trim()]);
      setPlatformInput('');
    }
  };

  const removePlatform = (platform: string) => {
    setPlatformTargets(platformTargets.filter((p) => p !== platform));
  };

  const addTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setValidationErrors([]);
    setSaving(true);

    try {
      if (isEditing && id) {
        const updateData: SkillUpdate = {
          name,
          description: description || undefined,
          version,
          content,
          platform_targets: platformTargets,
          tags: tags,
        };
        await skillsApi.update(parseInt(id), updateData);
      } else {
        const createData: SkillCreate = {
          name,
          slug,
          description: description || undefined,
          version,
          content,
          platform_targets: platformTargets,
          tags: tags,
        };
        await skillsApi.create(createData);
      }
      navigate('/skills');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string; errors?: { type: string; message: string }[] } } };
      if (axiosError.response?.data?.errors) {
        setValidationErrors(axiosError.response.data.errors);
      } else {
        setError(axiosError.response?.data?.detail || 'Failed to save skill');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleValidate = async () => {
    if (!content.trim()) return;
    try {
      const response = await skillsApi.validate(content, platformTargets);
      setValidationErrors(response.data.errors);
    } catch (err) {
      console.error('Validation failed:', err);
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{isEditing ? 'Edit Skill' : 'New Skill'}</h1>
        <p className="text-gray-500 mt-1">{isEditing ? 'Update your skill' : 'Create a new AI agent skill'}</p>
      </div>

      {error && (
        <div className="card border-red-200">
          <div className="card-body text-red-600">{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Basic Information</h2>
          </div>
          <div className="card-body space-y-4">
            <div>
              <label htmlFor="name" className="form-label">Name *</label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="form-input"
                required
                maxLength={255}
              />
            </div>

            <div>
              <label htmlFor="slug" className="form-label">Slug *</label>
              <input
                id="slug"
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                className="form-input"
                required
                maxLength={255}
                disabled={isEditing}
              />
              {isEditing && <p className="form-error">Slug cannot be changed after creation</p>}
            </div>

            <div>
              <label htmlFor="version" className="form-label">Version *</label>
              <input
                id="version"
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="form-input"
                required
                pattern="^\\d+\\.\\d+\\.\\d+$"
                placeholder="1.0.0"
              />
              <p className="form-error">Use semantic versioning (e.g., 1.0.0)</p>
            </div>

            <div>
              <label htmlFor="description" className="form-label">Description</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="form-input"
                rows={3}
                placeholder="Optional description of the skill"
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Content *</h2>
          </div>
          <div className="card-body">
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="form-input font-mono"
              rows={20}
              placeholder="Skill content in Markdown format..."
              required
            />
            <div className="flex gap-2 mt-3">
              <button type="button" onClick={handleValidate} className="btn btn-outline">
                Validate
              </button>
            </div>
          </div>
        </div>

        {validationErrors.length > 0 && (
          <div className="card border-yellow-200">
            <div className="card-header">
              <h2 className="text-lg font-semibold text-yellow-800">Validation Issues</h2>
            </div>
            <div className="card-body">
              <ul className="space-y-2">
                {validationErrors.map((err, i) => (
                  <li key={i} className="text-yellow-800 text-sm">
                    <span className="font-medium">{err.type}:</span> {err.message}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Platform Targets</h2>
          </div>
          <div className="card-body">
            <div className="flex gap-2 mb-4">
              <select
                value={platformInput}
                onChange={(e) => setPlatformInput(e.target.value)}
                className="form-input w-48"
              >
                <option value="">Select platform...</option>
                {platforms.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <input
                type="text"
                value={platformInput}
                onChange={(e) => setPlatformInput(e.target.value)}
                className="form-input flex-1"
                placeholder="Or type custom platform..."
              />
              <button type="button" onClick={addPlatform} className="btn btn-outline">Add</button>
            </div>
            <div className="flex flex-wrap gap-2">
              {platformTargets.map((platform) => (
                <span key={platform} className="badge badge-primary flex items-center gap-1">
                  {platform}
                  <button type="button" onClick={() => removePlatform(platform)} className="text-xs hover:text-red-600">×</button>
                </span>
              ))}
              {platformTargets.length === 0 && (
                <span className="text-sm text-gray-500">No platforms specified (runs on all)</span>
              )}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Tags</h2>
          </div>
          <div className="card-body">
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                className="form-input flex-1"
                placeholder="Add tag..."
              />
              <button type="button" onClick={addTag} className="btn btn-outline">Add</button>
            </div>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <span key={tag} className="badge badge-secondary flex items-center gap-1">
                  {tag}
                  <button type="button" onClick={() => removeTag(tag)} className="text-xs hover:text-red-600">×</button>
                </span>
              ))}
              {tags.length === 0 && <span className="text-sm text-gray-500">No tags</span>}
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <button type="submit" disabled={saving} className="btn btn-primary">
            {saving ? <div className="loading-spinner" /> : (isEditing ? 'Update Skill' : 'Create Skill')}
          </button>
          <button type="button" onClick={() => navigate('/skills')} className="btn btn-outline">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}