import React from 'react';
import Typography from '../ui/Typography';

interface AnswerOptionProps {
  letter: string;
  text: string;
  isSelected?: boolean;
  isCorrect?: boolean;
  isIncorrect?: boolean;
  onClick: () => void;
  className?: string;
  disabled?: boolean;
  testId?: string;
}

export const AnswerOption: React.FC<AnswerOptionProps> = ({
  letter,
  text,
  isSelected = false,
  isCorrect = false,
  isIncorrect = false,
  onClick,
  className = '',
  disabled = false,
  testId,
}) => {
  // Determine the style based on the current state
  const getContainerClass = () => {
    if (isCorrect) {
      return 'bg-success-main border-success-main';
    }
    if (isIncorrect) {
      return 'bg-error-main border-error-main';
    }
    if (isSelected) {
      return 'bg-primary-main border-primary-main';
    }
    return 'bg-background-light border-gray-300';
  };

  // Text color based on state
  const getTextColor = () => {
    if (isSelected || isCorrect || isIncorrect) {
      return 'text-primary-contrastText';
    }
    return 'text-text-primary';
  };

  return (
    <button
      className={`flex flex-row items-center p-4 rounded-2xl border mb-3 transition-colors ${getContainerClass()} ${className}`}
      onClick={onClick}
      disabled={disabled}
      data-testid={testId}
    >
      <div className={`w-8 h-8 rounded-full bg-background-default flex justify-center items-center mr-4`}>
        <Typography
          variant="bodyMedium"
          className="font-bold"
        >
          {letter}
        </Typography>
      </div>
      <Typography
        variant="bodyMedium"
        className={`flex-1 font-medium ${getTextColor()}`}
      >
        {text}
      </Typography>
    </button>
  );
};

export default AnswerOption;