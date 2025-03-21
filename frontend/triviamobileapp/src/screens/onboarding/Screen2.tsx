// src/screens/onboarding/Screen2.tsx
import React from 'react';
import OnboardingScreen from '../../components/onboarding/OnboardingScreen';
import { onboardingData, themes } from '../../assets/onboardingData';

interface Screen2Props {
  onContinue: () => void;
  paginationVisibility?: boolean;
}

const Screen2: React.FC<Screen2Props> = ({ onContinue, paginationVisibility = true }) => {
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
      paginationVisibility={paginationVisibility}
    />
  );
};

export default Screen2;