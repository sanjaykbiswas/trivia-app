
import React from 'react';

interface QuestionTimerProps {
  timeRemaining: number;
  totalTime: number;
}

const QuestionTimer: React.FC<QuestionTimerProps> = ({ timeRemaining, totalTime }) => {
  const progressPercentage = (timeRemaining / totalTime) * 100;
  const displayTime = Math.max(0, Math.ceil(timeRemaining)).toString();

  return (
    <div className="mb-6">
      <div className="flex items-center justify-center mb-2">
        <div className="bg-gray-200 rounded-full w-full max-w-md h-3 overflow-hidden">
          <div 
            className={`h-full transition-all duration-300 ${
              progressPercentage > 66 ? 'bg-green-500' :
              progressPercentage > 33 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
        <span className="text-lg font-medium ml-3">{displayTime}s</span>
      </div>
    </div>
  );
};

export default QuestionTimer;
