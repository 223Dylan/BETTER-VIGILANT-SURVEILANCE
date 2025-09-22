# Frontend Architecture Guide

This guide provides a comprehensive overview of the React/TypeScript frontend architecture for the Shoplifting Detection System.

## Table of Contents

1. [Technology Stack](#technology-stack)
2. [Project Structure](#project-structure)
3. [Component Architecture](#component-architecture)
4. [Routing & Navigation](#routing--navigation)
5. [Authentication & Authorization](#authentication--authorization)
6. [State Management](#state-management)
7. [API Integration](#api-integration)
8. [Styling Approach](#styling-approach)
9. [Video Streaming](#video-streaming)
10. [Development Workflow](#development-workflow)
11. [Best Practices](#best-practices)

## Technology Stack

### Core Framework
- **React 18.2.0** - Modern React with hooks and concurrent features
- **TypeScript 4.9.5** - Type safety and enhanced developer experience
- **React Router v6** - Client-side routing with modern patterns

### UI & Styling
- **Material-UI v7.1.1** - Comprehensive React component library
- **Tailwind CSS 3.3.5** - Utility-first CSS framework
- **@emotion/react & @emotion/styled** - CSS-in-JS styling solution

### Data Visualization
- **Chart.js 4.4.9** - Flexible charting library
- **react-chartjs-2 5.3.0** - React wrapper for Chart.js
- **Recharts 2.15.3** - React-specific charting library

### Video & Media
- **HLS.js 1.6.5** - HTTP Live Streaming support
- **@types/hls.js** - TypeScript definitions for HLS.js

### HTTP & API
- **Axios 1.9.0** - Promise-based HTTP client
- **@types/axios** - TypeScript definitions

### Development Tools
- **React Scripts 5.0.1** - Build tooling and development server
- **ESLint 8.57.1** - Code linting and quality
- **PostCSS 8.4.31** - CSS processing
- **Autoprefixer 10.4.16** - CSS vendor prefixing

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── alerts/          # Alert-related components
│   ├── auth/            # Authentication components
│   ├── common/          # Shared/common components
│   ├── layout/          # Layout components
│   └── user/            # User management components
├── pages/               # Page-level components
├── services/            # API and external service integrations
├── types/               # TypeScript type definitions
├── hooks/               # Custom React hooks (if any)
├── utils/               # Utility functions (if any)
├── App.tsx              # Root application component
├── index.tsx            # Application entry point
└── index.css            # Global styles
```

### TypeScript Path Aliases

Configured in `tsconfig.json` for cleaner imports:

```typescript
"paths": {
  "@components/*": ["components/*"],
  "@pages/*": ["pages/*"],
  "@types/*": ["types/*"],
  "@utils/*": ["utils/*"],
  "@services/*": ["services/*"]
}
```

**Usage Example:**
```typescript
// Instead of: import { AlertCard } from '../../../components/alerts/AlertCard'
import { AlertCard } from '@components/alerts/AlertCard';
```

## Component Architecture

### Component Organization

#### 1. **Feature-Based Components** (`components/`)

**Alerts System** (`components/alerts/`)
- `AlertActions.tsx` - Alert action buttons (acknowledge, dismiss)
- `AlertCard.tsx` - Individual alert display
- `AlertDetailModal.tsx` - Detailed alert view
- `AlertFilters.tsx` - Alert filtering controls
- `AlertList.tsx` - Alert list container
- `AlertNotifications.tsx` - Real-time notifications
- `AlertStats.tsx` - Alert statistics
- `AlertUtils.tsx` - Alert utility functions
- `index.ts` - Barrel exports

**Authentication** (`components/auth/`)
- `LoginForm.tsx` - User login interface

**Common Components** (`components/common/`)
- `ProtectedRoute.tsx` - Route protection wrapper

**Layout** (`components/layout/`)
- `MainLayout.tsx` - Application shell with navigation

**User Management** (`components/user/`)
- `UserSettings.tsx` - User preferences and settings

#### 2. **Camera Components** (root level)
- `ActiveCameraGrid.tsx` - Grid of active camera feeds
- `AddCameraForm.tsx` - Camera addition form
- `AddCameraModal.tsx` - Camera addition modal
- `CameraCard.tsx` - Individual camera display
- `CameraDetailPanel.tsx` - Detailed camera information
- `CameraGrid.tsx` - Camera grid layout
- `CameraPerformancePanel.tsx` - Performance metrics
- `CameraSettingsPanel.tsx` - Camera configuration

#### 3. **Utility Components**
- `LoadingOverlay.tsx` - Loading state overlay
- `VideoFeed.tsx` - Live video feed display
- `VideoFileUpload.tsx` - Video file upload
- `VideoPlayer.tsx` - Video playback component

#### 4. **Dashboard Components**
- `DetectionChart.tsx` - Real-time detection analytics with hourly trends
- `RecentSystemEventsPanel.tsx` - Paginated audit log display with 5 events per page
- `MetricsDashboard.tsx` - System metrics overview
- `QuickSettingsPanel.tsx` - Quick access settings
- `AlertsNotificationPanel.tsx` - Active alerts and notifications
- `CameraPerformancePanel.tsx` - Individual camera performance metrics

### Dashboard Architecture

#### Main Dashboard Layout

The main dashboard (`src/pages/Dashboard.tsx`) follows a multi-section layout:

1. **Header Section**
   - System title and description
   - Quick action buttons (Manage Cameras, View Alerts)

2. **Stats Grid**
   - Active Cameras count (enabled/total)
   - System Alerts count (cameras with health errors)
   - Detections (24h) count (actual detection events from last 24 hours)

3. **Analytics Section**
   - `DetectionChart` component with real-time WebSocket updates
   - Hourly detection trends using AreaChart visualization
   - No auto-refresh controls (removed for simplicity)

4. **Performance Section**
   - Camera-specific performance metrics
   - Selectable camera dropdown

5. **Recent Events Section**
   - `RecentSystemEventsPanel` with audit log events
   - 5 events per page with pagination controls
   - No auto-refresh (loads once on page load)

#### Dashboard Metrics

**Current Dashboard Stats:**
```typescript
const stats = [
  {
    name: 'Active Cameras',
    value: `${cameraStats.active}/${cameraStats.total}`,
    icon: VideoCameraIcon,
    color: cameraStats.active > 0 ? 'bg-green-500' : 'bg-gray-400'
  },
  {
    name: 'System Alerts',
    value: cameraStats.error.toString(), // Camera health errors only
    icon: cameraStats.error > 0 ? ExclamationTriangleIcon : BellIcon,
    color: cameraStats.error > 0 ? 'bg-red-500' : 'bg-blue-500'
  },
  {
    name: 'Detections (24h)',
    value: cameraStats.detections24h.toString(), // Real detection count
    icon: ChartBarIcon,
    color: 'bg-purple-500'
  }
];
```

**Data Sources:**
- Active Cameras: `cameraService.getCameras()` with health status filtering
- System Alerts: Camera health errors (`c.health?.status === 'error'`)
- Detections (24h): `metricsService.getMetricsSummary().total_detections_today`

### Component Patterns

#### 1. **Functional Components with Hooks**
```typescript
import React, { useState, useEffect } from 'react';

interface ComponentProps {
  prop1: string;
  prop2?: number;
}

const MyComponent: React.FC<ComponentProps> = ({ prop1, prop2 = 0 }) => {
  const [state, setState] = useState<string>('');

  useEffect(() => {
    // Side effects
  }, []);

  return (
    <div>
      {/* Component JSX */}
    </div>
  );
};

export default MyComponent;
```

#### 2. **Props Interface Definitions**
```typescript
// Always define props interfaces
interface AlertCardProps {
  alert: Alert;
  onAcknowledge: (id: string) => void;
  onDismiss: (id: string) => void;
  compact?: boolean;
}
```

#### 3. **Event Handler Patterns**
```typescript
// Use callback functions for events
const handleCameraAdd = useCallback((camera: Camera) => {
  // Handle camera addition
}, []);

// Pass event handlers as props
<AddCameraForm onAdd={handleCameraAdd} />
```

## Routing & Navigation

### Route Structure

```typescript
// App.tsx - Main routing configuration
<Router>
  <Routes>
    {/* Public routes */}
    <Route path="/login" element={<LoginForm />} />

    {/* Protected routes with layout */}
    <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/cameras" element={<ProtectedRoute><CamerasPage /></ProtectedRoute>} />
      <Route path="/alerts" element={<ProtectedRoute><AlertsPage /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><UserSettings /></ProtectedRoute>} />

      {/* Admin-only routes */}
      <Route path="/analytics" element={<ProtectedRoute requiredRole="admin"><AnalyticsPage /></ProtectedRoute>} />
      <Route path="/users" element={<ProtectedRoute requiredRole="admin"><UsersPage /></ProtectedRoute>} />
    </Route>

    {/* Redirects */}
    <Route path="/" element={<Navigate to="/dashboard" replace />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
</Router>
```

### Protected Routes

```typescript
// components/common/ProtectedRoute.tsx
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole
}) => {
  const isAuthenticated = authService.isAuthenticated();
  const currentUser = authService.getCurrentUser();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && currentUser?.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};
```

### Navigation Structure

**Main Navigation Areas:**
- **Dashboard** - System overview and metrics
- **Cameras** - Camera management and live feeds
- **Alerts** - Alert management and history
- **Analytics** - Advanced analytics (Admin only)
- **Users** - User management (Admin only)
- **Settings** - User preferences

## Authentication & Authorization

### Authentication Flow

```typescript
// services/auth.service.ts pattern
class AuthService {
  private static instance: AuthService;

  login(credentials: LoginCredentials): Promise<AuthResponse>
  logout(): void
  isAuthenticated(): boolean
  getCurrentUser(): User | null
  getToken(): string | null
}
```

### Role-Based Access Control

**User Roles:**
- **Admin** - Full system access
- **Operator** - Camera and alert management
- **Viewer** - Read-only access

**Implementation:**
```typescript
// In ProtectedRoute component
if (requiredRole && currentUser?.role !== requiredRole) {
  return <Navigate to="/dashboard" replace />;
}

// In components
const isAdmin = currentUser?.role === 'admin';
```

### Token Management

- **Storage**: localStorage for auth tokens
- **Interceptors**: Automatic token injection in API requests
- **Expiration**: Automatic logout on 401 responses

## State Management

### Current Approach

**Local Component State** (useState, useReducer)
- Form data
- UI state (loading, errors)
- Component-specific data

**Service Layer State**
- Authentication state (AuthService)
- API responses (ApiService)
- Real-time data (WebSocket connections)

### State Patterns

#### 1. **Form State Management**
```typescript
const [formData, setFormData] = useState<CameraFormData>({
  name: '',
  source: '',
  // ...other fields
});

const handleInputChange = (field: keyof CameraFormData, value: string) => {
  setFormData(prev => ({ ...prev, [field]: value }));
};
```

#### 2. **Loading and Error States**
```typescript
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

const fetchData = async () => {
  try {
    setLoading(true);
    setError(null);
    const data = await apiService.getData();
    // Handle success
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};
```

#### 3. **Real-time Data Updates**
```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8001/ws');

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Update component state based on real-time data
  };

  return () => ws.close();
}, []);
```

## API Integration

### Service Architecture

```typescript
// services/api.service.ts
class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: 'http://localhost:8001',
      headers: { 'Content-Type': 'application/json' }
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor for auth
    this.api.interceptors.request.use(config => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }
}
```

### Service Layer Pattern

**Individual Service Files:**
- `auth.service.ts` - Authentication operations
- `camera.service.ts` - Camera management
- `alert.service.ts` - Alert operations
- `user.service.ts` - User management
- `metrics.service.ts` - Analytics and metrics

**Usage in Components:**
```typescript
import { cameraService } from '@services/camera.service';

const CamerasPage: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const data = await cameraService.getAllCameras();
        setCameras(data);
      } catch (error) {
        // Handle error
      }
    };

    fetchCameras();
  }, []);
};
```

## Styling Approach

### Hybrid Styling Strategy

**1. Material-UI Components**
- Primary UI components (buttons, inputs, modals)
- Theme consistency
- Accessibility built-in

**2. Tailwind CSS Classes**
- Layout and spacing utilities
- Responsive design
- Custom styling when needed

**3. Emotion Styled Components**
- Complex component styling
- Dynamic styles based on props

### Implementation Examples

```typescript
// Material-UI + Tailwind combination
import { Button, TextField } from '@mui/material';

const LoginForm: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        <TextField
          fullWidth
          label="Email"
          variant="outlined"
          className="mb-4"
        />
        <Button
          fullWidth
          variant="contained"
          className="bg-blue-600 hover:bg-blue-700"
        >
          Login
        </Button>
      </div>
    </div>
  );
};
```

### Responsive Design

```typescript
// Tailwind responsive classes
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {cameras.map(camera => (
    <CameraCard key={camera.id} camera={camera} />
  ))}
