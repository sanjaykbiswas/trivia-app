// frontend/triviamobileapp/src/services/QuestionService.ts
// Service for fetching questions from the backend API
import { SUPABASE_URL } from '@env';
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SUPABASE_ANON_KEY } from '@env';

// Question model based on backend API structure
export interface Question {
  id: string;
  content: string;
  category: string;
  correct_answer: string;
  incorrect_answers: string[];
  difficulty?: string;
}

class QuestionService {
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
   * Fetch random game questions for the given categories
   * 
   * @param categories Optional array of category IDs
   * @param count Number of questions to fetch (default: 10)
   */
  async getGameQuestions(categories?: string[], count: number = 10): Promise<Question[]> {
    try {
      // For development or if API isn't set up yet, use mock data
      if (!SUPABASE_URL || SUPABASE_URL === '') {
        console.warn('SUPABASE_URL not configured, using mock questions data');
        
        // If we have categories, use the first one as filter
        const categoryFilter = categories && categories.length > 0 ? categories[0] : undefined;
        return this.getMockQuestions(count, categoryFilter);
      }
      
      // Build API URL with query parameters
      // The API URL might need to be adjusted based on your backend setup
      // Try different paths if one doesn't work
      
      // Option 1: Direct endpoint (assuming FastAPI is directly exposed)
      let url = `${SUPABASE_URL}/api/questions/game?count=${count}`;
      
      // Option 2: If there's a specific base path in your API
      // let url = `${SUPABASE_URL}/api/v1/questions/game?count=${count}`;
      
      // Add categories parameter if provided
      if (categories && categories.length > 0) {
        // Convert array to comma-separated string and append to URL
        const categoriesParam = categories.join(',');
        url += `&categories=${encodeURIComponent(categoriesParam)}`;
      }
      
      console.log(`Fetching questions from: ${url}`);
      
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
      
      // Always return mock data for now to avoid disrupting the user experience
      console.warn('Falling back to mock questions due to API error');
      
      // If we have categories, use the first one as filter
      const categoryFilter = categories && categories.length > 0 ? categories[0] : undefined;
      return this.getMockQuestions(count, categoryFilter);
    }
  }
  
