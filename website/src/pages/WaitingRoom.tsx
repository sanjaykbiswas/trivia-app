// src/pages/WaitingRoom.tsx
// --- START OF MODIFIED FILE ---
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams, useSearchParams, Link } from 'react-router-dom';
import { Users, Copy, Anchor, ArrowLeft, ChevronDown, Settings, Loader2, RefreshCw } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import PlayerAvatar from '@/components/PlayerAvatar';
import { Player } from '@/types/gameTypes'; // Player type still useful for local structure
// Import API functions
import { joinGameSession, getGameParticipants, startGame } from '@/services/gameApi';
// Keep name assignment util (might be needed if localStorage name is null)
import { getPirateNameForUserId } from '@/utils/gamePlayUtils';
// Import API types for state and payload
import { ApiParticipant, ApiGameSessionResponse, ApiGameJoinRequest } from '@/types/apiTypes';

const POLLING_INTERVAL = 5000; // Fetch participants every 5 seconds

const WaitingRoom: React.FC = () => {
  const { role } = useParams<{ role?: string }>(); // captain or scallywag (or undefined for solo)
  const [searchParams] = useSearchParams();
  const gameCode = searchParams.get('gameCode'); // Can be null for solo
  // Settings from URL (might be null for Scallywags initially)
  const categoryParam = searchParams.get('category');
  const questionsParam = searchParams.get('questions');
  const timeParam = searchParams.get('time');

  const navigate = useNavigate();

  // State
  // Use ApiGameSessionResponse | null for gameSession state
  const [gameSession, setGameSession] = useState<ApiGameSessionResponse | null>(null);
  const [crewMembers, setCrewMembers] = useState<ApiParticipant[]>([]); // Holds actual participants from API
  const [isVoyageDetailsOpen, setIsVoyageDetailsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false); // General loading state (joining, starting)
  const [isFetchingParticipants, setIsFetchingParticipants] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [currentUserDisplayName, setCurrentUserDisplayName] = useState<string | null>(null);
  const [joinAttempted, setJoinAttempted] = useState(false); // Prevent multiple join attempts

  // Refs
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Get current user info from localStorage on mount
  useEffect(() => {
      const storedUserId = localStorage.getItem('tempUserId');
      const storedName = localStorage.getItem('tempUserDisplayName');
      if (!storedUserId) {
          console.error("Waiting Room: tempUserId not found in localStorage!");
          toast.error("Session Error", { description: "Could not find your user ID. Please go back."});
          // Optionally navigate back
          // navigate(role ? '/crew' : '/');
      } else {
        setCurrentUserId(storedUserId);
      }
      // Use stored name, or assign one if somehow missing
      setCurrentUserDisplayName(storedName || (storedUserId ? getPirateNameForUserId(storedUserId) : 'Unknown Pirate'));
      console.log("Waiting Room: Current User ID:", storedUserId, "Name:", storedName || 'Assigned Name');
  }, [role, navigate]); // Add navigate to dependency array

  // --- Scallywag Join Game Logic ---
  useEffect(() => {
      // Only run if scallywag, gameCode exists, user info is loaded, AND join hasn't been attempted
      if (role === 'scallywag' && gameCode && currentUserId && currentUserDisplayName && !joinAttempted) {
          setJoinAttempted(true); // Mark join as attempted
          const performJoin = async () => {
              setIsLoading(true); // Show loading indicator during join
              console.log(`Scallywag ${currentUserDisplayName} (${currentUserId}) attempting to join game ${gameCode}`);
              try {
                  const joinPayload: ApiGameJoinRequest = {
                       game_code: gameCode,
                       display_name: currentUserDisplayName // Use the assigned/stored name
                  };
                  const sessionData = await joinGameSession(joinPayload, currentUserId);
                  console.log("Successfully joined game:", sessionData);
                  setGameSession(sessionData); // Store joined session details
                  fetchParticipants(sessionData.id); // Fetch participants immediately
                  startParticipantPolling(sessionData.id); // Start polling

              } catch (error) {
                  console.error("Failed to join game:", error);
                  const errorMsg = error instanceof Error ? error.message : "Could not join the game.";
                  toast.error("Join Failed", { description: errorMsg });
                  navigate('/crew'); // Navigate back to role select on failure
              } finally {
                  setIsLoading(false);
              }
          };
          performJoin();
      }
      // Don't include navigate in dependencies here to avoid re-joining on navigation changes
      // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role, gameCode, currentUserId, currentUserDisplayName, joinAttempted]);

  // --- Captain Initial Load & Session State Handling ---
   useEffect(() => {
       // If captain and we have a gameCode (e.g., after creating game)
       if (role === 'captain' && gameCode && currentUserId) {
           console.log(`Captain ${currentUserId} arrived for game ${gameCode}.`);
           // TODO: In a real app, fetch the game session details by gameCode or ID here
           // to populate `gameSession` state accurately.
           // For now, we'll construct a partial state based on URL params for display.
           setGameSession(prev => ({
               // Keep existing fields if joining (though unlikely for captain), or set defaults
               id: prev?.id || 'unknown-game-id', // Need the actual ID for polling/starting
               code: gameCode,
               status: prev?.status || 'pending',
               pack_id: prev?.pack_id || categoryParam || 'unknown-pack',
               max_participants: prev?.max_participants || 10,
               question_count: parseInt(questionsParam || '10'),
               time_limit_seconds: parseInt(timeParam || '30'),
               current_question_index: prev?.current_question_index || 0,
               participant_count: prev?.participant_count || 0, // Will be updated by polling
               is_host: true, // Captain is host
               created_at: prev?.created_at || new Date().toISOString(),
           }));
            // Fetch initial participants (needs game ID)
            // fetchParticipants(gameSession?.id); // PROBLEM: gameSession.id might not be set yet
            // Let's fetch participants when gameSession ID becomes available in the polling effect
           startParticipantPolling(gameSession?.id); // Start polling (might need ID)

       } else if (!gameCode && role !== 'captain' && role !== 'scallywag') { // Solo mode
            console.log(`Solo player ${currentUserId} setting up voyage.`);
             // Construct minimal session state for solo display
             setGameSession({
                 id: 'solo-game-' + currentUserId, // Fake ID for solo
                 code: 'SOLO',
                 status: 'pending',
                 pack_id: categoryParam || 'unknown-pack',
                 max_participants: 1,
                 question_count: parseInt(questionsParam || '10'),
                 time_limit_seconds: parseInt(timeParam || '30'),
                 current_question_index: 0,
                 participant_count: 1,
                 is_host: true,
                 created_at: new Date().toISOString(),
             });
             // Add the solo player to the crew list for display
             if (currentUserId && currentUserDisplayName) {
                 setCrewMembers([{ id: currentUserId, display_name: currentUserDisplayName, score: 0, is_host: true }]);
             }
       }
   }, [role, gameCode, currentUserId, currentUserDisplayName, categoryParam, questionsParam, timeParam, startParticipantPolling]); // Added startParticipantPolling


  // --- Participant Fetching Function ---
  const fetchParticipants = useCallback(async (gameIdToFetch?: string) => {
      const targetGameId = gameIdToFetch || gameSession?.id;
      if (!targetGameId || targetGameId.startsWith('unknown') || targetGameId.startsWith('solo')) {
        console.log("Skipping participant fetch: No valid game ID available.", targetGameId);
        return; // Don't fetch if ID is unknown or for solo
      }

      console.log(`Fetching participants for game ID: ${targetGameId}`);
      setIsFetchingParticipants(true);
      try {
          const response = await getGameParticipants(targetGameId);
          setCrewMembers(response.participants); // Update state with API data
          // Update participant count in gameSession state as well
          setGameSession(prev => prev ? { ...prev, participant_count: response.total } : null);
          console.log("Fetched participants:", response.participants);
      } catch (error) {
          console.error("Failed to fetch participants:", error);
          // Avoid spamming toasts on polling errors
          // toast.error("Update Failed", { description: "Could not fetch updated player list." });
          // Stop polling on persistent errors?
          // if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
      } finally {
          setIsFetchingParticipants(false);
      }
  }, [gameSession?.id]); // Depend only on gameSession.id for stability

  // --- Participant Polling Effect ---
  const startParticipantPolling = useCallback((gameIdToPoll?: string) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    const targetGameId = gameIdToPoll || gameSession?.id;
    // Only poll in crew mode if we have a valid game ID
    if (gameCode && targetGameId && !targetGameId.startsWith('unknown') && !targetGameId.startsWith('solo')) {
        console.log(`Starting participant polling for game ID: ${targetGameId}`);
        // Initial fetch right away
        fetchParticipants(targetGameId);
        // Then set interval
        pollingIntervalRef.current = setInterval(() => {
            fetchParticipants(targetGameId);
        }, POLLING_INTERVAL);
    } else {
         console.log("Not starting polling (no gameCode or invalid gameId).");
    }
    // Cleanup function
    return () => {
      if (pollingIntervalRef.current) {
        console.log("Clearing participant polling interval.");
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [gameCode, gameSession?.id, fetchParticipants]); // Depend on gameCode, session ID, and fetch function

  // Start/Restart polling when gameSession ID becomes available
  useEffect(() => {
     return startParticipantPolling(); // Cleanup is handled inside
  }, [startParticipantPolling]); // Re-run only if the function itself changes

  // --- Game Start Logic ---
  const handleStartGame = async () => {
    if (!gameSession?.id || !currentUserId || gameSession.id.startsWith('unknown')) {
      toast.error("Error", { description: "Cannot start game. Missing game or user information." });
      return;
    }
    setIsLoading(true);
    console.log(`Captain ${currentUserDisplayName} (${currentUserId}) attempting to start game ${gameSession.id}`);
    if (pollingIntervalRef.current) { // Stop polling before starting
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
    }
    try {
        const startResponse = await startGame(gameSession.id, currentUserId);
        console.log("Game started successfully:", startResponse);
        if (startResponse.status === 'active') {
            // Navigate to countdown, passing necessary info via state if needed
            // The GameplayScreen will fetch the first question based on the game state
            navigate(`/countdown?questions=${startResponse.current_question?.time_limit ?? gameSession.question_count}`);
        } else {
            throw new Error(`Backend reported unexpected status after start: ${startResponse.status}`);
        }
    } catch (error) {
        console.error("Failed to start game:", error);
        const errorMsg = error instanceof Error ? error.message : "Could not start the game.";
        toast.error("Start Failed", { description: errorMsg });
        startParticipantPolling(gameSession.id); // Restart polling on error
    } finally {
        setIsLoading(false);
    }
  };

  // --- Helper Functions ---
  const copyGameCodeToClipboard = () => {
    if (gameCode) {
      navigator.clipboard.writeText(gameCode)
        .then(() => { toast.success('Copied to clipboard', { description: 'Game code copied successfully!' }); })
        .catch(() => { toast.error('Failed to copy', { description: 'Could not copy code.' }); });
    }
  };

 const getBackLink = () => {
     // Captain goes back to category select (GameSelect) for the *same* game code
     if (role === 'captain') return `/crew/captain?gameCode=${gameCode}`;
     // Scallywag goes back to role selection
     if (role === 'scallywag') return `/crew`;
     // Solo goes back to solo category select
     return '/solo';
  };

  // Determine host and display name
  const hostParticipant = crewMembers.find(p => p.is_host);
  const isCurrentUserHost = currentUserId === hostParticipant?.id;
  const hostDisplayName = hostParticipant?.display_name || 'The Captain';

  // Settings derived from gameSession state or URL params
  const displayCategory = gameSession?.pack_id || categoryParam || 'Unknown';
  const displayQuestions = gameSession?.question_count ?? questionsParam ?? 'N/A';
  const displayTime = gameSession?.time_limit_seconds ?? timeParam ?? 'N/A';
  const settingsAvailable = !!gameSession; // Settings are available if we have session data

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Back Button and Game Code */}
        <div className="flex items-center justify-between mb-6">
          <Link to={getBackLink()} className="flex items-center text-pirate-navy hover:text-pirate-accent">
            <ArrowLeft className="h-4 w-4 mr-2" />
            <span>Back</span>
          </Link>
          {gameCode && (
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-2 text-pirate-navy" />
              <span className="text-sm font-mono bg-pirate-navy/10 px-2 py-1 rounded">
                {gameCode}
              </span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button onClick={copyGameCodeToClipboard} className="ml-2 p-1 text-pirate-navy hover:text-pirate-gold transition-colors rounded-full hover:bg-pirate-navy/10" aria-label="Copy game code"><Copy className="h-4 w-4" /></button>
                  </TooltipTrigger>
                  <TooltipContent><p>Copy game code</p></TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          )}
        </div>

        {/* Main Content Area */}
        <div className="map-container p-6 md:p-8 mb-10 relative">
           {/* Loading Overlay for initial join or captain loading */}
           {(isLoading && !gameSession && role !== 'solo') && (
               <div className="absolute inset-0 bg-pirate-parchment/80 flex items-center justify-center rounded-xl z-20">
                   <Loader2 className="h-8 w-8 animate-spin text-pirate-navy" />
                   <span className="ml-2 font-semibold text-pirate-navy">{role === 'scallywag' ? 'Joining Crew...' : 'Loading Game...'}</span>
               </div>
           )}

          {/* Player List */}
          <div className="mb-8">
            <div className='flex justify-between items-center mb-6'>
                <h2 className="font-pirate text-3xl md:text-4xl text-pirate-navy">
                  {gameCode ? `Crew Members (${crewMembers.length})` : 'Your Voyage'}
                </h2>
                {gameCode && ( // Show refresh only in crew mode
                    <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" onClick={() => fetchParticipants(gameSession?.id)} disabled={isFetchingParticipants} className='text-pirate-navy/70 hover:text-pirate-navy disabled:opacity-50'>
                            <RefreshCw className={`h-4 w-4 ${isFetchingParticipants ? 'animate-spin' : ''}`} />
                        </Button>
                        </TooltipTrigger>
                        <TooltipContent> <p>Refresh List</p> </TooltipContent>
                    </Tooltip>
                    </TooltipProvider>
                )}
            </div>
             <div className={`grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 ${!gameCode ? 'justify-center' : ''}`}>
               {crewMembers.map((member) => (
                 <Card key={member.id} className="p-4 flex items-center space-x-3 border-pirate-navy/20 shadow-md">
                   <PlayerAvatar playerId={member.id} name={member.display_name} size="md" />
                   <div>
                     <p className="font-medium text-pirate-navy">{member.display_name}</p>
                     {gameCode && <p className="text-xs text-pirate-navy/70">{member.is_host ? 'Captain' : 'Crew Member'}</p>}
                   </div>
                 </Card>
               ))}
               {/* Placeholder/Loading Indicator */}
               {isFetchingParticipants && crewMembers.length === 0 && gameCode && ( // Show only in crew mode when loading empty
                    <Card className="p-4 flex items-center justify-center space-x-3 border-pirate-navy/20 border-dashed shadow-inner bg-pirate-parchment/50 min-h-[76px]">
                      <Loader2 className="h-5 w-5 animate-spin text-pirate-navy/50"/>
                      <p className="text-xs text-pirate-navy/50">Loading Crew...</p>
                    </Card>
               )}
             </div>
          </div>

          {/* Action Button / Waiting Message */}
          {gameCode ? ( // --- Crew Mode ---
            isCurrentUserHost ? ( // Captain's view
               <div className="mt-10">
                 <PirateButton onClick={handleStartGame} className="w-full py-3 text-lg" variant="accent" disabled={!settingsAvailable || crewMembers.length < 1 || isLoading} >
                   {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Anchor className="h-5 w-5" />}
                   {isLoading ? 'Starting...' : 'All aboard? Set sail!'}
                 </PirateButton>
                 {!settingsAvailable && <p className="text-xs text-center mt-2 text-pirate-navy/60">Waiting for voyage details...</p>}
                 {crewMembers.length < 1 && settingsAvailable && <p className="text-xs text-center mt-2 text-pirate-navy/60">Waiting for crew members...</p>}
               </div>
             ) : ( // Scallywag's view
               <div className="mt-10 text-center text-pirate-navy/80">
                 <p>Waiting for {hostDisplayName} to start the voyage...</p>
                 <div className="animate-pulse mt-2 text-2xl">⚓️</div>
               </div>
             )
           ) : ( // --- Solo Mode ---
             <div className="mt-10">
                 <PirateButton onClick={() => navigate(`/countdown?questions=${displayQuestions}`)} className="w-full py-3 text-lg" variant="accent" >
                   <Anchor className="h-5 w-5" />
                   Start Solo Voyage!
                 </PirateButton>
             </div>
           )}
         </div>

        {/* --- Collapsible Voyage Details --- */}
         {settingsAvailable && ( // Show if settings known (gameSession exists)
            <Collapsible open={isVoyageDetailsOpen} onOpenChange={setIsVoyageDetailsOpen} className="mb-8">
              <Card className="p-4 flex items-center min-h-[60px] bg-pirate-parchment/50">
                <CollapsibleTrigger className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2"> <Settings className="h-5 w-5 text-pirate-black" /> <h3 className="font-pirate text-2xl text-pirate-black">Voyage Details</h3> </div>
                  <ChevronDown className={`h-5 w-5 transition-transform duration-200 ${isVoyageDetailsOpen ? 'rotate-180' : ''}`} />
                </CollapsibleTrigger>
              </Card>
              <CollapsibleContent className="mt-2">
                <Card className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="border border-pirate-navy/10 rounded p-3">
                      <p className="text-xs text-pirate-navy/50 mb-1">Category</p>
                      {/* TODO: Display actual Pack Name based on pack_id */}
                      <p className="font-medium capitalize">{displayCategory.replace('-', ' ') || 'Unknown'}</p>
                    </div>
                    <div className="border border-pirate-navy/10 rounded p-3">
                      <p className="text-xs text-pirate-navy/50 mb-1">Questions</p>
                      <p className="font-medium">{displayQuestions}</p>
                    </div>
                    <div className="border border-pirate-navy/10 rounded p-3">
                      <p className="text-xs text-pirate-navy/50 mb-1">Time per Question</p>
                      <p className="font-medium">{displayTime ? `${displayTime} seconds` : 'N/A'}</p>
                    </div>
                  </div>
                </Card>
              </CollapsibleContent>
            </Collapsible>
          )}
       </main>
       {/* Footer */}
       <footer className="ocean-bg py-8">
         <div className="container mx-auto text-center text-white relative z-10">
           <p className="font-pirate text-xl mb-2">Ready the cannons!</p>
           <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
         </div>
       </footer>
     </div>
   );
 };

 export default WaitingRoom;
// --- END OF MODIFIED FILE ---