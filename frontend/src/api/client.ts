import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
}

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      setAccessToken(null);
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface Skill {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  version: string;
  content: string;
  platform_targets: string[];
  tags: string[];
  author_id: number;
  created_at: string;
  updated_at: string;
}

export interface SkillListResponse {
  items: Skill[];
  total: number;
  skip: number;
  limit: number;
}

export interface SkillCreate {
  name: string;
  slug: string;
  description?: string;
  version: string;
  content: string;
  platform_targets: string[];
  tags: string[];
}

export interface SkillUpdate {
  name?: string;
  description?: string;
  version?: string;
  content?: string;
  platform_targets?: string[];
  tags?: string[];
}

export interface SkillValidationResponse {
  valid: boolean;
  errors: Array<{ type: string; message: string }>;
}

export interface SkillExportResponse {
  content: string;
  format: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  roles: string[];
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface OIDCLoginResponse {
  authorization_url: string;
  state: string;
}

export const skillsApi = {
  list: (params?: { skip?: number; limit?: number; search?: string; platform?: string; tag?: string }) =>
    api.get<SkillListResponse>('/skills', { params }),

  get: (id: number) => api.get<Skill>(`/skills/${id}`),

  getBySlug: (slug: string) => api.get<Skill>(`/skills/slug/${slug}`),

  create: (data: SkillCreate) => api.post<Skill>('/skills', data),

  update: (id: number, data: SkillUpdate) => api.patch<Skill>(`/skills/${id}`, data),

  delete: (id: number) => api.delete(`/skills/${id}`),

  validate: (content: string, platform_targets: string[] = []) =>
    api.post<SkillValidationResponse>('/skills/validate', { content, platform_targets }),

  export: (id: number, format: 'markdown' | 'json' = 'markdown') =>
    api.get<SkillExportResponse>(`/skills/${id}/export`, { params: { format } }),

  search: (query: string, limit = 10) => api.get<Skill[]>(`/skills/search/${encodeURIComponent(query)}`, { params: { limit } }),
};

export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post<Token>('/auth/register', data),
  login: (email: string, password: string) =>
    api.post<Token>('/auth/login', new URLSearchParams({ username: email, password })),

  getMe: () => api.get<User>('/auth/me'),

  logout: () => api.post('/auth/logout'),

  oidcLogin: () => api.get<OIDCLoginResponse>('/auth/oidc/login'),

  oidcConfig: () => api.get('/auth/oidc/config'),
};

export const healthApi = {
  check: () => api.get('/health'),
  dbCheck: () => api.get('/health/db'),
};

export default api;