</div>
```

## Video Streaming

### HLS.js Integration

```typescript
import Hls from 'hls.js';

const VideoFeed: React.FC<{ streamUrl: string }> = ({ streamUrl }) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(streamUrl);
      hls.attachMedia(videoRef.current);

      return () => hls.destroy();
    }
  }, [streamUrl]);

  return (
    <video
      ref={videoRef}
      controls
      className="w-full h-auto"
      autoPlay
      muted
    />
  );
};
```

### Video Component Patterns

**1. Live Feed Display**
- Real-time streaming with HLS.js
- Error handling for connection issues
- Loading states and fallbacks

**2. Video Upload**
- File upload with progress indicators
- Format validation
- Preview functionality

**3. Video Playback**
- Recorded video playback
- Seeking and controls
- Multiple format support

## Development Workflow

### Local Development Setup

```bash
# Install dependencies
npm install

# Start development server
npm start

# Development server runs on http://localhost:3000
# API proxy configured to http://localhost:8001
```

### Build Process

```bash
# Production build
npm run build

# Test build locally
npm run build && npx serve -s build
```

### Code Quality

```bash
# Linting
npm run lint
npm run lint:fix

# Type checking
npx tsc --noEmit
```

### Environment Configuration

**Development** (`package.json`):
```json
{
  "proxy": "http://localhost:8001"
}
```

**Production**: Configure environment variables for API endpoints

## Best Practices

### 1. **Component Design**
- Keep components small and focused
- Use TypeScript interfaces for all props
- Implement proper error boundaries
- Use React.memo for expensive components

### 2. **State Management**
- Prefer local state when possible
- Use custom hooks for shared logic
- Implement proper cleanup in useEffect

### 3. **Performance**
- Lazy load heavy components
- Optimize re-renders with useCallback/useMemo
- Implement virtual scrolling for large lists

### 4. **Error Handling**
- Implement error boundaries
- Show user-friendly error messages
- Log errors for debugging

### 5. **Accessibility**
- Use semantic HTML elements
- Implement proper ARIA labels
- Ensure keyboard navigation works

### 6. **Testing**
- Write unit tests for utility functions
- Integration tests for critical user flows
- Use React Testing Library patterns

## Future Considerations

### Potential Improvements

1. **State Management**: Consider Redux Toolkit for complex state
2. **Real-time Updates**: Implement WebSocket hooks
3. **Offline Support**: Add service worker for offline functionality
4. **Performance**: Implement code splitting and lazy loading
5. **Testing**: Add comprehensive test suite
6. **Documentation**: Add Storybook for component documentation

### Migration Paths

- **React 19**: Plan for upcoming React features
- **Material-UI v6**: Stay updated with MUI releases
- **Vite**: Consider migrating from Create React App to Vite

---

This architecture guide should be updated as the frontend evolves. Keep this document in sync with actual implementation changes and architectural decisions.
