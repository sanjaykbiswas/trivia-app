'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Typography from '../../components/ui/Typography';
import Button from '../../components/ui/Button';
import AnswerOption from '../../components/game/AnswerOption';
import FeedbackPanel from '../../components/game/FeedbackPanel';
import { QuestionWithOptions } from '../../../lib/utils';

export default function GamePage({ params }: { params: { packId: string } }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const packName = searchParams.get('name') || 'Trivia Pack';
  
  // Game states
  const [questions, setQuestions] = useState<QuestionWithOptions[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswerIndex, setSelectedAnswerIndex] = useState<number | null>(null);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [isCorrectAnswer, setIsCorrectAnswer] = useState(false);
  const [score, setScore] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Current question helper
  const currentQuestion = questions[currentQuestionIndex];
  
  // Fetch questions when component mounts
  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/questions/${params.packId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch questions: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.questions || data.questions.length === 0) {
          throw new Error('No questions available for this pack');
        }
        
        setQuestions(data.questions);
      } catch (err) {
        console.error('Error fetching questions:', err);
        setError('Failed to load questions. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchQuestions();
  }, [params.packId]);
  
  // Handle option selection
  const handleSelectOption = (index: number) => {
    if (isAnswerSubmitted) return;
    setSelectedAnswerIndex(index);
  };
  
  // Submit answer
  const handleSubmitAnswer = () => {
    if (isAnswerSubmitted) {
      // If already submitted, proceed to next question
      handleNextQuestion();
      return;
    }
    
    setIsAnswerSubmitted(true);
    
    // Check if answer is correct
    const isCorrect = selectedAnswerIndex === currentQuestion.correctAnswerIndex;
    setIsCorrectAnswer(isCorrect);
    
    // Update score if correct
    if (isCorrect) {
      setScore(prevScore => prevScore + 1);
    }
  };
  
  // Proceed to next question
  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      // Move to next question
      setCurrentQuestionIndex(prevIndex => prevIndex + 1);
      setSelectedAnswerIndex(null);
      setIsAnswerSubmitted(false);
    } else {
      // End of quiz - return to home with score
      router.push(`/?score=${score}&total=${questions.length}`);
    }
  };
  
  // Handle back button click
  const handleBackClick = () => {
    if (confirm('Are you sure you want to quit this game?')) {
      router.push('/solo');
    }
  };

  return (
    <div className="min-h-screen p-6 pb-24 relative">
      {/* Header with back button and pack name */}
      <div className="flex items-center mb-6">
        <button 
          className="w-10 h-10 rounded-full bg-background-light flex justify-center items-center mr-4"
          onClick={handleBackClick}
        >
          <Typography variant="bodyMedium">←</Typography>
        </button>
        <Typography variant="bodyMedium" className="font-medium">
          {packName}
        </Typography>
      </div>
      
      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-12 h-12 border-4 border-primary-main border-t-transparent rounded-full animate-spin mb-4"></div>
          <Typography variant="bodyMedium">Loading questions...</Typography>
        </div>
      )}
      
      {/* Error state */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <Typography 
            variant="bodyLarge" 
            color="text-error-main"
            className="mb-4 text-center"
          >
            {error}
          </Typography>
          <Button
            title="Back to Packs"
            onClick={() => router.push('/solo')}
            variant="contained"
            size="medium"
          />
        </div>
      )}
      
      {/* Question content */}
      {!loading && !error && currentQuestion && (
        <div>
          {/* Question progress */}
          <Typography 
            variant="bodyMedium" 
            color="text-text-secondary"
            className="mb-1"
          >
            Question {currentQuestionIndex + 1} of {questions.length}
          </Typography>
          
          {/* Question text */}
          <Typography 
            variant="heading2" 
            className="mb-8 leading-tight"
          >
            {currentQuestion.question}
          </Typography>
          
          {/* Answer options */}
          <div className="mb-6">
            {currentQuestion.options.map((option, index) => (
              <AnswerOption
                key={index}
                letter={String.fromCharCode(65 + index)} // A, B, C, D
                text={option}
                isSelected={selectedAnswerIndex === index}
                isCorrect={isAnswerSubmitted && index === currentQuestion.correctAnswerIndex}
                isIncorrect={isAnswerSubmitted && selectedAnswerIndex === index && index !== currentQuestion.correctAnswerIndex}
                onClick={() => handleSelectOption(index)}
                disabled={isAnswerSubmitted}
              />
            ))}
          </div>
          
          {/* Submit/Next button */}
          <Button
            title={isAnswerSubmitted ? (currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'Finish Quiz') : 'Submit Answer'}
            onClick={handleSubmitAnswer}
            disabled={selectedAnswerIndex === null && !isAnswerSubmitted}
            variant="contained"
            size="large"
            fullWidth
          />
          
          {/* Feedback panel */}
          {isAnswerSubmitted && (
            <FeedbackPanel
              isCorrect={isCorrectAnswer}
              correctAnswer={currentQuestion.options[currentQuestion.correctAnswerIndex]}
              onNextPress={handleNextQuestion}
              isLastQuestion={currentQuestionIndex === questions.length - 1}
            />
          )}
        </div>
      )}
    </div>
  );
}