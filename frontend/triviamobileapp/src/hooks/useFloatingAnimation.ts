// src/hooks/useFloatingAnimation.ts
import { useEffect } from 'react';
import { 
  useSharedValue, 
  withRepeat, 
  withTiming, 
  withDelay, 
  Easing, 
  cancelAnimation, 
  EasingFunction,
  withSequence
} from 'react-native-reanimated';

interface FloatingAnimationOptions {
  duration?: number;
  displacement?: number;
  delay?: number;
  easing?: EasingFunction;
}

export const useFloatingAnimation = (options: FloatingAnimationOptions = {}) => {
  const {
    duration = 1500,
    displacement = 10,
    delay = 0,
    easing = Easing.inOut(Easing.sin)
  } = options;
  
  // Use shared value for better performance
  const animatedValue = useSharedValue(0);
  
  useEffect(() => {
    // Set up animation with proper cleanup
    const timingConfig = {
      duration: duration / 2, // Half duration for each direction
      easing
    };
    
    // Animate up and down in a sequence
    const sequence = withSequence(
      withTiming(1, timingConfig),
      withTiming(0, timingConfig)
    );
    
    // Create the repeating animation
    const repeatingAnimation = withRepeat(
      sequence,
      -1, // Infinite repetitions
      false // Don't reverse (we're already handling that in the sequence)
    );
    
    // Add delay if needed
    const animation = delay > 0 
      ? withDelay(delay, repeatingAnimation)
      : repeatingAnimation;
    
    // Start the animation
    animatedValue.value = animation;
    
    // Cleanup function to stop animation
    return () => {
      cancelAnimation(animatedValue);
    };
  }, [animatedValue, duration, displacement, delay, easing]);
  
  return {
    value: animatedValue,
    displacement
  };
};

// Hook for creating multiple staggered animations
export const useMultipleFloatingAnimations = (
  count: number,
  baseOptions: FloatingAnimationOptions = {}
) => {
  const animations = [];
  
  for (let i = 0; i < count; i++) {
    // Create staggered animations with varying parameters
    const options = {
      ...baseOptions,
      duration: baseOptions.duration ? baseOptions.duration + (i * 200) : 1500 + (i * 200),
      delay: baseOptions.delay ? baseOptions.delay + (i * 150) : i * 150,
    };
    
    animations.push(useFloatingAnimation(options));
  }
  
  return animations;
};