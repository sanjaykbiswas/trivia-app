import { createClient, SupabaseClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@env';

// Make sure polyfills are processed first
import 'react-native-url-polyfill/auto';

class AuthService {
  private supabase: SupabaseClient;
  
  constructor() {
    // Check if environment variables are available
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
      console.error('Supabase credentials are missing. Make sure .env file is properly configured.');
    }
    
    try {
      this.supabase = createClient(
        SUPABASE_URL || '', 
        SUPABASE_ANON_KEY || '', 
        {
          auth: {
            storage: AsyncStorage,
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: false,
          },
        }
      );
    } catch (error) {
      console.error('Failed to initialize Supabase client:', error);
      // Initialize with a dummy client to prevent crashes
      this.supabase = {} as SupabaseClient;
    }
  }
  
  async signUp(email: string, password: string) {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.signUp({
      email,
      password,
    });
  }
  
  async signIn(email: string, password: string) {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.signInWithPassword({
      email,
      password,
    });
  }
  
  async signOut() {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.signOut();
  }
  
  async resetPassword(email: string) {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.resetPasswordForEmail(email);
  }
  
  async getCurrentUser() {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.getUser();
  }
  
  async getSession() {
    if (!this.supabase.auth) return { data: { session: null }, error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.getSession();
  }
  
  // New placeholder methods for social login
  async signInWithApple() {
    // This would be implemented with @invertase/react-native-apple-authentication
    console.log('Apple Sign In (placeholder method in service)');
    return { error: { message: 'Apple Sign In not yet implemented' } };
  }
  
  async signInWithGoogle() {
    // This would be implemented with @react-native-google-signin/google-signin
    console.log('Google Sign In (placeholder method in service)');
    return { error: { message: 'Google Sign In not yet implemented' } };
  }
  
  getSupabaseClient() {
    return this.supabase;
  }
}

export default new AuthService();