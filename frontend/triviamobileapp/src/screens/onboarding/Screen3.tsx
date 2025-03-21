import React from 'react';
import OnboardingScreen from '../../components/onboarding/OnboardingScreen';
import { onboardingData, themes } from '../../assets/onboardingData';

interface Screen3Props {
  onContinue: () => void;
  paginationVisibility?: boolean;
}

const Screen3: React.FC<Screen3Props> = ({ onContinue, paginationVisibility = true }) => {
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
      paginationVisibility={paginationVisibility}
    />
  );
};

export default Screen3;