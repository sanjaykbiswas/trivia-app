// website/src/pages/GameSelect.tsx
// --- START OF FILE ---
import React, { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, BookOpen, Globe, Lightbulb, Film, Dices, Users, Copy, Search, Music, Map, Trophy, Utensils, BriefcaseMedical, Building2, PenTool, Landmark, Languages, LucideIcon, Ship, BookText, Loader2, AlertCircle // Added Loader2, AlertCircle
} from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Skeleton } from '@/components/ui/skeleton'; // Import Skeleton
import GameSettings from '@/components/GameSettings';
import { createGameSession } from '@/services/gameApi';
import { fetchPacks } from '@/services/packApi'; // <<< NEW: Import fetchPacks
import { ApiPackResponse, GameCreationPayload, ApiGameSessionResponse } from '@/types/apiTypes'; // <<< NEW: Import ApiPackResponse

// --- NEW: Icon Mapping ---
// Helper to get an icon based on pack name (case-insensitive partial match)
const getIconForPack = (packName: string): React.ReactNode => {
    const lowerName = packName.toLowerCase();
    if (lowerName.includes("history")) return <BookOpen className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("science")) return <Lightbulb className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("entertainment")) return <Film className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("music")) return <Music className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("geography")) return <Map className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("sport")) return <Trophy className="h-6 w-6 text-pirate-navy" />; // Match "sports" or "sport"
    if (lowerName.includes("food") || lowerName.includes("drink")) return <Utensils className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("medicine")) return <BriefcaseMedical className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("architecture")) return <Building2 className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("art")) return <PenTool className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("politic")) return <Landmark className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("language")) return <Languages className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("maritime") || lowerName.includes("ship") || lowerName.includes("pirate")) return <Ship className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("literature") || lowerName.includes("book")) return <BookText className="h-6 w-6 text-pirate-navy" />;
    if (lowerName.includes("random") || lowerName.includes("mix")) return <Dices className="h-6 w-6 text-pirate-navy" />;
    // Default icon
    return <Globe className="h-6 w-6 text-pirate-navy" />;
};
// --- END Icon Mapping ---

interface CategoryCardProps {
  title: string;
  icon: React.ReactNode;
  description: string;
  onClick: () => void;
}

// CategoryCard component remains the same
const CategoryCard: React.FC<CategoryCardProps> = ({ title, icon, description, onClick }) => {
  return (
    <div onClick={onClick} className="cursor-pointer">
      <Card className="h-full border-pirate-navy/20 hover:border-pirate-gold transition-colors p-6 flex flex-col items-center text-center hover:shadow-md">
        <div className="bg-pirate-navy/10 p-3 rounded-full mb-4">
          {icon}
        </div>
        <h3 className="font-pirate text-xl text-pirate-navy mb-2">{title}</h3>
        <p className="text-pirate-navy/70 text-sm">{description || "Test your knowledge in this category!"}</p> {/* Added default desc */}
      </Card>
    </div>
  );
};


// <<< REMOVED the hardcoded Category interface >>>

interface GameSelectProps {
  mode: 'solo' | 'crew';
}

