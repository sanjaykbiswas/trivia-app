import { useCallback } from 'react';
import { Dimensions } from 'react-native';
import { 
  useSharedValue, 
  withSpring, 
  WithSpringConfig,
  runOnJS 
} from 'react-native-reanimated';

const { width } = Dimensions.get('window');

/**
 * Custom hook for managing swipe animations with proper cleanup
 */
export const useSwipeAnimation = (onTransitionComplete: (newIndex: number) => void) => {
  // Shared animation values
  const translateX = useSharedValue(0);
  const isAnimating = useSharedValue(false);
  
  // Default spring configuration - adjusted for smoother animations
  const springConfig: WithSpringConfig = {
    damping: 25,        // Increased damping for less oscillation
    stiffness: 100,     // Slightly higher stiffness for faster initial movement
    mass: 1,
    overshootClamping: false,
    restDisplacementThreshold: 0.01,  // More precise stopping point
    restSpeedThreshold: 0.01,         // More precise stopping point
  };
  
  /**
   * Animate screen transition
   * @param currentIndex Current screen index
   * @param direction -1 for next, 1 for previous
   * @param velocity Optional initial velocity
   */
  const animateTransition = useCallback((currentIndex: number, direction: number, velocity = 0) => {
    if (isAnimating.value) return;
    
    isAnimating.value = true;
    
    // Calculate new index
    const newIndex = direction < 0 ? currentIndex + 1 : currentIndex - 1;
    
    // Add velocity to spring config if provided
    const config = velocity ? 
      { ...springConfig, velocity } : 
      springConfig;
    
    // Animate with completion callback
    translateX.value = withSpring(direction * width, config, (finished) => {
      if (finished) {
        // Reset position immediately after the animation completes
        translateX.value = 0;
        // Notify parent component of index change
        runOnJS(onTransitionComplete)(newIndex);
        // Reset animation flag
        isAnimating.value = false;
      } else {
        // Animation was interrupted
        isAnimating.value = false;
      }
    });
  }, [translateX, isAnimating, onTransitionComplete]);
  
  /**
   * Reset to center (cancel swipe)
   */
  const cancelSwipe = useCallback((velocity = 0) => {
    const config = velocity ? 
      { ...springConfig, velocity: velocity / 2 } : 
      springConfig;
      
    translateX.value = withSpring(0, config);
  }, [translateX, springConfig]);
  
  return {
    translateX,
    isAnimating,
    animateTransition,
    cancelSwipe
  };
};