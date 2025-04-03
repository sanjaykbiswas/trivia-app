// src/pages/WaitingRoom.tsx
// --- START OF FILE ---
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams, Link } from 'react-router-dom';
import { Users, Copy, Anchor, ArrowLeft, ChevronDown, Settings, Loader2 } from 'lucide-react'; // Added Loader2
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import PlayerAvatar from '@/components/PlayerAvatar';
import { Player } from '@/types/gameTypes';
import { mockPlayers, getPlayerById } from '@/utils/gamePlayUtils';

const WaitingRoom: React.FC = () => {
  const { role } = useParams<{ role?: string }>();
  const [searchParams] = useSearchParams();
  const gameCode = searchParams.get('gameCode');
  // Game settings might be null initially for Scallywags
  const category = searchParams.get('category');
  const questions = searchParams.get('questions');
  const time = searchParams.get('time');

  const navigate = useNavigate();
  const [crewMembers, setCrewMembers] = useState<Player[]>([]);
  const [isVoyageDetailsOpen, setIsVoyageDetailsOpen] = useState(false);
  const [isLoadingSettings, setIsLoadingSettings] = useState(role !== 'captain' && (!category || !questions || !time)); // True if Scallywag and settings aren't in URL

  // Determine who the captain is (Adapt this for your real data source)
  const captainId = mockPlayers.find(p => p.id === 'p1')?.id; // Example: Assume p1 is captain
  const captain = captainId ? getPlayerById(mockPlayers, captainId) : undefined;

  // Simulate fetching/joining players & potentially game settings for Scallywags
  useEffect(() => {
    // --- Simulate Initial Player Fetch ---
    let initialCrew: Player[] = [];
    if (gameCode) { // Crew mode
      // Assume Captain (p1) is always present if game exists
      const cap = mockPlayers.find(p => p.id === captainId);
      if (cap) initialCrew.push(cap);
      // Maybe add the current user if they are a scallywag?
      if (role === 'scallywag') {
          // Find a mock player who ISN'T the captain to represent the current user
          const currentUserMock = mockPlayers.find(p => p.id !== captainId); // Example: grab the next available
          if (currentUserMock && !initialCrew.find(p=>p.id === currentUserMock.id)) {
              initialCrew.push(currentUserMock);
          }
      }
    } else { // Solo mode
       const soloPlayer = mockPlayers.find(p => p.id === 'p1');
       if (soloPlayer) initialCrew.push(soloPlayer);
    }
    setCrewMembers(initialCrew);

    // --- Simulate More Players Joining (Crew Mode Only) ---
    let joinTimer: NodeJS.Timeout | undefined;
    if (gameCode) {
        joinTimer = setInterval(() => {
            setCrewMembers(currentCrew => {
                if (currentCrew.length >= mockPlayers.length) {
                    clearInterval(joinTimer); // Stop if all mock players joined
                    return currentCrew;
                }
                const existingIds = new Set(currentCrew.map(p => p.id));
                const potentialNewPlayer = mockPlayers.find(p => !existingIds.has(p.id));
                if (potentialNewPlayer) {
                    // Only add one player per interval for demo effect
                    return [...currentCrew, potentialNewPlayer];
                }
                return currentCrew; // No new player found this interval
            });
        }, 3000 + Math.random() * 4000); // Join between 3-7 seconds
    }

     // --- Simulate Settings Arriving for Scallywag ---
     // In a real app, this would be driven by WebSocket events or polling
     let settingsTimer: NodeJS.Timeout | undefined;
     if (isLoadingSettings) {
         settingsTimer = setTimeout(() => {
             console.log("Simulating Captain finalizing settings...");
             setIsLoadingSettings(false);
             // In a real app, you'd now have the actual category/q/t values
             // For demo, we just stop showing the loading state
         }, 5000 + Math.random() * 5000); // Settings appear after 5-10 seconds
     }

    // Cleanup timers on component unmount
    return () => {
        if (joinTimer) clearInterval(joinTimer);
        if (settingsTimer) clearTimeout(settingsTimer);
    };
  }, [gameCode, role, captainId, isLoadingSettings]); // Dependencies


  const copyGameCodeToClipboard = () => {
    // ... (clipboard logic remains the same) ...
    if (gameCode) {
      navigator.clipboard.writeText(gameCode)
        .then(() => { toast('Copied to clipboard', { description: 'Game code copied successfully!' }); })
        .catch(() => { toast('Failed to copy', { description: 'Please try copying manually' }); });
    }
  };

  const startGame = () => {
    // Navigate to countdown, ensuring necessary params are passed if needed later
    navigate(`/countdown?questions=${questions || 10}`);
  };

  const getBackLink = () => {
    if (role === 'captain') {
       return `/crew/${role}?gameCode=${gameCode}`; // Back to GameSelect for Captain
    } else if (role) {
      return `/crew`; // Back to RoleSelect for Scallywag
    } else {
      return '/solo'; // Back to Solo GameSelect
    }
  };

  const isCaptain = role === 'captain';
  const settingsAvailable = category && questions && time;

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <Link to={getBackLink()} className="flex items-center text-pirate-navy hover:text-pirate-accent">
            <ArrowLeft className="h-4 w-4 mr-2" />
            <span>Back</span>
          </Link>
          {/* ... (Game Code Display) ... */}
          {gameCode && (
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-2 text-pirate-navy" />
              <span className="text-sm font-mono bg-pirate-navy/10 px-2 py-1 rounded">
                {gameCode}
              </span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={copyGameCodeToClipboard}
                      className="ml-2 p-1 text-pirate-navy hover:text-pirate-gold transition-colors rounded-full hover:bg-pirate-navy/10"
                      aria-label="Copy game code"
                    ><Copy className="h-4 w-4" /></button>
                  </TooltipTrigger>
                  <TooltipContent><p>Copy game code</p></TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          )}
        </div>

        <div className="map-container p-6 md:p-8 mb-10">
          {/* --- Player List --- */}
          <div className="mb-8">
            <h2 className="font-pirate text-3xl md:text-4xl mb-6 text-pirate-navy">
              {gameCode ? `Scallywags on Deck (${crewMembers.length})` : 'Prepare Your Voyage'}
            </h2>
             {/* Parent div: Applies grid layout for crew, centers content for solo */}
             <div className={`grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 ${!gameCode ? 'justify-center' : ''}`}>
               {crewMembers.map((member) => (
                // FIX: Removed conditional classes from Card causing width/centering issues in solo mode
                <Card key={member.id} className="p-4 flex items-center space-x-3 border-pirate-navy/20 shadow-md">
                   <PlayerAvatar playerId={member.id} name={member.name} size="md" />
                   <div>
                     <p className="font-medium text-pirate-navy">{member.name}</p>
                     {gameCode && <p className="text-xs text-pirate-navy/70">{member.id === captain?.id ? 'Captain' : 'Crew Member'}</p>}
                   </div>
                 </Card>
               ))}
               {/* Placeholder if waiting for players */}
               {gameCode && crewMembers.length < mockPlayers.length && (
                    <Card className="p-4 flex items-center justify-center space-x-3 border-pirate-navy/20 border-dashed shadow-inner bg-pirate-parchment/50 min-h-[76px]"> {/* Added min-height */}
                      <div className="text-center text-pirate-navy/50 animate-pulse">
                          <Users className="h-6 w-6 mx-auto mb-1"/>
                          <p className="text-xs">Waiting...</p>
                      </div>
                    </Card>
               )}
             </div>
          </div>

          {/* --- Action Button / Waiting Message --- */}
          {gameCode ? ( // Crew Mode
            isCaptain ? ( // Captain's view - Can only start if settings are chosen
               <div className="mt-10">
                 <PirateButton
                   onClick={startGame}
                   className="w-full py-3 text-lg"
                   variant="accent"
                   // Captain must have selected settings (which would add params to URL)
                   disabled={!settingsAvailable || crewMembers.length < 1}
                 >
                   <Anchor className="h-5 w-5" />
                   All aboard? Set sail!
                 </PirateButton>
                 {!settingsAvailable && <p className="text-xs text-center mt-2 text-pirate-navy/60">Select voyage details first!</p>}
               </div>
             ) : ( // Scallywag's view
               <div className="mt-10 text-center text-pirate-navy/80">
                 {isLoadingSettings ? (
                     <div className='flex items-center justify-center gap-2'>
                         <Loader2 className="h-5 w-5 animate-spin" />
                         <span>Captain {captain?.name ? `(${captain.name})` : ''} is charting the route...</span>
                     </div>
                 ) : (
                    <>
                     <p>Waiting for the Captain {captain?.name ? `(${captain.name})` : ''} to start the voyage...</p>
                     <div className="animate-pulse mt-2 text-2xl">⚓️</div>
                    </>
                 )}
               </div>
             )
           ) : ( // Solo Mode
             <div className="mt-10">
                 <PirateButton
                   onClick={startGame}
                   className="w-full py-3 text-lg"
                   variant="accent"
                 >
                   <Anchor className="h-5 w-5" />
                   Start Solo Voyage!
                 </PirateButton>
             </div>
           )}
         </div>


         {/* --- Collapsible Voyage Details --- */}
         {/* Only show if settings ARE available (Captain has finished setup OR Solo game) */}
         {(settingsAvailable || !gameCode) && (
            <Collapsible
              open={isVoyageDetailsOpen}
              onOpenChange={setIsVoyageDetailsOpen}
              className="mb-8"
            >
              <Card className="p-4 flex items-center min-h-[60px] bg-pirate-parchment/50">
                <CollapsibleTrigger className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <Settings className="h-5 w-5 text-pirate-black" />
                    <h3 className="font-pirate text-2xl text-pirate-black">Voyage Details</h3>
                  </div>
                  <ChevronDown className={`h-5 w-5 transition-transform duration-200 ${isVoyageDetailsOpen ? 'rotate-180' : ''}`} />
                </CollapsibleTrigger>
              </Card>
              <CollapsibleContent className="mt-2">
                <Card className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="border border-pirate-navy/10 rounded p-3">
                      <p className="text-xs text-pirate-navy/50 mb-1">Category</p>
                      <p className="font-medium capitalize">{category?.replace('-', ' ') || 'N/A'}</p>
                    </div>
                    <div className="border border-pirate-navy/10 rounded p-3">
                      <p className="text-xs text-pirate-navy/50 mb-1">Questions</p>
                      <p className="font-medium">{questions || 'N/A'}</p>
                    </div>
                    <div className="border border-pirate-navy/10 rounded p-3">
                      <p className="text-xs text-pirate-navy/50 mb-1">Time per Question</p>
                      <p className="font-medium">{time ? `${time} seconds` : 'N/A'}</p>
                    </div>
                  </div>
                </Card>
              </CollapsibleContent>
            </Collapsible>
          )}
       </main>

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
// --- END OF FILE ---