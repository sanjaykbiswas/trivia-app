// src/screens/onboarding/Screen4.tsx
import React from 'react';
import OnboardingScreen from '../../components/onboarding/OnboardingScreen';
import { onboardingData, themes } from '../../assets/onboardingData';

interface Screen4Props {
  onContinue: () => void;
}

const Screen4: React.FC<Screen4Props> = ({ onContinue }) => {
  const data = onboardingData[3];
  const theme = themes[data.theme];
  
  return (
    <OnboardingScreen
      icon={data.icon}
      title={data.title}
      subtitle={data.subtitle}
      primaryColor={theme.primary}
      secondaryColor={theme.secondary}
      currentStep={3}
      totalSteps={4}
      onContinue={onContinue}
      floatingEmojis={data.floatingEmojis}
      buttonText="Get Started"
    />
  );
};

export default Screen4;