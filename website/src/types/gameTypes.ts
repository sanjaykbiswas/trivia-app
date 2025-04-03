export interface Answer {
  id: string;
  text: string;
  letter: string;
}

export interface Question {
  id: string;
  text: string;
  category: string;
  answers: Answer[];
  correctAnswer: string;
  timeLimit: number;
}

export interface Player {
  id: string;
  name: string;
  avatar?: string; // This should hold the emoji, initials, or URL
}

export interface PlayerSelection {
  playerId: string;
  answerId: string;
}