import 'react-native-gesture-handler';  // This import must be first!
import React, { useEffect, useState } from 'react';
import { StatusBar, LogBox, Text, View, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

// Import screens directly as a temporary measure for debugging
import { SplashScreen } from './src/screens/splash';
import { OnboardingScreen } from './src/screens/onboarding';

// Silence warnings that might appear with animations
LogBox.ignoreLogs([
  'Sending `onAnimatedValueUpdate` with no listeners registered',
  'Non-serializable values were found in the navigation state',
  'Animated: `useNativeDriver` was not specified',
  'NativeAnimatedModule'
]);

/**
 * Simple App component for debugging
 * Directly uses screens without navigation
 */
function App(): React.JSX.Element {
  // Current screen state
  const [currentScreen, setCurrentScreen] = useState<'splash' | 'onboarding'>('splash');

  // Navigation handlers
  const handleSplashComplete = () => {
    console.log('Splash complete, transitioning to onboarding');
    setCurrentScreen('onboarding');
  };

  const handleGetStarted = () => {
    console.log('Get Started pressed');
    // This would typically navigate to another screen
  };

  const handleSignIn = () => {
    console.log('Sign In pressed');
    // This would typically navigate to another screen
  };

  // Render the current screen
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar 
          barStyle="dark-content" 
          backgroundColor="transparent" 
          translucent a
        />
        
        {/* Render splash or onboarding directly for debugging */}
        {currentScreen === 'splash' ? (
          <SplashScreen onSplashComplete={handleSplashComplete} />
        ) : (
          <OnboardingScreen
            onGetStarted={handleGetStarted}
            onSignIn={handleSignIn}
          />
        )}
        
        {/* Debug indicator to ensure rendering is happening */}
        <View style={styles.debugContainer}>
          <Text style={styles.debugText}>
            Current screen: {currentScreen}
          </Text>
        </View>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  debugContainer: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0,0,0,0.7)',
    padding: 10,
    borderRadius: 5,
  },
  debugText: {
    color: 'white',
    fontSize: 12,
  },
});

export default App;