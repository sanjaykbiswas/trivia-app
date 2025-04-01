import React from 'react';
import Typography from '../ui/Typography';

interface PackCardProps {
  title: string;
  onClick: () => void;
  className?: string;
  testId?: string;
}

const PackCard: React.FC<PackCardProps> = ({
  title,
  onClick,
  className = '',
  testId,
}) => {
  return (
    <button
      className={`w-40 h-40 bg-gray-200 rounded-2xl overflow-hidden shadow hover:shadow-md transition-shadow ${className}`}
      onClick={onClick}
      data-testid={testId}
    >
      <div className="flex flex-col h-full p-3 justify-center items-center">
        <Typography 
          variant="bodyMedium" 
          className="font-semibold text-center"
        >
          {title}
        </Typography>
      </div>
    </button>
  );
};

export default PackCard;