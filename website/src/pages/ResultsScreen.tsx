// src/pages/ResultsScreen.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, useParams, useSearchParams } from 'react-router-dom';
import { Trophy, RotateCcw, Home, Star } from 'lucide-react'; // Added Star
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import PlayerAvatar from '@/components/PlayerAvatar';
import { Player } from '@/types/gameTypes';
import confetti from 'canvas-confetti';

// Define result type extending Player
interface PlayerResult extends Player {
  score: number;
}

const ResultsScreen: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { role } = useParams<{ role?: string }>();
  const [searchParams] = useSearchParams();
  const gameCode = searchParams.get('gameCode');
  const isSoloMode = !gameCode; // Determine mode based on gameCode presence
  const [playerResults, setPlayerResults] = useState<PlayerResult[]>([]);

  useEffect(() => {
    const results = location.state?.results as PlayerResult[] || [];
    console.log("Received results:", results); // Debug log

    // Sort players by score (highest first) - still useful for crew mode
    const sortedResults = [...results].sort((a, b) => b.score - a.score);
    setPlayerResults(sortedResults);

    // Launch confetti only if there's a winner with a positive score
    if (sortedResults.length > 0 && sortedResults[0].score > 0) {
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
    // Navigation logic remains the same
    const category = searchParams.get('category') || '';
    const questions = searchParams.get('questions') || '';
    const time = searchParams.get('time') || '';

    if (gameCode && role) { // Crew game
       if (role === 'captain') {
         navigate(`/crew/captain?gameCode=${gameCode}`);
       } else {
         navigate(`/crew/waiting/${role}?gameCode=${gameCode}&category=${category}&questions=${questions}&time=${time}`);
       }
    } else { // Solo game
       navigate('/solo');
    }
  };

  const handleReturnHome = () => {
    navigate('/');
  };

  const getPositionLabel = (index: number): string => {
    switch (index) {
      case 0: return '1st';
      case 1: return '2nd';
      case 2: return '3rd';
      default: return `${index + 1}th`;
    }
  };

  // Get the single player result for solo mode
  const soloPlayer = isSoloMode && playerResults.length > 0 ? playerResults[0] : null;
  console.log("Solo Player Data:", soloPlayer); // Debug log

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          {/* *** MODIFICATION: Conditional Title *** */}
          <h1 className="font-pirate text-4xl md:text-5xl text-pirate-navy mb-2">
            Voyage Complete!
          </h1>
          {/* *** MODIFICATION: Conditional Description *** */}
          <p className="text-pirate-navy/80 font-medium">
            {isSoloMode
              ? "See how you stacked up against the challenges"
              : "See how your crew stacked up against the challenges"}
          </p>
        </div>

        <div className="map-container p-6 md:p-8 mb-8">
          <div className="mb-8">
             {/* *** MODIFICATION: Conditional Header *** */}
            <div className="flex items-center justify-center mb-6">
              {isSoloMode ? (
                 <Star className="h-8 w-8 text-pirate-gold mr-3" />
              ) : (
                 <Trophy className="h-8 w-8 text-pirate-gold mr-3" />
              )}
              <h2 className="font-pirate text-3xl text-pirate-navy">
                {isSoloMode ? "Final Score" : "Final Standings"}
              </h2>
            </div>

            {/* *** MODIFICATION: Conditional Result Display *** */}
            {isSoloMode ? (
              // Solo Mode Display
              soloPlayer ? (
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
                 <p className="text-center text-pirate-navy/60 py-4">No score available.</p>
              )
            ) : (
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
                        {index === 0 && (
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
                 {playerResults.length === 0 && (
                     <p className="text-center text-pirate-navy/60 py-4">No results available.</p>
                 )}
              </div>
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
              {gameCode ? 'Same crew, new journey' : 'Play Again'}
            </PirateButton>

            <PirateButton
              onClick={handleReturnHome}
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