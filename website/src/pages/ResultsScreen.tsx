// src/pages/ResultsScreen.tsx
import React, { useEffect, useState, useCallback } from 'react'; // Added useCallback
import { useNavigate, useLocation, useParams, useSearchParams } from 'react-router-dom';
import { Trophy, RotateCcw, Home, Star } from 'lucide-react'; // Added Star
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import PlayerAvatar from '@/components/PlayerAvatar';
import { Player } from '@/types/gameTypes'; // Keep Player if used
import confetti from 'canvas-confetti';

// Define result type extending Player
interface PlayerResult extends Player {
  score: number;
}

const ResultsScreen: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { role } = useParams<{ role?: string }>(); // Keep role if needed for Play Again logic
  const [searchParams] = useSearchParams();
  const gameCode = searchParams.get('gameCode'); // Keep for Play Again logic
  const [playerResults, setPlayerResults] = useState<PlayerResult[]>([]);

  useEffect(() => {
    const results = location.state?.results as PlayerResult[] || [];
    console.log("Received results:", results); // Debug log

    // Sort players by score (highest first) - still useful for crew mode
    const sortedResults = [...results].sort((a, b) => b.score - a.score);
    setPlayerResults(sortedResults);

    // Launch confetti only if there's a winner with a positive score (and more than one player for crew mode visual effect)
    if (sortedResults.length > 0 && sortedResults[0].score > 0 && sortedResults.length > 1) {
      launchConfetti();
    } else if (sortedResults.length === 1 && sortedResults[0].score > 0) {
      // Optional: slightly different confetti for solo win?
       launchConfetti();
    }
  }, [location.state]);

  const launchConfetti = () => {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  };

  const handlePlayAgain = () => {
    // Navigation logic remains the same - relies on gameCode to decide where to go
    if (gameCode && role) { // Crew game
       // Navigate back to the waiting room for the same game code
       // Note: We might need to pass back original settings if we want to start *exactly* the same game again
       navigate(`/crew/waiting/${role}?gameCode=${gameCode}`);
    } else { // Solo game
       // Navigate back to the solo game selection screen
       navigate('/solo');
    }
  };

  const getPositionLabel = (index: number): string => {
    switch (index) {
      case 0: return '1st';
      case 1: return '2nd';
      case 2: return '3rd';
      default: return `${index + 1}th`;
    }
  };

  // Determine display mode based on results length
  const displayMode: 'solo' | 'crew' | 'empty' = playerResults.length === 1 ? 'solo' : playerResults.length > 1 ? 'crew' : 'empty';
  // Get the single player result for solo mode
  const soloPlayer = displayMode === 'solo' ? playerResults[0] : null;
  console.log("Display Mode:", displayMode); // Debug log
  console.log("Solo Player Data:", soloPlayer); // Debug log

  // Stable back link function
  const getBackLink = useCallback(() => role === 'captain' || role === 'scallywag' ? '/crew' : '/', [role]);

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          {/* Title remains the same */}
          <h1 className="font-pirate text-4xl md:text-5xl text-pirate-navy mb-2">
            Voyage Complete!
          </h1>
          {/* Conditional Description based on displayMode */}
          <p className="text-pirate-navy/80 font-medium">
            {displayMode === 'solo'
              ? "See how you stacked up against the challenges"
              : "See how your crew stacked up against the challenges"}
          </p>
        </div>

        <div className="map-container p-6 md:p-8 mb-8">
          <div className="mb-8">
             {/* Conditional Header Icon/Text based on displayMode */}
            <div className="flex items-center justify-center mb-6">
              {displayMode === 'solo' ? (
                 <Star className="h-8 w-8 text-pirate-gold mr-3" />
              ) : (
                 <Trophy className="h-8 w-8 text-pirate-gold mr-3" />
              )}
              <h2 className="font-pirate text-3xl text-pirate-navy">
                {displayMode === 'solo' ? "Final Score" : "Final Standings"}
              </h2>
            </div>

            {/* Conditional Result Display based on displayMode */}
            {displayMode === 'solo' ? (
              // Solo Mode Display
              soloPlayer ? (
                // Display the solo player card if soloPlayer data exists
                <Card className="p-6 flex flex-col items-center border-2 border-pirate-gold bg-pirate-gold/5">
                  <PlayerAvatar
                    playerId={soloPlayer.id}
                    name={soloPlayer.name} // Use the name from the result
                    size="lg"
                    className="mb-4 border-2 border-pirate-gold"
                  />
                  <p className="font-bold text-xl text-pirate-navy mb-2">
                    {soloPlayer.name} {/* Display the name */}
                  </p>
                  <div className="flex items-baseline bg-pirate-parchment px-6 py-3 rounded-full">
                    <span className="font-bold text-4xl text-pirate-navy">{soloPlayer.score}</span>
                    <span className="text-lg text-pirate-navy/70 ml-2">pts</span>
                  </div>
                </Card>
              ) : (
                 // This branch runs if displayMode is 'solo' but soloPlayer is null (error case)
                 <p className="text-center text-pirate-navy/60 py-4">No score available for solo player.</p>
              )
            ) : displayMode === 'crew' ? (
              // Crew Mode Display (Existing Logic)
              <div className="grid gap-4">
                {playerResults.map((player, index) => (
                  <Card
                    key={player.id}
                    className={`p-4 flex items-center justify-between border-2 ${
                      index === 0 ? 'border-pirate-gold bg-pirate-gold/5' : 'border-pirate-navy/20'
                    }`}
                  >
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0 font-bold text-pirate-navy/70 w-8 text-center">
                        {getPositionLabel(index)}
                      </div>
                      <PlayerAvatar
                        playerId={player.id}
                        name={player.name} // Use name from result
                        size="lg"
                        className={index === 0 ? "border-2 border-pirate-gold" : ""}
                      />
                      <div>
                        <p className={`font-bold text-lg ${index === 0 ? 'text-pirate-navy' : 'text-pirate-navy/90'}`}>
                          {player.name} {/* Display name */}
                        </p>
                        {index === 0 && player.score > 0 && ( // Only show winner if score > 0
                          <p className="text-xs text-pirate-gold font-medium">Winner!</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center bg-pirate-parchment px-4 py-2 rounded-full">
                      <span className="font-bold text-xl text-pirate-navy">{player.score}</span>
                      <span className="text-xs text-pirate-navy/70 ml-1">pts</span>
                    </div>
                  </Card>
                ))}
                {/* Display message if crew mode detected but results array is empty */}
                 {playerResults.length === 0 && (
                     <p className="text-center text-pirate-navy/60 py-4">No crew results found.</p>
                 )}
              </div>
            ) : (
              // Empty Mode Display (displayMode === 'empty')
              <p className="text-center text-pirate-navy/60 py-4">No results available for this game.</p>
            )}
            {/* *** END MODIFICATION *** */}
          </div>

          {/* Buttons remain the same */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
            <PirateButton
              onClick={handlePlayAgain}
              variant="primary"
              icon={<RotateCcw className="h-5 w-5" />}
             >
              {/* Text depends on whether it was a crew game (has gameCode) */}
              {gameCode ? 'Same crew, new journey' : 'Play Again'}
            </PirateButton>

            <PirateButton
              onClick={() => navigate('/')} // Simplified Return Home
              variant="secondary"
              icon={<Home className="h-5 w-5" />}
            >
              Return Home
            </PirateButton>
          </div>
        </div>
      </main>

      {/* Footer remains the same */}
      <footer className="ocean-bg py-8">
        <div className="container mx-auto text-center text-white relative z-10">
          <p className="font-pirate text-xl mb-2">Adventure awaits, matey!</p>
          <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
};

export default ResultsScreen;