// src/components/QuestionCard.tsx
import React from 'react';
import { Card } from '@/components/ui/card';
import { Player, Answer } from '@/types/gameTypes';
import AnswerButton, { AnswerButtonProps } from './AnswerButton';
import AnswerItem from './AnswerItem';

interface QuestionCardProps {
  questionText: string;
  answers: Answer[];
  selectedAnswer: string | null;
  isAnswered: boolean; // Still needed to pass down as isRevealed
  correctAnswer: string;
  onAnswerSelect: (answerId: string) => void;
  playerSelectionsByAnswer: Record<string, Player[]>;
  maxHeight: number | null;
  questionTextClass: string;
  answerRefs: React.MutableRefObject<(HTMLDivElement | null)[]>;
  answerButtonProps: Omit<AnswerButtonProps, 'children'>;
}

const QuestionCard: React.FC<QuestionCardProps> = ({
  questionText,
  answers,
  selectedAnswer,
  isAnswered, // Used for isRevealed prop
  correctAnswer,
  onAnswerSelect,
  playerSelectionsByAnswer,
  maxHeight,
  questionTextClass,
  answerRefs,
  answerButtonProps
}) => {
  return (
    <Card className="bg-white p-6 shadow-lg w-full flex flex-col">
      <h2 className={`${questionTextClass} mb-8 mt-2 text-pirate-black text-center line-clamp-5 px-0 md:px-4`}>
        {questionText}
      </h2>

      {/* REMOVED mb-10 from this grid div */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 flex-grow"> {/* Removed mb-10 */}
        {answers.map((answer, index) => (
          <AnswerItem
            key={answer.id}
            ref={el => answerRefs.current[index] = el} // Pass ref down
            answer={answer}
            isSelected={selectedAnswer === answer.id}
            isCorrect={answer.id === correctAnswer}
            isRevealed={isAnswered}
            onClick={() => onAnswerSelect(answer.id)}
            playersWhoSelected={playerSelectionsByAnswer[answer.id] || []}
            height={maxHeight}
          />
        ))}
      </div>

      {/* ADDED wrapper div with mt-6 */}
      <div className="mt-6"> {/* Added this wrapper */}
        <AnswerButton {...answerButtonProps} />
      </div>
    </Card>
  );
};

export default QuestionCard;