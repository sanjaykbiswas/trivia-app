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
  // Cache for category name to ID mapping
  private categoryNameToId: Record<string, string> = {};
  // Cache for category ID to name mapping
  private categoryIdToName: Record<string, string> = {};

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
      
      // Update our cache
      if (data) {
        data.forEach(category => {
          this.categoryNameToId[category.name.toLowerCase()] = category.id;
          this.categoryIdToName[category.id] = category.name;
        });
      }
      
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
      
      // Update our cache
      if (data) {
        data.forEach(category => {
          this.categoryNameToId[category.name.toLowerCase()] = category.id;
          this.categoryIdToName[category.id] = category.name;
        });
      }
      
      return data || [];
    } catch (error) {
      console.error('Error fetching popular categories:', error);
      // Return empty array on error to prevent app crashes
      return [];
    }
  }
  
  /**
   * Convert category name to ID
   */
  async getCategoryIdByName(categoryName: string): Promise<string | null> {
    if (!categoryName) return null;
    
    // Check cache first (case-insensitive)
    const lowercaseName = categoryName.toLowerCase();
    if (this.categoryNameToId[lowercaseName]) {
      return this.categoryNameToId[lowercaseName];
    }
    
    try {
      // Look up in database
      if (!this.supabase) {
        throw new Error('Supabase client not initialized');
      }
      
      const { data, error } = await this.supabase
        .from('categories')
        .select('id')
        .ilike('name', categoryName)
        .limit(1);
      
      if (error) {
        throw error;
      }
      
      if (data && data.length > 0) {
        // Update cache
        this.categoryNameToId[lowercaseName] = data[0].id;
        return data[0].id;
      }
      
      return null;
    } catch (error) {
      console.error(`Error looking up category ID for ${categoryName}:`, error);
      return null;
    }
  }
  
  /**
   * Convert category ID to name
   */
  async getCategoryNameById(categoryId: string): Promise<string | null> {
    if (!categoryId) return null;
    
    // Check cache first
    if (this.categoryIdToName[categoryId]) {
      return this.categoryIdToName[categoryId];
    }
    
    try {
      // Look up in database
      if (!this.supabase) {
        throw new Error('Supabase client not initialized');
      }
      
      const { data, error } = await this.supabase
        .from('categories')
        .select('name')
        .eq('id', categoryId)
        .limit(1);
      
      if (error) {
        throw error;
      }
      
      if (data && data.length > 0) {
        // Update cache
        this.categoryIdToName[categoryId] = data[0].name;
        return data[0].name;
      }
      
      return null;
    } catch (error) {
      console.error(`Error looking up category name for ${categoryId}:`, error);
      return null;
    }
  }
  
  /**
   * Get or create a category by name
   */
  async getOrCreateCategoryByName(categoryName: string): Promise<Category | null> {
    if (!categoryName) return null;
    
    try {
      // First try to find by name
      const existingId = await this.getCategoryIdByName(categoryName);
      
      if (existingId) {
        // Get the full category
        if (!this.supabase) {
          throw new Error('Supabase client not initialized');
        }
        
        const { data, error } = await this.supabase
          .from('categories')
          .select('*')
          .eq('id', existingId)
          .limit(1);
        
        if (error) throw error;
        
        if (data && data.length > 0) {
          return data[0];
        }
      }
      
      // If not found, create new category
      if (!this.supabase) {
        throw new Error('Supabase client not initialized');
      }
      
      const { data, error } = await this.supabase
        .from('categories')
        .insert([
          { name: categoryName, play_count: 0, creator: 'user' }
        ])
        .select('*');
      
      if (error) throw error;
      
      if (data && data.length > 0) {
        // Update cache
        this.categoryNameToId[categoryName.toLowerCase()] = data[0].id;
        this.categoryIdToName[data[0].id] = categoryName;
        return data[0];
      }
      
      return null;
    } catch (error) {
      console.error(`Error getting/creating category ${categoryName}:`, error);
      return null;
    }
  }
}

export default new CategoryService();