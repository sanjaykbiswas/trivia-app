import React, { useState, useEffect } from 'react';
import { StatusBar } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

// Screens
import HomeScreen from '../screens/HomeScreen';
import OnboardingNavigator from './OnboardingNavigator';

// For testing, you can import built-in first-run detection
// import AsyncStorage from '@react-native-async-storage/async-storage';

interface AppNavigatorProps {
  skipOnboarding?: boolean;
}

// Modify this interface to match your OnboardingNavigator component structure
interface OnboardingProps {
  onComplete: () => void;
}

const AppNavigator: React.FC<AppNavigatorProps> = ({ skipOnboarding = false }) => {
  // Track whether the user has completed onboarding
  const [onboardingComplete, setOnboardingComplete] = useState<boolean>(skipOnboarding);
  
  // Check if onboarding has been completed previously
  useEffect(() => {
    // Here you would typically check AsyncStorage or some other persistent storage
    // For example:
    // const checkOnboarding = async () => {
    //   try {
    //     const value = await AsyncStorage.getItem('@onboarding_complete');
    //     if (value === 'true') {
    //       setOnboardingComplete(true);
    //     }
    //   } catch (error) {
    //     console.error('Error checking onboarding status:', error);
    //   }
    // };
    // 
    // checkOnboarding();
    
    // For now, we'll just use the skipOnboarding prop
    setOnboardingComplete(skipOnboarding);
  }, [skipOnboarding]);
  
  // Handler for when onboarding is complete
  const handleOnboardingComplete = () => {
    // Here you would typically save to AsyncStorage
    // For example:
    // AsyncStorage.setItem('@onboarding_complete', 'true');
    setOnboardingComplete(true);
  };
  
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar 
          barStyle="light-content"
          backgroundColor="transparent"
          translucent 
        />
        
        {onboardingComplete ? (
          // Main App Flow
          <HomeScreen />
        ) : (
          // Onboarding Flow
          <OnboardingNavigator onComplete={handleOnboardingComplete} />
        )}
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
};

export default AppNavigator;