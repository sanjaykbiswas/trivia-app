// src/screens/onboarding/Screen2.tsx
import React from 'react';
import OnboardingScreen from '../../components/onboarding/OnboardingScreen';
import { onboardingData, themes } from '../../assets/onboardingData';

interface Screen2Props {
  onContinue: () => void;
}

const Screen2: React.FC<Screen2Props> = ({ onContinue }) => {
  const data = onboardingData[1];
  const theme = themes[data.theme];
  
  return (
    <OnboardingScreen
      icon={data.icon}
      title={data.title}
      subtitle={data.subtitle}
      primaryColor={theme.primary}
      secondaryColor={theme.secondary}
      currentStep={1}
      totalSteps={4}
      onContinue={onContinue}
      floatingEmojis={data.floatingEmojis}
    />
  );
};

export default Screen2;