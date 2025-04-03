// src/utils/gamePlayUtils.ts
import { Question, Player } from '@/types/gameTypes';

// Define the list of themed emojis (keep as is)
export const THEMED_AVATAR_EMOJIS = [
  '🏴‍☠️', '🦜', '⚓️', '🧭', '🗺️', '⚔️', '💰', '💎', '☠️', '⛵️',
  '🏝️', '🧔', '👩‍🦰', '👨‍🦳', '🧑‍✈️', '🕵️', '🔭', '📜', '🗝️', '🐙'
];

// Simple hash function for string IDs (keep as is)
const simpleHashCode = (str: string): number => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0; // Convert to 32bit integer
  }
  return Math.abs(hash); // Ensure positive number
};

// Function to get a consistent emoji based on player ID (keep as is)
export const getEmojiForPlayerId = (playerId: string): string => {
  const hash = simpleHashCode(playerId);
  const index = hash % THEMED_AVATAR_EMOJIS.length;
  return THEMED_AVATAR_EMOJIS[index];
};

// --- NEW: Predefined Pirate Names ---
export const PREDEFINED_PIRATE_NAMES = [
    "One-Eyed Jack", "Calico Anne", "Salty Dog Sam", "Mad Morgan", "Cutlass Kate",
    "Barnacle Bill", "Stormy Sue", "Cannonball Chris", "Pegleg Pete", "Siren Sarah",
    "Ironhook", "Lady Vane", "Sharkbait", "Dead-Eye Dan", "Coral Queen",
    "Buccaneer Bob", "Rum Runner Riley", "Marauder Mike", "Sea Serpent Steve", "Goldtooth Gary"
]; // 20 names

// --- NEW: Function to assign a name based on User ID ---
export const getPirateNameForUserId = (userId: string): string => {
    if (!userId) {
        console.warn("Attempted to get pirate name for empty userId, returning default.");
        return PREDEFINED_PIRATE_NAMES[0]; // Return a default if ID is somehow missing
    }
    const hash = simpleHashCode(userId);
    const index = hash % PREDEFINED_PIRATE_NAMES.length;
    return PREDEFINED_PIRATE_NAMES[index];
};
// --- END NEW ---


// --- Mock Data (Keep for now, but Waiting Room won't use names from here) ---
// Mock questions for development (keep as is)
export const mockQuestions: Question[] = [
    // ... (keep mock questions as they are) ...
    { id: '1', text: "Which famous historical pirate sailed the seas with a terrifying black beard and became notorious for his fierce battles while commanding the powerful ship known as Queen Anne's Revenge?", category: "Pirate History", answers: [ { id: 'a', text: "Blackbeard the fearsome pirate", letter: "A" }, { id: 'b', text: "Captain Kidd treasure hunter", letter: "B" }, { id: 'c', text: "Anne Bonny fierce fighter", letter: "C" }, { id: 'd', text: "Jack Sparrow fictional captain", letter: "D" } ], correctAnswer: 'a', timeLimit: 20 }, { id: '2', text: "What was the name of the pirate code that governed behavior aboard pirate ships in the Golden Age of Piracy?", category: "Pirate Code", answers: [ { id: 'a', text: "The Black Spot", letter: "A" }, { id: 'b', text: "Articles of Agreement", letter: "B" }, { id: 'c', text: "Pirate's Charter", letter: "C" }, { id: 'd', text: "Rules of Engagement", letter: "D" } ], correctAnswer: 'b', timeLimit: 20 }, { id: '3', text: "Which island was a notorious pirate haven in the Caribbean during the Golden Age of Piracy?", category: "Pirate Havens", answers: [ { id: 'a', text: "Bermuda", letter: "A" }, { id: 'b', text: "Jamaica", letter: "B" }, { id: 'c', text: "Nassau (New Providence)", letter: "C" }, { id: 'd', text: "Cuba", letter: "D" } ], correctAnswer: 'c', timeLimit: 20 },
];

// Mock players for development - these IDs will be used for assignment, but names ignored
export const mockPlayers: Player[] = [
  { id: 'p1', name: 'IGNORED' }, // Name will be replaced by assigned name
  { id: 'p2', name: 'IGNORED' },
  { id: 'p3', name: 'IGNORED' },
  { id: 'p4', name: 'IGNORED' },
  { id: 'p5', name: 'IGNORED' },
];

// Helper function to find player by ID (keep as is)
export const getPlayerById = (players: Player[], id: string): Player | undefined => {
  return players.find(p => p.id === id);
};

// Calculate question text size class based on length (keep as is)
export const getQuestionTextClass = (text: string): string => {
  const wordCount = text.split(' ').length;
  if (wordCount > 20) return 'text-lg md:text-xl';
  if (wordCount > 15) return 'text-xl md:text-2xl';
  return 'text-2xl md:text-3xl';
};