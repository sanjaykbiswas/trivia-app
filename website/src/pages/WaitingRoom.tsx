// website/src/pages/WaitingRoom.tsx
// --- START OF FULL MODIFIED FILE ---
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams, useSearchParams, Link, useLocation } from 'react-router-dom';
import { Users, Copy, Anchor, ArrowLeft, ChevronDown, Settings, Loader2, RefreshCw, Pencil } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import PlayerAvatar from '@/components/PlayerAvatar';
// Keep Player type if used
// import { Player } from '@/types/gameTypes';
import { joinGameSession, getGameParticipants, startGame } from '@/services/gameApi';
import { updateUser } from '@/services/userApi';
import { getPirateNameForUserId } from '@/utils/gamePlayUtils';
import { ApiParticipant, ApiGameSessionResponse, ApiGameJoinRequest } from '@/types/apiTypes';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useForm } from "react-hook-form";
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form";

// WebSocket Imports
import { useWebSocket } from '@/hooks/useWebSocket';
import { IncomingWsMessage } from '@/types/websocketTypes';

interface EditNameFormValues {
  newName: string;
}

const WaitingRoom: React.FC = () => {
  const { role } = useParams<{ role?: string }>();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const gameCode = searchParams.get('gameCode');
  const navigate = useNavigate();

  // State
  const [gameSession, setGameSession] = useState<ApiGameSessionResponse | null>(null);
  const [crewMembers, setCrewMembers] = useState<ApiParticipant[]>([]);
  const [isVoyageDetailsOpen, setIsVoyageDetailsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [currentUserDisplayName, setCurrentUserDisplayName] = useState<string | null>(null);
  const [joinAttempted, setJoinAttempted] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isUpdatingName, setIsUpdatingName] = useState(false);
  const [packName, setPackName] = useState<string | null>(null);

  // Refs
  const gameSessionRef = useRef(gameSession);
   useEffect(() => { gameSessionRef.current = gameSession; }, [gameSession]); // Keep ref updated

  // Form Hook
  const editNameForm = useForm<EditNameFormValues>({ defaultValues: { newName: '' } });

  // --- Function to fetch participants ---
   const fetchParticipants = useCallback(async (currentGameId: string | undefined) => {
      if (!currentGameId) {
          console.warn("fetchParticipants called without a valid gameId.");
          return;
      }
      console.log(`Fetching participants for game ${currentGameId}...`);
      try {
          const response = await getGameParticipants(currentGameId);
          setCrewMembers(response.participants);
          console.log("Participants fetched:", response.participants);
      } catch (error) {
          console.error("Failed to fetch participants:", error);
           // Avoid repeated toasts if WS is already trying to reconnect
           // We can check wsStatus here if needed, or just be less aggressive with toasts
           // For simplicity, let's only toast if the error is *not* a network error likely caused by WS disconnect
           if (!(error instanceof Error && error.message.toLowerCase().includes('networkerror'))) {
             toast.error("Sync Error", { description: "Could not update participant list." });
           }
      }
  // Removed wsStatus dependency - fetch is triggered by WS onOpen or join logic now
  }, []);


  // --- WebSocket Message Handler ---
   const handleWebSocketMessage = useCallback((message: IncomingWsMessage) => {
    console.log("Received WebSocket Message:", message.type, message.payload);
    switch (message.type) {
      case 'participant_update': {
        const updatedParticipant = message.payload;
        setCrewMembers(prev => {
          const existingIndex = prev.findIndex(p => p.user_id === updatedParticipant.user_id);
          if (existingIndex > -1) {
            const newCrew = [...prev];
            newCrew[existingIndex] = { ...newCrew[existingIndex], ...updatedParticipant }; // Merge data
            return newCrew;
          } else {
            // Add new participant only if they aren't already visually present (handles potential race conditions)
             if (!prev.some(p => p.user_id === updatedParticipant.user_id)) {
                 return [...prev, updatedParticipant];
             }
             return prev; // Avoid adding duplicate if already present
          }
        });
        // Update current user's display name if it changed
        if (updatedParticipant.user_id === currentUserId && updatedParticipant.display_name !== currentUserDisplayName) {
          console.log(`Updating current user name via WS: ${updatedParticipant.display_name}`);
          setCurrentUserDisplayName(updatedParticipant.display_name);
          localStorage.setItem('tempUserDisplayName', updatedParticipant.display_name);
          editNameForm.setValue('newName', updatedParticipant.display_name); // Update form default
        }
        break;
      }
      case 'participant_left': {
        const { user_id, display_name } = message.payload;
        setCrewMembers(prev => prev.filter(p => p.user_id !== user_id));
        // Only show toast if it wasn't the current user leaving
        if(user_id !== currentUserId) {
           toast.info(`${display_name} left the crew.`);
        }
        break;
      }
      case 'user_name_updated': {
         const { user_id, new_display_name } = message.payload;
         setCrewMembers(prev => prev.map(p => p.user_id === user_id ? { ...p, display_name: new_display_name } : p));
         if (user_id === currentUserId) {
           setCurrentUserDisplayName(new_display_name);
           localStorage.setItem('tempUserDisplayName', new_display_name);
           editNameForm.setValue('newName', new_display_name); // Update form default
         }
         break;
      }
      case 'game_started': {
        const { game_id, total_questions } = message.payload;
        console.log(`Game ${game_id} started via WebSocket! Navigating...`);
        toast.success("Game Started!", { description: "Get ready to answer!" });
        navigate(`/countdown`, {
          state: {
            gameId: game_id,
            packName: packName, // Pass packName
            totalQuestions: total_questions, // Pass total questions
            // gameSession: message.payload // Can pass the whole payload if needed later
          }
        });
        break;
      }
      case 'game_cancelled': {
        toast.error("Game Cancelled", { description: "The Captain has cancelled the game." });
        navigate(getBackLink()); // Use helper for back link
        break;
      }
      case 'error': {
        toast.error("Server Error", { description: message.payload.message });
        break;
      }
      default:
        console.warn("Received unknown WebSocket message type:", message.type);
    }
  // Dependencies: Ensure currentUserDisplayName, currentUserId, navigate, packName, getBackLink are stable or included
  }, [currentUserId, currentUserDisplayName, navigate, packName, editNameForm]); // Removed getBackLink from deps, should be stable

  // --- Initialize WebSocket Connection (Deferred) ---
   const canConnectWebSocket = !!gameSession?.id && !!currentUserId && !gameSession.id.startsWith('unknown');

   const { status: wsStatus } = useWebSocket({
     gameId: canConnectWebSocket ? gameSession.id : null,
     userId: canConnectWebSocket ? currentUserId : null,
     onMessage: handleWebSocketMessage,
     onOpen: () => {
       console.log("WebSocket connected callback triggered.");
       // Fetch initial participants on successful connect
       if (gameSessionRef.current?.id && !gameSessionRef.current.id.startsWith('unknown')) {
         fetchParticipants(gameSessionRef.current.id);
       }
     },
     onClose: (event) => console.log("WebSocket closed callback:", event.code),
     onError: (event) => toast.error("Connection Error", { description: "Lost connection to the game server." }),
   });
   // --- End WebSocket Initialization ---


  // --- User Initialization Effect ---
  useEffect(() => {
    const storedUserId = localStorage.getItem('tempUserId');
    const storedName = localStorage.getItem('tempUserDisplayName');
    if (!storedUserId) {
      console.error("Waiting Room: tempUserId not found in localStorage!");
      toast.error("Session Error", { description: "Could not find your user ID. Please go back."});
      navigate('/crew');
    } else {
      setCurrentUserId(storedUserId);
      const nameToSet = storedName || getPirateNameForUserId(storedUserId);
      setCurrentUserDisplayName(nameToSet);
      editNameForm.setValue('newName', nameToSet); // Set initial form value
    }
  }, [navigate, editNameForm]);

  // --- Initialize Captain/Scallywag state ---
  useEffect(() => {
      const stateFromNavigation = location.state as { gameSession?: ApiGameSessionResponse, packName?: string } | undefined;

      if (role === 'captain' && currentUserId && currentUserDisplayName && !gameSession) {
          if (stateFromNavigation?.gameSession && stateFromNavigation.gameSession.code === gameCode) {
              console.log("Captain: Initializing with gameSession from navigation state:", stateFromNavigation);
              setGameSession(stateFromNavigation.gameSession);
              setPackName(stateFromNavigation.packName || 'Unknown Pack');
              // Set initial crew member (will be updated by WS onOpen)
              setCrewMembers([{ id: 'captain-participant-' + currentUserId, user_id: currentUserId, display_name: currentUserDisplayName, score: 0, is_host: true }]);
              setIsLoading(false);
          } else {
              console.warn("Captain: gameSession missing/mismatched in navigation state.");
              toast.error("Game Error", { description: "Could not load game session details." });
              setIsLoading(false);
              navigate('/crew');
          }
      } else if (role === 'scallywag') {
           // Scallywag waits for join effect
           if (stateFromNavigation?.packName && !packName) {
             setPackName(stateFromNavigation.packName);
           }
      } else if (isLoading && gameSession) {
           // If we were loading and gameSession arrived, stop loading
           setIsLoading(false);
      }
  // Only re-run if essential static info changes or user details become available
  }, [role, gameCode, currentUserId, currentUserDisplayName, gameSession, navigate, location.state, packName, isLoading]);


  // --- Scallywag Join Game Logic ---
  useEffect(() => {
      if (role === 'scallywag' && gameCode && currentUserId && currentUserDisplayName && !gameSession && !joinAttempted) {
          setJoinAttempted(true);
          const performJoin = async () => {
              setIsLoading(true);
              try {
                  const joinPayload: ApiGameJoinRequest = { game_code: gameCode, display_name: currentUserDisplayName };
                  console.log(`Scallywag ${currentUserDisplayName} (${currentUserId}) attempting to join game ${gameCode}`);
                  const sessionData = await joinGameSession(joinPayload, currentUserId);
                  console.log("Join successful, received session data:", sessionData);
                  gameSessionRef.current = sessionData; // Update ref
                  setGameSession(sessionData); // Update state - this will trigger WS connection

                   // Set packName if available from location state, otherwise handle later maybe
                   if (!packName && location.state?.packName) {
                     setPackName(location.state.packName);
                   } else if (!packName && sessionData.pack_id) {
                     console.warn("Scallywag joined, but pack name needs fetching (not implemented).");
                     setPackName("Pack Loading..."); // Placeholder
                   }
                   // Initial participant fetch is now handled by WS onOpen

              } catch (error) {
                  console.error("Failed to join game:", error);
                  const errorMsg = error instanceof Error ? error.message : "Could not join the game.";
                  toast.error("Join Failed", { description: errorMsg });
                  navigate('/crew'); // Send back to role select on join failure
              } finally {
                  setIsLoading(false);
              }
          };
          performJoin();
      }
  // Only trigger join when essential conditions are met and join hasn't been attempted/successful
  }, [role, gameCode, currentUserId, currentUserDisplayName, gameSession, joinAttempted, navigate, packName, location.state]);


  // --- Game Start Logic ---
  const handleStartGame = async () => {
    if (!gameSession?.id || !currentUserId || gameSession.id.startsWith('unknown')) {
      toast.error("Error", { description: "Cannot start game. Missing game or user information." });
      return;
    }
    // Check for >= 2 players ONLY in crew mode (role == captain)
    if (role === 'captain' && gameCode && crewMembers.length < 2) {
        toast.error("Need More Crew!", { description: "At least one other pirate must join before you can set sail." });
        return;
    }

    setIsLoading(true); // Show loading indicator while starting
    try {
        await startGame(gameSession.id, currentUserId);
        // Don't navigate here. Let the 'game_started' WS message handle navigation.
        console.log("Start game request sent successfully. Waiting for WebSocket confirmation...");
        // Optionally disable the start button further here if needed
    } catch (error) {
        console.error("Failed to send start game request:", error);
        const errorMsg = error instanceof Error ? error.message : "Could not start the game.";
        toast.error("Start Failed", { description: errorMsg });
        setIsLoading(false); // Re-enable button on failure
    }
    // Note: setIsLoading(false) is NOT called on success, as we navigate away upon WS confirmation.
  };

  // --- Edit Name Logic ---
  const handleEditNameSubmit = async (data: EditNameFormValues) => {
    if (!currentUserId) { toast.error("Error", { description: "Cannot update name. User ID missing." }); return; }
    const newName = data.newName.trim();
    if (!newName || newName === currentUserDisplayName) { setIsEditModalOpen(false); return; }

    setIsUpdatingName(true);
    try {
        // Update backend first
        await updateUser(currentUserId, { displayname: newName });
        // Update local state & storage immediately for responsiveness
        setCurrentUserDisplayName(newName);
        localStorage.setItem('tempUserDisplayName', newName);
         // Update the crew list locally - WS broadcast will confirm for others
         setCrewMembers(prevCrew =>
            prevCrew.map(member =>
                member.user_id === currentUserId ? { ...member, display_name: newName } : member
            )
         );
        toast.success("Name Changed!", { description: `Ye be known as ${newName} now!` });
        setIsEditModalOpen(false);
    } catch (error) {
        console.error("Failed to update name:", error);
        toast.error("Update Failed", { description: error instanceof Error ? error.message : "Could not change your name." });
        setIsEditModalOpen(false); // Close modal even on failure
    } finally {
        setIsUpdatingName(false);
    }
  };


  // --- Helper Functions ---
  const copyGameCodeToClipboard = () => { if (gameCode) { navigator.clipboard.writeText(gameCode).then(() => toast.success('Copied!')).catch(() => toast.error('Copy failed')); } };
  const getBackLink = () => role === 'captain' || role === 'scallywag' ? '/crew' : '/'; // Simplified
  const handleOpenEditModal = () => { if (currentUserDisplayName) { editNameForm.setValue('newName', currentUserDisplayName); } setIsEditModalOpen(true); };


  // --- Derived Data ---
  const hostParticipant = crewMembers.find(p => p.is_host);
  const isCurrentUserHost = currentUserId === hostParticipant?.user_id;
  const hostDisplayName = hostParticipant?.display_name || 'The Captain';
  const displayCategory = packName || (isLoading ? 'Loading...' : 'Unknown Pack');
  const displayQuestions = gameSession?.question_count ?? (isLoading ? '-' : 'N/A');
  const displayTime = gameSession?.time_limit_seconds ?? (isLoading ? '-' : 'N/A');
  const settingsAvailable = !!gameSession && !isLoading; // Game session loaded and not in general loading state
  // Updated canStartGame logic for crew mode
  const canStartGame = settingsAvailable && !isLoading && isCurrentUserHost && (role === 'captain' ? crewMembers.length >= 2 : true);


  // --- Render Logic ---
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Back Button and Game Code */}
        <div className="flex items-center justify-between mb-6">
          <Link to={getBackLink()} className="flex items-center text-pirate-navy hover:text-pirate-accent"><ArrowLeft className="h-4 w-4 mr-2" /><span>Back</span></Link>
          {gameCode && (
             <div className="flex items-center">
               <Users className="h-4 w-4 mr-2 text-pirate-navy" />
               <span className="text-sm font-mono bg-pirate-navy/10 px-2 py-1 rounded">{gameCode}</span>
               <TooltipProvider><Tooltip><TooltipTrigger asChild><button onClick={copyGameCodeToClipboard} className="ml-2 p-1 text-pirate-navy hover:text-pirate-gold transition-colors rounded-full hover:bg-pirate-navy/10" aria-label="Copy game code"><Copy className="h-4 w-4" /></button></TooltipTrigger><TooltipContent><p>Copy game code</p></TooltipContent></Tooltip></TooltipProvider>
             </div>
          )}
        </div>

        {/* Main Content Area */}
        <div className="map-container p-6 md:p-8 mb-10 relative">
           {(isLoading && !gameSession) && ( // Show loading overlay only if gameSession is not yet loaded
               <div className="absolute inset-0 bg-pirate-parchment/80 flex items-center justify-center rounded-xl z-20">
                   <Loader2 className="h-8 w-8 animate-spin text-pirate-navy" /><span className="ml-2 font-semibold text-pirate-navy">{role === 'scallywag' ? 'Joining Crew...' : 'Loading Game...'}</span>
               </div>
           )}

          {/* Player List */}
          <div className="mb-8">
             <div className='flex justify-between items-center mb-6'>
               <h2 className="font-pirate text-3xl md:text-4xl text-pirate-navy">Crew Members ({crewMembers.length})</h2>
                <TooltipProvider><Tooltip><TooltipTrigger asChild><Button variant="ghost" size="icon" onClick={() => fetchParticipants(gameSession?.id)} className="text-pirate-navy/70 hover:text-pirate-navy hover:bg-pirate-navy/10" aria-label="Refresh crew list"><RefreshCw className="h-5 w-5" /></Button></TooltipTrigger><TooltipContent><p>Refresh Crew List</p></TooltipContent></Tooltip></TooltipProvider>
             </div>
            {/* Participant Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
             {crewMembers.map((member) => {
                const isYou = member.user_id === currentUserId;
                return (
                  <Card key={member.id || member.user_id} className={cn("p-4 flex items-center space-x-3 border-pirate-navy/20 shadow-md relative", isYou && "bg-pirate-navy text-white border-pirate-gold border-2")}>
                    <PlayerAvatar playerId={member.user_id} name={member.display_name} size="md" />
                    <div className="flex-1 overflow-hidden">
                      <p className={cn("font-medium truncate", isYou ? "text-white" : "text-pirate-navy")}>{member.display_name}</p>
                      <p className={cn("text-xs", isYou ? "text-white/80" : "text-pirate-navy/70")}>{member.is_host ? 'Captain' : 'Crew Member'} {isYou ? '(You)' : ''}</p>
                    </div>
                     {isYou && (<Button variant="ghost" size="icon" className="shrink-0 h-6 w-6 text-white/70 hover:text-white hover:bg-white/10 p-0" onClick={handleOpenEditModal} aria-label="Edit name" disabled={isUpdatingName}><Pencil className="h-4 w-4" /></Button>)}
                  </Card>
                );
             })}
              {(crewMembers.length === 0 && !isLoading) && (<p className="col-span-full text-center py-4 text-pirate-navy/60">Waiting for pirates to assemble...</p>)}
            </div>
          </div>

          {/* Start Button / Waiting Message */}
          {role === 'captain' ? (
            <div className="mt-10">
               <PirateButton onClick={handleStartGame} className="w-full py-3 text-lg" variant="accent" disabled={!canStartGame || isLoading}>
                 {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Anchor className="h-5 w-5" />}
                 {isLoading ? 'Starting...' : 'All aboard? Set sail!'}
               </PirateButton>
               {!settingsAvailable && <p className="text-xs text-center mt-2 text-pirate-navy/60">Loading game details...</p>}
               {settingsAvailable && crewMembers.length < 2 && !isLoading && <p className="text-xs text-center mt-2 text-pirate-navy/60">Waiting for at least one crew member to join...</p>}
            </div>
          ) : ( // Scallywag's view
            <div className="mt-10 text-center text-pirate-navy/80">
              <p>Waiting for {hostDisplayName} to start the voyage...</p>
              <div className="animate-pulse mt-2 text-2xl">⚓️</div>
            </div>
          )}
        </div>

        {/* Collapsible Voyage Details */}
        {settingsAvailable && (
          <Collapsible open={isVoyageDetailsOpen} onOpenChange={setIsVoyageDetailsOpen} className="mb-8">
            <Card className="p-4 flex items-center min-h-[60px] bg-pirate-parchment/50"><CollapsibleTrigger className="flex items-center justify-between w-full"><div className="flex items-center gap-2"> <Settings className="h-5 w-5 text-pirate-black" /> <h3 className="font-pirate text-2xl text-pirate-black">Voyage Details</h3> </div><ChevronDown className={`h-5 w-5 transition-transform duration-200 ${isVoyageDetailsOpen ? 'rotate-180' : ''}`} /></CollapsibleTrigger></Card>
            <CollapsibleContent className="mt-2"><Card className="p-6"><div className="grid grid-cols-1 md:grid-cols-3 gap-4"><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Category</p><p className="font-medium capitalize">{displayCategory}</p></div><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Questions</p><p className="font-medium">{displayQuestions}</p></div><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Time per Question</p><p className="font-medium">{displayTime !== 'N/A' ? `${displayTime} seconds` : 'N/A'}</p></div></div></Card></CollapsibleContent>
          </Collapsible>
        )}
      </main>

      {/* Edit Name Dialog */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="sm:max-w-[425px] bg-pirate-parchment border-pirate-wood"><DialogHeader><DialogTitle className="font-pirate text-pirate-navy text-2xl">Change Yer Pirate Name</DialogTitle></DialogHeader>
          <Form {...editNameForm}><form onSubmit={editNameForm.handleSubmit(handleEditNameSubmit)} className="space-y-4 py-4">
            <FormField control={editNameForm.control} name="newName" rules={{ required: "A pirate needs a name!", maxLength: { value: 18, message: "Name be too long! (Max 18 chars)" }, minLength: { value: 1, message: "Name cannot be empty." } }} render={({ field }) => (<FormItem><Label htmlFor="newName" className="text-left text-pirate-navy/90">New Name</Label><FormControl><Input id="newName" {...field} className="border-pirate-navy/30 focus-visible:ring-pirate-gold" maxLength={18} autoComplete="off" /></FormControl><FormMessage /></FormItem>)} />
            <DialogFooter><PirateButton type="submit" variant="primary" disabled={isUpdatingName}>{isUpdatingName ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null} Change Name</PirateButton></DialogFooter>
          </form></Form>
        </DialogContent>
      </Dialog>

      {/* Footer */}
      <footer className="ocean-bg py-8"><div className="container mx-auto text-center text-white relative z-10"><p className="font-pirate text-xl mb-2">Gather yer wits, the voyage awaits!</p><p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p></div></footer>
    </div>
  );
};

export default WaitingRoom;
// --- END OF FULL MODIFIED FILE ---