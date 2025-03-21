import React, { useState, useCallback, useMemo } from 'react';
import { StyleSheet, View, Dimensions } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useAnimatedGestureHandler,
  runOnJS,
  interpolate,
  Extrapolate,
} from 'react-native-reanimated';
import { PanGestureHandler } from 'react-native-gesture-handler';
import Screen1 from '../screens/onboarding/Screen1';
import Screen2 from '../screens/onboarding/Screen2';
import Screen3 from '../screens/onboarding/Screen3';
import Screen4 from '../screens/onboarding/Screen4';
import { useSwipeAnimation } from '../hooks/useSwipeAnimation';
import { themes } from '../assets/onboardingData';

const { width } = Dimensions.get('window');
const SWIPE_THRESHOLD = width * 0.25;
const SCREEN_COUNT = 4;

const OnboardingNavigator: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Handle screen index change
  const handleIndexChange = useCallback((newIndex: number) => {
    // Ensure index is within bounds
    if (newIndex >= 0 && newIndex < SCREEN_COUNT) {
      setCurrentIndex(newIndex);
    }
  }, []);
  
  // Initialize the swipe animation hook
  const { translateX, isAnimating, animateTransition, cancelSwipe } = useSwipeAnimation(handleIndexChange);
  
  // Handle continue button press
  const handleContinue = useCallback(() => {
    if (currentIndex < SCREEN_COUNT - 1) {
      animateTransition(currentIndex, -1); // Go to next
    }
  }, [currentIndex, animateTransition]);
  
  // Handle completion (last screen)
  const handleComplete = useCallback(() => {
    console.log('Onboarding complete');
    // Here you would navigate to your main app
    // navigation.replace('MainApp');
  }, []);
  
  // Get active dot color based on current screen
  const getActiveDotColor = (index: number): string => {
    const themeKeys = Object.keys(themes);
    const theme = themes[themeKeys[index] as keyof typeof themes];
    return theme?.primary || '#7B61FF';
  };
  
  // Create memoized screen components to avoid re-renders
  const screens = useMemo(() => [
    <Screen1 onContinue={handleContinue} paginationVisibility={false} />,
    <Screen2 onContinue={handleContinue} paginationVisibility={false} />,
    <Screen3 onContinue={handleContinue} paginationVisibility={false} />,
    <Screen4 onContinue={handleComplete} paginationVisibility={false} />,
  ], [handleContinue, handleComplete]);
  
  // Gesture handler for swipe detection
  const gestureHandler = useAnimatedGestureHandler({
    onStart: (_, ctx: any) => {
      if (isAnimating.value) return;
      ctx.startX = translateX.value;
    },
    onActive: (event, ctx) => {
      if (isAnimating.value) return;
      
      // Apply resistance at boundaries
      let delta = event.translationX;
      if ((currentIndex === 0 && delta > 0) || (currentIndex === SCREEN_COUNT - 1 && delta < 0)) {
        delta = delta * 0.2; // Higher resistance at boundaries
      }
      
      translateX.value = ctx.startX + delta;
    },
    onEnd: (event) => {
      if (isAnimating.value) return;
      
      const velocity = event.velocityX;
      const isQuickSwipe = Math.abs(velocity) > 800;
      
      if ((event.translationX < -SWIPE_THRESHOLD || (isQuickSwipe && velocity < 0)) && 
          currentIndex < SCREEN_COUNT - 1) {
        // Swipe left - go to next
        runOnJS(animateTransition)(currentIndex, -1, velocity);
      } else if ((event.translationX > SWIPE_THRESHOLD || (isQuickSwipe && velocity > 0)) && 
                currentIndex > 0) {
        // Swipe right - go to previous
        runOnJS(animateTransition)(currentIndex, 1, velocity);
      } else {
        // Return to current screen
        cancelSwipe(velocity);
      }
    },
  });

  // Animation styles
  const currentScreenStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
    zIndex: 2, // Keep current screen on top during normal viewing
  }));
  
  const prevScreenStyle = useAnimatedStyle(() => {
    // Only show previous screen when swiping right
    const opacity = interpolate(
      translateX.value,
      [0, width * 0.3, width],
      [0, 0.5, 1],
      Extrapolate.CLAMP
    );
    
    return {
      transform: [{ 
        translateX: interpolate(
          translateX.value,
          [0, width],
          [-width * 0.3, 0], // Adjusted for better parallax effect
          Extrapolate.CLAMP
        ) 
      }],
      opacity,
      zIndex: translateX.value > 0 ? 3 : 1, // Bring to front when swiping right
    };
  });
  
  const nextScreenStyle = useAnimatedStyle(() => {
    // Only show next screen when swiping left
    const opacity = interpolate(
      translateX.value,
      [-width, -width * 0.3, 0],
      [1, 0.5, 0],
      Extrapolate.CLAMP
    );
    
    return {
      transform: [{ 
        translateX: interpolate(
          translateX.value,
          [-width, 0],
          [0, width * 0.3], // Adjusted for better parallax effect
          Extrapolate.CLAMP
        ) 
      }],
      opacity,
      zIndex: translateX.value < 0 ? 3 : 1, // Bring to front when swiping left
    };
  });

  return (
    <View style={styles.container}>
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Animated.View style={styles.gestureContainer}>
          {/* Current Screen */}
          <Animated.View style={[styles.screenContainer, currentScreenStyle]}>
            {screens[currentIndex]}
          </Animated.View>
          
          {/* Previous Screen (if not on first screen) */}
          {currentIndex > 0 && (
            <Animated.View style={[styles.screenContainer, prevScreenStyle]}>
              {screens[currentIndex - 1]}
            </Animated.View>
          )}
          
          {/* Next Screen (if not on last screen) */}
          {currentIndex < SCREEN_COUNT - 1 && (
            <Animated.View style={[styles.screenContainer, nextScreenStyle]}>
              {screens[currentIndex + 1]}
            </Animated.View>
          )}
          
          {/* Pagination dots - centralized here instead of in individual screens */}
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
    position: 'relative',
  },
  screenContainer: {
    ...StyleSheet.absoluteFillObject,
    width: width,
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