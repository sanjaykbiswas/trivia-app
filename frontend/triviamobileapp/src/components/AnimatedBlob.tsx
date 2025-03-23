import React, { useEffect } from 'react';
import { StyleSheet, ViewStyle } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withRepeat,
  Easing,
  interpolate,
} from 'react-native-reanimated';

interface AnimatedBlobProps {
  style?: ViewStyle;
  color: string;
  size: number;
  duration?: number;
  delay?: number;
}

const AnimatedBlob: React.FC<AnimatedBlobProps> = ({
  style,
  color,
  size,
  duration = 8000,
  delay = 0,
}) => {
  // Animation values
  const scaleValue = useSharedValue(0);
  const moveValue = useSharedValue(0);
  
  // Start animations on component mount
  useEffect(() => {
    // Initial delay
    const timerId = setTimeout(() => {
      // Scaling animation
      scaleValue.value = withRepeat(
        withTiming(1, {
          duration: duration,
          easing: Easing.inOut(Easing.sin),
        }),
        -1,
        true
      );
      
      // Movement animation
      moveValue.value = withRepeat(
        withTiming(1, {
          duration: duration * 1.2, // Slightly different timing creates organic movement
          easing: Easing.inOut(Easing.cubic),
        }),
        -1,
        true
      );
    }, delay);
    
    // Cleanup
    return () => {
      clearTimeout(timerId);
    };
  }, []);
  
  // Animated styles
  const animatedStyle = useAnimatedStyle(() => {
    const scale = interpolate(
      scaleValue.value,
      [0, 0.5, 1],
      [0.9, 1.1, 0.9]
    );
    
    const translateX = interpolate(
      moveValue.value,
      [0, 0.5, 1],
      [-10, 10, -10]
    );
    
    const translateY = interpolate(
      moveValue.value,
      [0, 0.5, 1],
      [-5, 15, -5]
    );
    
    // Add a slight rotation
    const rotate = interpolate(
      moveValue.value,
      [0, 1],
      [0, 10]
    );
    
    return {
      transform: [
        { scale },
        { translateX },
        { translateY },
        { rotate: `${rotate}deg` },
      ],
    };
  });
  
  return (
    <Animated.View
      style={[
        styles.blob,
        {
          backgroundColor: color,
          width: size,
          height: size,
          borderRadius: size / 2,
        },
        animatedStyle,
        style,
      ]}
    />
  );
};

const styles = StyleSheet.create({
  blob: {
    position: 'absolute',
    opacity: 0.5,
  },
});

export default AnimatedBlob;