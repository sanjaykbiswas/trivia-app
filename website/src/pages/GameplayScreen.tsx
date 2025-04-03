// src/pages/GameplayScreen.tsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import GameHeader from '@/components/GameHeader';
import QuestionCard from '@/components/QuestionCard';
import QuestionTimer from '@/components/QuestionTimer';
import { Player, PlayerSelection } from '@/types/gameTypes'; // Question type not needed directly
import { mockQuestions, mockPlayers, getPlayerById, getQuestionTextClass } from '@/utils/gamePlayUtils';
import { useGameTimer } from '@/hooks/useGameTimer'; // Import timer hook
import { useQuestionManager } from '@/hooks/useQuestionManager'; // Import question manager hook

const GameplayScreen: React.FC = () => {
  const [searchParams] = useSearchParams();
  const totalQuestionsParam = searchParams.get('questions');
  const defaultTotalQuestions = 10; // Define default centrally if needed
  const totalQuestions = totalQuestionsParam ? parseInt(totalQuestionsParam) : defaultTotalQuestions;

  // --- State Managed by Hooks ---
  const {
    currentQuestion: question, // Renamed for convenience
    currentQuestionIndex,
    isLastQuestion,
    nextQuestion,
    totalQuestionsToPlay // Get the actual number being played
  } = useQuestionManager(mockQuestions, totalQuestions); // Use the question manager hook

  // --- Local State for Gameplay Interaction ---
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [score, setScore] = useState(0); // Overall score (if needed for display during game)
  const [players] = useState<Player[]>(mockPlayers);
  const [playerSelections, setPlayerSelections] = useState<PlayerSelection[]>([]);
  const [playerScores, setPlayerScores] = useState<Record<string, number>>({});
  const [maxHeight, setMaxHeight] = useState<number | null>(null);
  const answerRefs = useRef<(HTMLDivElement | null)[]>([]);
  const navigate = useNavigate();

  // --- Timer Hook ---
  // The 'handleSubmit' function will now also act as the onTimeout callback
  const timeRemaining = useGameTimer(
    question?.timeLimit || 10, // Use question's time limit, provide default
    isAnswered,               // Pause when answered
    () => handleSubmit()      // Call handleSubmit on timeout
  );

  // --- Effects ---
  // Initialize player scores
  useEffect(() => {
    const initialScores: Record<string, number> = {};
    players.forEach(player => { initialScores[player.id] = 0; });
    setPlayerScores(initialScores);
  }, [players]); // Run only when players array potentially changes (likely only once)

  // Reset state for new question (triggered by `question` changing via hook)
  useEffect(() => {
    if (question) {
      setSelectedAnswer(null);
      setIsAnswered(false);
      setIsCorrect(false); // Reset correctness indicator
      setPlayerSelections([]); // Reset selections for the new question
      // Height calculation reset is now handled within its own effect
    }
  }, [question]); // Depend on the question object from the hook

  // Calculate equal heights for answer boxes
  useEffect(() => {
      if (!question) return; // Don't run if there's no question

    setMaxHeight(null);
    answerRefs.current = answerRefs.current.slice(0, question.answers.length);

    const timer = setTimeout(() => {
      // Check refs array length against the *current* question's answers
      if (answerRefs.current.length === question.answers.length) {
        let highest = 0;
        answerRefs.current.forEach(ref => {
          if (ref && ref.offsetHeight > highest) {
            highest = ref.offsetHeight;
          }
        });
        if (highest > 0) {
          setMaxHeight(highest);
        }
      }
    }, 100);

    return () => clearTimeout(timer);
  }, [question?.answers]); // Depend specifically on the answers array of the current question


  // --- Event Handlers ---
  const handleAnswerSelect = (answerId: string) => {
    if (!isAnswered) {
      setSelectedAnswer(answerId);
      // Simulate player selection (same as before)
       setPlayerSelections(prev => {
        const newSelections = [...prev];
        const existingIndex = newSelections.findIndex(s => s.playerId === 'p1');
        if (existingIndex >= 0) newSelections[existingIndex].answerId = answerId;
        else newSelections.push({ playerId: 'p1', answerId });
        return newSelections;
      });
      // Simulate other players (same as before)
      if (playerSelections.filter(p => p.playerId !== 'p1').length === 0) {
         setTimeout(() => {
          const otherPlayers = players.filter(p => p.id !== 'p1');
          const otherSelections = otherPlayers.map(player => ({
            playerId: player.id,
            answerId: question!.answers[Math.floor(Math.random() * question!.answers.length)].id // Use question! assertion
          }));
          setPlayerSelections(prev => {
             const currentOtherIds = new Set(prev.filter(s => s.playerId !== 'p1').map(s => s.playerId));
             const newOtherSelections = otherSelections.filter(s => !currentOtherIds.has(s.playerId));
             return [...prev, ...newOtherSelections];
           });
        }, Math.random() * 1000 + 500);
      }
    }
  };

  // Function to handle moving to next question OR ending game
  const advanceGame = () => {
    if (!isLastQuestion) {
      nextQuestion(); // Use the function from the hook
    } else {
      // End the game - navigate to results
      const playerResultsArray = players.map(player => ({
        ...player,
        score: playerScores[player.id] || 0
      }));
      navigate('/results', { state: { results: playerResultsArray } });
    }
  };

  // Handles both submit button click and timer timeout
  const handleSubmit = () => {
    if (isAnswered || !question) return; // Prevent double submission or running without a question

    setIsAnswered(true); // Mark as answered FIRST
    const isAnswerCorrect = selectedAnswer === question.correctAnswer;
    setIsCorrect(isAnswerCorrect);

    // Update score for the current player (p1)
    if (isAnswerCorrect) {
      setScore(prev => prev + 1); // Optional: Update local score if needed during gameplay
      setPlayerScores(prev => ({ ...prev, 'p1': (prev['p1'] || 0) + 1 }));
    }

    // Update AI player scores (run this regardless of player 1's answer)
    playerSelections.forEach(selection => {
      if (selection.playerId !== 'p1') {
        const isCorrectSelection = selection.answerId === question.correctAnswer;
        if (isCorrectSelection) {
          setPlayerScores(prev => ({ ...prev, [selection.playerId]: (prev[selection.playerId] || 0) + 1 }));
        }
      }
    });

    // Wait 3 seconds before advancing
    setTimeout(() => {
      advanceGame();
    }, 3000);
  };

  // --- Derived Data ---
  // Group player selections by answer (requires question to exist)
  const playerSelectionsByAnswer = question ? question.answers.reduce<Record<string, Player[]>>((acc, answer) => {
    acc[answer.id] = playerSelections
      .filter(selection => selection.answerId === answer.id)
      .map(selection => {
        const player = getPlayerById(players, selection.playerId);
        return player ? player : { id: selection.playerId, name: `Player ${selection.playerId.substring(0, 4)}`, avatar: '👤' };
      });
    return acc;
  }, {}) : {};

  // Determine question text class (requires question to exist)
  const questionTextClass = question ? getQuestionTextClass(question.text) : 'text-2xl md:text-3xl'; // Default class

  // --- Render ---
  // Handle loading state or end of questions more gracefully
  if (!question) {
     // Could show a loading spinner or a "Game Over" message before navigation
    return <div className="min-h-screen flex items-center justify-center">Loading question...</div>;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <GameHeader />

      <main className="flex-1 container mx-auto px-4 py-6 flex flex-col">
        <div className="text-center mb-2">
          <h2 className="font-pirate text-3xl text-pirate-navy">
            {question.category}
          </h2>
          {/* Use state from hook for question count */}
          <p className="text-pirate-navy/80 font-medium">Question {currentQuestionIndex + 1} of {totalQuestionsToPlay}</p>
        </div>

        {/* Use timeRemaining from hook */}
        <QuestionTimer
          timeRemaining={timeRemaining}
          totalTime={question.timeLimit}
        />

        <div className="map-container p-0 mb-6 flex-1 flex">
          <QuestionCard
            questionText={question.text}
            answers={question.answers}
            selectedAnswer={selectedAnswer}
            isAnswered={isAnswered}
            correctAnswer={question.correctAnswer}
            onAnswerSelect={handleAnswerSelect}
            playerSelectionsByAnswer={playerSelectionsByAnswer}
            maxHeight={maxHeight}
            questionTextClass={questionTextClass}
            answerRefs={answerRefs}
            answerButtonProps={{
              onSubmit: handleSubmit, // Submit handler remains the same
              disabled: !selectedAnswer && !isAnswered, // Disable logic remains
              isAnswered: isAnswered,
              isCorrect: isCorrect,
            }}
          />
        </div>
      </main>

      <style>
        {`
        @keyframes shake { /* Keep shake animation */ }
        .animate-shake { /* Keep shake animation */ }
        `}
      </style>

      <footer className="ocean-bg py-8">
        <div className="container mx-auto text-center text-white relative z-10">
          <p className="font-pirate text-xl mb-2">Answer wisely, matey!</p>
          <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
};

export default GameplayScreen;