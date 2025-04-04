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
import { Player } from '@/types/gameTypes'; // Keep this if used indirectly or needed later
import { joinGameSession, getGameParticipants, startGame } from '@/services/gameApi'; // Keep API calls for initial join/start
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

// --- WebSocket Imports ---
import { useWebSocket } from '@/hooks/useWebSocket';
import { IncomingWsMessage } from '@/types/websocketTypes';
// --- End WebSocket Imports ---

// Remove polling interval constant
// const POLLING_INTERVAL = 5000;

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
  const [isLoading, setIsLoading] = useState(true); // Used for initial join/load and game start
  // const [isFetchingParticipants, setIsFetchingParticipants] = useState(false); // No longer needed for polling
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [currentUserDisplayName, setCurrentUserDisplayName] = useState<string | null>(null);
  const [joinAttempted, setJoinAttempted] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isUpdatingName, setIsUpdatingName] = useState(false);
  const [packName, setPackName] = useState<string | null>(null); // Keep packName state

  // Refs - Remove polling ref
  // const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const gameSessionRef = useRef(gameSession); // Keep for accessing latest session state in callbacks

  // Form Hook (Unchanged)
  const editNameForm = useForm<EditNameFormValues>({ defaultValues: { newName: '' } });

  // --- WebSocket Message Handler ---
  const handleWebSocketMessage = useCallback((message: IncomingWsMessage) => {
    console.log("Received WebSocket Message:", message.type, message.payload);
    switch (message.type) {
      case 'participant_update': {
        const updatedParticipant = message.payload;
        setCrewMembers(prev => {
          const existingIndex = prev.findIndex(p => p.user_id === updatedParticipant.user_id);
          if (existingIndex > -1) {
            // Update existing participant (e.g., name change)
            const newCrew = [...prev];
            newCrew[existingIndex] = { ...newCrew[existingIndex], ...updatedParticipant }; // Merge updates
            return newCrew;
          } else {
            // Add new participant
            return [...prev, updatedParticipant];
          }
        });
        // Update current user's display name if it changed
        if (updatedParticipant.user_id === currentUserId && updatedParticipant.display_name !== currentUserDisplayName) {
          console.log(`Updating current user name via WS: ${updatedParticipant.display_name}`);
          setCurrentUserDisplayName(updatedParticipant.display_name);
          localStorage.setItem('tempUserDisplayName', updatedParticipant.display_name);
        }
        break;
      }
      case 'participant_left': {
        const { user_id } = message.payload;
        setCrewMembers(prev => prev.filter(p => p.user_id !== user_id));
        toast.info(`${message.payload.display_name} left the crew.`);
        break;
      }
      case 'user_name_updated': { // Can likely remove this if participant_update handles it, but keep for robustness
         const { user_id, new_display_name } = message.payload;
         setCrewMembers(prev => prev.map(p => p.user_id === user_id ? { ...p, display_name: new_display_name } : p));
         if (user_id === currentUserId) {
           setCurrentUserDisplayName(new_display_name);
           localStorage.setItem('tempUserDisplayName', new_display_name);
         }
         break;
      }
      case 'game_started': {
        const { game_id, total_questions } = message.payload;
        console.log(`Game ${game_id} started via WebSocket!`);
        toast.success("Game Started!", { description: "Get ready to answer!" });
        // Navigate to countdown, passing necessary state
        navigate(`/countdown`, {
          state: {
            gameId: game_id,
            packName: packName, // Pass packName from component state
            totalQuestions: total_questions,
            // Optionally pass gameSession details if needed by countdown/gameplay
            gameSession: message.payload // Pass the full payload if helpful
          }
        });
        break;
      }
      case 'game_cancelled': {
        toast.error("Game Cancelled", { description: "The Captain has cancelled the game." });
        // Navigate back or disable interactions
        navigate(getBackLink());
        break;
      }
      case 'error': {
        toast.error("Server Error", { description: message.payload.message });
        break;
      }
      default:
        console.warn("Received unknown WebSocket message type:", message.type);
    }
  }, [currentUserId, currentUserDisplayName, navigate, packName]); // Include packName

  // --- Initialize WebSocket Connection ---
  const { status: wsStatus } = useWebSocket({
    gameId: gameSession?.id && !gameSession.id.startsWith('unknown') ? gameSession.id : null, // Only connect with a valid game ID
    userId: currentUserId,
    onMessage: handleWebSocketMessage,
    onOpen: () => {
        console.log("WebSocket connected callback triggered.");
        // Fetch initial participant list upon connection
        if (gameSession?.id && !gameSession.id.startsWith('unknown')) {
             fetchParticipants(gameSession.id);
        }
    },
    onClose: (event) => console.log("WebSocket closed callback:", event.code),
    onError: (event) => toast.error("Connection Error", { description: "Lost connection to the game server." }),
  });

  // --- User Initialization Effect (Unchanged) ---
  useEffect(() => {
    const storedUserId = localStorage.getItem('tempUserId');
    const storedName = localStorage.getItem('tempUserDisplayName');
    if (!storedUserId) {
      console.error("Waiting Room: tempUserId not found in localStorage!");
      toast.error("Session Error", { description: "Could not find your user ID. Please go back."});
      navigate('/crew'); // Go back if no user ID
    } else {
      setCurrentUserId(storedUserId);
      const nameToSet = storedName || getPirateNameForUserId(storedUserId);
      setCurrentUserDisplayName(nameToSet);
      editNameForm.setValue('newName', nameToSet);
    }
  }, [navigate, editNameForm]); // Removed role as it's not needed here

  // --- Initialize Captain/Solo state from location (Mostly Unchanged) ---
  useEffect(() => {
      const stateFromNavigation = location.state as { gameSession?: ApiGameSessionResponse, packName?: string } | undefined;
      if (role === 'captain' && currentUserId && currentUserDisplayName && !gameSession) {
          setIsLoading(true); // Start loading for captain init
          if (stateFromNavigation?.gameSession && stateFromNavigation.gameSession.code === gameCode) {
              console.log("Captain: Initializing with gameSession from navigation state:", stateFromNavigation);
              setGameSession(stateFromNavigation.gameSession);
              setPackName(stateFromNavigation.packName || 'Unknown Pack');
              setCrewMembers([{ id: 'captain-participant-' + currentUserId, user_id: currentUserId, display_name: currentUserDisplayName, score: 0, is_host: true }]);
              // Fetch initial participants maybe, but WS onOpen will also fetch
              fetchParticipants(stateFromNavigation.gameSession.id);
          } else {
              console.warn("Captain: gameSession missing/mismatched in navigation state.");
              // Consider if captain should *always* have a session from GameSelect
              toast.error("Game Error", { description: "Could not load game session details." });
              navigate('/crew'); // Go back if session is missing
          }
          setIsLoading(false); // Finish loading after captain init
      } else if (role !== 'captain' && !gameSession && location.state?.packName) {
          // Preserve pack name if passed to scallywag via state (e.g., deep link scenario)
          setPackName(location.state.packName);
      }
  // location.state added
  }, [role, gameCode, currentUserId, currentUserDisplayName, gameSession, navigate, location.state, fetchParticipants]);


  // --- Scallywag Join Game Logic (Modified: Fetch participants after join) ---
  useEffect(() => {
      if (role === 'scallywag' && gameCode && currentUserId && currentUserDisplayName && !joinAttempted && !gameSession) {
          setJoinAttempted(true);
          const performJoin = async () => {
              setIsLoading(true);
              try {
                  const joinPayload: ApiGameJoinRequest = { game_code: gameCode, display_name: currentUserDisplayName };
                  const sessionData = await joinGameSession(joinPayload, currentUserId);
                  setGameSession(sessionData); // Set game session *before* fetching participants/connecting WS
                  // Pack name might come from navigation state or needs fetching
                  if (!packName && location.state?.packName) {
                     setPackName(location.state.packName);
                  } else if (!packName && sessionData.pack_id) {
                     // TODO: Fetch pack details if needed
                     console.warn("Scallywag joined, but pack name needs fetching (not implemented).");
                     setPackName("Pack Loading..."); // Placeholder
                  }
                  // WebSocket connection will be established by the main connect effect now that gameSession.id is set
                  // Fetch initial participants immediately after join success
                  fetchParticipants(sessionData.id);
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
  }, [role, gameCode, currentUserId, currentUserDisplayName, joinAttempted, navigate, gameSession, packName, location.state, fetchParticipants]); // Add fetchParticipants


  // --- Game Start Logic (Modified: Relies on WS for navigation trigger) ---
  const handleStartGame = async () => {
    if (!gameSession?.id || !currentUserId || gameSession.id.startsWith('unknown')) {
      toast.error("Error", { description: "Cannot start game. Missing game or user information." });
      return;
    }
    // Crew Game: Check participant count
    if (gameCode && crewMembers.length < 2) {
        toast.error("Need More Crew!", { description: "At least one other pirate must join before you can set sail." });
        return;
    }

    setIsLoading(true); // Show loading on the start button
    try {
        // Call the API to *request* the start
        await startGame(gameSession.id, currentUserId);
        // DO NOT NAVIGATE HERE. Wait for the 'game_started' WebSocket message.
        console.log("Start game request sent successfully. Waiting for WebSocket confirmation...");
        // Optionally disable button further or show a "Starting..." state locally
    } catch (error) {
        console.error("Failed to send start game request:", error);
        const errorMsg = error instanceof Error ? error.message : "Could not start the game.";
        toast.error("Start Failed", { description: errorMsg });
        setIsLoading(false); // Re-enable button if API call failed
    }
    // Note: setIsLoading(false) is handled implicitly when navigation occurs via WebSocket message
  };

  // --- Edit Name Logic (Modified: Use WS broadcast indirectly via user service) ---
  const handleEditNameSubmit = async (data: EditNameFormValues) => {
    if (!currentUserId) { toast.error("Error", { description: "Cannot update name. User ID missing." }); return; }
    const newName = data.newName.trim();
    if (!newName || newName === currentUserDisplayName) { setIsEditModalOpen(false); return; }

    setIsUpdatingName(true);
    try {
        // Update backend (this service call now handles WS broadcast)
        await updateUser(currentUserId, { displayname: newName });
        // Update local state immediately for responsiveness
        setCurrentUserDisplayName(newName);
        localStorage.setItem('tempUserDisplayName', newName);
        // Update name in the local crew list as well
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
        setIsEditModalOpen(false); // Close modal even on error
    } finally {
        setIsUpdatingName(false);
    }
  };


  // --- Helper Functions (Unchanged) ---
  const copyGameCodeToClipboard = () => { if (gameCode) { navigator.clipboard.writeText(gameCode).then(() => toast.success('Copied!')).catch(() => toast.error('Copy failed')); } };
  const getBackLink = () => role === 'captain' || role === 'scallywag' ? '/crew' : '/';
  const handleOpenEditModal = () => { if (currentUserDisplayName) { editNameForm.setValue('newName', currentUserDisplayName); } setIsEditModalOpen(true); };


  // --- Derived Data (Mostly Unchanged) ---
  const hostParticipant = crewMembers.find(p => p.is_host);
  const isCurrentUserHost = currentUserId === hostParticipant?.user_id;
  const hostDisplayName = hostParticipant?.display_name || 'The Captain';
  const displayCategory = packName || 'Unknown Pack';
  const displayQuestions = gameSession?.question_count ?? 'N/A';
  const displayTime = gameSession?.time_limit_seconds ?? 'N/A';
  const settingsAvailable = !!gameSession && !gameSession.id.startsWith('unknown');
  // Modify canStartGame check for crew mode
  const canStartGame = settingsAvailable && !isLoading && isCurrentUserHost && (role === 'captain' ? crewMembers.length >= 2 : true);


  // --- Render Logic (Mostly Unchanged structure, some conditional text updates) ---
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
           {(isLoading && !gameSession && role !== 'captain') && ( // Show loading only if not captain and no session yet
               <div className="absolute inset-0 bg-pirate-parchment/80 flex items-center justify-center rounded-xl z-20">
                   <Loader2 className="h-8 w-8 animate-spin text-pirate-navy" /><span className="ml-2 font-semibold text-pirate-navy">{role === 'scallywag' ? 'Joining Crew...' : 'Loading...'}</span>
               </div>
           )}

          {/* Player List */}
          <div className="mb-8">
            <div className='flex justify-between items-center mb-6'>
              <h2 className="font-pirate text-3xl md:text-4xl text-pirate-navy">Crew Members ({crewMembers.length})</h2>
              {/* Refresh button removed - relies on WS now */}
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
             {/* Placeholder/Waiting messages */}
             {crewMembers.length === 0 && role === 'scallywag' && (<div className="col-span-full text-center py-4"><p className="text-pirate-navy/60">Waiting for the Captain and crew...</p></div>)}
             {crewMembers.length <= 1 && role === 'captain' && (<div className="col-span-full text-center py-4"><p className="text-pirate-navy/60">Waiting for crew to join...</p></div>)}
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

        {/* Collapsible Voyage Details (Unchanged) */}
        {settingsAvailable && (
          <Collapsible open={isVoyageDetailsOpen} onOpenChange={setIsVoyageDetailsOpen} className="mb-8">
            <Card className="p-4 flex items-center min-h-[60px] bg-pirate-parchment/50"><CollapsibleTrigger className="flex items-center justify-between w-full"><div className="flex items-center gap-2"> <Settings className="h-5 w-5 text-pirate-black" /> <h3 className="font-pirate text-2xl text-pirate-black">Voyage Details</h3> </div><ChevronDown className={`h-5 w-5 transition-transform duration-200 ${isVoyageDetailsOpen ? 'rotate-180' : ''}`} /></CollapsibleTrigger></Card>
            <CollapsibleContent className="mt-2"><Card className="p-6"><div className="grid grid-cols-1 md:grid-cols-3 gap-4"><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Category</p><p className="font-medium capitalize">{displayCategory}</p></div><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Questions</p><p className="font-medium">{displayQuestions}</p></div><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Time per Question</p><p className="font-medium">{displayTime ? `${displayTime} seconds` : 'N/A'}</p></div></div></Card></CollapsibleContent>
          </Collapsible>
        )}
      </main>

      {/* Edit Name Dialog (Unchanged) */}
      <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
        <DialogContent className="sm:max-w-[425px] bg-pirate-parchment border-pirate-wood"><DialogHeader><DialogTitle className="font-pirate text-pirate-navy text-2xl">Change Yer Pirate Name</DialogTitle></DialogHeader>
          <Form {...editNameForm}><form onSubmit={editNameForm.handleSubmit(handleEditNameSubmit)} className="space-y-4 py-4">
            <FormField control={editNameForm.control} name="newName" rules={{ required: "A pirate needs a name!", maxLength: { value: 18, message: "Name be too long! (Max 18 chars)" }, minLength: { value: 1, message: "Name cannot be empty." } }} render={({ field }) => (<FormItem><Label htmlFor="newName" className="text-left text-pirate-navy/90">New Name</Label><FormControl><Input id="newName" {...field} className="border-pirate-navy/30 focus-visible:ring-pirate-gold" maxLength={18} autoComplete="off" /></FormControl><FormMessage /></FormItem>)} />
            <DialogFooter><PirateButton type="submit" variant="primary" disabled={isUpdatingName}>{isUpdatingName ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null} Change Name</PirateButton></DialogFooter>
          </form></Form>
        </DialogContent>
      </Dialog>

      {/* Footer (Unchanged) */}
      <footer className="ocean-bg py-8"><div className="container mx-auto text-center text-white relative z-10"><p className="font-pirate text-xl mb-2">Ready the cannons!</p><p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p></div></footer>
    </div>
  );
};

export default WaitingRoom;
// --- END OF FULL MODIFIED FILE ---