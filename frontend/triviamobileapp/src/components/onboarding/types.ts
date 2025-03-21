import { DimensionValue } from 'react-native';

export interface FloatingElement {
  emoji: string;
  position: {
    top?: string | number;
    bottom?: string | number;
    left?: string | number;
    right?: string | number;
  };
}

export interface OnboardingScreenProps {
  // Content props
  icon: string;
  title: string;
  subtitle: string;
  
  // Style props
  primaryColor: string;
  secondaryColor: string;
  
  // Navigation props
  currentStep: number;
  totalSteps: number;
  onContinue: () => void;
  
  // Optional props
  buttonText?: string;
  floatingEmojis?: FloatingElement[];
  
  // Added prop to control pagination visibility
  paginationVisibility?: boolean;
}