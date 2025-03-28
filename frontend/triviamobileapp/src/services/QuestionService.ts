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
      
      // Set the API URL based on platform since API_URL isn't available from .env
      if (Platform.OS === 'ios') {
        this.baseApiUrl = 'http://localhost:8000';
      } else {
        this.baseApiUrl = 'http://10.0.2.2:8000'; // Android emulator
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
      const response = await fetch(`${this.baseApiUrl}/`, { 
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      
      if (response.ok) {
        console.log('FastAPI backend is available!');
        this.useDirectSupabase = false;
      } else {
        console.log('FastAPI backend returned error status:', response.status);
        this.useDirectSupabase = true;
      }
    } catch (error) {
      console.log('FastAPI backend is not available:', error);
      this.useDirectSupabase = true;
    }
  }

  /**
   * Fetch random game questions
   */
  async getGameQuestions(categories?: string[], count: number = 10): Promise<Question[]> {
    console.log(`Getting ${count} game questions`, categories ? `for categories: ${categories}` : '');
    
    try {
      // Direct Supabase approach - use if API is unavailable
      if (this.useDirectSupabase) {
        console.log('Using direct Supabase access for questions');
        return this.getQuestionsFromSupabase(categories, count);
      }
      
      // API approach - the original implementation
      let url = `${this.baseApiUrl}/questions/game?count=${count}`;
      
      if (categories && categories.length > 0) {
        const categoriesParam = categories.join(',');
        url += `&categories=${encodeURIComponent(categoriesParam)}`;
      }
      
      console.log(`Fetching from API: ${url}`);
      
      const response = await fetch(url);
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
        questionsQuery = questionsQuery.in('category', categories);
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
      
      return questions;
    } catch (error) {
      console.error('Error retrieving questions from Supabase:', error);
      return [];
    }
  }
  
  /**
   * Fetch questions for a specific category
   */
  async getQuestionsByCategory(categoryId: string, count: number = 10): Promise<Question[]> {
    console.log(`Getting ${count} questions for category: ${categoryId}`);
    
    try {
      // Direct Supabase approach if API is unavailable
      if (this.useDirectSupabase) {
        console.log('Using direct Supabase access for category questions');
        return this.getQuestionsFromSupabase([categoryId], count);
      }
      
      // First try the category endpoint
      const url = `${this.baseApiUrl}/questions/category/${categoryId}?limit=${count}`;
      console.log(`Fetching from API: ${url}`);
      
      const response = await fetch(url);
      console.log(`Response status: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        
        // If the category endpoint failed, try generating questions
        console.log('Category endpoint failed, trying to generate questions');
        return this.generateQuestionsWithAnswers(categoryId, count);
      }
      
      // The category endpoint might return questions without answers
      // We need to get the complete questions with answers
      try {
        console.log('Category endpoint successful, generating complete questions');
        return this.generateQuestionsWithAnswers(categoryId, count);
      } catch (genError) {
        console.error('Error generating complete questions:', genError);
        
        // Fall back to direct Supabase
        console.log('Falling back to direct Supabase access');
        return this.getQuestionsFromSupabase([categoryId], count);
      }
    } catch (error) {
      console.error(`Error in getQuestionsByCategory:`, error);
      
      // Fall back to direct Supabase
      console.log('Error occurred, falling back to direct Supabase access');
      return this.getQuestionsFromSupabase([categoryId], count);
    }
  }

  /**
   * Generate complete questions with answers
   */
  async generateQuestionsWithAnswers(category: string, count: number = 10, difficulty?: string): Promise<Question[]> {
    try {
      if (!this.baseApiUrl) {
        throw new Error('API URL not configured');
      }
      
      const url = `${this.baseApiUrl}/questions/generate-complete`;
      console.log(`Generating questions via API: ${url}`);
      
      const requestBody = {
        category,
        count,
        deduplicate: true,
        ...(difficulty && { difficulty })
      };
      
      console.log('Request payload:', JSON.stringify(requestBody));
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      console.log(`Response status: ${response.status} ${response.statusText}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log(`Successfully generated ${data.length} questions`);
      
      return data;
    } catch (error) {
      console.error(`Error generating questions:`, error);
      throw error;
    }
  }
}

// Export as singleton
export default new QuestionService();