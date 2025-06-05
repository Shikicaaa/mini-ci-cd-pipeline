import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginForm from './components/loginform';
import RegisterForm from './components/RegisterForm';
import HomePage from './components/HomePage';
import { AuthProvider } from './auth/AuthContext';
import Dashboard from './pages/Dashboard';
import ThankYouForm from './components/ThankYouForm';
import NotificationCenter from './components/NotificationCenter';
import './index.css'
import './App.css'


const App = () => {
  // console.log(import.meta.env.VITE_API_URL)
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          <Route path="/thank-you" element={<ThankYouForm />}/>
        </Routes>
      </Router>
      <NotificationCenter />
    </AuthProvider>
  );
};

export default App;