// website/src/pages/WaitingRoom.tsx
// --- START OF FULL MODIFIED FILE ---
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams, useSearchParams, Link, useLocation } from 'react-router-dom'; // Added useLocation
import { Users, Copy, Anchor, ArrowLeft, ChevronDown, Settings, Loader2, RefreshCw, Pencil } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import PlayerAvatar from '@/components/PlayerAvatar';
import { Player } from '@/types/gameTypes';
import { joinGameSession, getGameParticipants, startGame } from '@/services/gameApi';
import { updateUser } from '@/services/userApi';
import { getPirateNameForUserId } from '@/utils/gamePlayUtils';
import { ApiParticipant, ApiGameSessionResponse, ApiGameJoinRequest } from '@/types/apiTypes';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
    // DialogClose is NOT imported as we removed the explicit cancel button
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useForm } from "react-hook-form"
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form"

const POLLING_INTERVAL = 5000;

interface EditNameFormValues {
  newName: string;
}

const WaitingRoom: React.FC = () => {
  const { role } = useParams<{ role?: string }>();
  const [searchParams] = useSearchParams();
  const location = useLocation(); // <-- Get location object
  const gameCode = searchParams.get('gameCode');
  const categoryParam = searchParams.get('category'); // Still useful for display if needed
  const questionsParam = searchParams.get('questions'); // Still useful for display if needed
  const timeParam = searchParams.get('time'); // Still useful for display if needed

  const navigate = useNavigate();

  // State
  const [gameSession, setGameSession] = useState<ApiGameSessionResponse | null>(null);
  const [crewMembers, setCrewMembers] = useState<ApiParticipant[]>([]);
  const [isVoyageDetailsOpen, setIsVoyageDetailsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingParticipants, setIsFetchingParticipants] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [currentUserDisplayName, setCurrentUserDisplayName] = useState<string | null>(null);
  const [joinAttempted, setJoinAttempted] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isUpdatingName, setIsUpdatingName] = useState(false);
  const [packName, setPackName] = useState<string | null>(location.state?.packName || null); // <-- ADD state for packName

  // Refs
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Form Hook for Edit Name
  const editNameForm = useForm<EditNameFormValues>({
    defaultValues: { newName: '' },
  });

  // --- Participant Fetching and Polling Callbacks ---
  const fetchParticipants = useCallback(async (gameIdToFetch?: string) => {
      const targetGameId = gameIdToFetch || gameSession?.id;
      // Allow fetching even with 'unknown' ID initially for captain, but not for solo
      if (!targetGameId || targetGameId.startsWith('solo')) {
        console.log("Skipping participant fetch: Solo game or no ID.", targetGameId);
        return;
      }
      // Scallywags need to wait for the real ID from the session state after joining
      if (role === 'scallywag' && targetGameId.startsWith('unknown')) {
         console.log("Skipping participant fetch: Scallywag waiting for captain's real game ID.", targetGameId);
         return;
      }

      console.log(`Fetching participants for game ID: ${targetGameId}`);
      setIsFetchingParticipants(true);
      try {
          const response = await getGameParticipants(targetGameId);
          // --- MODIFICATION: Update crewMembers AND currentUserDisplayName if needed ---
          setCrewMembers(response.participants);
          // Find the current user in the updated list and update their local name state if different
          const currentUserData = response.participants.find(p => p.user_id === currentUserId);
          if (currentUserData && currentUserData.display_name !== currentUserDisplayName) {
              console.log(`Updating local display name from fetched participants: ${currentUserData.display_name}`);
              setCurrentUserDisplayName(currentUserData.display_name);
              // Optionally update localStorage too, though less critical if fetched on reload
              localStorage.setItem('tempUserDisplayName', currentUserData.display_name);
          }
          // --- END MODIFICATION ---
          setGameSession(prev => prev ? { ...prev, participant_count: response.total } : null);
          console.log("Fetched participants:", response.participants);
      } catch (error) {
          if (error instanceof Error && error.message.includes('404')) {
              console.warn(`Participant fetch failed (likely placeholder/old ID or game ended): ${error.message}`);
              // If game not found during polling, maybe stop polling?
              if (pollingIntervalRef.current) {
                  console.log("Stopping polling due to 404.");
                  clearInterval(pollingIntervalRef.current);
                  pollingIntervalRef.current = null;
                  // Optionally navigate back or show error message
                  toast.error("Game Not Found", { description: "The game session seems to have ended or doesn't exist."});
                  // Consider navigation: navigate(getBackLink());
              }
          } else {
              console.error("Failed to fetch participants:", error);
          }
      } finally {
          setIsFetchingParticipants(false);
      }
  // Added currentUserId and currentUserDisplayName to dependencies
  }, [gameSession?.id, role, currentUserId, currentUserDisplayName]); // Removed fetchParticipants from dependencies

  const startParticipantPolling = useCallback((gameIdToPoll?: string) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    const targetGameId = gameIdToPoll || gameSession?.id;
    // Only poll if it's crew mode (gameCode exists) AND we have a targetGameId that isn't for solo
    if (gameCode && targetGameId && !targetGameId.startsWith('solo')) {
        console.log(`Starting participant polling for game ID: ${targetGameId}`);
        fetchParticipants(targetGameId); // Initial fetch
        pollingIntervalRef.current = setInterval(() => {
            // Check inside interval if the session still exists and isn't solo
            const currentSessionId = gameSessionRef.current?.id; // Use ref to get latest session ID
            if (currentSessionId && !currentSessionId.startsWith('solo')) {
                 fetchParticipants(currentSessionId);
            } else {
                console.log("Stopping polling inside interval: No valid game ID or session changed.");
                if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
            }
        }, POLLING_INTERVAL);
    } else {
         console.log("Not starting polling (no gameCode, invalid gameId, or solo mode). ID:", targetGameId);
    }
    return () => {
      if (pollingIntervalRef.current) {
        console.log("Clearing participant polling interval.");
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  // Use ref instead of state for gameSession ID inside interval
  }, [gameCode, fetchParticipants]); // Removed gameSession?.id

  // Ref to store the latest gameSession ID for use in interval
  const gameSessionRef = useRef(gameSession);
  useEffect(() => {
    gameSessionRef.current = gameSession;
  }, [gameSession]);


  // --- Effects ---
  useEffect(() => {
      const storedUserId = localStorage.getItem('tempUserId');
      const storedName = localStorage.getItem('tempUserDisplayName');
      if (!storedUserId) {
          console.error("Waiting Room: tempUserId not found in localStorage!");
          toast.error("Session Error", { description: "Could not find your user ID. Please go back."});
      } else {
        setCurrentUserId(storedUserId);
        const nameToSet = storedName || getPirateNameForUserId(storedUserId);
        setCurrentUserDisplayName(nameToSet);
        editNameForm.setValue('newName', nameToSet);
      }
  }, [role, navigate, editNameForm]);

  // Initialize Captain/Solo state from location
  useEffect(() => {
      const stateFromNavigation = location.state as { gameSession?: ApiGameSessionResponse, packName?: string } | undefined; // <-- Add packName to type

      if (role === 'captain' && currentUserId && currentUserDisplayName && !gameSession) {
          if (stateFromNavigation?.gameSession && stateFromNavigation.gameSession.code === gameCode) {
              console.log("Captain: Initializing with gameSession from navigation state:", stateFromNavigation);
              setGameSession(stateFromNavigation.gameSession);
              setPackName(stateFromNavigation.packName || 'Unknown Pack'); // <-- Set packName from state
              setCrewMembers([{
                  id: 'captain-participant-' + currentUserId,
                  user_id: currentUserId,
                  display_name: currentUserDisplayName,
                  score: 0,
                  is_host: true
              }]);
              startParticipantPolling(stateFromNavigation.gameSession.id);
          } else {
              console.warn("Captain: gameSession missing/mismatched in navigation state. Using placeholder.");
              const placeholderSession = {
                 id: 'unknown-game-id-' + Date.now(),
                 code: gameCode || 'UNKNOWN', status: 'pending', pack_id: categoryParam || 'unknown-pack',
                 max_participants: 10, question_count: parseInt(questionsParam || '10'),
                 time_limit_seconds: parseInt(timeParam || '30'), current_question_index: 0,
                 participant_count: 1, is_host: true, created_at: new Date().toISOString(),
              };
              setGameSession(placeholderSession);
              setPackName(categoryParam || 'Unknown Pack'); // <-- Use categoryParam as fallback
              setCrewMembers([{
                 id: 'temp-captain-part-id-' + currentUserId, user_id: currentUserId,
                 display_name: currentUserDisplayName, score: 0, is_host: true
             }]);
             startParticipantPolling(placeholderSession.id);
          }
      }
      // Solo Mode Logic removed - handled by GameSelect navigation now
  // Add location.state to dependencies
  }, [role, gameCode, currentUserId, currentUserDisplayName, gameSession, location.state, categoryParam, questionsParam, timeParam, startParticipantPolling]); // Added location.state


  // Scallywag Join Game Logic
  useEffect(() => {
      if (role === 'scallywag' && gameCode && currentUserId && currentUserDisplayName && !joinAttempted && !gameSession) {
          setJoinAttempted(true);
          const performJoin = async () => {
              setIsLoading(true);
              try {
                  const joinPayload: ApiGameJoinRequest = {
                       game_code: gameCode,
                       display_name: currentUserDisplayName
                  };
                  const sessionData = await joinGameSession(joinPayload, currentUserId);
                  setGameSession(sessionData);
                  // Fetch pack details IF packName wasn't passed (might happen if directly joining via URL)
                  if (!packName && sessionData.pack_id) {
                       // Ideally, fetch pack name here based on sessionData.pack_id
                       // For now, we'll rely on it potentially being passed or fallback
                       console.warn("Pack name not available for joined Scallywag initially.");
                       // You might need an API call to get pack details based on ID here
                       // setPackName(fetchedPackName);
                  }
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
  // Add packName to dependency array
  }, [role, gameCode, currentUserId, currentUserDisplayName, joinAttempted, navigate, startParticipantPolling, gameSession, packName]);

  // Cleanup polling on component unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);


  // --- Game Start Logic ---
  const handleStartGame = async () => {
    // Check if the game can be started (captain, valid session, enough players)
    // *** MODIFICATION: Check crewMembers.length >= 2 for crew games ***
    if (!gameSession?.id || !currentUserId || gameSession.id.startsWith('unknown') || (gameCode && crewMembers.length < 2)) {
      if (gameCode && crewMembers.length < 2) {
          toast.error("Need More Crew!", { description: "At least one other pirate must join before you can set sail." });
      } else {
          toast.error("Error", { description: "Cannot start game. Missing game or user information." });
      }
      return;
    }
    // Stop polling before starting
    if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
        console.log("Stopped polling before starting game.");
    }
    setIsLoading(true);
    try {
        const currentSession = gameSession; // Use captured session
        const startResponse = await startGame(currentSession.id, currentUserId);
        if (startResponse.status === 'active') {
            navigate(`/countdown`, {
              state: {
                gameId: currentSession.id,
                totalQuestions: currentSession.question_count,
                packName: packName // <-- ADD packName here
              }
            });
        } else {
            throw new Error(`Backend reported unexpected status after start: ${startResponse.status}`);
        }
    } catch (error) {
        console.error("Failed to start game:", error);
        const errorMsg = error instanceof Error ? error.message : "Could not start the game.";
        toast.error("Start Failed", { description: errorMsg });
        startParticipantPolling(gameSession.id); // Restart polling if start fails
    } finally {
        setIsLoading(false);
    }
  };

  // --- Edit Name Logic ---
  const handleOpenEditModal = () => {
    if (currentUserDisplayName) {
        editNameForm.setValue('newName', currentUserDisplayName);
    }
    setIsEditModalOpen(true);
  };

  const handleEditNameSubmit = async (data: EditNameFormValues) => {
    if (!currentUserId) {
        toast.error("Error", { description: "Cannot update name. User ID missing." });
        return;
    }
    const newName = data.newName.trim();
    if (!newName || newName === currentUserDisplayName) {
        setIsEditModalOpen(false);
        return;
    }

    setIsUpdatingName(true);
    try {
        await updateUser(currentUserId, { displayname: newName });
        setCurrentUserDisplayName(newName);
        localStorage.setItem('tempUserDisplayName', newName);
        setCrewMembers(prevCrew =>
            prevCrew.map(member =>
                member.user_id === currentUserId
                ? { ...member, display_name: newName }
                : member
            )
        );
        toast.success("Name Changed!", { description: `Ye be known as ${newName} now!` });
        setIsEditModalOpen(false);

    } catch (error) {
        console.error("Failed to update name:", error);
        toast.error("Update Failed", { description: error instanceof Error ? error.message : "Could not change your name." });
        setIsEditModalOpen(false);
    } finally {
        setIsUpdatingName(false);
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
     if (role === 'captain') return `/crew`;
     if (role === 'scallywag') return `/crew`;
     // Solo mode shouldn't reach here now, but keep a fallback
     return '/';
  };

  // --- Derived Data ---
  const hostParticipant = crewMembers.find(p => p.is_host);
  const isCurrentUserHost = currentUserId === hostParticipant?.user_id;
  const hostDisplayName = hostParticipant?.display_name || 'The Captain';

  // --- Use packName from state for display ---
  const displayCategory = packName || categoryParam?.replace(/-/g, ' ') || 'Unknown Pack'; // Prioritize state packName
  const displayQuestions = gameSession?.question_count ?? questionsParam ?? 'N/A';
  const displayTime = gameSession?.time_limit_seconds ?? timeParam ?? 'N/A';
  const settingsAvailable = !!gameSession;
  const canStartGame = settingsAvailable && !isLoading && isCurrentUserHost && crewMembers.length >= 2; // *** ADDED crewMembers.length check ***

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
           {/* Loading Overlay for Initial Join/Load */}
           {(isLoading && !gameSession && role !== 'solo') && (
               <div className="absolute inset-0 bg-pirate-parchment/80 flex items-center justify-center rounded-xl z-20">
                   <Loader2 className="h-8 w-8 animate-spin text-pirate-navy" />
                   <span className="ml-2 font-semibold text-pirate-navy">{role === 'scallywag' ? 'Joining Crew...' : 'Setting Course...'}</span>
               </div>
           )}

          {/* Player List */}
          <div className="mb-8">
            <div className='flex justify-between items-center mb-6'>
                <h2 className="font-pirate text-3xl md:text-4xl text-pirate-navy">
                  {gameCode ? `Crew Members (${gameSession?.participant_count ?? crewMembers.length})` : 'Your Voyage'}
                </h2>
                {gameCode && ( // Only show refresh for crew games
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
                {crewMembers.map((member) => {
                  const isYou = member.user_id === currentUserId;
                  return (
                    <Card
                      key={member.id || member.user_id}
                      className={cn(
                        "p-4 flex items-center space-x-3 border-pirate-navy/20 shadow-md relative",
                        isYou && "bg-pirate-navy text-white border-pirate-gold border-2"
                      )}
                    >
                      <PlayerAvatar playerId={member.user_id} name={member.display_name} size="md" />
                      <div className="flex-1 overflow-hidden">
                        <p className={cn(
                            "font-medium truncate",
                            isYou ? "text-white" : "text-pirate-navy"
                          )}
                        >
                          {member.display_name}
                        </p>
                        {gameCode && (
                          <p className={cn( "text-xs", isYou ? "text-white/80" : "text-pirate-navy/70" )}>
                            {member.is_host ? 'Captain' : 'Crew Member'} {isYou ? '(You)' : ''}
                          </p>
                        )}
                      </div>
                      {isYou && gameCode && (
                         <Button
                           variant="ghost"
                           size="icon"
                           className="shrink-0 h-6 w-6 text-white/70 hover:text-white hover:bg-white/10 p-0"
                           onClick={handleOpenEditModal}
                           aria-label="Edit name"
                           disabled={isUpdatingName}
                         >
                           <Pencil className="h-4 w-4" />
                         </Button>
                       )}
                    </Card>
                  )
                 })}
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
             isCurrentUserHost ? ( // Captain's view
                <div className="mt-10">
                  {/* *** MODIFIED: Added disabled condition crewMembers.length < 2 *** */}
                  <PirateButton onClick={handleStartGame} className="w-full py-3 text-lg" variant="accent" disabled={!settingsAvailable || crewMembers.length < 2 || isLoading} >
                    {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Anchor className="h-5 w-5" />}
                    {isLoading ? 'Starting...' : 'All aboard? Set sail!'}
                  </PirateButton>
                  {!settingsAvailable && <p className="text-xs text-center mt-2 text-pirate-navy/60">Waiting for voyage details...</p>}
                  {/* *** MODIFIED: Added waiting for crew message *** */}
                  {settingsAvailable && !isLoading && crewMembers.length < 2 && <p className="text-xs text-center mt-2 text-pirate-navy/60">Waiting for at least one crew member to join...</p>}
                </div>
              ) : ( // Scallywag's view
                <div className="mt-10 text-center text-pirate-navy/80">
                  <p>Waiting for {hostDisplayName} to start the voyage...</p>
                  <div className="animate-pulse mt-2 text-2xl">⚓️</div>
                </div>
              )
            ) : null /* Solo Mode Start Button Removed */
           }
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
                      <p className="font-medium capitalize">{displayCategory}</p> {/* Use displayCategory */}
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

       {/* --- Edit Name Dialog --- */}
        <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
            <DialogContent className="sm:max-w-[425px] bg-pirate-parchment border-pirate-wood">
            <DialogHeader>
                <DialogTitle className="font-pirate text-pirate-navy text-2xl">Change Yer Pirate Name</DialogTitle>
            </DialogHeader>
            <Form {...editNameForm}>
                <form onSubmit={editNameForm.handleSubmit(handleEditNameSubmit)} className="space-y-4 py-4">
                <FormField
                    control={editNameForm.control}
                    name="newName"
                    rules={{
                    required: "A pirate needs a name!",
                    maxLength: { value: 18, message: "Name be too long! (Max 18 chars)" },
                    minLength: { value: 1, message: "Name cannot be empty." }
                    }}
                    render={({ field }) => (
                    <FormItem>
                        <Label htmlFor="newName" className="text-left text-pirate-navy/90">New Name</Label>
                        <FormControl>
                         <Input
                           id="newName"
                           {...field}
                           className="border-pirate-navy/30 focus-visible:ring-pirate-gold"
                           maxLength={18}
                           autoComplete="off"
                         />
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                    )}
                />
                <DialogFooter>
                    <PirateButton type="submit" variant="primary" disabled={isUpdatingName}>
                    {isUpdatingName ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    Change Name
                    </PirateButton>
                </DialogFooter>
                </form>
            </Form>
            </DialogContent>
        </Dialog>
       {/* --- End Edit Name Dialog --- */}

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