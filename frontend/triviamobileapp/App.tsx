import 'react-native-gesture-handler';  // This import must be first!
import React from 'react';
import { StatusBar, LogBox } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import OnboardingNavigator from './src/navigation/OnboardingNavigator';

// Silence reanimated warnings (if any)
LogBox.ignoreLogs([
  'Sending `onAnimatedValueUpdate` with no listeners registered',
  'Non-serializable values were found in the navigation state'
]);

function App(): React.JSX.Element {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" translucent />
        <OnboardingNavigator />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

export default App;