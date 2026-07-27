import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import IngestPage from './pages/IngestPage';
import { AuthProvider } from './contexts/AuthContext';
import { IngestionProvider } from './contexts/IngestionContext';

function App() {
  return (
    <AuthProvider>
      <IngestionProvider>
        <Router>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/ingest" element={<IngestPage />} />
            {/* Redirect unknown routes to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </IngestionProvider>
    </AuthProvider>
  );
}

export default App;