const GameSelect: React.FC<GameSelectProps> = ({ mode }) => {
  const { role } = useParams<{ role?: string }>();
  const [searchParams] = useSearchParams();
  const gameCodeFromUrl = searchParams.get('gameCode');
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  // --- NEW State Variables ---
  const [availablePacks, setAvailablePacks] = useState<ApiPackResponse[]>([]);
  const [selectedPack, setSelectedPack] = useState<ApiPackResponse | null>(null); // Store the whole selected pack object
  const [isLoadingPacks, setIsLoadingPacks] = useState(true); // Loading state for fetching packs
  const [fetchPacksError, setFetchPacksError] = useState<string | null>(null); // Error state for fetching packs
  const [isCreatingGame, setIsCreatingGame] = useState(false); // Renamed from isLoading
  // --- END NEW State ---

  // Placeholder User ID - Replace with actual user auth logic later
  const hostUserId = "a1b2c3d4-e5f6-7890-1234-567890abcdef"; // Example static UUID

  // --- NEW: Fetch Packs useEffect ---
  useEffect(() => {
    const loadPacks = async () => {
      setIsLoadingPacks(true);
      setFetchPacksError(null);
      try {
        const response = await fetchPacks();
        setAvailablePacks(response.packs);
      } catch (error) {
        console.error("Failed to fetch packs:", error);
        const errorMsg = error instanceof Error ? error.message : "Could not load categories.";
        setFetchPacksError(errorMsg);
        toast.error("Failed to Load Categories", { description: errorMsg });
      } finally {
        setIsLoadingPacks(false);
      }
    };

    loadPacks();
  }, []); // Empty dependency array means run once on mount
  // --- END Fetch Packs useEffect ---


  useEffect(() => {
    // Navigation logic remains the same
    if (mode === 'crew' && (!role || !gameCodeFromUrl)) {
      navigate('/crew');
    }
  }, [mode, role, gameCodeFromUrl, navigate]);

  // getPageTitle, getPageDescription, getBackLink, copyGameCodeToClipboard remain the same...
   const getPageTitle = () => {
    if (mode === 'solo') return 'Solo Journey';
    // Title for captain creating game
    if (mode === 'crew' && role === 'captain') return 'Chart Your Course, Captain!';
    return ''; // No title needed if scallywag joins via code
  };

  const getPageDescription = () => {
    if (mode === 'solo') return 'Test your knowledge on a solo adventure!';
    if (mode === 'crew' && role === 'captain') return 'Select a category and configure the rules for your crew.';
    return '';
  };

  const getBackLink = () => {
    if (mode === 'solo') return '/';
    return '/crew';
  };

   const copyGameCodeToClipboard = () => {
    if (gameCodeFromUrl) {
      navigator.clipboard.writeText(gameCodeFromUrl)
        .then(() => {
          toast('Copied to clipboard', { description: 'Game code copied successfully!' });
        })
        .catch(() => {
          toast('Failed to copy', { description: 'Please try copying manually' });
        });
    }
  };

  // --- UPDATED Handlers ---
  const handlePackSelect = (pack: ApiPackResponse) => {
    setSelectedPack(pack);
  };

  const handleBackToCategories = () => {
    setSelectedPack(null);
  };

  const handleGameSettingsSubmit = async (gameSettings: {
    numberOfQuestions: number;
    timePerQuestion: number;
    focus: string; // Focus might be used later for selecting specific questions
  }) => {
    if (!selectedPack) return; // Use selectedPack now

    setIsCreatingGame(true); // Start loading

    // --- Use ACTUAL pack_id ---
    const payload: GameCreationPayload = {
      pack_id: selectedPack.id, // <<< Use the ID from the fetched pack
      max_participants: 10, // Keep default or allow configuration
      question_count: gameSettings.numberOfQuestions,
      time_limit_seconds: gameSettings.timePerQuestion,
    };
    // --- END ---

    try {
      console.log("Calling createGameSession with:", payload, hostUserId);
      const createdGame: ApiGameSessionResponse = await createGameSession(payload, hostUserId);
      console.log("Game created successfully:", createdGame);

      const newGameCode = createdGame.code;
      // Pass selected pack info if needed by WaitingRoom, otherwise just navigate
      const targetPath = mode === 'solo'
        ? `/solo/waiting?gameCode=${newGameCode}`
        : `/crew/waiting/${role}?gameCode=${newGameCode}`;

      navigate(targetPath, {
        state: {
          gameSession: createdGame,
          categoryName: selectedPack.name, // Pass name instead of slug
          questionCount: createdGame.question_count,
          timeLimit: createdGame.time_limit_seconds,
        }
      });

    } catch (error) {
      console.error("Failed to create game:", error);
      toast.error("Failed to Create Game", {
        description: error instanceof Error ? error.message : "An unknown error occurred.",
      });
    } finally {
      setIsCreatingGame(false); // Stop loading
    }
  };
  // --- END UPDATED Handlers ---

  // --- UPDATED Filtering Logic ---
  const filteredPacks = availablePacks.filter(pack =>
    pack.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (pack.description && pack.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );
  // --- END ---

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          {/* Back button logic */}
          {!selectedPack ? ( // <<< Changed condition
            <Link to={getBackLink()} className="flex items-center text-pirate-navy hover:text-pirate-accent">
              <ArrowLeft className="h-4 w-4 mr-2" />
              <span>Back</span>
            </Link>
          ) : (
            <button
              onClick={handleBackToCategories}
              disabled={isCreatingGame} // <<< Changed state variable
              className="flex items-center text-pirate-navy hover:text-pirate-accent disabled:opacity-50"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              <span>Back to Categories</span>
            </button>
          )}

          {/* Game Code Display remains the same */}
           {mode === 'crew' && gameCodeFromUrl && (
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-2 text-pirate-navy" />
              <span className="text-sm font-mono bg-pirate-navy/10 px-2 py-1 rounded">
                {gameCodeFromUrl}
              </span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={copyGameCodeToClipboard}
                      className="ml-2 p-1 text-pirate-navy hover:text-pirate-gold transition-colors rounded-full hover:bg-pirate-navy/10"
                      aria-label="Copy game code"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Copy game code</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          )}
        </div>

        <div className="map-container p-6 md:p-8 mb-10 relative">
          {getPageTitle() && <h1 className="pirate-heading text-3xl md:text-4xl mb-3">{getPageTitle()}</h1>}
          {getPageDescription() && <p className="text-pirate-navy/80 mb-8">{getPageDescription()}</p>}

          {/* Conditional Rendering: Show Loading, Error, Categories, or Settings */}
          {isLoadingPacks ? (
            // --- Loading State ---
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 h-[calc(100vh-350px)]">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="p-6 flex flex-col items-center">
                  <Skeleton className="h-12 w-12 rounded-full mb-4 bg-pirate-navy/10" />
                  <Skeleton className="h-5 w-3/4 mb-2 bg-pirate-navy/10" />
                  <Skeleton className="h-4 w-full bg-pirate-navy/5" />
                  <Skeleton className="h-4 w-5/6 mt-1 bg-pirate-navy/5" />
                </Card>
              ))}
            </div>
          ) : fetchPacksError ? (
             // --- Error State ---
            <div className="text-center py-10 text-destructive">
                <AlertCircle className="h-12 w-12 mx-auto mb-4" />
                <h3 className="font-semibold text-lg mb-2">Failed to Load Categories</h3>
                <p className="text-sm">{fetchPacksError}</p>
                <PirateButton onClick={() => window.location.reload()} className="mt-4" variant="secondary">
                    Try Again
                </PirateButton>
            </div>
          ) : !selectedPack ? (
            // --- Category Selection State ---
            <>
              <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-pirate-navy/50" />
                <Input
                  placeholder="Search categories..."
                  className="pl-10 border-pirate-navy/20 focus-visible:ring-pirate-gold"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <ScrollArea className="h-[calc(100vh-350px)] pr-4"> {/* Adjusted height slightly */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredPacks.map((pack) => ( // <<< Map over filteredPacks
                    <CategoryCard
                      key={pack.id}
                      title={pack.name}
                      icon={getIconForPack(pack.name)} // <<< Use icon mapping
                      description={pack.description || ""}
                      onClick={() => handlePackSelect(pack)} // <<< Pass the whole pack
                    />
                  ))}

                  {filteredPacks.length === 0 && !isLoadingPacks && ( // <<< Check loading state
                    <div className="col-span-full text-center py-10">
                      <p className="text-pirate-navy/60 text-lg">No categories match your search</p>
                      <p className="text-pirate-navy/40">Try a different search term</p>
                    </div>
                  )}
                   {availablePacks.length === 0 && !isLoadingPacks && !fetchPacksError && ( // Handle case where fetch succeeded but no packs exist
                        <div className="col-span-full text-center py-10">
                            <p className="text-pirate-navy/60 text-lg">No trivia packs available right now.</p>
                            <p className="text-pirate-navy/40">Check back later!</p>
                        </div>
                   )}
                </div>
              </ScrollArea>
            </>
          ) : (
             // --- Game Settings State ---
             // Adapt GameSettings to accept pack name/description if needed
             // Or just pass the relevant parts
            <GameSettings
              category={{ // Adapt the props passed to GameSettings
                 title: selectedPack.name,
                 icon: getIconForPack(selectedPack.name),
                 description: selectedPack.description || '',
                 slug: selectedPack.name.toLowerCase().replace(/\s+/g, '-'), // Generate slug if needed
                 focuses: [] // Focuses aren't directly available from pack
              }}
              onSubmit={handleGameSettingsSubmit}
              mode={mode}
              role={role}
            />
          )}

          {/* Loading Indicator for Game Creation */}
          {isCreatingGame && (
            <div className="absolute inset-0 bg-pirate-parchment/80 flex items-center justify-center rounded-xl z-20">
              <Loader2 className="h-8 w-8 animate-spin text-pirate-navy" />
              <span className="ml-2 font-semibold text-pirate-navy">Creating Game...</span>
            </div>
          )}
        </div>
      </main>

      {/* Footer remains the same */}
      <footer className="ocean-bg py-8">
        <div className="container mx-auto text-center text-white relative z-10">
          <p className="font-pirate text-xl mb-2">Choose yer category, matey!</p>
          <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
};

export default GameSelect;
// --- END OF FILE ---