// frontend/triviamobileapp/src/contexts/AuthContext.tsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import { Platform } from 'react-native';
import { Session, User } from '@supabase/supabase-js';
import AuthService from '../services/AuthService';
import UserService from '../services/UserService';

interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signIn: (email: string) => Promise<any>;
  signUp: (email: string) => Promise<any>;
  signOut: () => Promise<void>;
  signInWithApple: () => Promise<any>;
  signInWithGoogle: () => Promise<any>;
  createTemporaryUser: (username: string) => Promise<any>;
  isTemporaryUser: () => Promise<boolean>;
  getCurrentUsername: () => Promise<string | null>;
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
        console.log('Auth state changed:', event);
        setSession(session);
        setUser(session?.user ?? null);
      }
    );
    
    // Clean up subscription
    return () => {
      subscription.unsubscribe();
    };
  }, []);
  
  // When auth state changes and we have a user, handle identity linking
  useEffect(() => {
    if (user) {
      // Attempt to link identities if needed
      UserService.handlePostAuthLinking().then(linked => {
        if (linked) {
          console.log('Successfully linked identities after authentication');
        }
      });
    }
  }, [user]);
  
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
  
  // Implement sign in with Apple
  const signInWithApple = async () => {
    if (Platform.OS !== 'ios') {
      return { error: { message: 'Apple Sign In is only available on iOS devices' } };
    }
    
    try {
      const response = await AuthService.signInWithApple();
      return response;
    } catch (error: any) {
      console.error('Apple Sign In error in context:', error);
      return { error: { message: error.message || 'Apple Sign In failed' } };
    }
  };
  
  // Implement sign in with Google
  const signInWithGoogle = async () => {
    try {
      const response = await AuthService.signInWithGoogle();
      return response;
    } catch (error: any) {
      console.error('Google Sign In error in context:', error);
      return { error: { message: error.message || 'Google Sign In failed' } };
    }
  };
  
  // Create temporary user with just a display name
  const createTemporaryUser = async (username: string) => {
    return UserService.createTemporaryUser(username);
  };
  
  // Check if current user is temporary
  const isTemporaryUser = async () => {
    return UserService.isTemporaryUser();
  };
  
  // Get current username
  const getCurrentUsername = async () => {
    return UserService.getCurrentUsername();
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
        signInWithGoogle,
        createTemporaryUser,
        isTemporaryUser,
        getCurrentUsername
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