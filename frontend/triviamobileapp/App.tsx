import 'react-native-gesture-handler';  // This import must be first!
import React, { useEffect, useState } from 'react';
import { StatusBar, LogBox } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Import your main navigation component here
// import MainNavigator from './src/navigation/MainNavigator';

// Silence warnings that might appear with animations
LogBox.ignoreLogs([
  'Sending `onAnimatedValueUpdate` with no listeners registered',
  'Non-serializable values were found in the navigation state',
  'Animated: `useNativeDriver` was not specified',
  'NativeAnimatedModule'
]);

// You might want to define app themes or context providers
// export const ThemeContext = React.createContext(null);

function App(): React.JSX.Element {
  // Example state for app initialization
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Example effect for initialization logic
  useEffect(() => {
    const initialize = async () => {
      try {
        // Check if user is logged in
        const userToken = await AsyncStorage.getItem('userToken');
        
        // Set authentication state based on token existence
        setIsAuthenticated(!!userToken);
        
        // Any other initialization logic
      } catch (error) {
        console.error('Initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initialize();
  }, []);

  // You could add a loading screen here if isLoading is true
  if (isLoading) {
    return (
      // Return your loading component here
      <SafeAreaProvider>
        <StatusBar 
          barStyle="dark-content" 
          backgroundColor="transparent" 
          translucent 
        />
        {/* <LoadingScreen /> */}
      </SafeAreaProvider>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar 
          barStyle="dark-content" 
          backgroundColor="transparent" 
          translucent 
        />
        {/* Conditionally render based on authentication state */}
        {/* {isAuthenticated ? <MainNavigator /> : <AuthNavigator />} */}
        
        {/* Or just use a single navigator */}
        {/* <MainNavigator /> */}
        
        {/* Placeholder for development */}
        {/* Replace this with your actual navigator component */}
        <YourMainAppComponent />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

// Temporary placeholder component - replace with your actual component
const YourMainAppComponent = () => {
  return (
    <SafeAreaProvider>
      {/* Your application content goes here */}
    </SafeAreaProvider>
  );
};

export default App;