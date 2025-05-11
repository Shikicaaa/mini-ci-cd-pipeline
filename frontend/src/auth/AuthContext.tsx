import { createContext, useContext, useEffect, useState } from 'react';
import { parseJwt } from '../utils/jwt';

interface AuthContextType {
    username: string | null;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType>({ username: null, logout: () => {} });

export const useAuth = () => useContext(AuthContext);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [username, setUsername] = useState<string | null>(null);

    useEffect(() => {
        const getTokenFromCookies = () => {
            const match = document.cookie.match(/(?:^|; )token=([^;]*)/);
            return match ? decodeURIComponent(match[1]) : null;
        };
    
        const token = getTokenFromCookies();
    
        if (token) {
            const payload = parseJwt(token);
    
            if (payload && payload.sub) {
                const currentTime = Math.floor(Date.now() / 1000);
                if (payload.exp && payload.exp > currentTime) {
                    setUsername(payload.sub);
    
                    const timeout = (payload.exp - currentTime) * 1000;
                    const logoutTimer = setTimeout(() => {
                        logout();
                    }, timeout);
    
                    return () => clearTimeout(logoutTimer);
                } else {
                    logout();
                }
            }
        }
    }, []);

    const logout = () => {
        document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
        setUsername(null);
        window.location.href = '/';
    };

    return (
        <AuthContext.Provider value={{ username, logout }}>
            {children}
        </AuthContext.Provider>
    );
};