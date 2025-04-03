
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import GameHeader from '@/components/GameHeader';

const CountdownScreen: React.FC = () => {
  const [count, setCount] = useState(3);
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setInterval(() => {
      setCount((prevCount) => {
        if (prevCount <= 1) {
          clearInterval(timer);
          // Navigate to gameplay after countdown finishes
          setTimeout(() => navigate('/gameplay'), 1500);
          return 0;
        }
        return prevCount - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [navigate]);

  return (
    <div className="min-h-screen flex flex-col">
      <GameHeader />
      
      <main className="flex-1 flex flex-col items-center justify-center">
        <div className="text-center">
          <h1 className="font-pirate text-5xl mb-8 text-pirate-navy">
            Game Starting in...
          </h1>
          
          {count > 0 ? (
            <div className="animate-bounce">
              <span className="font-pirate text-8xl text-pirate-gold">{count}</span>
            </div>
          ) : (
            <div className="animate-scale-in">
              <span className="font-pirate text-8xl text-pirate-accent">Ahoy!</span>
            </div>
          )}
          
          <div className="mt-10">
            <div className="ship-animation">
              <div className="ship">
                <span role="img" aria-label="ship">⛵</span>
              </div>
              <div className="waves">
                <span>〰️〰️〰️〰️〰️〰️〰️〰️</span>
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <style>
        {`
        .ship-animation {
          position: relative;
          height: 100px;
          width: 300px;
          margin: 0 auto;
        }
        
        .ship {
          position: absolute;
          top: 0;
          left: 0;
          font-size: 3rem;
          animation: sail 3s infinite linear;
        }
        
        .waves {
          position: absolute;
          bottom: 0;
          left: 0;
          font-size: 1.5rem;
          width: 100%;
          letter-spacing: -5px;
          animation: wave 2s infinite linear;
        }
        
        @keyframes sail {
          0% {
            transform: translateY(0) rotate(0deg);
          }
          25% {
            transform: translateY(-10px) rotate(5deg);
          }
          50% {
            transform: translateY(0) rotate(0deg);
          }
          75% {
            transform: translateY(-10px) rotate(-5deg);
          }
          100% {
            transform: translateY(0) rotate(0deg);
          }
        }
        
        @keyframes wave {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-20px);
          }
        }
        `}
      </style>
      
      <footer className="ocean-bg py-8">
        <div className="container mx-auto text-center text-white relative z-10">
          <p className="font-pirate text-xl mb-2">Prepare to set sail!</p>
          <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
};

export default CountdownScreen;
