// website/src/pages/GameplayScreen.tsx
// --- START OF FULL MODIFIED FILE ---
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import GameHeader from '@/components/GameHeader';
import QuestionCard from '@/components/QuestionCard';
import QuestionTimer from '@/components/QuestionTimer';
import { Player, PlayerSelection, PlayerResult, Question, Answer } from '@/types/gameTypes';
import { getGamePlayQuestions } from '@/services/gameApi';
import { getPlayerById, getQuestionTextClass, getPirateNameForUserId } from '@/utils/gamePlayUtils';
import { useGameTimer } from '@/hooks/useGameTimer';
import { useQuestionManager } from '@/hooks/useQuestionManager';
import { toast } from 'sonner';
import { Loader2, AlertTriangle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import PirateButton from '@/components/PirateButton'; // Import PirateButton for error state

const GameplayScreen: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // --- Get Data from Navigation State ---
  const gameId = location.state?.gameId as string | undefined;
  const packId = location.state?.packId as string | undefined; // Keep packId if needed elsewhere
  const packName = location.state?.packName as string | undefined; // <-- Get packName
  const totalQuestionsSetting = location.state?.totalQuestions as number | undefined;
  const gameCode = searchParams.get('gameCode');
  const isSoloMode = !gameCode;

  // --- State for Fetched Questions and Loading/Error ---
  const [gameQuestions, setGameQuestions] = useState<Question[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const [questionFetchError, setQuestionFetchError] = useState<string | null>(null);
  const [fetchedCorrectAnswers, setFetchedCorrectAnswers] = useState<Record<string, string>>({}); // Store correct answers by question ID

  // --- Fetch Game Questions ---
  useEffect(() => {
     // Check for gameId and packName now
     if (!gameId || !packName) {
       console.error("GameplayScreen: Missing gameId or packName in location state!", location.state);
       toast.error("Game Error", { description: "Missing game/pack information. Returning home." });
       navigate('/');
       return;
     }

    const fetchQuestions = async () => {
      setIsLoadingQuestions(true);
      setQuestionFetchError(null);
      console.log(`Fetching questions for game ID: ${gameId}`);
      try {
        const response = await getGamePlayQuestions(gameId);
        console.log("API response for questions:", response);

        // --- **CORRECTNESS FIX**: Need original answers *before* formatting ---
        // We need the backend to tell us the correct answer text explicitly,
        // as we cannot reliably deduce it after shuffling on the frontend.
        //
        // **ASSUMPTION FOR NOW:** Backend MUST return the correct answer text
        // alongside the question data or options (e.g., in a separate field).
        // Let's assume `ApiGamePlayQuestion` now has an optional `correct_answer_text` field.
        // If not, this correctness logic will fail.

        const correctAnswersMap: Record<string, string> = {}; // question_id -> correct_answer_text
        // Populate this map if the backend provides the correct answer text.
        // Example (assuming backend adds 'correct_answer_text'):
        // response.questions.forEach(apiQ => {
        //   if (apiQ.correct_answer_text) {
        //      correctAnswersMap[apiQ.question_id] = apiQ.correct_answer_text;
        //   }
        // });
        // setFetchedCorrectAnswers(correctAnswersMap); // Store for later use

        // Map API response to frontend Question type
        const formattedQuestions: Question[] = response.questions.map((apiQ): Question => {
            // Find the ID corresponding to the correct answer text *before* shuffling
            // This is still problematic if backend doesn't provide correct answer text
            const correctAnswerText = fetchedCorrectAnswers[apiQ.question_id] || ""; // Get correct text if available
            let correctAnswerId = "";

            const answersWithOptions: Answer[] = apiQ.options.map((optionText, optionIndex): Answer => {
                const answerId = `${apiQ.question_id}-${optionIndex}`;
                // Check if this option is the correct one
                // This comparison is flawed without backend confirmation
                if (optionText === correctAnswerText) {
                   correctAnswerId = answerId;
                }
                return {
                    id: answerId,
                    text: optionText,
                    letter: String.fromCharCode(65 + optionIndex), // A, B, C, D...
                };
            });

            // If we couldn't identify the correct answer ID, log a warning
            if (!correctAnswerId && correctAnswerText) {
                console.warn(`Could not find ID for correct answer text "${correctAnswerText}" in options for question ${apiQ.question_id}`);
            }

            return {
                id: apiQ.question_id,
                text: apiQ.question_text,
                category: packId || 'Trivia', // Keep packId here if the type expects it, or update type
                answers: answersWithOptions, // Use the mapped answers
                correctAnswer: correctAnswerId, // Use the ID found above (might be empty)
                timeLimit: apiQ.time_limit,
            };
        });

        console.log("Formatted questions:", formattedQuestions);
        setGameQuestions(formattedQuestions);

      } catch (error) {
        console.error("Failed to fetch game questions:", error);
        const errorMsg = error instanceof Error ? error.message : "Could not load questions.";
        setQuestionFetchError(errorMsg);
        toast.error("Failed to Load Questions", { description: errorMsg });
      } finally {
        setIsLoadingQuestions(false);
      }
    };

    fetchQuestions();
  // <-- Add packName dependency
  }, [gameId, navigate, packId, packName]);

  // --- State Managed by Hooks ---
  const {
    currentQuestion: question,
    currentQuestionIndex,
    isLastQuestion,
    nextQuestion,
    totalQuestionsToPlay
  } = useQuestionManager(gameQuestions, totalQuestionsSetting ?? gameQuestions.length);

  // --- Local State ---
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [score, setScore] = useState(0);
  const [playerSelections, setPlayerSelections] = useState<PlayerSelection[]>([]);
  const [maxHeight, setMaxHeight] = useState<number | null>(null);
  const answerRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [currentUserDisplayName, setCurrentUserDisplayName] = useState<string | null>(null);

  // --- User Info Effect ---
  useEffect(() => {
    const storedUserId = localStorage.getItem('tempUserId');
    const storedName = localStorage.getItem('tempUserDisplayName');
    if (storedUserId) {
      setCurrentUserId(storedUserId);
      setCurrentUserDisplayName(storedName || getPirateNameForUserId(storedUserId));
    } else {
      console.error("Gameplay: User ID not found!");
      toast.error("Session Error", { description: "User ID missing. Please restart." });
      navigate('/');
    }
  }, [navigate]);

  // --- Timer Hook & Submit Logic ---
  const handleSubmit = useCallback(() => {
    if (isAnswered || !question || !currentUserId) return;

    setIsAnswered(true);
    // --- **CORRECTNESS FIX**: Compare selected ID with the identified correct ID ---
    const isAnswerCorrect = selectedAnswer === question.correctAnswer;
    setIsCorrect(isAnswerCorrect);
    console.log(`Selected ID: ${selectedAnswer}, Correct ID: ${question.correctAnswer}, Is Correct: ${isAnswerCorrect}`);

    if (isAnswerCorrect) {
      setScore(prev => prev + 1); // Basic scoring
    }

    setTimeout(() => {
      if (!isLastQuestion) {
        nextQuestion();
      } else {
        let playerResultsArray: PlayerResult[] = [];
        if (isSoloMode && currentUserId && currentUserDisplayName !== null) {
          playerResultsArray = [{ id: currentUserId, name: currentUserDisplayName, score: score }];
        } else {
          console.warn("Crew mode results calculation needed.");
          if (currentUserId && currentUserDisplayName !== null) {
            playerResultsArray = [{ id: currentUserId, name: currentUserDisplayName, score: score }];
          }
        }
        const resultsPath = gameCode ? `/results?gameCode=${gameCode}` : '/results';
        navigate(resultsPath, { state: { results: playerResultsArray } });
      }
    }, 3000);
  }, [isAnswered, question, currentUserId, isLastQuestion, nextQuestion, isSoloMode, currentUserDisplayName, score, gameCode, navigate, selectedAnswer]);

  const timeRemaining = useGameTimer(
    question?.timeLimit || 30,
    isAnswered,
    handleSubmit
  );

  // --- Effects ---
  useEffect(() => {
    if (question) {
      setSelectedAnswer(null);
      setIsAnswered(false);
      setIsCorrect(false);
      setPlayerSelections([]);
      setMaxHeight(null);
      answerRefs.current = [];
    }
  }, [question]);

  useEffect(() => {
    if (!question || !question.answers) return;

    // Ensure refs array is ready for the current number of answers
    answerRefs.current = answerRefs.current.slice(0, question.answers.length);

    const timer = setTimeout(() => {
        if (answerRefs.current.length === question.answers.length) {
            let highest = 0;
            answerRefs.current.forEach(ref => {
                if (ref && ref.offsetHeight > highest) {
                    highest = ref.offsetHeight;
                }
            });
            if (highest > 0) {
                setMaxHeight(highest);
            } else {
                console.warn("Could not determine answer height after delay.");
            }
        }
    }, 150);

    return () => clearTimeout(timer);
  }, [question]);

  // --- Event Handlers ---
  const handleAnswerSelect = (answerId: string) => {
    if (!isAnswered) {
      setSelectedAnswer(answerId);
      if (currentUserId) {
        setPlayerSelections([{ playerId: currentUserId, answerId }]);
      }
    }
  };

  // --- Derived Data ---
  const playerSelectionsByAnswer = useMemo(() => {
      if (isSoloMode || !question) return {};
      const selections: Record<string, Player[]> = {};
      return selections;
  }, [isSoloMode, question, playerSelections]);

  const questionTextClass = question ? getQuestionTextClass(question.text) : 'text-2xl md:text-3xl';

  // --- Render ---
  if (isLoadingQuestions) {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center">
            <Loader2 className="h-12 w-12 animate-spin text-pirate-navy mb-4" />
            <p className="text-pirate-navy/80">Loading Questions...</p>
        </div>
    );
  }

  if (questionFetchError) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <Card className="p-6 text-center border-destructive bg-destructive/10">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-destructive mb-2">Error Loading Game</h2>
            <p className="text-destructive/80 mb-4">{questionFetchError}</p>
            <PirateButton onClick={() => navigate('/')} variant="secondary">
                Return Home
            </PirateButton>
        </Card>
      </div>
    );
  }

  if (!question || !currentUserId || !packName) { // <-- Add packName check
    // Check if fetching finished but yielded no questions
    if (!isLoadingQuestions && gameQuestions.length === 0) {
      return (
         <div className="min-h-screen flex flex-col items-center justify-center p-4">
           <Card className="p-6 text-center border-pirate-navy/20 bg-pirate-parchment">
               <AlertTriangle className="h-12 w-12 text-pirate-navy/50 mx-auto mb-4" />
               <h2 className="text-xl font-semibold text-pirate-navy mb-2">No Questions Found</h2>
               <p className="text-pirate-navy/80 mb-4">
                 There seem to be no questions available for this game session.
               </p>
               <PirateButton onClick={() => navigate('/')} variant="secondary">
                   Return Home
               </PirateButton>
           </Card>
         </div>
       );
    }
    // Otherwise, it might be an intermediate state or an unexpected issue
    console.log("GameplayScreen: No current question, user ID, or packName available. Current index:", currentQuestionIndex, "Total fetched:", gameQuestions.length);
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  // --- Main Gameplay Render ---
  return (
    <div className="min-h-screen flex flex-col">
      <GameHeader />

      <main className="flex-1 container mx-auto px-4 py-6 flex flex-col">
        <div className="text-center mb-2">
          {/* --- USE packName directly --- */}
          <h2 className="font-pirate text-3xl text-pirate-navy capitalize">
             {packName.replace(/-/g, ' ')} {/* <-- Display packName */}
          </h2>
          <p className="text-pirate-navy/80 font-medium">Question {currentQuestionIndex + 1} of {totalQuestionsToPlay}</p>
        </div>

        <QuestionTimer
          timeRemaining={timeRemaining}
          totalTime={question.timeLimit}
        />

        <div className="map-container p-0 mb-6 flex-1 flex">
          <QuestionCard
            questionText={question.text} // This remains correct
            answers={question.answers}
            selectedAnswer={selectedAnswer}
            isAnswered={isAnswered}
            correctAnswer={question.correctAnswer} // Pass the identified correct answer ID
            onAnswerSelect={handleAnswerSelect}
            playerSelectionsByAnswer={playerSelectionsByAnswer}
            maxHeight={maxHeight}
            questionTextClass={questionTextClass}
            answerRefs={answerRefs}
            answerButtonProps={{
              onSubmit: handleSubmit,
              disabled: !selectedAnswer && !isAnswered,
              isAnswered: isAnswered,
              isCorrect: isCorrect, // Pass correctness state
            }}
          />
        </div>
      </main>

      <style>
        {`
        @keyframes shake { 0%, 100% { transform: translateX(0); } 10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); } 20%, 40%, 60%, 80% { transform: translateX(5px); } }
        .animate-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }
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
// --- END OF FULL MODIFIED FILE ---