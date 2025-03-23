import 'react-native-gesture-handler';  // This import must be first!
import React from 'react';
import { StatusBar, LogBox } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import AppNavigator from './src/navigation/AppNavigator';

// Silence warnings that might appear with animations
LogBox.ignoreLogs([
  'Sending `onAnimatedValueUpdate` with no listeners registered',
  'Non-serializable values were found in the navigation state',
  'Animated: `useNativeDriver` was not specified',
  'NativeAnimatedModule'
]);

function App(): React.JSX.Element {
  // For development, you can skip onboarding by setting this to true
  const skipOnboarding = false;
  
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar 
          barStyle="dark-content" 
          backgroundColor="transparent" 
          translucent 
        />
        <AppNavigator skipOnboarding={skipOnboarding} />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

export default App;