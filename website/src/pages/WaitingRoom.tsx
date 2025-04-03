// src/pages/WaitingRoom.tsx
// --- START OF FULL MODIFIED FILE ---
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
import { Button } from '@/components/ui/button'; // Correct import
import { cn } from '@/lib/utils'; // Import cn for conditional classes

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

  // --- Participant Fetching and Polling Callbacks (Defined Early) ---
  const fetchParticipants = useCallback(async (gameIdToFetch?: string) => {
      const targetGameId = gameIdToFetch || gameSession?.id;
      if (!targetGameId || targetGameId.startsWith('unknown') || targetGameId.startsWith('solo')) {
        console.log("Skipping participant fetch: No valid game ID available.", targetGameId);
        return;
      }

      console.log(`Fetching participants for game ID: ${targetGameId}`);
      setIsFetchingParticipants(true);
      try {
          const response = await getGameParticipants(targetGameId);
          setCrewMembers(response.participants);
          // Update participant count in gameSession state based on API response
          setGameSession(prev => prev ? { ...prev, participant_count: response.total } : null);
          console.log("Fetched participants:", response.participants);
      } catch (error) {
          console.error("Failed to fetch participants:", error);
      } finally {
          setIsFetchingParticipants(false);
      }
  }, [gameSession?.id]); // Depend only on gameSession.id

  const startParticipantPolling = useCallback((gameIdToPoll?: string) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    const targetGameId = gameIdToPoll || gameSession?.id;
    if (gameCode && targetGameId && !targetGameId.startsWith('unknown') && !targetGameId.startsWith('solo')) {
        console.log(`Starting participant polling for game ID: ${targetGameId}`);
        fetchParticipants(targetGameId); // Initial fetch
        pollingIntervalRef.current = setInterval(() => {
            fetchParticipants(targetGameId);
        }, POLLING_INTERVAL);
    } else {
         console.log("Not starting polling (no gameCode or invalid gameId).");
    }
    return () => { // Cleanup function
      if (pollingIntervalRef.current) {
        console.log("Clearing participant polling interval.");
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [gameCode, gameSession?.id, fetchParticipants]); // Depend on relevant state/callbacks


  // --- Effects ---

  // Get current user info from localStorage on mount
  useEffect(() => {
      const storedUserId = localStorage.getItem('tempUserId');
      const storedName = localStorage.getItem('tempUserDisplayName');
      if (!storedUserId) {
          console.error("Waiting Room: tempUserId not found in localStorage!");
          toast.error("Session Error", { description: "Could not find your user ID. Please go back."});
          // navigate(role ? '/crew' : '/'); // Optional: force navigation back
      } else {
        setCurrentUserId(storedUserId);
        // Ensure display name is set, assign if missing
        setCurrentUserDisplayName(storedName || getPirateNameForUserId(storedUserId));
      }
      console.log("Waiting Room: Current User ID:", storedUserId, "Name:", storedName || 'Assigned Name');
  }, [role, navigate]);

  // Scallywag Join Game Logic
  useEffect(() => {
      if (role === 'scallywag' && gameCode && currentUserId && currentUserDisplayName && !joinAttempted) {
          setJoinAttempted(true);
          const performJoin = async () => {
              setIsLoading(true);
              console.log(`Scallywag ${currentUserDisplayName} (${currentUserId}) attempting to join game ${gameCode}`);
              try {
                  const joinPayload: ApiGameJoinRequest = {
                       game_code: gameCode,
                       display_name: currentUserDisplayName
                  };
                  const sessionData = await joinGameSession(joinPayload, currentUserId);
                  console.log("Successfully joined game:", sessionData);
                  setGameSession(sessionData);
                  // Fetch immediately after join using the new session's ID
                  fetchParticipants(sessionData.id);
                  // Start polling using the new session's ID
                  startParticipantPolling(sessionData.id);

              } catch (error) {
                  console.error("Failed to join game:", error);
                  const errorMsg = error instanceof Error ? error.message : "Could not join the game.";
                  toast.error("Join Failed", { description: errorMsg });
                  navigate('/crew');
              } finally {
                  setIsLoading(false);
              }
          };
          performJoin();
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [role, gameCode, currentUserId, currentUserDisplayName, joinAttempted]); // Exclude fetch/startPolling from deps

  // Captain Initial Load & Session State Handling
   useEffect(() => {
       // Ensure this runs only once for the captain when necessary info is available
       if (role === 'captain' && gameCode && currentUserId && currentUserDisplayName && !gameSession) {
           console.log(`Captain ${currentUserId} setting up initial state for game ${gameCode}.`);

           // Set initial gameSession state based on URL params etc.
           const initialSessionData = {
               id: 'unknown-game-id-' + Date.now(), // Temporary ID until/if fetched
               code: gameCode,
               status: 'pending',
               pack_id: categoryParam || 'unknown-pack',
               max_participants: 10, // Default or from previous screen if available
               question_count: parseInt(questionsParam || '10'),
               time_limit_seconds: parseInt(timeParam || '30'),
               current_question_index: 0,
               participant_count: 1, // Start with the captain
               is_host: true,
               created_at: new Date().toISOString(),
           };
           console.log("Setting captain initial game session state:", initialSessionData);
           setGameSession(initialSessionData);

           // Set initial crewMembers state to include only the captain
           console.log("Setting captain initial crew members state.");
           setCrewMembers([{
               id: 'temp-captain-part-id', // Temporary participant record ID
               user_id: currentUserId, // The captain's actual user ID
               display_name: currentUserDisplayName,
               score: 0,
               is_host: true
           }]);
           // Polling will start/restart based on the gameSession.id update in the other effect
       } else if (!gameCode && role !== 'captain' && role !== 'scallywag') { // Solo mode
            console.log(`Solo player ${currentUserId} setting up voyage.`);
             setGameSession({
                 id: 'solo-game-' + currentUserId,
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
             if (currentUserId && currentUserDisplayName) {
                 setCrewMembers([{
                    id: 'temp-solo-part-id',
                    user_id: currentUserId,
                    display_name: currentUserDisplayName,
                    score: 0,
                    is_host: true
                }]);
             }
       }
       // Intentionally exclude gameSession to prevent loop on initial set
       // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [role, gameCode, currentUserId, currentUserDisplayName, categoryParam, questionsParam, timeParam]);

  // Start/Restart polling when gameSession ID becomes valid for crew mode
  useEffect(() => {
     if (gameSession?.id && !gameSession.id.startsWith('unknown') && !gameSession.id.startsWith('solo')) {
         return startParticipantPolling(gameSession.id);
     } else {
         if (pollingIntervalRef.current) {
             clearInterval(pollingIntervalRef.current);
             pollingIntervalRef.current = null;
         }
     }
  }, [gameSession?.id, startParticipantPolling]); // Depend on gameSession.id


  // --- Game Start Logic ---
  const handleStartGame = async () => {
    if (!gameSession?.id || !currentUserId || gameSession.id.startsWith('unknown')) {
      toast.error("Error", { description: "Cannot start game. Missing game or user information." });
      return;
    }
    setIsLoading(true);
    console.log(`Captain ${currentUserDisplayName} (${currentUserId}) attempting to start game ${gameSession.id}`);
    if (pollingIntervalRef.current) { // Stop polling
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
    }
    try {
        const startResponse = await startGame(gameSession.id, currentUserId);
        console.log("Game started successfully:", startResponse);
        if (startResponse.status === 'active') {
            // Pass game settings needed for GameplayScreen via state
            navigate(`/countdown`, {
                state: {
                    gameId: gameSession.id,
                    totalQuestions: startResponse.current_question?.time_limit ?? gameSession.question_count, // Or use gameSession.question_count directly
                    // Add other relevant game settings if needed by GameplayScreen
                }
            });
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
     // Captain should go back to category select IF they created the game from there
     // This might require more state tracking. For now, simpler logic:
     if (role === 'captain') return `/crew`; // Go back to role select
     if (role === 'scallywag') return `/crew`; // Go back to role select
     return '/solo'; // Solo goes back to solo category select
  };

  // --- Derived Data ---
  const hostParticipant = crewMembers.find(p => p.is_host);
  // *** USE user_id FOR HOST CHECK ***
  const isCurrentUserHost = currentUserId === hostParticipant?.user_id;
  const hostDisplayName = hostParticipant?.display_name || 'The Captain';

  const displayCategory = gameSession?.pack_id || categoryParam || 'Unknown';
  const displayQuestions = gameSession?.question_count ?? questionsParam ?? 'N/A';
  const displayTime = gameSession?.time_limit_seconds ?? timeParam ?? 'N/A';
  const settingsAvailable = !!gameSession;

  // --- Render ---
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
           {/* Loading Overlay */}
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
                  {gameCode ? `Crew Members (${gameSession?.participant_count ?? crewMembers.length})` : 'Your Voyage'}
                </h2>
                {gameCode && (
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
               {/* Display Crew Members */}
               {crewMembers.map((member) => {
                 // *** UPDATED HIGHLIGHTING LOGIC ***
                 const isYou = member.user_id === currentUserId; // Compare USER IDs
                 // *** END UPDATED LOGIC ***
                 return (
                   <Card
                     key={member.id} // Keep using participant record ID as key
                     className={cn(
                       "p-4 flex items-center space-x-3 border-pirate-navy/20 shadow-md",
                       isYou && "bg-pirate-navy text-white border-pirate-gold border-2" // Highlight classes
                     )}
                   >
                     {/* Pass USER_ID to PlayerAvatar for consistent emoji */}
                     <PlayerAvatar playerId={member.user_id} name={member.display_name} size="md" />
                     <div>
                       <p className={cn(
                           "font-medium",
                           isYou ? "text-white" : "text-pirate-navy" // Text color
                         )}
                       >
                         {member.display_name}
                       </p>
                       {gameCode && (
                         <p className={cn(
                             "text-xs",
                             isYou ? "text-white/80" : "text-pirate-navy/70" // Muted text color
                           )}
                         >
                           {member.is_host ? 'Captain' : 'Crew Member'} {isYou ? '(You)' : ''} {/* (You) indicator */}
                         </p>
                       )}
                        {!gameCode && isYou && ( // (You) for Solo
                           <p className="text-xs text-white/80">(You)</p>
                       )}
                     </div>
                   </Card>
                 )
                })}
               {/* Placeholder/Waiting Indicator */}
               {isFetchingParticipants && crewMembers.length === 0 && gameCode && (
                    <Card className="p-4 flex items-center justify-center space-x-3 border-pirate-navy/20 border-dashed shadow-inner bg-pirate-parchment/50 min-h-[76px]">
                      <Loader2 className="h-5 w-5 animate-spin text-pirate-navy/50"/>
                      <p className="text-xs text-pirate-navy/50">Loading Crew...</p>
                    </Card>
               )}
               {!isFetchingParticipants && crewMembers.length === 0 && role === 'scallywag' && gameCode && (
                   <div className="col-span-full text-center py-4">
                       <p className="text-pirate-navy/60">Waiting for the Captain and crew...</p>
                   </div>
               )}
                {!isFetchingParticipants && crewMembers.length <= 1 && role === 'captain' && gameCode && (
                   <div className="col-span-full text-center py-4">
                       <p className="text-pirate-navy/60">Waiting for crew to join...</p>
                   </div>
               )}
             </div>
          </div>

          {/* Action Button / Waiting Message */}
          {gameCode ? ( // Crew Mode
            // Use isCurrentUserHost derived from API data (comparing user_ids)
            isCurrentUserHost ? ( // Captain's view
               <div className="mt-10">
                 <PirateButton onClick={handleStartGame} className="w-full py-3 text-lg" variant="accent" disabled={!settingsAvailable || crewMembers.length < 1 || isLoading} >
                   {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Anchor className="h-5 w-5" />}
                   {isLoading ? 'Starting...' : 'All aboard? Set sail!'}
                 </PirateButton>
                 {!settingsAvailable && <p className="text-xs text-center mt-2 text-pirate-navy/60">Waiting for voyage details...</p>}
                 {crewMembers.length <= 1 && settingsAvailable && !isLoading && <p className="text-xs text-center mt-2 text-pirate-navy/60">Waiting for crew members to join...</p>}
               </div>
             ) : ( // Scallywag's view
               <div className="mt-10 text-center text-pirate-navy/80">
                 <p>Waiting for {hostDisplayName} to start the voyage...</p>
                 <div className="animate-pulse mt-2 text-2xl">⚓️</div>
               </div>
             )
           ) : ( // Solo Mode
             <div className="mt-10">
                 <PirateButton onClick={() => navigate(`/countdown?questions=${displayQuestions}`)} className="w-full py-3 text-lg" variant="accent" >
                   <Anchor className="h-5 w-5" />
                   Start Solo Voyage!
                 </PirateButton>
             </div>
           )}
         </div>

        {/* Collapsible Voyage Details */}
         {settingsAvailable && (
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
                      <p className="font-medium capitalize">{displayCategory.replace(/-/g, ' ') || 'Unknown'}</p>
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
// --- END OF FULL MODIFIED FILE ---