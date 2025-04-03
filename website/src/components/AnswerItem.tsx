// src/components/AnswerItem.tsx
import React from 'react';
import { Card } from '@/components/ui/card';
import PlayerAvatar from '@/components/PlayerAvatar';
import { Player, Answer } from '@/types/gameTypes';

interface AnswerItemProps {
  answer: Answer;
  isSelected: boolean;
  isCorrect: boolean;
  isRevealed: boolean; // Indicates if the correct/incorrect status should be shown
  onClick: () => void;
  playersWhoSelected: Player[];
  height: number | null; // For consistent height
}

const AnswerItem = React.forwardRef<HTMLDivElement, AnswerItemProps>(
  ({ answer, isSelected, isCorrect, isRevealed, onClick, playersWhoSelected, height }, ref) => {

    const revealedBgClass = isRevealed
      ? isCorrect ? 'bg-green-100' : isSelected ? 'bg-red-100' : ''
      : '';

    const selectionStyleClass = isSelected
        ? 'outline outline-4 outline-offset-[-1px] outline-pirate-gold border-transparent'
        : 'border border-pirate-navy/30';

    const showAvatars = isRevealed && playersWhoSelected && playersWhoSelected.length > 0;

    return (
      // REMOVED overflow-hidden from this Card
      <Card
        ref={ref}
        className={`p-4 cursor-pointer transition-all bg-pirate-parchment flex flex-col ${selectionStyleClass} ${revealedBgClass} hover:bg-pirate-navy/10 relative`} // Removed overflow-hidden
        onClick={onClick}
        style={height ? { height: `${height}px` } : {}}
      >
        {/* Answer Text Content */}
        <div className="flex items-start flex-grow">
          <div className="mr-3 flex-shrink-0 w-7 h-7 rounded-full bg-pirate-navy text-white flex items-center justify-center font-bold text-sm">
            {answer.letter}
          </div>
          <p className="font-medium text-lg break-words">{answer.text}</p>
        </div>

        {/* Player Avatars - Absolutely Positioned */}
        {showAvatars && (
          <div className="absolute bottom-0 right-4 transform translate-y-1/2 z-10">
            <div className="flex flex-row-reverse -space-x-2 space-x-reverse">
              {playersWhoSelected.map(player => (
                <PlayerAvatar
                  key={`${answer.id}-${player.id}`}
                  playerId={player.id}
                  name={player.name}
                  size="sm"
                  className="border-2 border-white bg-gray-300"
                />
              ))}
            </div>
          </div>
        )}
      </Card>
    );
  }
);

AnswerItem.displayName = 'AnswerItem';

export default AnswerItem;