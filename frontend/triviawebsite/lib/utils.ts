// Define types that match our database schema
export interface Pack {
    id: string;
    name: string;
    description?: string;
    price?: number;
    creator_type?: string;
    created_at?: string;
  }
  
  export interface Question {
    id: string;
    question: string;
    answer: string;
    pack_id: string;
    difficulty_initial?: string;
    difficulty_current?: string;
    created_at?: string;
  }
  
  export interface IncorrectAnswers {
    id: string;
    question_id: string;
    incorrect_answers: string[];
  }
  
  // Type for a complete question with all answer options
  export interface QuestionWithOptions {
    id: string;
    question: string;
    options: string[];
    correctAnswerIndex: number;
  }
  
  // Shuffle an array using Fisher-Yates algorithm
  export function shuffleArray<T>(array: T[]): T[] {
    const newArray = [...array];
    for (let i = newArray.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
    }
    return newArray;
  }
  
  // Prepare a question with shuffled answer options
  export function prepareQuestion(
    question: Question,
    incorrectAnswers: string[]
  ): QuestionWithOptions {
    // Combine correct and incorrect answers
    const allOptions = [question.answer, ...incorrectAnswers];
    
    // Shuffle options
    const shuffledOptions = shuffleArray(allOptions);
    
    // Find the index of the correct answer in the shuffled array
    const correctAnswerIndex = shuffledOptions.indexOf(question.answer);
    
    return {
      id: question.id,
      question: question.question,
      options: shuffledOptions,
      correctAnswerIndex
    };
  }