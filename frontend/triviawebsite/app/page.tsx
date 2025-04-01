'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Typography from './components/ui/Typography';
import SelectionOption from './components/ui/SelectionOption';
import ResultsModal from './components/game/ResultsModal';

export default function Home() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // States for score modal
  const [showScoreModal, setShowScoreModal] = useState(false);
  const [score, setScore] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  
  // Check for score parameters in URL
  useEffect(() => {
    const scoreParam = searchParams.get('score');
    const totalParam = searchParams.get('total');
    
    if (scoreParam && totalParam) {
      setScore(parseInt(scoreParam, 10));
      setTotalQuestions(parseInt(totalParam, 10));
      setShowScoreModal(true);
    }
  }, [searchParams]);
  
  const handleSoloPress = () => {
    router.push('/solo');
  };
  
  const handlePartyPress = () => {
    // For now, just alert since we're not implementing party mode
    alert('Party mode coming soon!');
  };
  
  const handleCloseScoreModal = () => {
    setShowScoreModal(false);
    
    // Remove query params from URL
    const newUrl = window.location.pathname;
    window.history.replaceState({}, '', newUrl);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center p-6">
      <div className="text-center mb-16">
        <Typography variant="heading1" className="font-bold mb-2">
          Trivia for
        </Typography>
        <Typography 
          variant="heading1" 
          className="text-primary-main font-bold animate-pulse"
        >
          everyone
        </Typography>
      </div>
      
      <div className="max-w-md mx-auto">
        <SelectionOption
          title="Solo"
          subtitle="Play competitively or in relaxed mode"
          emoji="🧠"
          onPress={handleSoloPress}
          testId="solo-option"
        />
        
        <SelectionOption
          title="Party"
          subtitle="Play games with friends"
          emoji="🎉"
          onPress={handlePartyPress}
          testId="party-option"
        />
      </div>
      
      {/* Results Modal */}
      <ResultsModal
        score={score}
        totalQuestions={totalQuestions}
        isOpen={showScoreModal}
        onClose={handleCloseScoreModal}
      />
    </div>
  );
}