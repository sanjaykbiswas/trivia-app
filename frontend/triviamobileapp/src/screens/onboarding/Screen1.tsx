import React from 'react';
import OnboardingScreen from '../../components/onboarding/OnboardingScreen';
import { onboardingData, themes } from '../../assets/onboardingData';

interface Screen1Props {
  onContinue: () => void;
  paginationVisibility?: boolean;
}

const Screen1: React.FC<Screen1Props> = ({ onContinue, paginationVisibility = true }) => {
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
      paginationVisibility={paginationVisibility}
    />
  );
};

export default Screen1;