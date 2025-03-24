import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { SplashScreen, OnboardingScreen, HomeScreen } from '../screens';
import { RootStackParamList } from './types';

const Stack = createStackNavigator<RootStackParamList>();

/**
 * AppNavigator component
 * Handles navigation between screens in the app using React Navigation
 */
const AppNavigator: React.FC = () => {
  return (
    <Stack.Navigator 
      initialRouteName="Splash"
      screenOptions={{ 
        headerShown: false,
        cardStyle: { backgroundColor: 'white' },
      }}
    >
      <Stack.Screen name="Splash" component={SplashScreen} />
      <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      <Stack.Screen name="Home" component={HomeScreen} />
      
      {/* Add more screens as you create them */}
      {/* 
      <Stack.Screen name="SignIn" component={SignInScreen} />
      <Stack.Screen name="SignUp" component={SignUpScreen} />
      <Stack.Screen name="GamePlay" component={GamePlayScreen} />
      <Stack.Screen name="Profile" component={ProfileScreen} />
      <Stack.Screen name="Settings" component={SettingsScreen} />
      */}
    </Stack.Navigator>
  );
};

export default AppNavigator;