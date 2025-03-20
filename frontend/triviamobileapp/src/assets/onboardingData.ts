// src/assets/onboardingData.ts

import { TextStyle } from 'react-native';

export interface OnboardingScreenData {
  id: string;
  icon: string;
  title: string;
  subtitle: string;
  theme: keyof typeof themes;
  floatingEmojis: Array<{
    emoji: string;
    position: {
      top?: string | number;
      bottom?: string | number;
      left?: string | number;
      right?: string | number;
    };
  }>;
}

export const themes = {
  purple: {
    primary: '#7B61FF',
    secondary: '#899DFF',
  },
  blue: {
    primary: '#2196F3',
    secondary: '#64B5F6',
  },
  green: {
    primary: '#4CAF50',
    secondary: '#81C784',
  },
  orange: {
    primary: '#FF9800',
    secondary: '#FFCC80',
  },
};

export const onboardingData: OnboardingScreenData[] = [
  {
    id: 'welcome',
    icon: '🧠',
    title: 'Welcome to\nOpen Trivia!',
    subtitle: 'Get ready to challenge your knowledge in exciting new ways',
    theme: 'purple',
    floatingEmojis: [
      {
        emoji: '❓',
        position: { top: '15%', left: '10%' }
      },
      {
        emoji: '💡',
        position: { top: '25%', right: '10%' }
      },
      {
        emoji: '🧠',
        position: { bottom: '30%', left: '15%' }
      },
      {
        emoji: '🎓',
        position: { bottom: '25%', right: '20%' }
      }
    ]
  },
  {
    id: 'categories',
    icon: '🏆',
    title: 'Endless\nCategories',
    subtitle: 'From science to pop culture, history to sports—find trivia in any subject you love',
    theme: 'blue',
    floatingEmojis: [
      {
        emoji: '🔬',
        position: { top: '18%', left: '12%' }
      },
      {
        emoji: '🎬',
        position: { top: '22%', right: '15%' }
      },
      {
        emoji: '📚',
        position: { bottom: '28%', left: '10%' }
      },
      {
        emoji: '⚽',
        position: { bottom: '22%', right: '15%' }
      }
    ]
  },
  {
    id: 'difficulty',
    icon: '🎯',
    title: 'Choose Your\nChallenge',
    subtitle: 'Set your own difficulty level—from beginner-friendly to expert-level brain teasers',
    theme: 'green',
    floatingEmojis: [
      {
        emoji: '👶',
        position: { top: '20%', left: '13%' }
      },
      {
        emoji: '👨‍🎓',
        position: { top: '28%', right: '12%' }
      },
      {
        emoji: '🧩',
        position: { bottom: '32%', left: '18%' }
      },
      {
        emoji: '🔥',
        position: { bottom: '25%', right: '18%' }
      }
    ]
  },
  {
    id: 'play',
    icon: '🎮',
    title: 'Ready to\nPlay?',
    subtitle: 'Challenge yourself or compete with friends—learn something new with every question',
    theme: 'orange',
    floatingEmojis: [
      {
        emoji: '👥',
        position: { top: '15%', left: '15%' }
      },
      {
        emoji: '🏅',
        position: { top: '25%', right: '15%' }
      },
      {
        emoji: '🎲',
        position: { bottom: '28%', left: '12%' }
      },
      {
        emoji: '🚀',
        position: { bottom: '22%', right: '16%' }
      }
    ]
  }
];