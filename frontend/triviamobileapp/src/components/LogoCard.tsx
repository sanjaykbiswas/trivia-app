import React, { useEffect } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withRepeat,
  Easing,
  interpolate,
  withDelay,
} from 'react-native-reanimated';
import LinearGradient from 'react-native-linear-gradient';
import { normalize, spacing } from '../utils/scaling';

const { width } = Dimensions.get('window');

interface LogoCardProps {
  style?: object;
}

const LogoCard: React.FC<LogoCardProps> = ({ style }) => {
  // Animation values
  const rotateValue = useSharedValue(0);
  const scaleValue = useSharedValue(1);
  const glowValue = useSharedValue(0);
  
  // Start animations on component mount
  useEffect(() => {
    // Subtle rotation animation
    rotateValue.value = withRepeat(
      withTiming(1, {
        duration: 10000,
        easing: Easing.inOut(Easing.sin),
      }),
      -1,
      true
    );
    
    // Subtle scale pulsing
    scaleValue.value = withRepeat(
      withTiming(1.03, {
        duration: 2000,
        easing: Easing.inOut(Easing.sin),
      }),
      -1,
      true
    );
    
    // Glow effect animation
    glowValue.value = withRepeat(
      withDelay(
        500,
        withTiming(1, {
          duration: 3000,
          easing: Easing.inOut(Easing.cubic),
        })
      ),
      -1,
      true
    );
    
    // Cleanup
    return () => {
      // Reset animations
      rotateValue.value = 0;
      scaleValue.value = 1;
      glowValue.value = 0;
    };
  }, []);
  
  // Card rotation animation style
  const cardAnimatedStyle = useAnimatedStyle(() => {
    const rotateInterpolated = interpolate(
      rotateValue.value,
      [0, 1],
      [-2, 2] // subtle rotation in degrees
    );
    
    return {
      transform: [
        { perspective: 1000 },
        { scale: scaleValue.value },
        { rotateY: `${rotateInterpolated}deg` },
        { rotateX: `${rotateInterpolated * 0.5}deg` }, // half the rotation for X axis
      ],
    };
  });
  
  // Glow effect animation style
  const borderGlowStyle = useAnimatedStyle(() => {
    const opacityInterpolated = interpolate(
      glowValue.value,
      [0, 0.5, 1],
      [0.5, 0.8, 0.5]
    );
    
    return {
      opacity: opacityInterpolated,
    };
  });
  
  return (
    <Animated.View style={[styles.container, cardAnimatedStyle, style]}>
      {/* Rainbow border effect */}
      <Animated.View style={[styles.glowBorder, borderGlowStyle]}>
        <LinearGradient
          colors={['#00E5E8', '#FF00FF', '#FFC100']}
          start={{x: 0, y: 0}}
          end={{x: 1, y: 1}}
          style={styles.gradientBorder}
        />
      </Animated.View>
      
      {/* Card background */}
      <LinearGradient
        colors={['#333333', '#111111']}
        start={{x: 0, y: 0}}
        end={{x: 1, y: 1}}
        style={styles.card}
      >
        {/* Overlay gradient for shine effect */}
        <LinearGradient
          colors={['rgba(123, 97, 255, 0.3)', 'rgba(123, 97, 255, 0)']}
          start={{x: 0, y: 0}}
          end={{x: 1, y: 1}}
          style={styles.shineOverlay}
        />
        
        {/* Logo content */}
        <View style={styles.content}>
          <Text style={styles.logoText}>open<Text style={styles.logoTextSpan}>trivia</Text></Text>
        </View>
      </LinearGradient>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
    aspectRatio: 1.6, // approximately the ratio in the design
    position: 'relative',
  },
  glowBorder: {
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    borderRadius: spacing(27),
    overflow: 'hidden',
  },
  gradientBorder: {
    width: '100%',
    height: '100%',
    borderRadius: spacing(27),
  },
  card: {
    flex: 1,
    borderRadius: spacing(25),
    padding: spacing(25),
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shineOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  content: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    color: 'white',
    fontSize: normalize(45),
    textAlign: 'center',
    fontWeight: '800',
    lineHeight: normalize(40),
    letterSpacing: -1,
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: spacing(2) },
    textShadowRadius: spacing(10),
  },
  logoTextSpan: {
    display: 'flex',
    fontSize: normalize(72),
    fontWeight: '900',
    color: 'white',
    marginTop: -spacing(5),
    letterSpacing: -2,
    textShadowColor: '#000',
    textShadowOffset: { width: spacing(3), height: spacing(3) },
    textShadowRadius: 0,
  },
});

export default LogoCard;