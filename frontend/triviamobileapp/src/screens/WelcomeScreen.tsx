import React, { useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Easing,
  Dimensions,
  StatusBar,
} from 'react-native';
import { Svg, Path, Circle } from 'react-native-svg';

// const WelcomeScreen = ({ navigation }) => {
const WelcomeScreen = () => {
  // Animation values
  const floatAnim = new Animated.Value(0);
  const shineAnim = new Animated.Value(0);
  
  useEffect(() => {
    // Floating animation for the icon
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: 1,
          duration: 1500,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 1500,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Shine animation for the button
    Animated.loop(
      Animated.timing(shineAnim, {
        toValue: 1,
        duration: 3000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  // Transform for the floating animation
  const floatTransform = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -10],
  });

  // Transform for the shine animation
  const shineTransform = shineAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-100, 400],
  });

  return (
    <View style={styles.container}>
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
              <Svg width={50} height={50} viewBox="0 0 512 512" style={styles.brainIcon}>
                <Path
                  d="M208 32c-52.4 0-95 42.6-95 95 0 16.1 4.1 31.3 11.4 44.6-24.5 17.8-40.4 46.7-40.4 79.4 0 15.7 3.7 30.6 10.2 43.8-32.4 15.9-54.8 49.2-54.8 87.8 0 53.9 43.7 97.6 97.6 97.6h16.2c8.5 0 16.6-1.6 24-4.3 19 17.1 44.1 27.5 71.6 27.5 29.5 0 56.1-11.8 75.5-31 19.4 19.2 46 31 75.5 31 27.5 0 52.6-10.4 71.6-27.5 7.4 2.8 15.5 4.3 24 4.3h16.2c53.9 0 97.6-43.7 97.6-97.6 0-38.6-22.4-71.9-54.8-87.8 6.5-13.2 10.2-28 10.2-43.8 0-32.7-15.9-61.6-40.4-79.4 7.3-13.3 11.4-28.5 11.4-44.6 0-52.4-42.6-95-95-95-30 0-56.6 13.9-74 35.6C342.6 45.9 316 32 286 32c-30 0-56.6 13.9-74 35.6C194.6 45.9 168 32 138 32h70zM144 224c-8.8 0-16-7.2-16-16s7.2-16 16-16h24c8.8 0 16 7.2 16 16s-7.2 16-16 16H144zm208-16c0-8.8 7.2-16 16-16h24c8.8 0 16 7.2 16 16s-7.2 16-16 16H368c-8.8 0-16-7.2-16-16zM256 288c-35.3 0-64-28.7-64-64s28.7-64 64-64 64 28.7 64 64-28.7 64-64 64z"
                  fill="white"
                />
              </Svg>
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
            // Navigate to the next screen when integrated with navigation
            console.log('Continue button pressed');
          }}
        >
          <Animated.View 
            style={[
              styles.buttonGlow, 
              { transform: [{ translateX: shineTransform }] }
            ]} 
          />
          <Text style={styles.buttonText}>Continue</Text>
        </TouchableOpacity>
      </View>
      
      {/* Create random synapse elements */}
      {Array(15).fill(0).map((_, i) => {
        const size = Math.random() * 15 + 5;
        return (
          <View
            key={i}
            style={[
              styles.synapse,
              {
                width: size,
                height: size,
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              },
            ]}
          />
        );
      })}
    </View>
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
  brainIcon: {
    width: 50,
    height: 50,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    zIndex: 2,
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
  buttonGlow: {
    position: 'absolute',
    width: 50,
    height: '100%',
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    transform: [{ skewX: '-15deg' }],
  },
  synapse: {
    position: 'absolute',
    backgroundColor: 'rgba(123, 97, 255, 0.1)',
    borderRadius: 50,
    zIndex: -1,
  },
});

export default WelcomeScreen;