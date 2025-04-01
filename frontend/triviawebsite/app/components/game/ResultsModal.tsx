import React from 'react';
import Typography from '../ui/Typography';
import Button from '../ui/Button';

interface ResultsModalProps {
  score: number;
  totalQuestions: number;
  onClose: () => void;
  isOpen: boolean;
}

export const ResultsModal: React.FC<ResultsModalProps> = ({
  score,
  totalQuestions,
  onClose,
  isOpen,
}) => {
  if (!isOpen) return null;

  // Calculate percentage
  const percentage = Math.round((score / totalQuestions) * 100);
  
  // Determine message based on score
  const getMessage = () => {
    if (percentage >= 90) return 'Excellent!';
    if (percentage >= 70) return 'Great job!';
    if (percentage >= 50) return 'Good effort!';
    return 'Keep practicing!';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-3xl p-8 w-11/12 max-w-md animate-scale-in">
        <Typography variant="heading2" className="text-center mb-2">
          Quiz Complete!
        </Typography>
        
        <Typography variant="heading1" className="text-center text-primary-main mb-4">
          {score}/{totalQuestions}
        </Typography>
        
        <Typography variant="heading4" className="text-center mb-6">
          {getMessage()}
        </Typography>
        
        <div className="w-full h-4 bg-gray-200 rounded-full mb-6">
          <div 
            className="h-full bg-primary-main rounded-full"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        
        <Button
          title="Back to Home"
          onClick={onClose}
          variant="contained"
          size="large"
          fullWidth
        />
      </div>
    </div>
  );
};

export default ResultsModal;