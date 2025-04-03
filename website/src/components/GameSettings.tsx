// src/components/GameSettings.tsx
// --- START OF FILE ---
import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import PirateButton from '@/components/PirateButton';
import { Anchor } from 'lucide-react';

interface Category {
  title: string;
  icon: React.ReactNode;
  description: string;
  slug: string;
  focuses: string[];
}

interface GameSettingsProps {
  category: Category;
  onSubmit: (settings: {
    numberOfQuestions: number;
    timePerQuestion: number;
    focus: string;
  }) => void;
  mode: 'solo' | 'crew';
  role?: string;
}

const GameSettings: React.FC<GameSettingsProps> = ({
  category,
  onSubmit,
  mode,
  role
}) => {
  const [numberOfQuestions, setNumberOfQuestions] = useState(10);
  const [timePerQuestion, setTimePerQuestion] = useState(30);
  const focus = category.focuses[0] || 'General';

  const handleSubmit = () => {
    onSubmit({
      numberOfQuestions,
      timePerQuestion,
      focus
    });
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-4">
        <div className="bg-pirate-navy/10 p-3 rounded-full">
          {category.icon}
        </div>
        <div>
          <h2 className="pirate-heading text-2xl">{category.title}</h2>
          <p className="text-pirate-navy/70">{category.description}</p>
        </div>
      </div>

      {/* Game settings card */}
      <Card className="p-6 space-y-6">
        <h3 className="pirate-heading text-xl mb-4">Game Settings</h3>

        <div className="space-y-2">
          <div className="flex justify-between">
            <Label htmlFor="questions">Number of Questions</Label>
            <span className="text-pirate-navy/70 text-sm font-mono">{numberOfQuestions}</span>
          </div>
          <Slider
            id="questions"
            min={5}
            max={30}
            step={5}
            value={[numberOfQuestions]}
            onValueChange={(value) => setNumberOfQuestions(value[0])}
            className="py-4"
          />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <Label htmlFor="time">Time per Question (seconds)</Label>
            <span className="text-pirate-navy/70 text-sm font-mono">{timePerQuestion}s</span>
          </div>
          <Slider
            id="time"
            min={10}
            max={60}
            step={5}
            value={[timePerQuestion]}
            onValueChange={(value) => setTimePerQuestion(value[0])}
            className="py-4"
          />
        </div>
      </Card>

      {mode === 'crew' && role === 'captain' && (
        <div className="flex justify-center mt-8">
          {/* FIX: Added w-full class */}
          <PirateButton
            onClick={handleSubmit}
            className="px-8 py-3 text-lg w-full"
            variant="accent"
          >
            <Anchor className="h-5 w-5" />
            Gather the Crew
          </PirateButton>
        </div>
      )}

      {(mode === 'solo' || role !== 'captain') && (
        <div className="flex justify-center mt-8">
          {/* FIX: Added w-full class */}
          <PirateButton
            onClick={handleSubmit}
            className="px-8 py-3 text-lg w-full"
            variant="accent"
          >
            Start Adventure
          </PirateButton>
        </div>
      )}
    </div>
  );
};

export default GameSettings;
// --- END OF FILE ---