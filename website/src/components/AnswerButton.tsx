// src/components/AnswerButton.tsx
// --- START OF FILE ---
import React from 'react';
import PirateButton from '@/components/PirateButton';

// Define and export the props interface
export interface AnswerButtonProps {
  onSubmit: () => void;
  disabled: boolean;
  isAnswered: boolean;
  isCorrect: boolean;
}

const AnswerButton: React.FC<AnswerButtonProps> = ({
  onSubmit,
  disabled,
  isAnswered,
  isCorrect
}) => {
  return (
    // REMOVED mt-4 from this div
    <div className="flex justify-center"> {/* Removed mt-4 */}
      <PirateButton
        onClick={onSubmit}
        disabled={disabled}
        // Updated line below - removed 'animate-bounce'
        className={`py-3 px-8 text-lg ${isAnswered ? (isCorrect ? '' : 'animate-shake') : ''}`}
        variant={isAnswered ? (isCorrect ? 'accent' : 'primary') : 'accent'}
      >
        {/* Dynamic button text based on state */}
        {isAnswered ? (isCorrect ? "Booty Secured! 💰" : "Booty Lost! 😢") : "Secure the Booty"}
      </PirateButton>
    </div>
  );
};

export default AnswerButton;
// --- END OF FILE ---