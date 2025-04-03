// src/pages/ResultsScreen.tsx
import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation, useParams, useSearchParams } from 'react-router-dom'; // Import useSearchParams
import { Trophy, RotateCcw, Home } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import PlayerAvatar from '@/components/PlayerAvatar'; // Correct import
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
  const [searchParams] = useSearchParams(); // Get search params hook
  const gameCode = searchParams.get('gameCode'); // Define gameCode at component level
  const [playerResults, setPlayerResults] = useState<PlayerResult[]>([]);

  useEffect(() => {
    // Get scores from location state
    const results = location.state?.results as PlayerResult[] || [];

    // Sort players by score (highest first)
    const sortedResults = [...results].sort((a, b) => b.score - a.score);
    setPlayerResults(sortedResults);

    // Launch confetti for the winner
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
    // gameCode is now available directly from component scope
    // const searchParams = new URLSearchParams(location.search); // No longer needed here
    // const gameCode = searchParams.get('gameCode') || ''; // No longer needed here

    // Retrieve other params needed for navigation (still needed if passing them)
    const category = searchParams.get('category') || '';
    const questions = searchParams.get('questions') || '';
    const time = searchParams.get('time') || '';
    // const focus = searchParams.get('focus') || '';

    if (gameCode && role) { // If it was a crew game
       if (role === 'captain') {
         // Captain goes back to category select for the same crew
         navigate(`/crew/captain?gameCode=${gameCode}`);
       } else {
         // Crew members go back to waiting room for the same game settings
         // Ensure all necessary params are passed
         navigate(`/crew/waiting/${role}?gameCode=${gameCode}&category=${category}&questions=${questions}&time=${time}`);
       }
    } else {
       // Solo player goes back to category select for solo mode
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

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="font-pirate text-4xl md:text-5xl text-pirate-navy mb-2">
            Voyage Complete!
          </h1>
          <p className="text-pirate-navy/80 font-medium">
            See how your crew stacked up against the challenges
          </p>
        </div>

        <div className="map-container p-6 md:p-8 mb-8">
          <div className="mb-8">
            <div className="flex items-center justify-center mb-6">
              <Trophy className="h-8 w-8 text-pirate-gold mr-3" />
              <h2 className="font-pirate text-3xl text-pirate-navy">Final Standings</h2>
            </div>

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
                      playerId={player.id} // Pass playerId
                      name={player.name}
                      size="lg" // Larger avatar on results screen
                      className={index === 0 ? "border-2 border-pirate-gold" : ""}
                    />
                    <div>
                      <p className={`font-bold text-lg ${index === 0 ? 'text-pirate-navy' : 'text-pirate-navy/90'}`}>
                        {player.name}
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
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
            <PirateButton
              onClick={handlePlayAgain}
              variant="primary"
              // Removed py-3 from className
              icon={<RotateCcw className="h-5 w-5" />}
            >
              {/* Use component-level gameCode for the text */}
              {gameCode ? 'Same crew, new journey' : 'Play Again'}
            </PirateButton>

            <PirateButton
              onClick={handleReturnHome}
              variant="secondary"
              // Removed py-3 from className
              icon={<Home className="h-5 w-5" />}
            >
              Return Home
            </PirateButton>
          </div>
        </div>
      </main>

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