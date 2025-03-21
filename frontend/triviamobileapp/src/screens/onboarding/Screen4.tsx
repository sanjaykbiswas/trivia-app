import React, { memo } from 'react';
import OnboardingScreen from '../../components/onboarding/OnboardingScreen';
import { onboardingData, themes } from '../../assets/onboardingData';

interface Screen4Props {
  onContinue: () => void;
  paginationVisibility?: boolean;
}

// Using memo to prevent unnecessary re-renders
const Screen4: React.FC<Screen4Props> = memo(({ 
  onContinue, 
  paginationVisibility = true 
}) => {
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
      paginationVisibility={paginationVisibility}
    />
  );
});

export default Screen4;