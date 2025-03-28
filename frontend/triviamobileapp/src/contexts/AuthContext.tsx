// frontend/triviamobileapp/src/contexts/AuthContext.tsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import { Platform, Alert } from 'react-native';
import { Session, User } from '@supabase/supabase-js';
import AuthService from '../services/AuthService';
import UserService from '../services/UserService';

interface AuthError {
  message: string;
  details?: string;
}

interface AuthResult {
  error?: AuthError | null;
  // Other properties can be added as needed
}

interface AuthContextType {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signIn: (email: string) => Promise<AuthResult>;
  signUp: (email: string) => Promise<AuthResult>;
  signOut: () => Promise<void>;
  signInWithApple: () => Promise<AuthResult>;
  signInWithGoogle: () => Promise<AuthResult>;
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
        
        // Log more details about the session
        if (session) {
          console.log('User authenticated:', session.user.id);
          console.log('Provider:', session.user.app_metadata.provider);
        } else {
          console.log('No active session');
        }
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
      }).catch(error => {
        console.error('Error handling post-auth linking:', error);
      });
    }
  }, [user]);
  
  const signIn = async (email: string): Promise<AuthResult> => {
    try {
      return await AuthService.signIn(email);
    } catch (error: any) {
      console.error('Sign in error:', error);
      return { error: { message: error.message || 'Failed to sign in' } };
    }
  };
  
  const signUp = async (email: string): Promise<AuthResult> => {
    try {
      return await AuthService.signUp(email);
    } catch (error: any) {
      console.error('Sign up error:', error);
      return { error: { message: error.message || 'Failed to sign up' } };
    }
  };
  
  const signOut = async () => {
    try {
      await AuthService.signOut();
      setSession(null);
      setUser(null);
    } catch (error: any) {
      console.error('Sign out error:', error);
      Alert.alert('Error', `Failed to sign out: ${error.message}`);
    }
  };
  
  // Implement sign in with Apple
  const signInWithApple = async (): Promise<AuthResult> => {
    if (Platform.OS !== 'ios') {
      return { error: { message: 'Apple Sign In is only available on iOS devices' } };
    }
    
    try {
      const response = await AuthService.signInWithApple();
      
      // If successful, ensure we update our state immediately
      if (!response.error && response.data?.session) {
        setSession(response.data.session);
        setUser(response.data.session.user);
      }
      
      return response;
    } catch (error: any) {
      console.error('Apple Sign In error in context:', error);
      return { error: { message: error.message || 'Apple Sign In failed' } };
    }
  };
  
  // Implement sign in with Google
  const signInWithGoogle = async (): Promise<AuthResult> => {
    try {
      console.log('Initiating Google Sign In from AuthContext');
      const response = await AuthService.signInWithGoogle();
      
      // If successful, ensure we update our state immediately
      if (!response.error && response.data?.session) {
        console.log('Google Sign In successful, updating session state');
        setSession(response.data.session);
        setUser(response.data.session.user);
      } else if (response.error) {
        console.error('Google Sign In error:', response.error);
      }
      
      return response;
    } catch (error: any) {
      console.error('Google Sign In unhandled error in context:', error);
      return { 
        error: { 
          message: error.message || 'Google Sign In failed',
          details: error.stack ? String(error.stack).substring(0, 200) : undefined
        } 
      };
    }
  };
  
  // Create temporary user with just a display name
  const createTemporaryUser = async (username: string) => {
    try {
      return await UserService.createTemporaryUser(username);
    } catch (error: any) {
      console.error('Create temporary user error:', error);
      return null;
    }
  };
  
  // Check if current user is temporary
  const isTemporaryUser = async () => {
    try {
      return await UserService.isTemporaryUser();
    } catch (error) {
      console.error('Check temporary user error:', error);
      return false;
    }
  };
  
  // Get current username
  const getCurrentUsername = async () => {
    try {
      return await UserService.getCurrentUsername();
    } catch (error) {
      console.error('Get current username error:', error);
      return null;
    }
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