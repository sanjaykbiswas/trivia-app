// website/src/pages/GameplayScreen.tsx
// --- START OF FULL MODIFIED FILE ---
import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import GameHeader from '@/components/GameHeader';
import QuestionCard from '@/components/QuestionCard';
import QuestionTimer from '@/components/QuestionTimer'; // Import the timer component
import { Player, PlayerSelection, PlayerResult, Question, Answer } from '@/types/gameTypes';
import { getGamePlayQuestions, submitAnswer as submitAnswerApi, getGameParticipants } from '@/services/gameApi';
import { getPlayerById, getQuestionTextClass, getPirateNameForUserId, getEmojiForPlayerId } from '@/utils/gamePlayUtils';
import { useGameTimer } from '@/hooks/useGameTimer';
import { useQuestionManager } from '@/hooks/useQuestionManager';
import { toast } from 'sonner';
import { Loader2, AlertTriangle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import PirateButton from '@/components/PirateButton';

// --- WebSocket Imports ---
import { useWebSocket } from '@/hooks/useWebSocket';
import { IncomingWsMessage } from '@/types/websocketTypes';
import { ApiParticipant, ApiGameSessionResponse, ApiGameSubmitAnswerRequest, ApiQuestionResultResponse } from '@/types/apiTypes'; // Added ApiQuestionResultResponse
// --- End WebSocket Imports ---

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
  const isSoloMode = !gameCode; // Determine mode based on gameCode presence

  // --- State for Fetched Questions and Loading/Error ---
  const [gameQuestions, setGameQuestions] = useState<Question[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const [questionFetchError, setQuestionFetchError] = useState<string | null>(null);

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
      try {
        const response = await getGamePlayQuestions(gameId);
        const formattedQuestions: Question[] = response.questions.map((apiQ): Question => {
            const answersWithOptions: Answer[] = apiQ.options.map((optionText, optionIndex): Answer => ({
                id: `${apiQ.question_id}-${optionIndex}`, text: optionText, letter: String.fromCharCode(65 + optionIndex)
            }));
            const correctAnswerId = apiQ.correct_answer_id;
            if (!correctAnswerId) console.error(`Missing correct_answer_id for question ${apiQ.question_id}`);
            return { id: apiQ.question_id, text: apiQ.question_text, category: packId || 'Trivia', answers: answersWithOptions, correctAnswer: correctAnswerId, timeLimit: apiQ.time_limit, };
        });
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
  const [currentParticipantId, setCurrentParticipantId] = useState<string | null>(null);


  // --- User Info Effect (Calls getGameParticipants) ---
  useEffect(() => {
    const storedUserId = localStorage.getItem('tempUserId');
    const storedName = localStorage.getItem('tempUserDisplayName');
    if (storedUserId) {
      setCurrentUserId(storedUserId);
      setCurrentUserDisplayName(storedName || getPirateNameForUserId(storedUserId));

      const fetchParticipantId = async () => {
           if (gameId && storedUserId) {
               try {
                   console.log(`Fetching participants in Gameplay to find participant ID for user ${storedUserId}...`);
                   const response = await getGameParticipants(gameId);
                   const currentUserParticipant = response.participants.find(p => p.user_id === storedUserId);
                   if (currentUserParticipant) {
                       setCurrentParticipantId(currentUserParticipant.id);
                       console.log(`Found participant ID: ${currentUserParticipant.id}`);
                   } else {
                       console.error(`Could not find participant record for user ${storedUserId} in game ${gameId}.`);
                       toast.error("Game Sync Error", { description: "Could not verify your participation. Submissions might fail." });
                   }
               } catch (error) {
                   console.error("Error fetching participant ID:", error);
                   toast.error("Game Sync Error", { description: "Could not verify participation." });
               }
           }
      };
      // Fetch participant ID only if it's *not* solo mode OR if needed for API submissions even in solo
      // Let's fetch it always for now, as submitAnswer API needs it.
      fetchParticipantId();

    } else {
      console.error("Gameplay: User ID not found!");
      toast.error("Session Error", { description: "User ID missing. Please restart." });
      navigate('/');
    }
  }, [navigate, gameId]);

  // --- WebSocket Message Handler (Only relevant for Crew mode) ---
  const handleWebSocketMessage = useCallback((message: IncomingWsMessage) => {
    // Skip handling if in solo mode
    if (isSoloMode) return;

    console.log("GameplayScreen Received WebSocket Message:", message.type, message.payload);
    switch (message.type) {
      case 'next_question': {
        const nextQuestionIndex = message.payload.index;
        console.log(`WS: Received next_question signal for index ${nextQuestionIndex}. Current index: ${currentQuestionIndexRef.current}`);
        if (nextQuestionIndex === currentQuestionIndexRef.current + 1) {
            console.log("WS: Advancing to next question based on WS message.");
            nextQuestionRef.current();
        } else {
            console.warn(`WS: Received next_question for index ${nextQuestionIndex}, but expected ${currentQuestionIndexRef.current + 1}. Ignoring.`);
        }
        break;
      }
      case 'game_over': {
        console.log("WS: Received game_over signal.");
        const resultsPayload = message.payload;
        const formattedResults: PlayerResult[] = resultsPayload.participants.map((p: ApiParticipant) => ({
             id: p.user_id, name: p.display_name, score: p.score,
             avatar: getEmojiForPlayerId(p.user_id)
        }));
        const resultsPath = gameCode ? `/results?gameCode=${gameCode}` : '/results';
        toast.info("Game Over!", { description: "Heading to the results..." });
        navigate(resultsPath, { state: { results: formattedResults } });
        break;
      }
       case 'game_cancelled': {
         toast.error("Game Cancelled", { description: "The Captain has cancelled the game." });
         navigate('/');
         break;
       }
       case 'error': {
         toast.error("Server Error", { description: message.payload.message });
         break;
       }
      // We don't need participant join/leave/name messages on the gameplay screen itself
      default: break;
    }
  }, [navigate, gameCode, isSoloMode]); // Added isSoloMode dependency

  // --- Refs for Stable Callbacks ---
  const nextQuestionRef = useRef(nextQuestion);
  const currentQuestionIndexRef = useRef(currentQuestionIndex);
  useEffect(() => { nextQuestionRef.current = nextQuestion; }, [nextQuestion]);
  useEffect(() => { currentQuestionIndexRef.current = currentQuestionIndex; }, [currentQuestionIndex]);

  // --- Initialize WebSocket Connection (Conditional) ---
  const { status: wsStatus } = useWebSocket({
    gameId: !isSoloMode ? gameId : null, // Pass null if solo
    userId: !isSoloMode ? currentUserId : null, // Pass null if solo
    onMessage: handleWebSocketMessage,
    onOpen: () => console.log("Gameplay WebSocket connected."),
    onClose: (event) => console.log("Gameplay WebSocket closed:", event.code),
    onError: (event) => {
        // Only show connection error toast in crew mode
        if (!isSoloMode) {
            toast.error("Connection Error", { description: "Lost connection during gameplay." })
        } else {
            console.log("Ignoring WS connection error in solo mode.");
        }
    },
  });
  // --- End WebSocket Initialization ---

  // --- handleSubmit ---
  const handleSubmit = useCallback(async () => {
    if (isAnswered || !question || !currentUserId || !gameId) {
       console.log("Submit prevented (GameplayScreen):", { isAnswered, question: !!question, currentUserId: !!currentUserId, gameId: !!gameId });
       return;
    }

    console.log(`Handling submit for Q Index: ${currentQuestionIndex}, Q ID: ${question.id}`);
    setIsAnswered(true);
    const answerIsCorrect = selectedAnswer === question.correctAnswer;
    setIsCorrect(answerIsCorrect);

    // Submit score/history via API (Required for both modes if tracking history/score on backend)
    let finalScoreAfterSubmit = score; // Start with current score
    if (selectedAnswer && currentParticipantId) {
       try {
           console.log(`${isSoloMode ? 'SOLO' : 'CREW'}: Submitting answer '${selectedAnswer}' via REST API (Participant: ${currentParticipantId})...`);
           const submitPayload: ApiGameSubmitAnswerRequest = { question_index: currentQuestionIndex, answer: selectedAnswer };
           const submitResult: ApiQuestionResultResponse = await submitAnswerApi(gameId, currentParticipantId, submitPayload);
           console.log(`${isSoloMode ? 'SOLO' : 'CREW'}: Answer submission API response:`, submitResult);
           if (submitResult?.total_score !== undefined) {
               finalScoreAfterSubmit = submitResult.total_score; // Update score based on API response
               setScore(finalScoreAfterSubmit);
           } else {
                console.warn("API submit response did not contain total_score.");
                // Simple local fallback score update if API fails/is weird
                if (answerIsCorrect) { finalScoreAfterSubmit = score + 1; setScore(finalScoreAfterSubmit); }
           }
       } catch (error) {
           console.error(`${isSoloMode ? 'SOLO' : 'CREW'}: Failed to submit answer via API:`, error);
           toast.error("Sync Failed", { description: "Could not record your answer." });
           // Simple local fallback score update if API fails
           if (answerIsCorrect) { finalScoreAfterSubmit = score + 1; setScore(finalScoreAfterSubmit); }
       }
    } else {
       console.log(`${isSoloMode ? 'SOLO' : 'CREW'}: No answer selected or participant ID missing, skipping API submit.`);
       // Keep finalScoreAfterSubmit as the current score
    }


    // *** ADDED SOLO Advancement Logic ***
    if (isSoloMode) {
        console.log("SOLO MODE: Triggering advancement locally.");
        // Use a short delay to allow the user to see the result feedback briefly
        setTimeout(() => {
            if (isLastQuestion) {
                console.log("SOLO MODE: Last question answered. Navigating to results.");
                // Prepare results locally for solo mode
                const finalResult: PlayerResult = {
                    id: currentUserId, // Use the actual user ID
                    name: currentUserDisplayName || 'Solo Player',
                    score: finalScoreAfterSubmit, // Use the score AFTER potential API update/fallback
                    avatar: getEmojiForPlayerId(currentUserId) // Assign avatar
                };
                navigate('/results', { state: { results: [finalResult] } }); // Pass single result
            } else {
                console.log("SOLO MODE: Advancing to next question locally.");
                nextQuestionRef.current(); // Use the ref to the hook's function
            }
        }, 1500); // 1.5 second delay
    } else {
         console.log("CREW MODE: Submit handled. Waiting for WebSocket signal to advance.");
         // In crew mode, advancement is handled by the 'next_question' or 'game_over' WS message
    }
  }, [
      isAnswered, question, currentUserId, gameId, selectedAnswer,
      currentQuestionIndex, currentParticipantId, isSoloMode, isLastQuestion,
      score, currentUserDisplayName, navigate // Keep dependencies
  ]);
  // --- End Solo Advancement Logic ---


  // --- Timer Hook ---
  const timeRemaining = useGameTimer(
    question?.id || `loading-${currentQuestionIndex}`,
    question?.timeLimit || 30,
    isAnswered,
    handleSubmit // Pass the potentially modified handleSubmit
  );

  // --- Effects (Reset, Height Calculation) ---
  useEffect(() => {
    if (question) {
      console.log(`Component State Reset Effect: New question loaded - ID: ${question.id}, Index: ${currentQuestionIndex}`);
      setSelectedAnswer(null);
      setIsAnswered(false);
      setIsCorrect(false);
      setPlayerSelections([]);
      setMaxHeight(null);
      answerRefs.current = [];
    }
  }, [question, currentQuestionIndex]);

  useEffect(() => {
     if (!question || !question.answers || maxHeight !== null || !answerRefs.current) return;
      answerRefs.current = answerRefs.current.slice(0, question.answers.length);
      let animationFrameId: number;
      const calculateHeight = () => {
          if (answerRefs.current.length === question.answers.length && answerRefs.current.every(Boolean)) {
              let highest = 0;
              answerRefs.current.forEach(ref => { if (ref) { const currentHeight = ref.getBoundingClientRect().height; if (currentHeight > highest) highest = currentHeight; } });
              if (highest > 0 && highest !== maxHeight) setMaxHeight(highest);
          }
      };
      const timeoutId = setTimeout(() => { animationFrameId = requestAnimationFrame(calculateHeight); }, 200);
      return () => { clearTimeout(timeoutId); if (animationFrameId) cancelAnimationFrame(animationFrameId); };
  }, [question, maxHeight]);

  // --- Event Handlers ---
  const handleAnswerSelect = (answerId: string) => { if (!isAnswered) { setSelectedAnswer(answerId); if (currentUserId) setPlayerSelections([{ playerId: currentUserId, answerId }]); } };

  // --- Derived Data ---
  const playerSelectionsByAnswer = useMemo(() => {
      // This is only relevant for crew mode display, safe to keep as is
      if (isSoloMode || !question) return {};
      const selections: Record<string, Player[]> = {};
      playerSelections.forEach(sel => {
          const player = getPlayerById([], sel.playerId); // Note: getPlayerById currently uses mock data
          if (player) { if (!selections[sel.answerId]) selections[sel.answerId] = []; selections[sel.answerId].push(player); }
      });
      return selections;
  }, [isSoloMode, question, playerSelections]);
  const questionTextClass = question ? getQuestionTextClass(question.text) : 'text-2xl md:text-3xl';

  // --- Loading and Error States ---
  if (isLoadingQuestions) { return (<div className="min-h-screen flex flex-col items-center justify-center"><Loader2 className="h-12 w-12 animate-spin text-pirate-navy mb-4" /><p className="text-pirate-navy/80">Shuffling the Deck...</p></div>); }
  if (questionFetchError) { return (<div className="min-h-screen flex flex-col items-center justify-center p-4"><Card className="p-6 text-center border-destructive bg-destructive/10"><AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" /><h2 className="text-xl font-semibold text-destructive mb-2">Stormy Seas Ahead!</h2><p className="text-destructive/80 mb-4">{questionFetchError}</p><PirateButton onClick={() => navigate('/')} variant="secondary">Abandon Ship (Return Home)</PirateButton></Card></div>); }
  if (!question || !currentUserId || !packName) { if (!isLoadingQuestions && gameQuestions.length === 0) { return (<div className="min-h-screen flex flex-col items-center justify-center p-4"><Card className="p-6 text-center border-pirate-navy/20 bg-pirate-parchment"><AlertTriangle className="h-12 w-12 text-pirate-navy/50 mx-auto mb-4" /><h2 className="text-xl font-semibold text-pirate-navy mb-2">Empty Chest!</h2><p className="text-pirate-navy/80 mb-4">No questions found in this treasure map.</p><PirateButton onClick={() => navigate('/')} variant="secondary">Return Home</PirateButton></Card></div>); } return <div className="min-h-screen flex items-center justify-center">Chartin' the Course...</div>; }

  // --- Main Gameplay Render ---
  return (
    <div className="min-h-screen flex flex-col">
      <GameHeader />
      <main className="flex-1 container mx-auto px-4 py-6 flex flex-col">
        <div className="text-center mb-2">
          <h2 className="font-pirate text-3xl text-pirate-navy capitalize">{packName.replace(/-/g, ' ')}</h2>
          <p className="text-pirate-navy/80 font-medium">Question {currentQuestionIndex + 1} of {totalQuestionsToPlay}</p>
        </div>
        <QuestionTimer timeRemaining={timeRemaining} totalTime={question.timeLimit} />
        <div className="map-container p-0 mb-6 flex-1 flex">
          <QuestionCard
            questionText={question.text}
            answers={question.answers}
            selectedAnswer={selectedAnswer}
            isAnswered={isAnswered} // Pass down isAnswered state
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
      <style>{`@keyframes shake { 0%, 100% { transform: translateX(0); } 10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); } 20%, 40%, 60%, 80% { transform: translateX(5px); } } .animate-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }`}</style>
      <footer className="ocean-bg py-8"><div className="container mx-auto text-center text-white relative z-10"><p className="font-pirate text-xl mb-2">Answer wisely, matey!</p><p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p></div></footer>
    </div>
  );
};

export default GameplayScreen;
// --- END OF FULL MODIFIED FILE ---