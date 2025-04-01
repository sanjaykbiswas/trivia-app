import React from 'react';
import Typography from '../ui/Typography';
import Button from '../ui/Button';

interface FeedbackPanelProps {
  isCorrect: boolean;
  correctAnswer: string;
  onNextPress: () => void;
  isLastQuestion: boolean;
}

export const FeedbackPanel: React.FC<FeedbackPanelProps> = ({
  isCorrect,
  correctAnswer,
  onNextPress,
  isLastQuestion,
}) => {
  return (
    <div className="fixed left-0 right-0 bottom-0 bg-background-default p-6 rounded-t-3xl shadow-lg border-t border-gray-200 animate-slide-up">
      <Typography
        variant="heading3"
        color={isCorrect ? 'text-success-main' : 'text-error-main'}
        className="text-center font-bold mb-1"
      >
        {isCorrect ? 'Correct!' : 'Incorrect'}
      </Typography>

      <Typography
        variant="bodyMedium"
        className="text-center mb-6"
      >
        {isCorrect
          ? 'Great job!'
          : `The correct answer is: ${correctAnswer}`}
      </Typography>

      <Button
        title={isLastQuestion ? 'Finish Quiz' : 'Next Question'}
        onClick={onNextPress}
        variant="contained"
        size="large"
        fullWidth
        className="mt-4"
      />
    </div>
  );
};

export default FeedbackPanel;