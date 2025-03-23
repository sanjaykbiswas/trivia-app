import React, { useState, useCallback, useMemo } from 'react';
import { StyleSheet, View, Dimensions } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useAnimatedGestureHandler,
  useSharedValue,
  withTiming,
  runOnJS,
  Easing,
} from 'react-native-reanimated';
import { PanGestureHandler } from 'react-native-gesture-handler';
import Screen1 from '../screens/onboarding/Screen1';
import Screen2 from '../screens/onboarding/Screen2';
import Screen3 from '../screens/onboarding/Screen3';
import Screen4 from '../screens/onboarding/Screen4';
import { themes } from '../assets/onboardingData';

const { width } = Dimensions.get('window');
const SWIPE_THRESHOLD = 60; // Reduced threshold for better responsiveness
const SCREEN_COUNT = 4;

interface OnboardingNavigatorProps {
  onComplete: () => void;
}

const OnboardingNavigator: React.FC<OnboardingNavigatorProps> = ({ onComplete }) => {
  // Track current screen index
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Animation values
  const opacity = useSharedValue(1);
  const isAnimating = useSharedValue(false);
  
  // Animation timing configuration for fade
  const fadeConfig = {
    duration: 250,
    easing: Easing.inOut(Easing.ease)
  };
  
  // Handle transition between screens
  const transitionToScreen = useCallback((nextIndex: number) => {
    if (isAnimating.value || nextIndex < 0 || nextIndex >= SCREEN_COUNT) return;
    
    isAnimating.value = true;
    
    // Fade out
    opacity.value = withTiming(0, fadeConfig, (finished) => {
      if (finished) {
        // Update index when fade out is complete
        runOnJS(setCurrentIndex)(nextIndex);
        
        // Fade in
        opacity.value = withTiming(1, fadeConfig, () => {
          isAnimating.value = false;
        });
      } else {
        isAnimating.value = false;
      }
    });
  }, [opacity, isAnimating]);
  
  // Handle continue button press
  const handleContinue = useCallback(() => {
    if (currentIndex < SCREEN_COUNT - 1) {
      transitionToScreen(currentIndex + 1);
    }
  }, [currentIndex, transitionToScreen]);
  
  // Handle completion (last screen)
  const handleComplete = useCallback(() => {
    console.log('Onboarding complete');
    // Call the onComplete callback to navigate to the main app
    onComplete();
  }, [onComplete]);
  
  // Get active dot color based on current screen
  const getActiveDotColor = useCallback((index: number): string => {
    const themeKeys = Object.keys(themes);
    const theme = themes[themeKeys[index] as keyof typeof themes];
    return theme?.primary || '#7B61FF';
  }, []);
  
  // Create memoized screen components
  const screens = useMemo(() => [
    <Screen1 onContinue={handleContinue} paginationVisibility={false} key="screen1" />,
    <Screen2 onContinue={handleContinue} paginationVisibility={false} key="screen2" />,
    <Screen3 onContinue={handleContinue} paginationVisibility={false} key="screen3" />,
    <Screen4 onContinue={handleComplete} paginationVisibility={false} key="screen4" />,
  ], [handleContinue, handleComplete]);
  
  // Gesture handler for swipe detection - using PanGestureHandler for compatibility
  const gestureHandler = useAnimatedGestureHandler({
    onStart: (_, ctx: any) => {
      // Don't start a gesture if we're already animating
      if (isAnimating.value) {
        ctx.shouldRespond = false;
        return;
      }
      ctx.shouldRespond = true;
    },
    onActive: (_, ctx) => {
      // We're not doing anything during the active phase for fade transitions
      // Just using gesture detector for swipe end
    },
    onEnd: (event, ctx) => {
      if (!ctx.shouldRespond) return;
      
      const { translationX, velocityX } = event;
      const isQuickSwipe = Math.abs(velocityX) > 800;
      
      if ((translationX < -SWIPE_THRESHOLD || (isQuickSwipe && velocityX < 0)) && 
          currentIndex < SCREEN_COUNT - 1) {
        // Swipe left - go to next
        runOnJS(transitionToScreen)(currentIndex + 1);
      } else if ((translationX > SWIPE_THRESHOLD || (isQuickSwipe && velocityX > 0)) && 
                currentIndex > 0) {
        // Swipe right - go to previous
        runOnJS(transitionToScreen)(currentIndex - 1);
      }
    },
  });

  // Animated style for fade transition
  const animatedStyle = useAnimatedStyle(() => {
    return {
      opacity: opacity.value,
    };
  });

  return (
    <View style={styles.container}>
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Animated.View style={styles.gestureContainer}>
          {/* Current Screen with fade animation */}
          <Animated.View style={[styles.screen, animatedStyle]}>
            {screens[currentIndex]}
          </Animated.View>
          
          {/* Pagination dots - fixed position */}
          <View style={styles.pagination} pointerEvents="none">
            {Array.from({length: SCREEN_COUNT}).map((_, index) => (
              <View 
                key={index} 
                style={[
                  styles.dot, 
                  index === currentIndex && [
                    styles.activeDot, 
                    {backgroundColor: getActiveDotColor(index)}
                  ]
                ]} 
              />
            ))}
          </View>
        </Animated.View>
      </PanGestureHandler>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9ff',
  },
  gestureContainer: {
    flex: 1,
    overflow: 'hidden',
  },
  screen: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  pagination: {
    position: 'absolute',
    bottom: 180,
    flexDirection: 'row',
    alignSelf: 'center',
    justifyContent: 'center',
    zIndex: 10,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#ddd',
    marginHorizontal: 6,
  },
  activeDot: {
    transform: [{ scale: 1.2 }],
  },
});

export default OnboardingNavigator;