import React, { useState, useEffect } from 'react';
import { View } from 'react-native';
// If AsyncStorage is not available, you'll need to install it:
// npm install @react-native-async-storage/async-storage
import AsyncStorage from '@react-native-async-storage/async-storage';
import OnboardingNavigator from './OnboardingNavigator';
import HomeScreen from '../screens/HomeScreen';

// Key for storing onboarding completed flag
const ONBOARDING_COMPLETED_KEY = 'onboarding_completed';

const AppNavigator: React.FC = () => {
  // State to track if onboarding is completed and if initial loading is done
  const [onboardingCompleted, setOnboardingCompleted] = useState<boolean | null>(null);
  
  // On first load, check if onboarding has been completed
  useEffect(() => {
    const checkOnboardingStatus = async () => {
      try {
        const value = await AsyncStorage.getItem(ONBOARDING_COMPLETED_KEY);
        setOnboardingCompleted(value === 'true');
      } catch (error) {
        console.error('Error checking onboarding status:', error);
        setOnboardingCompleted(false);
      }
    };
    
    checkOnboardingStatus();
  }, []);
  
  // Function to mark onboarding as completed and update state
  const handleOnboardingComplete = async () => {
    try {
      await AsyncStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
      setOnboardingCompleted(true);
    } catch (error) {
      console.error('Error saving onboarding status:', error);
    }
  };
  
  // Show loading state while checking onboarding status
  if (onboardingCompleted === null) {
    return <View style={{ flex: 1, backgroundColor: '#f8f9ff' }} />;
  }
  
  // If onboarding is completed, show HomeScreen, otherwise show OnboardingNavigator
  return onboardingCompleted ? (
    <HomeScreen />
  ) : (
    <OnboardingNavigator onOnboardingComplete={handleOnboardingComplete} />
  );
};

export default AppNavigator;