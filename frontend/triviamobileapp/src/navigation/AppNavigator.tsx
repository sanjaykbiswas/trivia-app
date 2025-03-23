import React, { useState } from 'react';
import { SplashScreen, OnboardingScreen } from '../screens';

/**
 * AppNavigator component
 * Handles navigation between screens in the app
 * This is a simple implementation without a navigation library
 * In a real app, you would use React Navigation
 */
const AppNavigator: React.FC = () => {
  // Current screen state
  const [currentScreen, setCurrentScreen] = useState<'splash' | 'onboarding'>('splash');

  // Navigation handlers
  const handleSplashComplete = () => {
    setCurrentScreen('onboarding');
  };

  const handleGetStarted = () => {
    // Navigate to sign up or home based on your requirements
    console.log('Get Started pressed');
    // This would typically navigate to another screen
    // setCurrentScreen('home');
  };

  const handleSignIn = () => {
    // Navigate to sign in screen
    console.log('Sign In pressed');
    // This would typically navigate to another screen
    // setCurrentScreen('signIn');
  };

  // Render the current screen
  if (currentScreen === 'splash') {
    return <SplashScreen onSplashComplete={handleSplashComplete} />;
  }

  return (
    <OnboardingScreen
      onGetStarted={handleGetStarted}
      onSignIn={handleSignIn}
    />
  );
};

export default AppNavigator;