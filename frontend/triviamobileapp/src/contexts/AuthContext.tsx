import React, { createContext, useState, useEffect, useContext } from 'react';
import { Session, User } from '@supabase/supabase-js';
import AuthService from '../services/AuthService';

interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<any>;
  signUp: (email: string, password: string) => Promise<any>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<any>;
  signInWithApple: () => Promise<any>;
  signInWithGoogle: () => Promise<any>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Load session on startup
    async function loadSession() {
      try {
        setLoading(true);
        const { data } = await AuthService.getSession();
        setSession(data.session);
        setUser(data.session?.user ?? null);
      } catch (error) {
        console.error('Error loading auth session:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadSession();
    
    // Set up auth state change listener
    const { data: { subscription } } = AuthService.getSupabaseClient().auth.onAuthStateChange(
      async (event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
      }
    );
    
    // Clean up subscription
    return () => {
      subscription.unsubscribe();
    };
  }, []);
  
  const signIn = async (email: string, password: string) => {
    return AuthService.signIn(email, password);
  };
  
  const signUp = async (email: string, password: string) => {
    return AuthService.signUp(email, password);
  };
  
  const signOut = async () => {
    await AuthService.signOut();
    setSession(null);
    setUser(null);
  };
  
  const resetPassword = async (email: string) => {
    return AuthService.resetPassword(email);
  };
  
  // New placeholder methods for social login
  const signInWithApple = async () => {
    // This would be implemented with @invertase/react-native-apple-authentication
    console.log('Apple Sign In (placeholder method)');
    return { error: { message: 'Apple Sign In not yet implemented' } };
  };
  
  const signInWithGoogle = async () => {
    // This would be implemented with @react-native-google-signin/google-signin
    console.log('Google Sign In (placeholder method)');
    return { error: { message: 'Google Sign In not yet implemented' } };
  };
  
  return (
    <AuthContext.Provider
      value={{
        session,
        user,
        loading,
        signIn,
        signUp,
        signOut,
        resetPassword,
        signInWithApple,
        signInWithGoogle
      }}
    >
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