// src/navigation/OnboardingNavigator.tsx
import React, { useState } from 'react';
import { View } from 'react-native';
import Screen1 from '../screens/onboarding/Screen1.tsx';
import Screen2 from '../screens/onboarding/Screen2.tsx';
import Screen3 from '../screens/onboarding/Screen3.tsx';
import Screen4 from '../screens/onboarding/Screen4.tsx';

const OnboardingNavigator: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState(0);
  
  const handleContinue = () => {
    if (currentScreen < 3) {
      setCurrentScreen(currentScreen + 1);
    } else {
      // Navigate to main app or login
      console.log('Onboarding complete');
    }
  };
  
  const renderCurrentScreen = () => {
    switch (currentScreen) {
      case 0:
        return <Screen1 onContinue={handleContinue} />;
      case 1:
        return <Screen2 onContinue={handleContinue} />;
      case 2:
        return <Screen3 onContinue={handleContinue} />;
      case 3:
        return <Screen4 onContinue={handleContinue} />;
      default:
        return <Screen1 onContinue={handleContinue} />;
    }
  };
  
  return (
    <View style={{ flex: 1 }}>
      {renderCurrentScreen()}
    </View>
  );
};

export default OnboardingNavigator;