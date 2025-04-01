'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Typography from '../components/ui/Typography';
import Button from '../components/ui/Button';
import PackCard from '../components/game/PackCard';
import { Pack } from '../../lib/utils';

export default function SoloPage() {
  const router = useRouter();
  const [packs, setPacks] = useState<Pack[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch packs on component mount
  useEffect(() => {
    const fetchPacks = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/packs');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch packs: ${response.statusText}`);
        }
        
        const data = await response.json();
        setPacks(data.packs || []);
      } catch (err) {
        console.error('Error fetching packs:', err);
        setError('Failed to load trivia packs. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPacks();
  }, []);
  
  const handlePackSelect = (packId: string, packName: string) => {
    router.push(`/game/${packId}?name=${encodeURIComponent(packName)}`);
  };
  
  const handleBackClick = () => {
    router.push('/');
  };

  return (
    <div className="min-h-screen p-6">
      {/* Header with back button */}
      <div className="flex items-center mb-8">
        <button 
          className="w-10 h-10 rounded-full bg-background-light flex justify-center items-center mr-4"
          onClick={handleBackClick}
        >
          <Typography variant="bodyMedium">←</Typography>
        </button>
        <Typography variant="heading2">Choose your pack</Typography>
      </div>
      
      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-12 h-12 border-4 border-primary-main border-t-transparent rounded-full animate-spin mb-4"></div>
          <Typography variant="bodyMedium">Loading packs...</Typography>
        </div>
      )}
      
      {/* Error state */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <Typography 
            variant="bodyLarge" 
            color="text-error-main"
            className="mb-4 text-center"
          >
            {error}
          </Typography>
          <Button
            title="Try Again"
            onClick={() => window.location.reload()}
            variant="contained"
            size="medium"
          />
        </div>
      )}
      
      {/* No packs found */}
      {!loading && !error && packs.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12">
          <Typography 
            variant="bodyLarge"
            className="mb-4 text-center"
          >
            No trivia packs available. Please check back later.
          </Typography>
        </div>
      )}
      
      {/* Pack grid */}
      {!loading && !error && packs.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {packs.map((pack) => (
            <PackCard
              key={pack.id}
              title={pack.name}
              onClick={() => handlePackSelect(pack.id, pack.name)}
              testId={`pack-${pack.id}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}