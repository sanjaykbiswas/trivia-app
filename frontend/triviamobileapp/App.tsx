import 'react-native-gesture-handler';  // This import must be first!
import { enableScreens } from 'react-native-screens';
enableScreens(); // Enable native screens implementation

import React, { useEffect } from 'react';
import { StatusBar, View, Linking, Platform } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { NavigationContainer } from '@react-navigation/native';
import { AppNavigator } from './src/navigation';
import { navigationRef } from './src/navigation/navigationRef';
import { ErrorBoundary } from './src/components/common';
import { AuthProvider } from './src/contexts/AuthContext';

/**
 * Main App component
 */
function App(): React.JSX.Element {
  // Deep linking configuration for magic link authentication
  const linking = {
    prefixes: ['triviamobileapp://', 'https://triviamobileapp.com'],
    
    // Handle auth redirects specifically
    config: {
      screens: {
        // Add your screen mappings
        Home: 'home',
        Onboarding: 'onboarding',
        SignIn: 'signin',
      },
    },
    
    // Custom function to handle URLs that don't match any screen
    async getInitialURL() {
      // Get the initial URL if the app was launched from an external URL
      const url = await Linking.getInitialURL();
      
      if (url != null) {
        // Check if the URL is an auth callback
        if (url.includes('auth/v1/callback')) {
          // Return a specific URL that will be handled in the nested navigator
          return 'signin';
        }
      }
      
      return url;
    },
    
    // Custom function to subscribe to incoming links
    subscribe(listener: (url: string) => void) {
      // Listen to incoming links from deep linking
      const linkingSubscription = Linking.addEventListener('url', ({ url }) => {
        // Check if the URL is an auth callback
        if (url.includes('auth/v1/callback')) {
          // Extract the token part or just redirect to a specific screen
          listener('signin');
          return;
        }
        
        listener(url);
      });
      
      return () => {
        // Clean up the event listener when the component unmounts
        linkingSubscription.remove();
      };
    },
  };

  // Handle initial URL on app launch
  useEffect(() => {
    const handleInitialURL = async () => {
      const url = await Linking.getInitialURL();
      if (url) {
        console.log('App opened with URL:', url);
        // The NavigationContainer will handle the deep link via the linking prop
      }
    };
    
    handleInitialURL();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ErrorBoundary>
        <AuthProvider>
          <SafeAreaProvider>
            <StatusBar 
              barStyle="dark-content" 
              backgroundColor="transparent" 
              translucent
            />
            <NavigationContainer ref={navigationRef} linking={linking}>
              <AppNavigator />
            </NavigationContainer>
          </SafeAreaProvider>
        </AuthProvider>
      </ErrorBoundary>
    </GestureHandlerRootView>
  );
}

export default App;