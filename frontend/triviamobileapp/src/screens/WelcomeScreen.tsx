import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  Animated,
  Easing,
  Dimensions,
  Platform,
  PixelRatio,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

// Get screen dimensions
const { width, height } = Dimensions.get('window');

// Create a scale based on screen size
const scale = Math.min(width, height) / 375; // Base scale on iPhone 8 dimensions (375pt width)

// Function to normalize font sizes for different screen densities
const normalize = (size: number): number => {
  const newSize = size * scale;
  if (Platform.OS === 'ios') {
    return Math.round(PixelRatio.roundToNearestPixel(newSize));
  }
  return Math.round(PixelRatio.roundToNearestPixel(newSize)) - 2; // Slightly smaller text on Android
};

// Function to create responsive spacing
const spacing = (size: number): number => {
  return Math.round(size * scale);
};

const WelcomeScreen: React.FC = () => {
  // Get safe area insets
  const insets = useSafeAreaInsets();
  
  // Animation value for floating effect
  const floatAnim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    // Create a reusable animation
    const createAnimation = (toValue: number) => {
      return Animated.timing(floatAnim, {
        toValue,
        duration: 1500,
        easing: Easing.inOut(Easing.sin),
        useNativeDriver: true,
      });
    };

    // Setup a looping animation sequence
    Animated.loop(
      Animated.sequence([
        createAnimation(1),
        createAnimation(0),
      ])
    ).start();
    
    // Clean up animation when component unmounts
    return () => floatAnim.stopAnimation();
  }, [floatAnim]);

  // Transform for floating effect
  const floatTransform = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -spacing(10)], // Scale the animation too
  });

  return (
    <View style={styles.container}>
      <StatusBar 
        barStyle="dark-content" 
        backgroundColor="#f8f9ff" 
        translucent={Platform.OS === 'android'}
      />
      
      <View style={styles.backgroundFill} />
      
      {/* Floating elements */}
      <View style={styles.floatingElementsContainer}>
        <Text style={[styles.element, { top: '15%', left: '10%' }]}>❓</Text>
        <Text style={[styles.element, { top: '25%', right: '10%' }]}>💡</Text>
        <Text style={[styles.element, { bottom: '30%', left: '15%' }]}>🧠</Text>
        <Text style={[styles.element, { bottom: '25%', right: '20%' }]}>🎓</Text>
      </View>
      
      {/* Main content */}
      <SafeAreaView edges={['right', 'left', 'top']} style={styles.safeContainer}>
        <View style={styles.mainContent}>
          {/* Floating brain icon */}
          <Animated.View 
            style={[
              styles.iconContainer, 
              { transform: [{ translateY: floatTransform }] }
            ]}
          >
            <View style={styles.iconInner}>
              <View style={styles.icon}>
                <View style={[styles.sparkle, { width: spacing(8), height: spacing(8), top: '20%', left: '20%' }]} />
                <View style={[styles.sparkle, { width: spacing(6), height: spacing(6), top: '30%', right: '20%' }]} />
                <View style={[styles.sparkle, { width: spacing(10), height: spacing(10), bottom: '20%', right: '30%' }]} />
                <Text style={styles.iconText}>🧠</Text>
              </View>
            </View>
          </Animated.View>
          
          {/* Title and subtitle */}
          <Text style={styles.title}>Welcome to Synquizitive</Text>
          <Text style={styles.subtitle}>Get ready to challenge your knowledge in exciting new ways</Text>
          
          {/* Pagination dots */}
          <View style={styles.pagination}>
            <View style={[styles.dot, styles.activeDot]} />
            <View style={styles.dot} />
            <View style={styles.dot} />
            <View style={styles.dot} />
          </View>
        </View>
      </SafeAreaView>

      {/* Continue button */}
      <View 
        style={[
          styles.buttonContainer, 
          { 
            paddingBottom: Math.max(insets.bottom, spacing(20)),
            paddingTop: spacing(20) 
          }
        ]}
      >
        <TouchableOpacity
          style={styles.touchableWrapper}
          activeOpacity={0.8}
          onPress={() => console.log('Continue button pressed')}
        >
          <LinearGradient
            colors={['#7B61FF', '#899DFF']}
            start={{x: 0, y: 0}}
            end={{x: 1, y: 1}}
            style={styles.gradientButton}
          >
            <Text style={styles.buttonText}>Continue</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9ff',
  },
  backgroundFill: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#f8f9ff',
  },
  safeContainer: {
    flex: 1,
  },
  floatingElementsContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 0,
  },
  element: {
    position: 'absolute',
    fontSize: normalize(24),
    opacity: 0.4,
  },
  mainContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing(20),
  },
  iconContainer: {
    width: spacing(160),
    height: spacing(160),
    borderRadius: spacing(80),
    backgroundColor: 'rgba(123, 97, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing(40),
  },
  iconInner: {
    width: spacing(130),
    height: spacing(130),
    borderRadius: spacing(65),
    backgroundColor: 'rgba(123, 97, 255, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    width: spacing(100),
    height: spacing(100),
    borderRadius: spacing(50),
    backgroundColor: '#7B61FF',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  iconText: {
    fontSize: normalize(40),
  },
  sparkle: {
    position: 'absolute',
    borderRadius: spacing(25),
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
  },
  title: {
    fontSize: normalize(32),
    fontWeight: '800',
    marginBottom: spacing(20),
    textAlign: 'center',
    color: '#7B61FF',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subtitle: {
    fontSize: normalize(18),
    textAlign: 'center',
    color: '#555',
    marginBottom: spacing(60),
    maxWidth: width * 0.8,
    lineHeight: normalize(24),
  },
  pagination: {
    flexDirection: 'row',
    marginBottom: spacing(40),
  },
  dot: {
    width: spacing(10),
    height: spacing(10),
    borderRadius: spacing(5),
    backgroundColor: '#ddd',
    marginHorizontal: spacing(6),
  },
  activeDot: {
    backgroundColor: '#7B61FF',
    transform: [{ scale: 1.2 }],
  },
  buttonContainer: {
    width: '100%',
    paddingHorizontal: spacing(20),
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9ff',
  },
  touchableWrapper: {
    width: '100%',
    alignItems: 'center',
  },
  gradientButton: {
    width: '100%',
    maxWidth: spacing(320),
    height: spacing(60),
    borderRadius: spacing(30),
    alignItems: 'center',
    justifyContent: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#7B61FF',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.5,
        shadowRadius: 15,
      },
      android: {
        elevation: 8,
      }
    }),
  },
  buttonText: {
    color: 'white',
    fontSize: normalize(20),
    fontWeight: 'bold',
    textAlign: 'center',
  },
});

export default WelcomeScreen;