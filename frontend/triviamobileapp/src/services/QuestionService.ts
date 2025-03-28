// frontend/triviamobileapp/src/services/QuestionService.ts
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@env';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

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
  private useDirectSupabase: boolean = false;
  private apiAvailable: boolean = false;
  private connectionTest: boolean = false; // Track if we've tested the connection

  constructor() {
    // Initialize Supabase client
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
      
      // Set the API URL based on platform
      if (Platform.OS === 'ios') {
        // Use localhost for iOS
        this.baseApiUrl = 'http://localhost:8000';
      } else {
        // Use special IP for Android emulator
        this.baseApiUrl = 'http://10.0.2.2:8000';
      }
      
      // Start with direct Supabase mode until we confirm the API works
      this.useDirectSupabase = true;
      
      console.log('QuestionService initialized:');
      console.log('- API URL:', this.baseApiUrl);
      console.log('- Direct Supabase mode:', this.useDirectSupabase);
      
      // Try to ping the API to see if it's available
      this.checkApiAvailability();
      
    } catch (error) {
      console.error('Failed to initialize QuestionService:', error);
      this.supabase = null;
      this.baseApiUrl = '';
      this.useDirectSupabase = true;
    }
  }

  /**
   * Check if the API is available
   */
  private async checkApiAvailability(): Promise<void> {
    try {
      console.log(`Checking FastAPI availability at: ${this.baseApiUrl}`);
      const controller = new AbortController();
      
      // Set a timeout for the fetch request
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`${this.baseApiUrl}/`, { 
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        console.log('🟢 FastAPI backend is available!');
        this.useDirectSupabase = false;
        this.apiAvailable = true;
      } else {
        console.log(`🔴 FastAPI backend returned error status: ${response.status}`);
        this.useDirectSupabase = true;
        this.apiAvailable = false;
      }
      
      this.connectionTest = true;
    } catch (error) {
      console.log(`🔴 FastAPI backend is not available:`, error);
      this.useDirectSupabase = true;
      this.apiAvailable = false;
      this.connectionTest = true;
    }
  }

  /**
   * Fetch random game questions
   */
  async getGameQuestions(categories?: string[], count: number = 10): Promise<Question[]> {
    console.log(`Getting ${count} game questions`, categories ? `for categories: ${categories}` : '');
    
    try {
      // If we haven't tested the connection and haven't explicitly marked it as available
      if (!this.connectionTest && !this.apiAvailable) {
        // Try to check API availability again
        await this.checkApiAvailability();
      }
      
      // Direct Supabase approach - use if API is unavailable
      if (this.useDirectSupabase) {
        console.log('Using direct Supabase access for questions');
        return this.getQuestionsFromSupabase(categories, count);
      }
      
      // API approach
      let url = `${this.baseApiUrl}/questions/game?count=${count}`;
      
      if (categories && categories.length > 0) {
        const categoriesParam = categories.join(',');
        url += `&categories=${encodeURIComponent(categoriesParam)}`;
      }
      
      console.log(`Fetching from API: ${url}`);
      
      // Add timeout to prevent hanging requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(url, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      console.log(`Response status: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        
        // Fall back to direct Supabase if API fails
        console.log('Falling back to direct Supabase access');
        return this.getQuestionsFromSupabase(categories, count);
      }
      
      const data = await response.json();
      console.log(`Received ${data.length} questions from API`);
      
      return data;
    } catch (error) {
      console.error('Error in getGameQuestions:', error);
      
      // Fall back to direct Supabase if API call throws an error
      console.log('Error occurred, falling back to direct Supabase access');
      return this.getQuestionsFromSupabase(categories, count);
    }
  }
  
  /**
   * Direct Supabase approach - queries questions and answers from Supabase
   */
  private async getQuestionsFromSupabase(categories?: string[], count: number = 10): Promise<Question[]> {
    try {
      if (!this.supabase) {
        throw new Error('Supabase client not initialized');
      }
      
      console.log('Querying Supabase for questions directly');
      
      // First, get questions with optional category filter
      let questionsQuery = this.supabase
        .from('questions')
        .select('*')
        .limit(count);
      
      // Add category filter if specified
      if (categories && categories.length > 0) {
        // Log the categories we're filtering by
        console.log(`Filtering by categories:`, categories);
        
        // Check if these are category IDs or names
        if (categories.some(c => c.includes('-'))) {
          // These look like UUIDs, use them directly
          questionsQuery = questionsQuery.in('category', categories);
        } else {
          // These might be category names, try both approaches
          try {
            // Try filtering by name first
            const { data: categoryData } = await this.supabase
              .from('categories')
              .select('name')
              .in('id', categories);
              
            if (categoryData && categoryData.length > 0) {
              // If we found categories by ID, use their names
              const categoryNames = categoryData.map(c => c.name);
              console.log(`Resolved category names:`, categoryNames);
              questionsQuery = questionsQuery.in('category', categoryNames);
            } else {
              // Otherwise use the original values
              questionsQuery = questionsQuery.in('category', categories);
            }
          } catch (e) {
            // If that fails, just use the original values
            console.log(`Category lookup failed, using original values:`, e);
            questionsQuery = questionsQuery.in('category', categories);
          }
        }
      }
      
      // Add order by for randomness
      questionsQuery = questionsQuery.order('created_at');
      
      const { data: questionData, error: questionError } = await questionsQuery;
      
      if (questionError) {
        console.error('Supabase question query error:', questionError);
        throw questionError;
      }
      
      if (!questionData || questionData.length === 0) {
        console.log('No questions found in Supabase');
        // Check if we have category information to provide a better error message
        if (categories && categories.length > 0) {
          console.log(`No questions found for categories: ${categories.join(', ')}`);
        }
        return [];
      }
      
      console.log(`Retrieved ${questionData.length} questions from Supabase`);
      
      // Get the question IDs to fetch their answers
      const questionIds = questionData.map(q => q.id);
      
      // Get answers for these questions
      const { data: answerData, error: answerError } = await this.supabase
        .from('answers')
        .select('*')
        .in('question_id', questionIds);
      
      if (answerError) {
        console.error('Supabase answer query error:', answerError);
        throw answerError;
      }
      
      console.log(`Retrieved ${answerData?.length || 0} answers from Supabase`);
      
      // Create a map of question_id to answer for easy lookup
      const answerMap: Record<string, any> = {};
      answerData?.forEach(answer => {
        answerMap[answer.question_id] = answer;
      });
      
      // Combine questions with their answers
      const questions: Question[] = questionData.map(question => {
        const answer = answerMap[question.id];
        
        // If no answer is found, create a placeholder
        if (!answer) {
          console.warn(`No answer found for question ${question.id}`);
          return {
            id: question.id,
            content: question.content,
            category: question.category,
            correct_answer: 'Unknown',
            incorrect_answers: ['Option 1', 'Option 2', 'Option 3'],
            difficulty: question.difficulty,
            modified_difficulty: question.modified_difficulty
          };
        }
        
        return {
          id: question.id,
          content: question.content,
          category: question.category,
          correct_answer: answer.correct_answer,
          incorrect_answers: answer.incorrect_answers || [],
          difficulty: question.difficulty,
          modified_difficulty: question.modified_difficulty
        };
      });
      
      // Only return questions that have both question content and answer data
      const validQuestions = questions.filter(q => 
        q.content && q.correct_answer && q.incorrect_answers && q.incorrect_answers.length > 0);
      
      console.log(`After filtering, returning ${validQuestions.length} valid questions`);
      
      return validQuestions;
    } catch (error) {
      console.error('Error retrieving questions from Supabase:', error);
      return [];
    }
  }
  
  /**
   * Fetch questions for a specific category
   */
  async getQuestionsByCategory(categoryId: string, count: number = 10): Promise<Question[]> {
    console.log(`Getting ${count} questions for category ID: ${categoryId}`);
    
    try {
      if (!this.connectionTest && !this.apiAvailable) {
        // Try to check API availability again
        await this.checkApiAvailability();
      }
      
      // Direct Supabase approach if API is unavailable
      if (this.useDirectSupabase) {
        console.log('Using direct Supabase access for category questions');
        
        // First, look up the category name if given an ID
        if (this.supabase && categoryId && categoryId.includes('-')) {
          try {
            const { data: categoryData } = await this.supabase
              .from('categories')
              .select('name')
              .eq('id', categoryId)
              .single();
              
            if (categoryData && categoryData.name) {
              console.log(`Category ${categoryId} resolves to name: ${categoryData.name}`);
              // We have two approaches:
              // 1. Get questions by category name
              // 2. Get questions by category ID
              // Let's try both in sequence
              
              // Approach 1: By category name
              const questionsByName = await this.getQuestionsFromSupabase([categoryData.name], count);
              if (questionsByName.length > 0) {
                console.log(`Found ${questionsByName.length} questions by category name`);
                return questionsByName;
              }
              
              // Approach 2: By category ID
              console.log(`No questions found by name, trying by ID`);
              return this.getQuestionsFromSupabase([categoryId], count);
            }
          } catch (e) {
            console.error('Error looking up category name:', e);
          }
        }
        
        // Default approach: try directly with the category ID
        return this.getQuestionsFromSupabase([categoryId], count);
      }
      
      // API approach - only used if API is available
      let url = `${this.baseApiUrl}/questions/game?count=${count}`;
      
      if (categoryId) {
        // Encode the category as a single-item array
        url += `&categories=${encodeURIComponent(categoryId)}`;
      }
      
      console.log(`Fetching from API: ${url}`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(url, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      console.log(`Response status: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        
        // Fall back to direct Supabase
        console.log('API request failed, falling back to direct Supabase access');
        return this.getQuestionsFromSupabase([categoryId], count);
      }
      
      const data = await response.json();
      console.log(`Received ${data.length} questions from API`);
      
      if (data.length === 0) {
        // If the API returned no questions, try Supabase directly
        console.log('No questions found through API, trying Supabase directly');
        return this.getQuestionsFromSupabase([categoryId], count);
      }
      
      return data;
    } catch (error) {
      console.error(`Error in getQuestionsByCategory:`, error);
      
      // Fall back to direct Supabase
      console.log('Error occurred, falling back to direct Supabase access');
      return this.getQuestionsFromSupabase([categoryId], count);
    }
  }
}

// Export as singleton
export default new QuestionService();