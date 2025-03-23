// src/components/onboarding/FloatingIcon.tsx
// Fixed version with safer animation handling

import React, { useMemo } from 'react';
import { StyleSheet, View, Text } from 'react-native';
import Animated, { 
  useAnimatedStyle, 
  interpolate, 
  Extrapolate 
} from 'react-native-reanimated';
import { spacing, normalize } from '../../utils/scaling';
import { useFloatingAnimation } from '../../hooks/useFloatingAnimation';

interface FloatingIconProps {
  icon: string;
  primaryColor: string;
}

const FloatingIcon: React.FC<FloatingIconProps> = ({ icon, primaryColor }) => {
  // Main floating animation with longer duration for smoother movement
  // Specify that this is a central icon animation
  const mainAnimation = useFloatingAnimation({
    duration: 2000,
    displacement: 10,
    animationType: 'centralIcon'
  });
  
  // Sparkle animations with staggered delays
  // All using the central icon animation type
  const sparkle1Animation = useFloatingAnimation({
    duration: 2800,
    delay: 0,
    animationType: 'centralIcon'
  });
  
  const sparkle2Animation = useFloatingAnimation({
    duration: 3200,
    delay: 1000,
    animationType: 'centralIcon'
  });
  
  const sparkle3Animation = useFloatingAnimation({
    duration: 2400,
    delay: 500,
    animationType: 'centralIcon'
  });
  
  // Pre-compute spacing values for animations
  const floatDistance = useMemo(() => -spacing(10), []);
  
  // Sparkle dimensions (pre-computed)
  const sparkle1Size = useMemo(() => ({
    width: spacing(8),
    height: spacing(8)
  }), []);
  
  const sparkle2Size = useMemo(() => ({
    width: spacing(6),
    height: spacing(6)
  }), []);
  
  const sparkle3Size = useMemo(() => ({
    width: spacing(10),
    height: spacing(10)
  }), []);
  
  // Main floating animation style with safer interpolation
  const floatStyle = useAnimatedStyle(() => {
    // Ensure we're using numbers, not objects
    const translateYValue = interpolate(
      mainAnimation.value.value,
      [0, 1],
      [0, floatDistance],
      Extrapolate.CLAMP
    );
    
    return {
      transform: [
        { translateY: translateYValue }
      ]
    };
  });
  
  // Styles for the three sparkles with safer interpolation
  const sparkle1Style = useAnimatedStyle(() => ({
    opacity: interpolate(
      sparkle1Animation.value.value,
      [0, 0.5, 1],
      [0.2, 0.7, 0.2],
      Extrapolate.CLAMP
    )
  }));
  
  const sparkle2Style = useAnimatedStyle(() => ({
    opacity: interpolate(
      sparkle2Animation.value.value,
      [0, 0.5, 1],
      [0.3, 0.8, 0.3],
      Extrapolate.CLAMP
    )
  }));
  
  const sparkle3Style = useAnimatedStyle(() => ({
    opacity: interpolate(
      sparkle3Animation.value.value,
      [0, 0.5, 1],
      [0.1, 0.6, 0.1],
      Extrapolate.CLAMP
    )
  }));

  return (
    <Animated.View 
      style={[
        styles.iconContainer, 
        { backgroundColor: `${primaryColor}20` }, // 12% opacity
        floatStyle
      ]}
    >
      <View 
        style={[
          styles.iconInner,
          { backgroundColor: `${primaryColor}40` } // 25% opacity
        ]}
      >
        <View 
          style={[
            styles.icon,
            { backgroundColor: primaryColor }
          ]}
        >
          <Animated.View 
            style={[
              styles.sparkle, 
              sparkle1Size,
              { 
                top: '20%', 
                left: '20%',
              },
              sparkle1Style
            ]} 
          />
          <Animated.View 
            style={[
              styles.sparkle, 
              sparkle2Size,
              { 
                top: '30%', 
                right: '20%',
              },
              sparkle2Style
            ]} 
          />
          <Animated.View 
            style={[
              styles.sparkle, 
              sparkle3Size,
              { 
                bottom: '20%', 
                right: '30%',
              },
              sparkle3Style
            ]} 
          />
          <Text style={styles.iconText}>{icon}</Text>
        </View>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  iconContainer: {
    width: spacing(160),
    height: spacing(160),
    borderRadius: spacing(80),
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing(40),
  },
  iconInner: {
    width: spacing(130),
    height: spacing(130),
    borderRadius: spacing(65),
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    width: spacing(100),
    height: spacing(100),
    borderRadius: spacing(50),
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
});

export default FloatingIcon;