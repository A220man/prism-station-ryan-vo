import '@testing-library/jest-dom';
import { vi } from 'vitest';

vi.mock('../api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
  setAccessToken: vi.fn(),
  skillsApi: {
    list: vi.fn(),
    get: vi.fn(),
    getBySlug: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    validate: vi.fn(),
    export: vi.fn(),
    search: vi.fn(),
  },
  authApi: {
    register: vi.fn(),
    login: vi.fn(),
    getMe: vi.fn(),
    logout: vi.fn(),
    oidcLogin: vi.fn(),
    oidcConfig: vi.fn(),
  },
  healthApi: {
    check: vi.fn(),
    dbCheck: vi.fn(),
  },
}));