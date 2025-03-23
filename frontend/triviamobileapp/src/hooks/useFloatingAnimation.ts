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

// Separate animation speed controllers
// Values < 1.0 make animations faster, values > 1.0 make animations slower
export const CENTRAL_ICON_SPEED_FACTOR = 1.0;  // Controls the central bouncing icon
export const FLOATING_EMOJI_SPEED_FACTOR = 1.2;  // Controls the background floating emojis - slightly slower for smoother large loops

interface FloatingAnimationOptions {
  duration?: number;
  displacement?: number;
  delay?: number;
  easing?: EasingFunction;
  animationType?: 'centralIcon' | 'floatingEmoji';
}

export const useFloatingAnimation = (options: FloatingAnimationOptions = {}) => {
  const {
    // Choose the appropriate speed factor based on animation type
    animationType = 'centralIcon',
    displacement = 10,
    delay = 0,
    easing = Easing.inOut(Easing.sin)
  } = options;
  
  // Select the speed factor based on animation type
  const speedFactor = animationType === 'centralIcon' 
    ? CENTRAL_ICON_SPEED_FACTOR 
    : FLOATING_EMOJI_SPEED_FACTOR;
  
  // Apply the selected speed factor to the duration
  const duration = options.duration 
    ? options.duration * speedFactor 
    : 1500 * speedFactor;
  
  // Calculate the actual delay with the speed factor
  const scaledDelay = delay * speedFactor;
  
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
    const animation = scaledDelay > 0 
      ? withDelay(scaledDelay, repeatingAnimation)
      : repeatingAnimation;
    
    // Start the animation
    animatedValue.value = animation;
    
    // Cleanup function to stop animation
    return () => {
      cancelAnimation(animatedValue);
    };
  }, [animatedValue, duration, displacement, scaledDelay, easing]);
  
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
  
  // Select the speed factor based on animation type
  const speedFactor = baseOptions.animationType === 'centralIcon' 
    ? CENTRAL_ICON_SPEED_FACTOR 
    : FLOATING_EMOJI_SPEED_FACTOR;
  
  for (let i = 0; i < count; i++) {
    // More variety in durations for more natural, less synchronized movement
    const durationVariance = Math.random() * 800 + 1000; // 1000-1800ms variance
    const delayVariance = Math.random() * 300; // 0-300ms additional random delay
    
    // Create staggered animations with varying parameters
    // Apply the selected speed factor to all durations and delays
    const options = {
      ...baseOptions,
      duration: baseOptions.duration 
        ? baseOptions.duration * speedFactor + (i * 400 * speedFactor) + durationVariance
        : 1500 * speedFactor + (i * 400 * speedFactor) + durationVariance,
      delay: baseOptions.delay 
        ? baseOptions.delay * speedFactor + (i * 300 * speedFactor) + delayVariance
        : i * 300 * speedFactor + delayVariance,
    };
    
    animations.push(useFloatingAnimation(options));
  }
  
  return animations;
};