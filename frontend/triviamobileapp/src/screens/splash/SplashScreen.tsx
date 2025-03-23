import React, { useEffect } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import { Container, Typography } from '../../components';
import { colors } from '../../theme';

interface SplashScreenProps {
  onSplashComplete: () => void;
  splashDuration?: number;
}

/**
 * SplashScreen component
 * Displays the app branding during initial load
 */
const SplashScreen: React.FC<SplashScreenProps> = ({
  onSplashComplete,
  splashDuration = 2000, // Default 2 seconds splash display
}) => {
  useEffect(() => {
    // Auto-navigate after splash duration
    const timer = setTimeout(() => {
      console.log('Splash screen timer completed');
      onSplashComplete();
    }, splashDuration);

    // Log when component mounts for debugging
    console.log('SplashScreen mounted');

    // Clean up timer if component unmounts
    return () => {
      console.log('SplashScreen unmounted, clearing timer');
      clearTimeout(timer);
    };
  }, [onSplashComplete, splashDuration]);

  // Use basic Text component as a fallback to verify rendering
  return (
    <View style={styles.container}>
      <View style={styles.logoContainer}>
        <Text style={styles.fallbackText}>Cal AI</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF', // Explicit background color
  },
  logoContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#F5F5F5', // Light background to ensure visibility
    borderRadius: 10,
  },
  appName: {
    fontWeight: '700',
    color: '#000000', // Explicitly black
    fontSize: 32,
  },
  fallbackText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#000000', // Explicitly black
  },
});

export default SplashScreen;