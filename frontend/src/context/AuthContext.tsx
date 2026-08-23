import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { secureStore, secureRetrieve, secureRemove } from '../utils/crypto';

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (token: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    useEffect(() => {
        let isMounted = true; // Memory leak prevention
        const checkAuth = async () => {
            try {
                const token = await secureRetrieve('access_token');
                if (isMounted) {
                    if (token) {
                        setIsAuthenticated(true);
                    } else {
                        setIsAuthenticated(false);
                    }
                    setIsLoading(false);
                }
            } catch (error) {
                if (isMounted) {
                    setIsAuthenticated(false);
                    setIsLoading(false);
                }
            }
        };
        
        checkAuth();

        return () => {
            isMounted = false; // Garbage collection optimization
        };
    }, []);

    const login = async (token: string) => {
        await secureStore('access_token', token);
        setIsAuthenticated(true);
    };

    const logout = () => {
        secureRemove('access_token');
        setIsAuthenticated(false);
    };

    return (
        <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
