import React from 'react';
import { Link } from 'react-router-dom';
import { Anchor, Compass } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Header: React.FC = () => {
  return (
    <header className="w-full py-4 px-6 flex justify-between items-center">
      <Link to="/" className="flex items-center gap-2">
        <Anchor className="text-pirate-navy h-6 w-6" />
        <h1 className="font-pirate text-2xl md:text-3xl text-pirate-navy">Trivia Trove</h1>
      </Link>

      <nav className="flex items-center gap-4">
        {/* Update link to point to /auth */}
        <Link to="/auth">
          <Button className="bg-pirate-black text-white hover:bg-pirate-navy rounded-full flex items-center gap-2">
            <span>Log In</span>
            <Compass className="h-4 w-4" />
          </Button>
        </Link>
      </nav>
    </header>
  );
};

export default Header;