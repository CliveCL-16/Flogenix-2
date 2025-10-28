import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  userType: 'user' | 'admin' | null;
  login: (email: string, password: string, type: 'user' | 'admin') => boolean;
  logout: () => void;
  userName: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userType, setUserType] = useState<'user' | 'admin' | null>(null);
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    // Check for existing session on mount
    const storedAuth = localStorage.getItem('demo_auth');
    if (storedAuth) {
      const { type, name } = JSON.parse(storedAuth);
      setIsAuthenticated(true);
      setUserType(type);
      setUserName(name);
    }
  }, []);

  const login = (email: string, password: string, type: 'user' | 'admin') => {
    // Demo credentials - NOT FOR PRODUCTION
    const demoCredentials = {
      user: { email: 'user@demo.com', password: 'user123', name: 'Sarah Johnson' },
      admin: { email: 'admin@demo.com', password: 'admin123', name: 'Admin User' }
    };

    const credentials = demoCredentials[type];
    if (email === credentials.email && password === credentials.password) {
      setIsAuthenticated(true);
      setUserType(type);
      setUserName(credentials.name);
      localStorage.setItem('demo_auth', JSON.stringify({ type, name: credentials.name }));
      return true;
    }
    return false;
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUserType(null);
    setUserName(null);
    localStorage.removeItem('demo_auth');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, userType, login, logout, userName }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
