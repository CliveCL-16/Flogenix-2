import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient, UserInfo, LoginCredentials, AuthResponse } from '@/lib/api';

interface AuthContextType {
  user: UserInfo | null;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  hasRole: (roles: string | string[]) => boolean;
  // Legacy support for existing components
  userType: 'user' | 'admin' | null;
  userName: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user is authenticated on app start
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          apiClient.setToken(token); // Ensure API client has the token
          const userData = await apiClient.getCurrentUser();
          setUser(userData);
        }
      } catch (error) {
        // Token might be expired or invalid
        apiClient.clearToken();
        // Try demo auth for backward compatibility
        const storedAuth = localStorage.getItem('demo_auth');
        if (storedAuth) {
          const { type, name } = JSON.parse(storedAuth);
          // Create mock user for demo
          setUser({
            id: 1,
            user_id: 'DEMO-USER',
            email: type === 'admin' ? 'admin@demo.com' : 'user@demo.com',
            username: name,
            first_name: name.split(' ')[0] || 'Demo',
            last_name: name.split(' ')[1] || 'User',
            role: type === 'admin' ? 'ADMIN' : 'USER',
            two_factor_enabled: false
          });
          // Set a demo token for API calls
          apiClient.setToken('demo-token');
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
    try {
      const response = await apiClient.login(credentials);
      setUser(response.user_info);
      return response;
    } catch (error) {
      // Fallback to demo authentication for development
      if (credentials.email_or_username === 'user@demo.com' && credentials.password === 'user123') {
        const demoUser: UserInfo = {
          id: 1,
          user_id: 'DEMO-USER',
          email: 'user@demo.com',
          username: 'sarah_johnson',
          first_name: 'Sarah',
          last_name: 'Johnson',
          role: 'USER',
          two_factor_enabled: false
        };
        
        setUser(demoUser);
        localStorage.setItem('demo_auth', JSON.stringify({ type: 'user', name: 'Sarah Johnson' }));
        apiClient.setToken('demo-token'); // Set demo token for API calls
        
        return {
          access_token: 'demo-token',
          refresh_token: 'demo-refresh',
          token_type: 'bearer',
          expires_in: 3600,
          user_info: demoUser
        };
      } else if (credentials.email_or_username === 'admin@demo.com' && credentials.password === 'admin123') {
        const demoAdmin: UserInfo = {
          id: 2,
          user_id: 'DEMO-ADMIN',
          email: 'admin@demo.com',
          username: 'admin_user',
          first_name: 'Admin',
          last_name: 'User',
          role: 'ADMIN',
          two_factor_enabled: false
        };
        
        setUser(demoAdmin);
        localStorage.setItem('demo_auth', JSON.stringify({ type: 'admin', name: 'Admin User' }));
        apiClient.setToken('demo-admin-token'); // Set demo token for API calls
        
        return {
          access_token: 'demo-admin-token',
          refresh_token: 'demo-admin-refresh',
          token_type: 'bearer',
          expires_in: 3600,
          user_info: demoAdmin
        };
      }
      
      throw error;
    }
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      apiClient.clearToken();
      localStorage.removeItem('demo_auth');
    }
  };

  const isAuthenticated = !!user;

  const hasRole = (roles: string | string[]): boolean => {
    if (!user) return false;
    const roleArray = Array.isArray(roles) ? roles : [roles];
    return roleArray.includes(user.role);
  };

  // Legacy compatibility
  const userType = user ? (user.role === 'ADMIN' || user.role === 'SUPER_ADMIN' ? 'admin' : 'user') : null;
  const userName = user ? `${user.first_name} ${user.last_name}` : null;

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    isAuthenticated,
    hasRole,
    userType,
    userName,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
