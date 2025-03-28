// frontend/triviamobileapp/src/services/CategoryService.ts
import { SUPABASE_URL } from '@env';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SUPABASE_ANON_KEY } from '@env';

export interface Category {
  id: string;
  name: string;
  play_count: number;
  price: number;
  creator: string;
}

class CategoryService {
  private supabase: SupabaseClient | null = null;

  constructor() {
    // Initialize Supabase client directly
    try {
      this.supabase = createClient(
        SUPABASE_URL, 
        SUPABASE_ANON_KEY,
        {
          auth: {
            storage: AsyncStorage,
            autoRefreshToken: true,
            persistSession: true,
          }
        }
      );
    } catch (error) {
      console.error('Failed to initialize Supabase client:', error);
      this.supabase = null;
    }
  }

  /**
   * Fetch all categories from the backend
   */
  async getAllCategories(): Promise<Category[]> {
    try {
      // Check if Supabase client is initialized
      if (!this.supabase) {
        throw new Error('Supabase client not initialized');
      }
      
      // Use Supabase client to query the categories table directly
      const { data, error } = await this.supabase
        .from('categories')
        .select('*');
      
      if (error) {
        throw new Error(`Supabase error: ${error.message}`);
      }
      
      console.log('Categories fetched from Supabase:', data);
      return data || [];
    } catch (error) {
      console.error('Error fetching categories:', error);
      // Return empty array on error to prevent app crashes
      return [];
    }
  }

  /**
   * Fetch popular categories based on play count
   */
  async getPopularCategories(limit = 10): Promise<Category[]> {
    try {
      // Check if Supabase client is initialized
      if (!this.supabase) {
        throw new Error('Supabase client not initialized');
      }
      
      const { data, error } = await this.supabase
        .from('categories')
        .select('*')
        .order('play_count', { ascending: false })
        .limit(limit);
      
      if (error) {
        throw new Error(`Supabase error: ${error.message}`);
      }
      
      return data || [];
    } catch (error) {
      console.error('Error fetching popular categories:', error);
      // Return empty array on error to prevent app crashes
      return [];
    }
  }
}

export default new CategoryService();