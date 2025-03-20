// src/screens/onboarding/Screen1.tsx
import React from 'react';
import OnboardingScreen from '../../components/onboarding/OnboardingScreen';
import { onboardingData, themes } from '../../assets/onboardingData';

interface Screen1Props {
  onContinue: () => void;
}

const Screen1: React.FC<Screen1Props> = ({ onContinue }) => {
  const data = onboardingData[0];
  const theme = themes[data.theme];
  
  return (
    <OnboardingScreen
      icon={data.icon}
      title={data.title}
      subtitle={data.subtitle}
      primaryColor={theme.primary}
      secondaryColor={theme.secondary}
      currentStep={0}
      totalSteps={4}
      onContinue={onContinue}
      floatingEmojis={data.floatingEmojis}
    />
  );
};

export default Screen1;