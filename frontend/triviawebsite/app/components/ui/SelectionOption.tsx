import React from 'react';
import Typography from './Typography';

interface SelectionOptionProps {
  title: string;
  subtitle: string;
  emoji?: string;
  onPress: () => void;
  className?: string;
  testId?: string;
}

/**
 * SelectionOption component
 * Card-like option button with title, subtitle and optional emoji
 */
const SelectionOption: React.FC<SelectionOptionProps> = ({
  title,
  subtitle,
  emoji,
  onPress,
  className = '',
  testId,
}) => {
  return (
    <button
      className={`flex flex-row items-center bg-background-light rounded-2xl p-4 mb-4 shadow-sm hover:shadow transition-all ${className}`}
      onClick={onPress}
      data-testid={testId}
    >
      {emoji && (
        <div className="w-10 h-10 flex justify-center items-center mr-4">
          <span className="text-3xl">{emoji}</span>
        </div>
      )}
      
      <div className="flex-1">
        <Typography variant="heading5" className="mb-1">
          {title}
        </Typography>
        <Typography 
          variant="bodySmall" 
          color="text-text-secondary"
          className="leading-5"
        >
          {subtitle}
        </Typography>
      </div>
    </button>
  );
};

export default SelectionOption;