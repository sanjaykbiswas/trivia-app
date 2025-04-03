
import React from 'react';
import { Link } from 'react-router-dom';
import { Anchor, Compass, Skull, MapPin } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1 flex flex-col items-center justify-center p-6 relative">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMwQTI0NjMiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDM0di00aC0ydjRoLTR2Mmg0djRoMnYtNGg0di0yaC00em0wLTMwVjBoLTJ2NGgtNHYyaDR2NGgyVjZoNFY0aC00ek02IDM0di00SDR2NEgwdjJoNHY0aDJ2LTRoNHYtMkg2ek02IDRWMEg0djRIMHYyaDR2NGgyVjZoNFY0SDZ6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30 -z-10"></div>
        
        <div className="w-full max-w-4xl flex flex-col items-center">
          <div className="flex items-center justify-center mb-4 animate-float">
            <Anchor className="text-pirate-gold h-12 w-12 mr-2" />
            <Skull className="text-pirate-navy h-10 w-10" />
            <MapPin className="text-pirate-accent h-10 w-10 ml-2" />
          </div>
          
          <h1 className="pirate-heading text-5xl md:text-7xl text-center mb-4">
            Trivia Trove
          </h1>
          
          <p className="text-xl md:text-2xl text-center text-pirate-navy/80 mb-12 max-w-2xl">
            Test your knowledge solo or challenge your friends!
          </p>
          
          <div className="grid gap-6 w-full max-w-md">
            <Link to="/crew" className="w-full">
              <PirateButton 
                variant="primary" 
                className="w-full text-lg"
                icon={<Compass className="h-5 w-5" />}
              >
                Play with a Crew
              </PirateButton>
            </Link>
            
            <Link to="/solo" className="w-full">
              <PirateButton 
                variant="secondary" 
                className="w-full text-lg"
              >
                Solo Journey
              </PirateButton>
            </Link>
          </div>
        </div>
      </main>
      
      <footer className="ocean-bg py-8 mt-12">
        <div className="container mx-auto text-center text-white relative z-10">
          <p className="font-pirate text-xl mb-2">Ahoy, Trivia Seekers!</p>
          <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
