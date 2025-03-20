// src/screens/onboarding/Screen3.tsx
import React from 'react';
import OnboardingScreen from '../../components/onboarding/OnboardingScreen';
import { onboardingData, themes } from '../../assets/onboardingData';

interface Screen3Props {
  onContinue: () => void;
}

const Screen3: React.FC<Screen3Props> = ({ onContinue }) => {
  const data = onboardingData[2];
  const theme = themes[data.theme];
  
  return (
    <OnboardingScreen
      icon={data.icon}
      title={data.title}
      subtitle={data.subtitle}
      primaryColor={theme.primary}
      secondaryColor={theme.secondary}
      currentStep={2}
      totalSteps={4}
      onContinue={onContinue}
      floatingEmojis={data.floatingEmojis}
    />
  );
};

export default Screen3;