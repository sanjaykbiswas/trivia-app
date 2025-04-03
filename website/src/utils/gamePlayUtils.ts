import { Question, Player } from '@/types/gameTypes';

// Define the list of themed emojis
export const THEMED_AVATAR_EMOJIS = [
  '🏴‍☠️', '🦜', '⚓️', '🧭', '🗺️', '⚔️', '💰', '💎', '☠️', '⛵️',
  '🏝️', '🧔', '👩‍🦰', '👨‍🦳', '🧑‍✈️', '🕵️', '🔭', '📜', '🗝️', '🐙'
]; // 20 emojis

// Simple hash function for string IDs (consistent per session)
const simpleHashCode = (str: string): number => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0; // Convert to 32bit integer
  }
  return Math.abs(hash); // Ensure positive number
};

// Function to get a consistent emoji based on player ID
export const getEmojiForPlayerId = (playerId: string): string => {
  const hash = simpleHashCode(playerId);
  const index = hash % THEMED_AVATAR_EMOJIS.length;
  return THEMED_AVATAR_EMOJIS[index];
};


// --- Mock Data ---

// Mock questions for development
export const mockQuestions: Question[] = [
  {
    id: '1',
    text: "Which famous historical pirate sailed the seas with a terrifying black beard and became notorious for his fierce battles while commanding the powerful ship known as Queen Anne's Revenge?",
    category: "Pirate History",
    answers: [
      { id: 'a', text: "Blackbeard the fearsome pirate", letter: "A" },
      { id: 'b', text: "Captain Kidd treasure hunter", letter: "B" },
      { id: 'c', text: "Anne Bonny fierce fighter", letter: "C" },
      { id: 'd', text: "Jack Sparrow fictional captain", letter: "D" }
    ],
    correctAnswer: 'a',
    timeLimit: 20
  },
  {
    id: '2',
    text: "What was the name of the pirate code that governed behavior aboard pirate ships in the Golden Age of Piracy?",
    category: "Pirate Code",
    answers: [
      { id: 'a', text: "The Black Spot", letter: "A" },
      { id: 'b', text: "Articles of Agreement", letter: "B" },
      { id: 'c', text: "Pirate's Charter", letter: "C" },
      { id: 'd', text: "Rules of Engagement", letter: "D" }
    ],
    correctAnswer: 'b',
    timeLimit: 20
  },
  {
    id: '3',
    text: "Which island was a notorious pirate haven in the Caribbean during the Golden Age of Piracy?",
    category: "Pirate Havens",
    answers: [
      { id: 'a', text: "Bermuda", letter: "A" },
      { id: 'b', text: "Jamaica", letter: "B" },
      { id: 'c', text: "Nassau (New Providence)", letter: "C" },
      { id: 'd', text: "Cuba", letter: "D" }
    ],
    correctAnswer: 'c',
    timeLimit: 20
  },
];

// Mock players for development - REMOVE the avatar property
export const mockPlayers: Player[] = [
  { id: 'p1', name: 'Captain Jack' }, // No avatar needed here anymore
  { id: 'p2', name: 'Blackbeard' },
  { id: 'p3', name: 'Anne Bonny' },
  { id: 'p4', name: 'Salty Dog Pete' },
  { id: 'p5', name: 'Scurvy Sam' },
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