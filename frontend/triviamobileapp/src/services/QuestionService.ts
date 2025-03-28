// frontend/triviamobileapp/src/services/QuestionService.ts
// Service for fetching questions from the backend API
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@env';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Question model based on backend API structure
export interface Question {
  id: string;
  content: string;
  category: string;
  correct_answer: string;
  incorrect_answers: string[];
  difficulty?: string;
  modified_difficulty?: string;
}

class QuestionService {
  private supabase: SupabaseClient | null = null;
  private baseApiUrl: string;

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
      
      // Set base API URL for FastAPI endpoints
      // The backend API is hosted at the same URL as Supabase but with different paths
      this.baseApiUrl = SUPABASE_URL;
      
      console.log('QuestionService initialized with base URL:', this.baseApiUrl);
    } catch (error) {
      console.error('Failed to initialize Supabase client:', error);
      this.supabase = null;
      this.baseApiUrl = '';
    }
  }

  /**
   * Fetch random game questions for the given categories
   * 
   * @param categories Optional array of category IDs
   * @param count Number of questions to fetch (default: 10)
   */
  async getGameQuestions(categories?: string[], count: number = 10): Promise<Question[]> {
    try {
      // Check if API URL is configured
      if (!this.baseApiUrl) {
        throw new Error('API URL not configured');
      }
      
      // Build API URL following FastAPI route structure
      // Based on backend/src/controllers/question_controller.py route definitions
      let url = `${this.baseApiUrl}/questions/game?count=${count}`;
      
      // Add categories parameter if provided
      if (categories && categories.length > 0) {
        // Convert array to comma-separated string and append to URL
        const categoriesParam = categories.join(',');
        url += `&categories=${encodeURIComponent(categoriesParam)}`;
      }
      
      console.log(`Fetching game questions from: ${url}`);
      
      // Make API request
      const response = await fetch(url);
      
      // Log more details about the response for debugging
      console.log(`API Response status: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        console.error(`API error ${response.status}: ${response.statusText}`);
        // For debugging, try to read the error message from response body
        try {
          const errorData = await response.text();
          console.error('Error response body:', errorData);
        } catch (e) {
          console.error('Could not read error response body');
        }
        
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`Received ${data.length} questions from API`);
      
      return data;
    } catch (error) {
      console.error('Error fetching game questions:', error);
      throw error;
    }
  }
  
  /**
   * Fetch random game questions for a specific category
   * 
   * @param categoryId Category ID
   * @param count Number of questions to fetch
   */
  async getQuestionsByCategory(categoryId: string, count: number = 10): Promise<Question[]> {
    console.log(`Fetching ${count} questions for category: ${categoryId}`);
    
    try {
      // Check if API URL is configured
      if (!this.baseApiUrl) {
        throw new Error('API URL not configured');
      }
      
      // Use the category endpoint as defined in backend/src/controllers/question_controller.py
      const url = `${this.baseApiUrl}/questions/category/${categoryId}?limit=${count}`;
      console.log(`Fetching from category endpoint: ${url}`);
      
      const response = await fetch(url);
      
      // Log response details
      console.log(`API Response status: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        console.error(`API error ${response.status}: ${response.statusText}`);
        try {
          const errorData = await response.text();
          console.error('Error response body:', errorData);
        } catch (e) {
          console.error('Could not read error response body');
        }
        
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`Successfully fetched ${data.length} questions from category endpoint`);
      
      return data;
    } catch (error) {
      console.error(`Error fetching questions for category ${categoryId}:`, error);
      throw error;
    }
  }

  /**
   * Get a complete question with answer by ID
   * 
   * @param questionId Question ID
   */
  async getQuestionById(questionId: string): Promise<Question | null> {
    try {
      // Check if API URL is configured
      if (!this.baseApiUrl) {
        throw new Error('API URL not configured');
      }
      
      // Use question endpoint as defined in backend/src/controllers/question_controller.py
      const url = `${this.baseApiUrl}/questions/${questionId}`;
      console.log(`Fetching question by ID from: ${url}`);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        console.error(`API error ${response.status}: ${response.statusText}`);
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching question ${questionId}:`, error);
      return null;
    }
  }
  
  /**
   * Generate new questions for a category
   * 
   * @param category Category name or ID
   * @param count Number of questions to generate
   * @param difficulty Optional difficulty level
   */
  async generateQuestions(category: string, count: number = 10, difficulty?: string): Promise<Question[]> {
    try {
      // Check if API URL is configured
      if (!this.baseApiUrl) {
        throw new Error('API URL not configured');
      }
      
      // Use generate-complete endpoint as defined in backend/src/controllers/question_controller.py
      const url = `${this.baseApiUrl}/questions/generate-complete`;
      console.log(`Generating questions for category ${category} from: ${url}`);
      
      // Prepare the request body with proper typing
      const requestBody: {
        category: string;
        count: number;
        deduplicate: boolean;
        difficulty?: string;
      } = {
        category,
        count,
        deduplicate: true
      };
      
      // Add difficulty if provided
      if (difficulty) {
        requestBody.difficulty = difficulty;
      }
      
      // Make POST request
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      if (!response.ok) {
        console.error(`API error ${response.status}: ${response.statusText}`);
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`Successfully generated ${data.length} questions`);
      
      return data;
    } catch (error) {
      console.error(`Error generating questions for category ${category}:`, error);
      throw error;
    }
  }
}

// Export as singleton
export default new QuestionService();