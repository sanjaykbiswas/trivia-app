// frontend/triviamobileapp/src/contexts/AuthContext.tsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import { Text } from 'react-native';
import { Session, User } from '@supabase/supabase-js';
import AuthService from '../services/AuthService';

interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signIn: (email: string) => Promise<any>;
  signUp: (email: string) => Promise<any>;
  signOut: () => Promise<void>;
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
        // Make sure we're not rendering error directly to the UI
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
  
  const signIn = async (email: string) => {
    return AuthService.signIn(email);
  };
  
  const signUp = async (email: string) => {
    return AuthService.signUp(email);
  };
  
  const signOut = async () => {
    await AuthService.signOut();
    setSession(null);
    setUser(null);
  };
  
  // Ensure we're not directly rendering text in JSX
  const signInWithApple = async () => {
    console.log('Apple Sign In (placeholder method)');
    return { error: { message: 'Apple Sign In not yet implemented' } };
  };
  
  const signInWithGoogle = async () => {
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