  /**
   * Get mock questions for development and testing
   */
  private getMockQuestions(count: number = 10, categoryFilter?: string): Question[] {
    // Extended mock questions database with various categories
    const mockQuestions = [
      // Geography questions
      {
        id: 'geo1',
        content: 'What is the capital city of Australia?',
        category: 'Geography',
        correct_answer: 'Canberra',
        incorrect_answers: ['Sydney', 'Melbourne', 'Perth'],
      },
      {
        id: 'geo2',
        content: 'What is the largest ocean on Earth?',
        category: 'Geography',
        correct_answer: 'Pacific Ocean',
        incorrect_answers: ['Atlantic Ocean', 'Indian Ocean', 'Arctic Ocean'],
      },
      {
        id: 'geo3',
        content: 'Which country is known as the Land of the Rising Sun?',
        category: 'Geography',
        correct_answer: 'Japan',
        incorrect_answers: ['China', 'Thailand', 'South Korea'],
      },
      {
        id: 'geo4',
        content: 'What is the capital of Japan?',
        category: 'Geography',
        correct_answer: 'Tokyo',
        incorrect_answers: ['Kyoto', 'Osaka', 'Hiroshima'],
      },
      {
        id: 'geo5',
        content: 'Which is the tallest mountain in the world?',
        category: 'Geography',
        correct_answer: 'Mount Everest',
        incorrect_answers: ['K2', 'Kangchenjunga', 'Makalu'],
      },
      
      // Science questions
      {
        id: 'sci1',
        content: 'Which planet is known as the Red Planet?',
        category: 'Science',
        correct_answer: 'Mars',
        incorrect_answers: ['Venus', 'Jupiter', 'Saturn'],
      },
      {
        id: 'sci2',
        content: 'Which element has the chemical symbol "O"?',
        category: 'Science',
        correct_answer: 'Oxygen',
        incorrect_answers: ['Gold', 'Osmium', 'Oreganum'],
      },
      {
        id: 'sci3',
        content: 'What is the hardest natural substance on Earth?',
        category: 'Science',
        correct_answer: 'Diamond',
        incorrect_answers: ['Titanium', 'Platinum', 'Graphene'],
      },
      {
        id: 'sci4',
        content: 'What is the chemical symbol for gold?',
        category: 'Science',
        correct_answer: 'Au',
        incorrect_answers: ['Ag', 'Fe', 'Go'],
      },
      {
        id: 'sci5',
        content: 'Which planet has the most moons?',
        category: 'Science',
        correct_answer: 'Saturn',
        incorrect_answers: ['Jupiter', 'Neptune', 'Uranus'],
      },
      
      // History questions
      {
        id: 'hist1',
        content: 'In what year did World War II end?',
        category: 'History',
        correct_answer: '1945',
        incorrect_answers: ['1939', '1944', '1946'],
      },
      {
        id: 'hist2',
        content: 'Who was the first President of the United States?',
        category: 'History',
        correct_answer: 'George Washington',
        incorrect_answers: ['Thomas Jefferson', 'John Adams', 'Abraham Lincoln'],
      },
      {
        id: 'hist3',
        content: 'Which ancient civilization built the Machu Picchu?',
        category: 'History',
        correct_answer: 'Inca',
        incorrect_answers: ['Maya', 'Aztec', 'Egypt'],
      },
      {
        id: 'hist4',
        content: 'What year was the Declaration of Independence signed?',
        category: 'History',
        correct_answer: '1776',
        incorrect_answers: ['1789', '1775', '1781'],
      },
      {
        id: 'hist5',
        content: 'Who painted the Sistine Chapel ceiling?',
        category: 'History',
        correct_answer: 'Michelangelo',
        incorrect_answers: ['Leonardo da Vinci', 'Raphael', 'Donatello'],
      },
      
      // Other categories
      {
        id: 'math1',
        content: 'What is the smallest prime number?',
        category: 'Mathematics',
        correct_answer: '2',
        incorrect_answers: ['0', '1', '3'],
      },
      {
        id: 'lit1',
        content: 'Who wrote "Romeo and Juliet"?',
        category: 'Literature',
        correct_answer: 'William Shakespeare',
        incorrect_answers: ['Charles Dickens', 'Jane Austen', 'Mark Twain'],
      },
      {
        id: 'animal1',
        content: 'Which mammal can fly?',
        category: 'Animals',
        correct_answer: 'Bat',
        incorrect_answers: ['Flying squirrel', 'Sugar glider', 'Colugo'],
      },
      {
        id: 'art1',
        content: 'Who painted the Mona Lisa?',
        category: 'Art',
        correct_answer: 'Leonardo da Vinci',
        incorrect_answers: ['Michelangelo', 'Pablo Picasso', 'Vincent van Gogh'],
      },
      {
        id: 'movies1',
        content: 'Which film won the Academy Award for Best Picture in 2020?',
        category: 'Movies',
        correct_answer: 'Parasite',
        incorrect_answers: ['1917', 'Joker', 'Once Upon a Time in Hollywood'],
      }
    ];
    
    // Filter by category if provided
    let filteredQuestions = mockQuestions;
    if (categoryFilter) {
      // Check if we have the actual category in our mock data
      const exactMatch = mockQuestions.filter(q => q.category.toLowerCase() === categoryFilter.toLowerCase());
      
      if (exactMatch.length > 0) {
        filteredQuestions = exactMatch;
      } else {
        // For demo purposes, just use a random subset if category not found
        console.log(`Category "${categoryFilter}" not found in mock data, using random questions`);
        filteredQuestions = mockQuestions.sort(() => 0.5 - Math.random()).slice(0, Math.min(count, mockQuestions.length));
      }
    }
    
    // If we don't have enough questions after filtering, repeat some
    if (filteredQuestions.length < count) {
      // Repeat the filtered questions until we have enough
      const repeatedQuestions = [];
      for (let i = 0; i < count; i++) {
        repeatedQuestions.push(filteredQuestions[i % filteredQuestions.length]);
      }
      return repeatedQuestions;
    }
    
    // If we have more than enough, return a random subset
    if (filteredQuestions.length > count) {
      return filteredQuestions.sort(() => 0.5 - Math.random()).slice(0, count);
    }
    
    // Return exactly what we have
    return filteredQuestions;
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
      // Option 1: If no SUPABASE_URL, directly return mock data
      if (!SUPABASE_URL || SUPABASE_URL === '') {
        console.warn('SUPABASE_URL not configured, using mock questions data for category:', categoryId);
        return this.getMockQuestions(count, categoryId);
      }
      
      // Option 2: Try direct category endpoint if available
      // Try a more direct category endpoint first
      const url = `${SUPABASE_URL}/api/questions/category/${categoryId}?limit=${count}`;
      console.log(`Trying direct category endpoint: ${url}`);
      
      const response = await fetch(url);
      
      if (response.ok) {
        const data = await response.json();
        console.log(`Successfully fetched ${data.length} questions from category endpoint`);
        
        // If we got data in a different format than expected, transform it
        const transformedData = data.map((item: any) => {
          // Basic validation and transformation if needed
          return {
            id: item.id || `mock-${Math.random()}`,
            content: item.content || item.question || "Question text not available",
            category: item.category || categoryId,
            correct_answer: item.correct_answer || "Answer not available",
            incorrect_answers: Array.isArray(item.incorrect_answers) ? 
              item.incorrect_answers : 
              ["Option 1", "Option 2", "Option 3"]
          };
        });
        
        return transformedData;
      } else {
        console.log(`Category endpoint returned ${response.status}, falling back to general endpoint`);
      }
      
      // If direct category endpoint failed, try the general endpoint with category filter
      return this.getGameQuestions([categoryId], count);
      
    } catch (error) {
      console.error(`Error in getQuestionsByCategory for ${categoryId}:`, error);
      
      // Fall back to mock data for this specific category
      console.warn(`Falling back to mock questions for category: ${categoryId}`);
      return this.getMockQuestions(count, categoryId);
    }
  }

  /**
   * Get a complete question with answer by ID
   * 
   * @param questionId Question ID
   */
  async getQuestionById(questionId: string): Promise<Question | null> {
    try {
      // Check if Supabase client is initialized
      if (!this.supabase) {
        throw new Error('Supabase client not initialized');
      }
      
      // Use REST API approach for consistency
      const response = await fetch(`${SUPABASE_URL}/questions/${questionId}`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching question ${questionId}:`, error);
      return null;
    }
  }
}

// Export as singleton
export default new QuestionService();