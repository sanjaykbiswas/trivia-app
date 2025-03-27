import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { 
  SplashScreen, 
  OnboardingScreen, 
  HomeScreen, 
  MultiplayerScreen, 
  GameSetupScreen,
  GameOptionsScreen,
  QuestionScreen,
  SignInScreen,
  SignUpScreen,
  ForgotPasswordScreen 
} from '../screens';
import { RootStackParamList } from './types';
import { useAuth } from '../contexts/AuthContext';

const Stack = createStackNavigator<RootStackParamList>();

/**
 * AppNavigator component
 * Handles navigation between screens in the app using React Navigation
 */
const AppNavigator: React.FC = () => {
  const { user, loading } = useAuth();
  
  // Show splash screen while loading authentication state
  if (loading) {
    return (
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Splash" component={SplashScreen} />
      </Stack.Navigator>
    );
  }

  return (
    <Stack.Navigator 
      initialRouteName="Onboarding"
      screenOptions={{ 
        headerShown: false,
        cardStyle: { backgroundColor: 'white' },
      }}
    >
      {/* Common screens available to all users */}
      <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="Multiplayer" component={MultiplayerScreen} />
      <Stack.Screen name="GameSetup" component={GameSetupScreen} />
      <Stack.Screen name="GameOptions" component={GameOptionsScreen} />
      <Stack.Screen name="QuestionScreen" component={QuestionScreen} />
      
      {/* Authentication screens */}
      <Stack.Screen name="SignIn" component={SignInScreen} />
      <Stack.Screen name="SignUp" component={SignUpScreen} />
      <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
    </Stack.Navigator>
  );
};

export default AppNavigator;