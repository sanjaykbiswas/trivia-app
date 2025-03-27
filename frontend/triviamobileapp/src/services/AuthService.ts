import { createClient, SupabaseClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Environment variables would be better, but for simplicity:
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

class AuthService {
  private supabase: SupabaseClient;
  
  constructor() {
    this.supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        storage: AsyncStorage as any,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
      },
    });
  }
  
  async signUp(email: string, password: string) {
    return this.supabase.auth.signUp({
      email,
      password,
    });
  }
  
  async signIn(email: string, password: string) {
    return this.supabase.auth.signInWithPassword({
      email,
      password,
    });
  }
  
  async signOut() {
    return this.supabase.auth.signOut();
  }
  
  async resetPassword(email: string) {
    return this.supabase.auth.resetPasswordForEmail(email);
  }
  
  async getCurrentUser() {
    return this.supabase.auth.getUser();
  }
  
  async getSession() {
    return this.supabase.auth.getSession();
  }
  
  getSupabaseClient() {
    return this.supabase;
  }
}

export default new AuthService();