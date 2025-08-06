import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { LoginForm } from './components/auth/LoginForm';
import { UserSettings } from './components/user/UserSettings';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { Permission } from './hooks/usePermissions';
import { ThemeProvider } from './contexts/ThemeContext';
import { NotificationProvider } from './contexts/NotificationContext';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard';
import CamerasPage from './pages/CamerasPage';
import AlertsPage from './pages/AlertsPage';
import UsersPage from './pages/UsersPage';
import AnalyticsPage from './pages/AnalyticsPage';
import NotificationsPage from './pages/NotificationsPage';

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <NotificationProvider>
        <Router>
          <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginForm />} />

          {/* Protected routes */}
          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            {/* Dashboard route */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            {/* Cameras route - requires camera view permission */}
            <Route
              path="/cameras"
              element={
                <ProtectedRoute requiredPermission={Permission.CAMERA_VIEW}>
                  <CamerasPage />
                </ProtectedRoute>
              }
            />

            {/* User routes */}
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <UserSettings />
                </ProtectedRoute>
              }
            />
            <Route
              path="/notifications"
              element={
                <ProtectedRoute>
                  <NotificationsPage />
                </ProtectedRoute>
              }
            />

            {/* Security routes */}
            <Route
              path="/alerts"
              element={
                <ProtectedRoute requiredPermission={Permission.ALERT_VIEW}>
                  <AlertsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute requiredPermission={Permission.ANALYTICS_VIEW}>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />

            {/* Admin routes */}
            <Route
              path="/users"
              element={
                <ProtectedRoute requiredPermission={Permission.USER_VIEW}>
                  <UsersPage />
                </ProtectedRoute>
              }
            />

            {/* Default route */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Route>

          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </Router>
      </NotificationProvider>
    </ThemeProvider>
  );
};

export default App;
