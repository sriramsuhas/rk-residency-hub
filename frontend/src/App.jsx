import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Profile from './pages/Profile';
import Home from './pages/Home';
import RoomListing from './pages/RoomListing';
import RoomDetails from './pages/RoomDetails';
import MyBookings from './pages/MyBookings';
import ReceptionBookings from './pages/ReceptionBookings';
import RaiseMaintenanceRequest from './pages/RaiseMaintenanceRequest';
import MyRequests from './pages/MyRequests';
import MyTasks from './pages/MyTasks';
import ReceptionMaintenance from './pages/ReceptionMaintenance';
import Reports from './pages/Reports';
import AuditLog from './pages/AuditLog';
import ManageRooms from './pages/ManageRooms';
import ManageUsers from './pages/ManageUsers';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rooms/:id"
            element={
              <ProtectedRoute>
                <RoomDetails />
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-bookings"
            element={
              <ProtectedRoute allowedRoles={['CUSTOMER']}>
                <MyBookings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reception/bookings"
            element={
              <ProtectedRoute allowedRoles={['RECEPTION', 'OWNER']}>
                <ReceptionBookings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/raise-request"
            element={
              <ProtectedRoute allowedRoles={['CUSTOMER']}>
                <RaiseMaintenanceRequest />
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-requests"
            element={
              <ProtectedRoute allowedRoles={['CUSTOMER']}>
                <MyRequests />
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-tasks"
            element={
              <ProtectedRoute allowedRoles={['HOUSEKEEPING']}>
                <MyTasks />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reception/maintenance"
            element={
              <ProtectedRoute allowedRoles={['RECEPTION', 'OWNER']}>
                <ReceptionMaintenance />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute allowedRoles={['RECEPTION', 'OWNER']}>
                <Reports />
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit-log"
            element={
              <ProtectedRoute allowedRoles={['OWNER']}>
                <AuditLog />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manage-rooms"
            element={
              <ProtectedRoute allowedRoles={['OWNER']}>
                <ManageRooms />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manage-users"
            element={
              <ProtectedRoute allowedRoles={['OWNER']}>
                <ManageUsers />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

