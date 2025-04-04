// src/pages/GameplayScreen.tsx
import React, { useState, useEffect, useRef, useMemo } from 'react'; // Added useMemo
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom'; // Added useLocation
import GameHeader from '@/components/GameHeader';
import QuestionCard from '@/components/QuestionCard';
import QuestionTimer from '@/components/QuestionTimer';
// *** MODIFICATION: Import Player and PlayerResult type ***
import { Player, PlayerSelection, PlayerResult } from '@/types/gameTypes';
import { mockQuestions, getPlayerById, getQuestionTextClass, getPirateNameForUserId } from '@/utils/gamePlayUtils'; // Removed mockPlayers import
import { useGameTimer } from '@/hooks/useGameTimer'; // Import timer hook
import { useQuestionManager } from '@/hooks/useQuestionManager'; // Import question manager hook

const GameplayScreen: React.FC = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation(); // Get location state
  const gameId = location.state?.gameId as string | undefined; // Get gameId from state
  const totalQuestionsParam = location.state?.totalQuestions as number | undefined; // Get totalQuestions from state
  const gameCode = searchParams.get('gameCode'); // Check if it's a crew game
  const isSoloMode = !gameCode;

  const defaultTotalQuestions = 10; // Define default centrally if needed
  const totalQuestions = totalQuestionsParam ?? defaultTotalQuestions;

  // --- State Managed by Hooks ---
  const {
    currentQuestion: question, // Renamed for convenience
    currentQuestionIndex,
    isLastQuestion,
    nextQuestion,
    totalQuestionsToPlay // Get the actual number being played
  } = useQuestionManager(mockQuestions, totalQuestions); // Use the question manager hook - using mock questions for now

  // --- Local State for Gameplay Interaction ---
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [score, setScore] = useState(0); // Player's score for this game
  // Removed useState for players - we only need the current user for solo
  const [playerSelections, setPlayerSelections] = useState<PlayerSelection[]>([]);
  // Removed playerScores - only track the single player's score for solo
  const [maxHeight, setMaxHeight] = useState<number | null>(null);
  const answerRefs = useRef<(HTMLDivElement | null)[]>([]);
  const navigate = useNavigate();

  // --- Get Current User Info (for Solo) ---
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [currentUserDisplayName, setCurrentUserDisplayName] = useState<string | null>(null);

  useEffect(() => {
    const storedUserId = localStorage.getItem('tempUserId');
    const storedName = localStorage.getItem('tempUserDisplayName');
    if (storedUserId) {
      setCurrentUserId(storedUserId);
      setCurrentUserDisplayName(storedName || getPirateNameForUserId(storedUserId)); // Fallback name generation
    } else {
      console.error("Gameplay: User ID not found!");
      // Handle error - maybe navigate back
      navigate('/');
    }
  }, [navigate]);


  // --- Timer Hook ---
  // The 'handleSubmit' function will now also act as the onTimeout callback
  const timeRemaining = useGameTimer(
    question?.timeLimit || 10, // Use question's time limit, provide default
    isAnswered,               // Pause when answered
    () => handleSubmit()      // Call handleSubmit on timeout
  );

  // --- Effects ---
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
      // Store the current player's selection
       setPlayerSelections(prev => {
        const newSelections = [...prev];
        // In solo, player ID comes from state; use 'p1' as placeholder if needed, but currentUserId is better
        const playerId = currentUserId || 'p1';
        const existingIndex = newSelections.findIndex(s => s.playerId === playerId);
        if (existingIndex >= 0) newSelections[existingIndex].answerId = answerId;
        else newSelections.push({ playerId: playerId, answerId });
        return newSelections;
      });

      // *** MODIFICATION: Only simulate AI players in crew mode ***
      if (!isSoloMode) {
          // Simulate other players (only relevant for potential future crew mode use here)
          // This logic should ideally move to a crew-specific gameplay component or be fetched
           setTimeout(() => {
            // Placeholder for fetching/simulating other players in crew mode
            console.log("Simulating other players (Crew Mode only)");
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
      // *** MODIFICATION: Change type to PlayerResult[] ***
      let playerResultsArray: PlayerResult[] = [];

      // *** MODIFICATION: Build results array based on mode ***
      if (isSoloMode && currentUserId && currentUserDisplayName !== null) {
        // Solo Mode: Use current user's data
        playerResultsArray = [{
          id: currentUserId,
          name: currentUserDisplayName, // Use the display name from state
          score: score // Use the final score from state - This is now valid
        }];
      } else {
        // Crew Mode: This part needs proper implementation if used
        // You would fetch final participant scores from the backend or use websocket data
        // For now, it might use outdated/mock data if called in crew mode context
        console.warn("Crew mode results calculation not fully implemented in this component.");
        // Placeholder using current state (might be incorrect for crew)
        if (currentUserId && currentUserDisplayName !== null) {
            // Ensure this object also matches PlayerResult
            playerResultsArray = [{ id: currentUserId, name: currentUserDisplayName, score: score }];
        }
      }

      console.log("Navigating to Results with:", playerResultsArray); // Debug log
      // Pass gameCode only if it exists (i.e., crew mode)
      const resultsPath = gameCode ? `/results?gameCode=${gameCode}` : '/results';
      navigate(resultsPath, { state: { results: playerResultsArray } });
    }
  };

  // Handles both submit button click and timer timeout
  const handleSubmit = () => {
    if (isAnswered || !question || !currentUserId) return; // Prevent double submission or running without a question

    setIsAnswered(true); // Mark as answered FIRST
    const isAnswerCorrect = selectedAnswer === question.correctAnswer;
    setIsCorrect(isAnswerCorrect);

    // Update score for the current player (solo)
    if (isAnswerCorrect) {
      setScore(prev => prev + 1);
    }

    // No AI player score updates needed for solo mode

    // Wait 3 seconds before advancing
    setTimeout(() => {
      advanceGame();
    }, 3000);
  };

  // --- Derived Data ---
  // Group player selections by answer (Only needed visually for crew mode)
  const playerSelectionsByAnswer = useMemo(() => {
      if (isSoloMode || !question) return {}; // Don't calculate for solo

      // Placeholder: In crew mode, this needs real data fetched from backend/websockets
      const selections: Record<string, Player[]> = {}; // Using Player type here is fine for display
       // Example structure if you had `crewMembers` state:
       // question.answers.forEach(answer => {
       //   selections[answer.id] = crewMembers.filter(m => playerSelections.find(ps => ps.playerId === m.id && ps.answerId === answer.id));
       // });
      return selections;
  }, [isSoloMode, question, playerSelections /*, crewMembers */ ]); // Add crewMembers if implemented


  // Determine question text class (requires question to exist)
  const questionTextClass = question ? getQuestionTextClass(question.text) : 'text-2xl md:text-3xl'; // Default class

  // --- Render ---
  // Handle loading state or end of questions more gracefully
  if (!question || !currentUserId) {
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
            // *** MODIFICATION: Pass empty object for solo selections ***
            playerSelectionsByAnswer={isSoloMode ? {} : playerSelectionsByAnswer}
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

      {/* Styles remain the same */}
      <style>
        {`
        @keyframes shake { /* Keep shake animation */ 0%, 100% { transform: translateX(0); } 10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); } 20%, 40%, 60%, 80% { transform: translateX(5px); } }
        .animate-shake { /* Keep shake animation */ animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }
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