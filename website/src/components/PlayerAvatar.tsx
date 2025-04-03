import React from 'react';
import { Avatar, AvatarFallback } from "@/components/ui/avatar"; // No need for AvatarImage now
import { getEmojiForPlayerId } from '@/utils/gamePlayUtils'; // Import the helper

interface PlayerAvatarProps {
  name: string; // Keep name for accessibility/tooltips if needed later
  playerId: string; // Use playerId for consistent emoji generation
  size?: "sm" | "md" | "lg";
  className?: string;
}

const PlayerAvatar: React.FC<PlayerAvatarProps> = ({
  playerId, // Receive playerId
  // name is kept in props for potential future use, but not directly used for display now
  size = "md",
  className = ""
}) => {
  // Get the consistent emoji for this player ID
  const selectedEmoji = getEmojiForPlayerId(playerId);

  const sizeClasses = {
    // Adjust text size slightly for emojis if needed
    sm: "h-6 w-6 text-sm",
    md: "h-8 w-8 text-base",
    lg: "h-10 w-10 text-lg"
  };

  return (
    // Apply base classes and size-specific classes
    <Avatar className={`${sizeClasses[size]} ${className}`}>
      {/* Fallback always shows the selected emoji with a grey background */}
      {/* Use a neutral grey - adjust hex/tailwind class as desired */}
      <AvatarFallback className="bg-gray-300 text-gray-800 flex items-center justify-center">
        {selectedEmoji}
      </AvatarFallback>
    </Avatar>
  );
};

export default PlayerAvatar;