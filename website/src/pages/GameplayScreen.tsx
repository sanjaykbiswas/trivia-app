// website/src/pages/GameplayScreen.tsx
// --- START OF FULL FILE WITH MODIFIED HOOK CALL ---
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import GameHeader from '@/components/GameHeader';
import QuestionCard from '@/components/QuestionCard';
import QuestionTimer from '@/components/QuestionTimer'; // Import the timer component
import { Player, PlayerSelection, PlayerResult, Question, Answer } from '@/types/gameTypes';
import { getGamePlayQuestions } from '@/services/gameApi';
import { getPlayerById, getQuestionTextClass, getPirateNameForUserId } from '@/utils/gamePlayUtils';
import { useGameTimer } from '@/hooks/useGameTimer'; // Import the updated hook
import { useQuestionManager } from '@/hooks/useQuestionManager';
import { toast } from 'sonner';
import { Loader2, AlertTriangle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import PirateButton from '@/components/PirateButton';

const GameplayScreen: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // --- Get Data from Navigation State ---
  const gameId = location.state?.gameId as string | undefined;
  const packId = location.state?.packId as string | undefined;
  const packName = location.state?.packName as string | undefined;
  const totalQuestionsSetting = location.state?.totalQuestions as number | undefined;
  const gameCode = searchParams.get('gameCode');
  const isSoloMode = !gameCode;

  // --- State for Fetched Questions and Loading/Error ---
  const [gameQuestions, setGameQuestions] = useState<Question[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const [questionFetchError, setQuestionFetchError] = useState<string | null>(null);
  const [fetchedCorrectAnswers, setFetchedCorrectAnswers] = useState<Record<string, string>>({});

  // --- Fetch Game Questions ---
  useEffect(() => {
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

        // Assume backend might provide correct answer text - adjust if needed
        const correctAnswersMap: Record<string, string> = {};
        // Populate correctAnswersMap if applicable

        const formattedQuestions: Question[] = response.questions.map((apiQ): Question => {
            const correctAnswerText = correctAnswersMap[apiQ.question_id] || "";
            let correctAnswerId = "";
            const answersWithOptions: Answer[] = apiQ.options.map((optionText, optionIndex): Answer => {
                const answerId = `${apiQ.question_id}-${optionIndex}`;
                if (optionText === correctAnswerText) {
                   correctAnswerId = answerId;
                }
                return { id: answerId, text: optionText, letter: String.fromCharCode(65 + optionIndex) };
            });
            if (!correctAnswerId && correctAnswerText) {
                console.warn(`Could not find ID for correct answer text "${correctAnswerText}" in options for question ${apiQ.question_id}`);
            }
            return {
                id: apiQ.question_id,
                text: apiQ.question_text,
                category: packId || 'Trivia',
                answers: answersWithOptions,
                correctAnswer: correctAnswerId, // Relies on accurate mapping above
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
  }, [gameId, navigate, packId, packName, location.state]);

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
    // Ensure we don't submit multiple times for the same question
    if (isAnswered || !question || !currentUserId) {
        console.log("Submit prevented: Already answered, no question, or no user ID.");
        return;
    }
    console.log(`Submitting answer for question ID: ${question.id}, Index: ${currentQuestionIndex}`);

    setIsAnswered(true); // Mark as answered immediately to pause timer and disable interactions
    const isAnswerCorrect = selectedAnswer === question.correctAnswer;
    setIsCorrect(isAnswerCorrect);
    console.log(`Selected ID: ${selectedAnswer}, Correct ID: ${question.correctAnswer}, Is Correct: ${isAnswerCorrect}`);

    if (isAnswerCorrect) {
      setScore(prev => prev + 1); // Basic scoring
    }

    // Delay before moving on
    setTimeout(() => {
        console.log(`Timeout finished for question Index: ${currentQuestionIndex}. Is last: ${isLastQuestion}`);
      if (!isLastQuestion) {
        console.log("Moving to next question...");
        nextQuestion(); // Call the function from the hook to advance the index
      } else {
        console.log("Last question answered. Navigating to results...");
        // Prepare results data
        let playerResultsArray: PlayerResult[] = [];
        if (currentUserId && currentUserDisplayName !== null) {
          playerResultsArray = [{ id: currentUserId, name: currentUserDisplayName, score: score }];
        } else {
           console.warn("Solo/Crew mode ended but couldn't find user details for results.");
        }
        if (!isSoloMode) {
           console.warn("Crew mode results calculation/fetching needed here.");
        }

        const resultsPath = gameCode ? `/results?gameCode=${gameCode}` : '/results';
        navigate(resultsPath, { state: { results: playerResultsArray } });
      }
    }, 3000); // 3-second delay
  }, [isAnswered, question, currentUserId, selectedAnswer, isLastQuestion, nextQuestion, isSoloMode, currentUserDisplayName, score, gameCode, navigate, currentQuestionIndex]); // Added currentQuestionIndex

  // *** MODIFIED useGameTimer CALL ***
  const timeRemaining = useGameTimer(
    question?.id || `loading-${currentQuestionIndex}`, // Pass question ID or a placeholder as the timerId
    question?.timeLimit || 30,                         // initialTime
    isAnswered,                                        // isPaused
    handleSubmit                                       // onTimeout callback
  );

  // --- Effects ---
  // Reset local component state when the question changes
  useEffect(() => {
    if (question) {
      console.log(`Component State Reset Effect: New question loaded - ID: ${question.id}, Index: ${currentQuestionIndex}`);
      setSelectedAnswer(null);
      setIsAnswered(false); // Ensure interactions are enabled for the new question
      setIsCorrect(false);
      setPlayerSelections([]);
      setMaxHeight(null);
      answerRefs.current = [];
    }
  }, [question, currentQuestionIndex]); // Trigger on question change or index change

  // Calculate answer item heights for consistent layout
  useEffect(() => {
    if (!question || !question.answers || maxHeight !== null) return; // Avoid recalculating if already set

    // Ensure refs array is ready
    answerRefs.current = answerRefs.current.slice(0, question.answers.length);

    // Use requestAnimationFrame to calculate height after layout stabilizes
    let animationFrameId: number;
    const calculateHeight = () => {
        if (answerRefs.current.length === question.answers.length) {
            let highest = 0;
            answerRefs.current.forEach(ref => {
                if (ref) {
                     // Force browser reflow to get accurate height, might be intensive
                     // ref.offsetHeight;
                     const currentHeight = ref.getBoundingClientRect().height;
                     if (currentHeight > highest) {
                        highest = currentHeight;
                     }
                }
            });
             if (highest > 0 && highest !== maxHeight) {
                 console.log(`Setting max answer height to: ${highest}px for question ${question.id}`);
                setMaxHeight(highest);
            } else if (highest === 0) {
                console.warn(`Could not determine answer height for question ${question.id}. Refs available: ${answerRefs.current.filter(Boolean).length}/${question.answers.length}`);
                // Maybe retry after another short delay if height is 0?
            }
        }
    };

    // Delay calculation slightly more robustly
    const timeoutId = setTimeout(() => {
         animationFrameId = requestAnimationFrame(calculateHeight);
    }, 200); // Increased delay slightly


    return () => {
        clearTimeout(timeoutId);
        if (animationFrameId) {
             cancelAnimationFrame(animationFrameId);
        }
    };
  // Recalculate only when the question changes
  }, [question, maxHeight]); // Added maxHeight to dependencies to prevent recalculation loop

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
      // Logic to populate selections for crew mode would go here (e.g., from WebSocket state)
      return selections;
  }, [isSoloMode, question, playerSelections]);

  const questionTextClass = question ? getQuestionTextClass(question.text) : 'text-2xl md:text-3xl';

  // --- Loading and Error States ---
  if (isLoadingQuestions) {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center">
            <Loader2 className="h-12 w-12 animate-spin text-pirate-navy mb-4" />
            <p className="text-pirate-navy/80">Shuffling the Deck...</p> {/* More thematic */}
        </div>
    );
  }

  if (questionFetchError) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <Card className="p-6 text-center border-destructive bg-destructive/10">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-destructive mb-2">Stormy Seas Ahead!</h2> {/* Thematic */}
            <p className="text-destructive/80 mb-4">{questionFetchError}</p>
            <PirateButton onClick={() => navigate('/')} variant="secondary">
                Abandon Ship (Return Home)
            </PirateButton>
        </Card>
      </div>
    );
  }

  if (!question || !currentUserId || !packName) {
    if (!isLoadingQuestions && gameQuestions.length === 0) {
      return (
         <div className="min-h-screen flex flex-col items-center justify-center p-4">
           <Card className="p-6 text-center border-pirate-navy/20 bg-pirate-parchment">
               <AlertTriangle className="h-12 w-12 text-pirate-navy/50 mx-auto mb-4" />
               <h2 className="text-xl font-semibold text-pirate-navy mb-2">Empty Chest!</h2> {/* Thematic */}
               <p className="text-pirate-navy/80 mb-4">
                 No questions found in this treasure map.
               </p>
               <PirateButton onClick={() => navigate('/')} variant="secondary">
                   Return Home
               </PirateButton>
           </Card>
         </div>
       );
    }
    console.log("GameplayScreen: Rendering loading/error because question, userId, or packName is missing.", { question: !!question, currentUserId, packName });
    return <div className="min-h-screen flex items-center justify-center">Chartin' the Course...</div>; // Thematic
  }

  // --- Main Gameplay Render ---
  return (
    <div className="min-h-screen flex flex-col">
      <GameHeader />

      <main className="flex-1 container mx-auto px-4 py-6 flex flex-col">
        <div className="text-center mb-2">
          <h2 className="font-pirate text-3xl text-pirate-navy capitalize">
             {packName.replace(/-/g, ' ')}
          </h2>
          <p className="text-pirate-navy/80 font-medium">Question {currentQuestionIndex + 1} of {totalQuestionsToPlay}</p>
        </div>

        {/* Display the timer - NO KEY NEEDED HERE ANYMORE */}
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
              onSubmit: handleSubmit,
              disabled: !selectedAnswer && !isAnswered,
              isAnswered: isAnswered,
              isCorrect: isCorrect,
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
// --- END OF FULL FILE WITH MODIFIED HOOK CALL ---