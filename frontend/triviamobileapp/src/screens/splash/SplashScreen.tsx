import React, { useEffect } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { RootStackParamList } from '../../navigation/types';

type SplashScreenProps = StackScreenProps<RootStackParamList, 'Splash'>;

/**
 * SplashScreen component
 * Displays the app branding during initial load
 */
const SplashScreen: React.FC<SplashScreenProps> = ({ navigation }) => {
  useEffect(() => {
    // Auto-navigate after splash duration
    const timer = setTimeout(() => {
      console.log('Splash screen timer completed');
      navigation.replace('Onboarding');
    }, 2000); // Default 2 seconds splash display

    // Clean up timer if component unmounts
    return () => {
      clearTimeout(timer);
    };
  }, [navigation]);

  return (
    <View style={styles.container}>
      <View style={styles.logoContainer}>
        <Text style={styles.fallbackText}>Open Trivia</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  logoContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    backgroundColor: 'transparent',
    borderRadius: 10,
  },
  fallbackText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#000000',
  },
});

export default SplashScreen;