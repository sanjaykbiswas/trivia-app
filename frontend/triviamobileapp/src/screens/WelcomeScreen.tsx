import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  StatusBar,
  Animated,
  Easing,
} from 'react-native';

const WelcomeScreen = () => {
  // Animation value for floating effect using useRef to persist between renders
  const floatAnim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    // Create and start the floating animation
    const startFloatingAnimation = () => {
      // Reset the animation value before starting a new animation cycle
      floatAnim.setValue(0);
      
      // Create a sequence of up and down movements
      Animated.loop(
        Animated.sequence([
          // Float up
          Animated.timing(floatAnim, {
            toValue: 1,
            duration: 1500,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true, // Better performance on native thread
          }),
          // Float down
          Animated.timing(floatAnim, {
            toValue: 0,
            duration: 1500,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      ).start();
    };

    // Start the animation when the component mounts
    startFloatingAnimation();
    
    // Clean up the animation when the component unmounts
    return () => {
      floatAnim.stopAnimation();
    };
  }, []); // Empty dependency array means this runs once on mount

  // Transform for the floating animation
  const floatTransform = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -10], // Move up by 10 units
  });

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      
      <View style={styles.floatingElements}>
        <Text style={[styles.element, styles.element1]}>❓</Text>
        <Text style={[styles.element, styles.element2]}>💡</Text>
        <Text style={[styles.element, styles.element3]}>🧠</Text>
        <Text style={[styles.element, styles.element4]}>🎓</Text>
      </View>
      
      <View style={styles.mainContent}>
        <Animated.View 
          style={[
            styles.iconContainer, 
            { transform: [{ translateY: floatTransform }] }
          ]}
        >
          <View style={styles.iconInner}>
            <View style={styles.icon}>
              <View style={[styles.sparkle, styles.sparkle1]} />
              <View style={[styles.sparkle, styles.sparkle2]} />
              <View style={[styles.sparkle, styles.sparkle3]} />
              <Text style={styles.iconText}>🧠</Text>
            </View>
          </View>
        </Animated.View>
        
        <Text style={styles.title}>Welcome to Synquizitive</Text>
        <Text style={styles.subtitle}>Get ready to challenge your knowledge in exciting new ways</Text>
        
        <View style={styles.pagination}>
          <View style={[styles.dot, styles.activeDot]} />
          <View style={styles.dot} />
          <View style={styles.dot} />
          <View style={styles.dot} />
        </View>
      </View>
      
      <View style={styles.bottomContainer}>
        <TouchableOpacity 
          style={styles.continueButton}
          onPress={() => {
            console.log('Continue button pressed');
          }}
        >
          <Text style={styles.buttonText}>Continue</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9ff',
    position: 'relative',
  },
  floatingElements: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    zIndex: 1,
  },
  element: {
    position: 'absolute',
    fontSize: 24,
    opacity: 0.4,
  },
  element1: {
    top: '15%',
    left: '10%',
  },
  element2: {
    top: '25%',
    right: '10%',
  },
  element3: {
    bottom: '30%',
    left: '15%',
  },
  element4: {
    bottom: '25%',
    right: '20%',
  },
  mainContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  iconContainer: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: 'rgba(123, 97, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 40,
  },
  iconInner: {
    width: 130,
    height: 130,
    borderRadius: 65,
    backgroundColor: 'rgba(123, 97, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#7B61FF',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  iconText: {
    fontSize: 40,
  },
  sparkle: {
    position: 'absolute',
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
  },
  sparkle1: {
    width: 8,
    height: 8,
    top: '20%',
    left: '20%',
  },
  sparkle2: {
    width: 6,
    height: 6,
    top: '30%',
    right: '20%',
  },
  sparkle3: {
    width: 10,
    height: 10,
    bottom: '20%',
    right: '30%',
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    marginBottom: 20,
    textAlign: 'center',
    color: '#7B61FF',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subtitle: {
    fontSize: 18,
    textAlign: 'center',
    color: '#555',
    marginBottom: 60,
    maxWidth: 280,
    lineHeight: 24,
  },
  pagination: {
    flexDirection: 'row',
    marginBottom: 40,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#ddd',
    marginHorizontal: 6,
  },
  activeDot: {
    backgroundColor: '#7B61FF',
    transform: [{ scale: 1.2 }],
  },
  bottomContainer: {
    padding: 20,
    width: '100%',
    position: 'absolute',
    bottom: 40,
  },
  continueButton: {
    backgroundColor: '#7B61FF',
    borderRadius: 30,
    paddingVertical: 18,
    width: '85%',
    alignSelf: 'center',
    overflow: 'hidden',
    shadowColor: 'rgba(123, 97, 255, 0.3)',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 1,
    shadowRadius: 15,
    elevation: 6,
  },
  buttonText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
  },
});

export default WelcomeScreen;