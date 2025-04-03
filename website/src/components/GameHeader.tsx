
import React from 'react';
import { Link } from 'react-router-dom';
import { Anchor } from 'lucide-react';
import { useIsMobile } from '@/hooks/use-mobile';

const GameHeader: React.FC = () => {
  const isMobile = useIsMobile();
  
  return (
    <header className="w-full py-4 px-6">
      {!isMobile && (
        <Link to="/" className="flex items-center gap-2">
          <Anchor className="text-pirate-navy h-6 w-6" />
          <h1 className="font-pirate text-2xl md:text-3xl text-pirate-navy">Trivia Trove</h1>
        </Link>
      )}
    </header>
  );
};

export default GameHeader;
