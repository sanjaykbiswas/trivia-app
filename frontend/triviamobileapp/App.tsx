import 'react-native-gesture-handler';  // This import must be first!
import { enableScreens } from 'react-native-screens';
enableScreens(); // Enable native screens implementation

import React from 'react';
import { StatusBar, View } from 'react-native';
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
            <NavigationContainer ref={navigationRef}>
              <AppNavigator />
            </NavigationContainer>
          </SafeAreaProvider>
        </AuthProvider>
      </ErrorBoundary>
    </GestureHandlerRootView>
  );
}

export default App;