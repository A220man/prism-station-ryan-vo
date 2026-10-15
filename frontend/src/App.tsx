import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Health } from './pages/Health';
import { SkillsList } from './pages/SkillsList';
import { SkillDetail } from './pages/SkillDetail';
import { SkillForm } from './pages/SkillForm';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token');
  return !token ? <>{children}</> : <Navigate to="/skills" replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      <Route element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route path="/" element={<Navigate to="/skills" replace />} />
        <Route path="/health" element={<Health />} />
        <Route path="/skills" element={<SkillsList />} />
        <Route path="/skills/new" element={<SkillForm />} />
        <Route path="/skills/:id" element={<SkillDetail />} />
        <Route path="/skills/:id/edit" element={<SkillForm />} />
      </Route>
      <Route path="*" element={<Navigate to="/skills" replace />} />
    </Routes>
  );
}