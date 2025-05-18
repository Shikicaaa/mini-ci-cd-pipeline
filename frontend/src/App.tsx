import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginForm from './components/loginform';
import RegisterForm from './components/RegisterForm';
import HomePage from './components/HomePage';
import { AuthProvider } from './auth/AuthContext';
import Dashboard from './pages/Dashboard';


const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;