// website/src/pages/WaitingRoom.tsx
// --- START OF FULL MODIFIED FILE ---
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams, useSearchParams, Link, useLocation } from 'react-router-dom';
import { Users, Copy, Anchor, ArrowLeft, ChevronDown, Settings, Loader2, RefreshCw, Pencil, AlertCircle } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import PlayerAvatar from '@/components/PlayerAvatar';
import { joinGameSession, getGameParticipants, startGame } from '@/services/gameApi';
import { updateUser } from '@/services/userApi';
import { getPirateNameForUserId } from '@/utils/gamePlayUtils';
import { ApiParticipant, ApiGameSessionResponse, ApiGameJoinRequest, ApiUserResponse } from '@/types/apiTypes';
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

// Simple Loading Indicator Component
const LoadingIndicator: React.FC<{ message?: string }> = ({ message = "Loading..." }) => (
  <div className="absolute inset-0 bg-pirate-parchment/80 flex flex-col items-center justify-center rounded-xl z-30">
    <Loader2 className="h-10 w-10 animate-spin text-pirate-navy mb-3" />
    <span className="font-semibold text-pirate-navy">{message}</span>
  </div>
);


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
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [currentUserDisplayName, setCurrentUserDisplayName] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isUpdatingName, setIsUpdatingName] = useState(false);
  const [packName, setPackName] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [initializationError, setInitializationError] = useState<string | null>(null);


  // Refs
  const gameSessionRef = useRef(gameSession);
  useEffect(() => { gameSessionRef.current = gameSession; }, [gameSession]);

  // Form Hook
  const editNameForm = useForm<EditNameFormValues>({ defaultValues: { newName: '' } });

  // --- Function to fetch participants (stable reference) ---
   const fetchParticipants = useCallback(async (currentGameId: string | undefined) => {
      if (!currentGameId) {
          console.warn("fetchParticipants called without a valid gameId.");
          return;
      }
      console.log(`[fetchParticipants] Fetching for game ${currentGameId}...`);
      try {
          const response = await getGameParticipants(currentGameId);
           setCrewMembers(prevCrew => {
               // Create a map of the newly fetched participants for efficient lookup
               const fetchedParticipantsMap = new Map(response.participants.map(p => [p.user_id, p]));
               // Create a map of the current crew members
               const currentCrewMap = new Map(prevCrew.map(p => [p.user_id, p]));
               // Merge: Update existing or add new ones from the fetched data
               fetchedParticipantsMap.forEach((value, key) => {
                   currentCrewMap.set(key, value);
               });
               // Ensure host status is correct (sometimes fetch might lag behind WS update)
               const finalCrew = Array.from(currentCrewMap.values()).map(p => ({
                   ...p,
                   // Re-assert host status based on gameSessionRef if available
                   is_host: p.user_id === gameSessionRef.current?.host_user_id
               }));
               console.log(`[fetchParticipants] Prev count: ${prevCrew.length}, Fetched: ${response.participants.length}, New count: ${finalCrew.length}`);
               return finalCrew;
           });
      } catch (error) {
          console.error("[fetchParticipants] Failed:", error);
           if (!(error instanceof Error && error.message.toLowerCase().includes('networkerror'))) {
               toast.error("Sync Error", { description: "Could not update participant list." });
           }
      }
   // Dependencies: Add gameSessionRef.current?.host_user_id? No, that would make it unstable.
   // Keep it empty, relying on the argument `currentGameId` is correct.
   // Host status correction added inside.
   }, []);


  // --- WebSocket Message Handler (Stable Reference) ---
  // Wrapped handleWebSocketMessage in useCallback
  const handleWebSocketMessage = useCallback((message: IncomingWsMessage) => {
    console.log("Received WebSocket Message:", message.type, message.payload);
    switch (message.type) {
      case 'participant_update': {
        const updatedParticipant = message.payload;
        setCrewMembers(prev => {
          const existingIndex = prev.findIndex(p => p.user_id === updatedParticipant.user_id);
          if (existingIndex > -1) {
            const newCrew = [...prev];
            const score = updatedParticipant.score ?? newCrew[existingIndex].score ?? 0;
            newCrew[existingIndex] = { ...newCrew[existingIndex], ...updatedParticipant, score };
             console.log(`[WS] Updated participant ${updatedParticipant.user_id}`);
            return newCrew;
          } else {
             const score = updatedParticipant.score ?? 0;
              console.log(`[WS] Added participant ${updatedParticipant.user_id}`);
             return [...prev, { ...updatedParticipant, score }];
          }
        });
        if (updatedParticipant.user_id === currentUserId && updatedParticipant.display_name !== currentUserDisplayName) {
          console.log(`[WS] Updating current user name via WS: ${updatedParticipant.display_name}`);
          setCurrentUserDisplayName(updatedParticipant.display_name);
          localStorage.setItem('tempUserDisplayName', updatedParticipant.display_name);
          editNameForm.setValue('newName', updatedParticipant.display_name);
        }
        break;
      }
      case 'participant_left': {
        const { user_id, display_name } = message.payload;
        setCrewMembers(prev => prev.filter(p => p.user_id !== user_id));
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
           editNameForm.setValue('newName', new_display_name);
         }
         break;
      }
      case 'game_started': {
        const { game_id, total_questions } = message.payload;
        console.log(`[WS] Game ${game_id} started! Navigating...`);
        toast.success("Game Started!", { description: "Get ready to answer!" });
        navigate(`/countdown`, {
          state: {
            gameId: game_id,
            packName: packName, // Pass the packName state
            totalQuestions: total_questions,
          }
        });
        break;
      }
      case 'game_cancelled': {
        toast.error("Game Cancelled", { description: "The Captain has cancelled the game." });
        navigate(getBackLink()); // Define getBackLink or replace with static path
        break;
      }
      case 'error': {
        toast.error("Server Error", { description: message.payload.message });
        break;
      }
      default:
        console.warn("Received unknown WebSocket message type:", message.type);
    }
  // Dependencies are crucial for useCallback stability
  }, [currentUserId, currentUserDisplayName, navigate, packName, editNameForm]); // Removed getBackLink


  // --- Consolidated Initialization Effect ---
   useEffect(() => {
       let didCancel = false;
       setInitializationError(null);

       const initialize = async () => {
           console.log("Starting Waiting Room Initialization...");
           // Start initializing IMMEDIATELY upon effect run
           setIsInitializing(true);

           let finalUserId: string | null = null;
           let finalUserName: string | null = null;
           let finalSessionData: ApiGameSessionResponse | null = null;
           let finalPackName: string | null = null;

           try {
               // 1. Get/Verify User ID and Name
               let userId = localStorage.getItem('tempUserId');
               let userName = localStorage.getItem('tempUserDisplayName');

               if (!userId) { throw new Error("User session not found. Please go back."); }
               if (!userName) {
                   userName = getPirateNameForUserId(userId);
                   localStorage.setItem('tempUserDisplayName', userName);
                   console.log(`User name was missing, assigned: ${userName}`);
                   updateUser(userId, { displayname: userName }).catch(err => console.warn("Background name update failed:", err));
               }
               finalUserId = userId;
               finalUserName = userName;
               console.log(`User Initialized: ID=${userId}, Name=${userName}`);

               if (didCancel) return;

               // 2. Handle Game Session based on Role
               const navState = location.state as { gameSession?: ApiGameSessionResponse, packName?: string } | undefined;

               if (role === 'captain') {
                   if (navState?.gameSession?.code === gameCode && navState?.gameSession?.id) {
                       finalSessionData = navState.gameSession;
                       finalPackName = navState.packName || 'Unknown Pack';
                       console.log("Captain: Using game session from navigation state.");
                       setCrewMembers([{ id: 'captain-temp-' + finalUserId, user_id: finalUserId, display_name: finalUserName, score: 0, is_host: true }]);
                   } else {
                       throw new Error("Captain is missing necessary game session data.");
                   }
               } else if (role === 'scallywag' && gameCode) {
                   console.log(`Scallywag: Attempting to join game ${gameCode}...`);
                   const joinPayload: ApiGameJoinRequest = { game_code: gameCode, display_name: userName };
                   finalSessionData = await joinGameSession(joinPayload, userId);
                   if (!finalSessionData?.id) throw new Error("Join response did not contain valid session data.");
                   console.log("Scallywag: Join successful.");
                   finalPackName = navState?.packName || 'Loading Pack...';
                   if (!navState?.packName && finalSessionData.pack_id) { console.warn(`Scallywag joined, pack name not in nav state. Pack ID: ${finalSessionData.pack_id}`); }
                   setCrewMembers([]);
               } else {
                   throw new Error(`Invalid role ('${role}') or missing game code for Scallywag.`);
               }

               if (didCancel) return;

               // 3. Set ALL state variables together AFTER successful async operations
               console.log("Initialization successful, setting final state.");
               setCurrentUserId(finalUserId);
               setCurrentUserDisplayName(finalUserName);
               editNameForm.setValue('newName', finalUserName);
               setGameSession(finalSessionData);
               gameSessionRef.current = finalSessionData;
               setPackName(finalPackName);

           } catch (error) {
                console.error("Initialization Error:", error);
                const errorMsg = error instanceof Error ? error.message : "Could not initialize the game room.";
                if (!didCancel) {
                    setInitializationError(errorMsg);
                    toast.error("Error", { description: errorMsg });
                    // Optional: navigate back only after setting error
                    // navigate(getBackLink());
                }
           } finally {
                // Set initializing false ONLY when initialization attempt is fully complete (success or fail)
                if (!didCancel) {
                    setIsInitializing(false);
                    console.log("Waiting Room Initialization Attempt Finished.");
                }
           }
       };

       initialize();

       return () => {
           didCancel = true;
           console.log("Waiting Room Initialization Effect Cleanup.");
       };
   }, [role, gameCode, navigate, location.state, editNameForm]); // Dependencies seem correct


  // --- Define onOpen Callback with useCallback ---
   const handleWebSocketOpen = useCallback(() => {
       console.log("[handleWebSocketOpen] WebSocket connected callback triggered.");
       // Fetch initial list of participants now that connection is open
       // Use the ref as state might not be updated yet in this callback closure
       if (gameSessionRef.current?.id) {
           console.log(`[handleWebSocketOpen] Calling fetchParticipants for game ${gameSessionRef.current.id}`);
           fetchParticipants(gameSessionRef.current.id);
       } else {
           console.warn("[handleWebSocketOpen] WS opened but gameSessionRef.current.id is missing.");
       }
   // Ensure fetchParticipants is stable (it has `[]` deps currently, which is okay)
   }, [fetchParticipants]);

  // --- Initialize WebSocket Connection ---
  // Pass stable IDs only when initialization is complete and successful
   const wsGameId = !isInitializing && !initializationError ? gameSession?.id : null;
   const wsUserId = !isInitializing && !initializationError ? currentUserId : null;

   const { status: wsStatus } = useWebSocket({
     gameId: wsGameId,
     userId: wsUserId,
     onMessage: handleWebSocketMessage, // Stable callback
     onOpen: handleWebSocketOpen,       // Stable callback
     onClose: (event) => console.log("Waiting Room WebSocket closed:", event.code),
     onError: (event) => {
          console.error("WebSocket connection error reported in WaitingRoom:", event);
          // Toasting is handled within the hook's handleClose based on retry logic
          // toast.warning("Connection Issue", { description: "Having trouble communicating..." });
     }
   });
   // --- End WebSocket Initialization ---


  // --- Other Handlers ---
  const handleStartGame = async () => {
    // No change needed here
    if (!gameSession?.id || !currentUserId) { toast.error("Error", { description: "Cannot start game. Missing info." }); return; }
    if (role === 'captain' && gameCode && crewMembers.length < 1) { toast.error("Need More Crew!", { description: "Usually, at least one other pirate must join." }); return; }
    setIsInitializing(true); // Use initializing state for loading
    try { await startGame(gameSession.id, currentUserId); }
    catch (error) { console.error("Start game error:", error); toast.error("Start Failed", { description: error instanceof Error ? error.message : "Could not start." }); setIsInitializing(false); }
  };

  const handleEditNameSubmit = async (data: EditNameFormValues) => {
     // No change needed here
    if (!currentUserId) { toast.error("Error", { description: "Cannot update name. User ID missing." }); return; }
    const newName = data.newName.trim();
    if (!newName || newName === currentUserDisplayName) { setIsEditModalOpen(false); return; }
    setIsUpdatingName(true);
    try { await updateUser(currentUserId, { displayname: newName }); toast.success("Name Change Sent!"); setIsEditModalOpen(false); }
    catch (error) { console.error("Update name error:", error); toast.error("Update Failed", { description: error instanceof Error ? error.message : "Could not change name." }); }
    finally { setIsUpdatingName(false); }
  };

  const copyGameCodeToClipboard = () => { if (gameCode) { navigator.clipboard.writeText(gameCode).then(() => toast.success('Copied!')).catch(() => toast.error('Copy failed')); } };
  // Define getBackLink within the component or ensure it's stable if imported
  const getBackLink = useCallback(() => role === 'captain' || role === 'scallywag' ? '/crew' : '/', [role]);
  const handleOpenEditModal = () => { if (currentUserDisplayName) { editNameForm.setValue('newName', currentUserDisplayName); } setIsEditModalOpen(true); };


  // --- Derived Data ---
  const hostParticipant = crewMembers.find(p => p.is_host);
  const isCurrentUserHost = currentUserId === hostParticipant?.user_id;
  const hostDisplayName = hostParticipant?.display_name || 'The Captain';
  const displayCategory = packName || (isInitializing ? 'Loading...' : 'Unknown Pack');
  const displayQuestions = gameSession?.question_count ?? (isInitializing ? '-' : 'N/A');
  const displayTime = gameSession?.time_limit_seconds ?? (isInitializing ? '-' : 'N/A');
  // Allow starting with 1+ for captain testing
  const canStartGame = !isInitializing && gameSession && isCurrentUserHost && (role === 'captain' ? crewMembers.length >= 1 : true);


  // --- Render Logic ---
  if (initializationError) {
      return (
          <div className="min-h-screen flex flex-col items-center justify-center p-4">
              <Card className="p-6 text-center border-destructive bg-destructive/10">
                  <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-destructive mb-2">Avast Ye, Landlubber!</h2>
                  <p className="text-destructive/80 mb-4">{initializationError}</p>
                  <PirateButton onClick={() => navigate(getBackLink())} variant="secondary">Return to Port</PirateButton>
              </Card>
          </div>
      );
  }

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
           {isInitializing && <LoadingIndicator message={role === 'scallywag' ? 'Joining Crew...' : 'Setting Course...'} />}

          {/* Player List */}
          <div className="mb-8">
             <div className='flex justify-between items-center mb-6'>
               <h2 className="font-pirate text-3xl md:text-4xl text-pirate-navy">Crew Members ({crewMembers.length})</h2>
                <TooltipProvider><Tooltip><TooltipTrigger asChild><Button variant="ghost" size="icon" onClick={() => fetchParticipants(gameSession?.id)} className="text-pirate-navy/70 hover:text-pirate-navy hover:bg-pirate-navy/10" aria-label="Refresh crew list" disabled={isInitializing || wsStatus !== 'connected'}><RefreshCw className={`h-5 w-5 ${wsStatus === 'connected' ? 'hover:animate-spin' : ''}`} /></Button></TooltipTrigger><TooltipContent><p>{wsStatus === 'connected' ? 'Refresh Crew List' : 'Connecting...'}</p></TooltipContent></Tooltip></TooltipProvider>
             </div>
            {/* Participant Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 min-h-[80px]"> {/* Added min-height */}
             {crewMembers.map((member) => {
                const isYou = member.user_id === currentUserId;
                return (
                  <Card key={member.id || member.user_id} className={cn("p-4 flex items-center space-x-3 border-pirate-navy/20 shadow-md relative", isYou && "bg-pirate-navy text-white border-pirate-gold border-2")}>
                    <PlayerAvatar playerId={member.user_id} name={member.display_name} size="md" />
                    <div className="flex-1 overflow-hidden">
                      <p className={cn("font-medium truncate", isYou ? "text-white" : "text-pirate-navy")}>{member.display_name}</p>
                      <p className={cn("text-xs", isYou ? "text-white/80" : "text-pirate-navy/70")}>{member.is_host ? 'Captain' : 'Crew Member'} {isYou ? '(You)' : ''}</p>
                    </div>
                     {isYou && (<Button variant="ghost" size="icon" className="shrink-0 h-6 w-6 text-white/70 hover:text-white hover:bg-white/10 p-0" onClick={handleOpenEditModal} aria-label="Edit name" disabled={isUpdatingName || isInitializing}><Pencil className="h-4 w-4" /></Button>)}
                  </Card>
                );
             })}
              {(crewMembers.length === 0 && !isInitializing) && (<p className="col-span-full text-center py-4 text-pirate-navy/60">Waiting for pirates to assemble...</p>)}
            </div>
          </div>

          {/* Start Button / Waiting Message */}
          {role === 'captain' ? (
            <div className="mt-10">
               <PirateButton onClick={handleStartGame} className="w-full py-3 text-lg" variant="accent" disabled={!canStartGame || isInitializing}>
                 {isInitializing ? <Loader2 className="h-5 w-5 animate-spin" /> : <Anchor className="h-5 w-5" />}
                 {isInitializing ? 'Initializing...' : 'All aboard? Set sail!'}
               </PirateButton>
               {!isInitializing && crewMembers.length < 1 && <p className="text-xs text-center mt-2 text-pirate-navy/60">Waiting for at least one crew member to join...</p>}
            </div>
          ) : ( // Scallywag's view
            <div className="mt-10 text-center text-pirate-navy/80">
              <p>Waiting for {hostDisplayName} to start the voyage...</p>
               <div className="animate-pulse mt-2 text-2xl">{wsStatus === 'connected' ? '⚓️' : <Loader2 className="inline-block h-6 w-6 animate-spin"/>}</div>
               {wsStatus !== 'connected' && <p className="text-xs mt-1">(Connecting...)</p>}
            </div>
          )}
        </div>

        {/* Collapsible Voyage Details */}
        {gameSession && !isInitializing && (
          <Collapsible open={isVoyageDetailsOpen} onOpenChange={setIsVoyageDetailsOpen} className="mb-8">
            <Card className="p-4 flex items-center min-h-[60px] bg-pirate-parchment/50"><CollapsibleTrigger className="flex items-center justify-between w-full"><div className="flex items-center gap-2"> <Settings className="h-5 w-5 text-pirate-black" /> <h3 className="font-pirate text-2xl text-pirate-black">Voyage Details</h3> </div><ChevronDown className={`h-5 w-5 transition-transform duration-200 ${isVoyageDetailsOpen ? 'rotate-180' : ''}`} /></CollapsibleTrigger></Card>
            <CollapsibleContent className="mt-2"><Card className="p-6"><div className="grid grid-cols-1 md:grid-cols-3 gap-4"><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Category</p><p className="font-medium capitalize">{displayCategory}</p></div><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Questions</p><p className="font-medium">{displayQuestions}</p></div><div className="border border-pirate-navy/10 rounded p-3"><p className="text-xs text-pirate-navy/50 mb-1">Time per Question</p><p className="font-medium">{displayTime !== '-' ? `${displayTime} seconds` : 'N/A'}</p></div></div></Card></CollapsibleContent>
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