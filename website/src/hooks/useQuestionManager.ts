// src/hooks/useQuestionManager.ts
import { useState, useMemo, useCallback } from 'react';
import { Question } from '@/types/gameTypes';

interface UseQuestionManagerReturn {
  currentQuestion: Question | null;
  currentQuestionIndex: number;
  isLastQuestion: boolean;
  nextQuestion: () => void; // Advances to the next question
  totalQuestionsToPlay: number;
}

/**
 * Custom hook to manage the flow of questions in the game.
 * @param allQuestions Array of all available questions.
 * @param totalQuestions Desired number of questions for this game session.
 * @returns An object containing the current question, index, navigation function, etc.
 */
export const useQuestionManager = (
  allQuestions: Question[],
  totalQuestions: number
): UseQuestionManagerReturn => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);

  // Determine the actual number of questions to play (don't exceed available)
  const totalQuestionsToPlay = useMemo(() =>
      Math.min(allQuestions.length, totalQuestions),
    [allQuestions.length, totalQuestions]
  );

  // Get the current question object based on the index
  const currentQuestion = useMemo(() =>
      (currentQuestionIndex < totalQuestionsToPlay) ? allQuestions[currentQuestionIndex] : null,
    [allQuestions, currentQuestionIndex, totalQuestionsToPlay]
  );

  // Check if the current question is the last one for this game session
  const isLastQuestion = useMemo(() =>
      currentQuestionIndex >= totalQuestionsToPlay - 1,
    [currentQuestionIndex, totalQuestionsToPlay]
  );

  // Function to advance to the next question
  const nextQuestion = useCallback(() => {
    if (!isLastQuestion) {
      setCurrentQuestionIndex(prevIndex => prevIndex + 1);
    }
    // If it is the last question, calling this does nothing further.
    // The calling component should handle game end logic based on `isLastQuestion`.
  }, [isLastQuestion]); // Dependency: only needs to know if it *can* advance

  return {
    currentQuestion,
    currentQuestionIndex,
    isLastQuestion,
    nextQuestion,
    totalQuestionsToPlay // Expose the calculated number of questions
  };
};