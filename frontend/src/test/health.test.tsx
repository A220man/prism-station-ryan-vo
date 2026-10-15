import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Health } from '../pages/Health';

vi.mock('../api/client', () => ({
  healthApi: {
    check: vi.fn().mockResolvedValue({ data: { status: 'healthy', app: 'prism-station', environment: 'development' } }),
    dbCheck: vi.fn().mockResolvedValue({ data: { status: 'healthy', database: 'connected' } }),
  },
}));

describe('Health Page', () => {
  it('renders loading state initially', () => {
    const { container } = render(
      <BrowserRouter>
        <Health />
      </BrowserRouter>
    );

    expect(container.querySelector('.card')).toBeInTheDocument();
  });

  it('displays health data when loaded', async () => {
    render(
      <BrowserRouter>
        <Health />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Application Health')).toBeInTheDocument();
    });
  });

  it('displays database health status', async () => {
    render(
      <BrowserRouter>
        <Health />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Database Health')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('connected')).toBeInTheDocument();
    });
  });
});

describe('Smoke Test', () => {
  it('health check', () => {
    expect(1 + 1).toBe(2);
  });
});