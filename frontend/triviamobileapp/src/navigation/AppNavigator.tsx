import React, { useState, useEffect, useCallback } from 'react';
import { View, StatusBar } from 'react-native';
// Uncomment if implementing AsyncStorage for persistence
// import AsyncStorage from '@react-native-async-storage/async-storage';

// Screens
import HomeScreen from '../screens/HomeScreen';
import OnboardingNavigator from './OnboardingNavigator';
import ErrorBoundary from '../components/ErrorBoundary';

interface AppNavigatorProps {
  skipOnboarding?: boolean;
}

const AppNavigator: React.FC<AppNavigatorProps> = ({ skipOnboarding = false }) => {
  // Track whether the user has completed onboarding
  const [onboardingComplete, setOnboardingComplete] = useState<boolean>(skipOnboarding);
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);
  
  // Check if onboarding has been completed previously
  useEffect(() => {
    // Uncomment to implement AsyncStorage persistence
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
    // if (!skipOnboarding) {
    //   checkOnboarding();
    // }
    
    // For now, we'll just use the skipOnboarding prop
    setOnboardingComplete(skipOnboarding);
  }, [skipOnboarding]);
  
  // Update StatusBar based on current screen
  useEffect(() => {
    StatusBar.setBarStyle(
      onboardingComplete ? "light-content" : "dark-content", 
      true
    );
  }, [onboardingComplete]);
  
  // Handler for when onboarding is complete
  const handleOnboardingComplete = useCallback(() => {
    setIsTransitioning(true);
    
    // Uncomment to implement AsyncStorage persistence
    // AsyncStorage.setItem('@onboarding_complete', 'true')
    //   .catch(err => console.error('Error saving onboarding state:', err));
    
    // Add delay to ensure clean transition
    setTimeout(() => {
      setOnboardingComplete(true);
      // Small additional delay before finishing transition
      setTimeout(() => {
        setIsTransitioning(false);
      }, 100);
    }, 300);
  }, []);
  
  if (isTransitioning) {
    // Simple loading screen during transition
    return <View style={{ flex: 1, backgroundColor: '#f8f9ff' }} />;
  }
  
  return onboardingComplete ? (
    <ErrorBoundary>
      <HomeScreen />
    </ErrorBoundary>
  ) : (
    <OnboardingNavigator onComplete={handleOnboardingComplete} />
  );
};

export default AppNavigator;