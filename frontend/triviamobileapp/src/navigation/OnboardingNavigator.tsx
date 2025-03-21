import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { StyleSheet, View, Dimensions } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useAnimatedGestureHandler,
  runOnJS,
  interpolate,
  Extrapolate,
  useDerivedValue,
  withTiming,
  cancelAnimation,
  useSharedValue,
} from 'react-native-reanimated';
import { PanGestureHandler } from 'react-native-gesture-handler';
import Screen1 from '../screens/onboarding/Screen1';
import Screen2 from '../screens/onboarding/Screen2';
import Screen3 from '../screens/onboarding/Screen3';
import Screen4 from '../screens/onboarding/Screen4';
import { themes } from '../assets/onboardingData';

const { width } = Dimensions.get('window');
const SWIPE_THRESHOLD = width * 0.2; // Reduced threshold for better responsiveness
const SCREEN_COUNT = 4;

const OnboardingNavigator: React.FC = () => {
  // Track current screen index
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Animation values
  const translateX = useSharedValue(0);
  const isAnimating = useSharedValue(false);
  
  // Handle screen index change
  const handleIndexChange = useCallback((newIndex: number) => {
    // Ensure index is within bounds
    if (newIndex >= 0 && newIndex < SCREEN_COUNT) {
      setCurrentIndex(newIndex);
    }
  }, []);
  
  // Animation timing configuration (smoother easing)
  const timingConfig = {
    duration: 300,
  };
  
  // Programmatically animate to next/previous screen
  const animateToScreen = useCallback((direction: number) => {
    if (isAnimating.value) return;
    
    const nextIndex = currentIndex + direction;
    // Validate next index is within bounds
    if (nextIndex < 0 || nextIndex >= SCREEN_COUNT) return;
    
    isAnimating.value = true;
    
    // Animate to next/previous screen
    translateX.value = withTiming(direction * -width, timingConfig, (finished) => {
      if (finished) {
        // Reset position and update index
        runOnJS(handleIndexChange)(nextIndex);
        translateX.value = 0;
        isAnimating.value = false;
      }
    });
  }, [currentIndex, translateX, isAnimating, handleIndexChange]);
  
  // Handle continue button press
  const handleContinue = useCallback(() => {
    if (currentIndex < SCREEN_COUNT - 1) {
      animateToScreen(1); // Go to next screen
    }
  }, [currentIndex, animateToScreen]);
  
  // Handle completion (last screen)
  const handleComplete = useCallback(() => {
    console.log('Onboarding complete');
    // Here you would navigate to your main app
    // navigation.replace('MainApp');
  }, []);
  
  // Clean up any ongoing animations when component unmounts
  useEffect(() => {
    return () => {
      cancelAnimation(translateX);
    };
  }, [translateX]);
  
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
  
  // Optimized gesture handler for swipe detection
  const gestureHandler = useAnimatedGestureHandler({
    onStart: (_, ctx: any) => {
      if (isAnimating.value) return;
      
      ctx.startX = translateX.value;
      ctx.active = true;
    },
    onActive: (event, ctx) => {
      if (!ctx.active || isAnimating.value) return;
      
      // Calculate new position with boundary resistance
      let newPosition = ctx.startX + event.translationX;
      
      // Apply resistance at boundaries
      if ((currentIndex === 0 && newPosition > 0) || 
          (currentIndex === SCREEN_COUNT - 1 && newPosition < 0)) {
        newPosition = newPosition * 0.2; // Stronger resistance at edges
      }
      
      translateX.value = newPosition;
    },
    onEnd: (event, ctx) => {
      if (!ctx.active || isAnimating.value) return;
      ctx.active = false;
      
      const velocity = event.velocityX;
      const isQuickSwipe = Math.abs(velocity) > 800;
      
      // Calculate if we should snap to next/previous screen
      if ((event.translationX < -SWIPE_THRESHOLD || (isQuickSwipe && velocity < 0)) && 
          currentIndex < SCREEN_COUNT - 1) {
        // Swipe left - go to next
        isAnimating.value = true;
        translateX.value = withTiming(-width, timingConfig, (finished) => {
          if (finished) {
            runOnJS(handleIndexChange)(currentIndex + 1);
            translateX.value = 0;
            isAnimating.value = false;
          }
        });
      } else if ((event.translationX > SWIPE_THRESHOLD || (isQuickSwipe && velocity > 0)) && 
                currentIndex > 0) {
        // Swipe right - go to previous
        isAnimating.value = true;
        translateX.value = withTiming(width, timingConfig, (finished) => {
          if (finished) {
            runOnJS(handleIndexChange)(currentIndex - 1);
            translateX.value = 0;
            isAnimating.value = false;
          }
        });
      } else {
        // Return to current screen (no change in index)
        translateX.value = withTiming(0, timingConfig);
      }
    },
    onCancel: (_, ctx) => {
      ctx.active = false;
      translateX.value = withTiming(0, timingConfig);
    },
  });

  // Improved animation styles with better performance
  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ translateX: translateX.value }],
    };
  });
  
  // Calculate next screen opacity and position
  const nextScreenStyle = useAnimatedStyle(() => {
    // Only show next screen when on a valid index and swiping left
    const shouldShow = currentIndex < SCREEN_COUNT - 1 && translateX.value < 0;
    
    const opacity = shouldShow 
      ? interpolate(
          translateX.value,
          [-width, -width * 0.3],
          [1, 0],
          Extrapolate.CLAMP
        )
      : 0;
      
    const screenTranslateX = shouldShow
      ? interpolate(
          translateX.value,
          [-width, 0],
          [0, width],
          Extrapolate.CLAMP
        )
      : width;
    
    return {
      opacity,
      transform: [{ translateX: screenTranslateX }],
      zIndex: 0, // Keep consistent z-index
      position: 'absolute',
      width: width,
      height: '100%',
    };
  });
  
  // Calculate previous screen opacity and position
  const prevScreenStyle = useAnimatedStyle(() => {
    // Only show previous screen when on a valid index and swiping right
    const shouldShow = currentIndex > 0 && translateX.value > 0;
    
    const opacity = shouldShow
      ? interpolate(
          translateX.value,
          [width * 0.3, width],
          [0, 1],
          Extrapolate.CLAMP
        )
      : 0;
      
    const screenTranslateX = shouldShow
      ? interpolate(
          translateX.value,
          [0, width],
          [-width, 0],
          Extrapolate.CLAMP
        )
      : -width;
    
    return {
      opacity,
      transform: [{ translateX: screenTranslateX }],
      zIndex: 0, // Keep consistent z-index
      position: 'absolute',
      width: width,
      height: '100%',
    };
  });

  return (
    <View style={styles.container}>
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Animated.View style={styles.gestureContainer}>
          {/* Previous Screen */}
          {currentIndex > 0 && (
            <Animated.View style={prevScreenStyle}>
              {screens[currentIndex - 1]}
            </Animated.View>
          )}
          
          {/* Next Screen */}
          {currentIndex < SCREEN_COUNT - 1 && (
            <Animated.View style={nextScreenStyle}>
              {screens[currentIndex + 1]}
            </Animated.View>
          )}
          
          {/* Current Screen (always on top) */}
          <Animated.View style={[styles.currentScreen, animatedStyle]}>
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
    overflow: 'hidden', // Prevent content from bleeding outside container
  },
  currentScreen: {
    width: width,
    height: '100%',
    zIndex: 1, // Keep current screen on top
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