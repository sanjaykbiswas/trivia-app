// src/navigation/OnboardingNavigator.tsx
import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Dimensions } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
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

const { width } = Dimensions.get('window');
const SWIPE_THRESHOLD = width * 0.3;

const OnboardingNavigator: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const translateX = useSharedValue(0);
  const isGestureActive = useSharedValue(false);
  
  const screens = [
    <Screen1 onContinue={() => handleContinue()} />,
    <Screen2 onContinue={() => handleContinue()} />,
    <Screen3 onContinue={() => handleContinue()} />,
    <Screen4 onContinue={() => handleComplete()} />,
  ];
  
  const handleContinue = () => {
    if (currentIndex < screens.length - 1) {
      // Animate to the next screen
      translateX.value = withSpring(-width, { 
        damping: 20,
        stiffness: 90,
        mass: 1,
        overshootClamping: false,
      });
      
      // After animation, reset translateX and update index
      setTimeout(() => {
        translateX.value = 0;
        setCurrentIndex(prev => prev + 1);
      }, 300);
    }
  };

  const handleComplete = () => {
    console.log('Onboarding complete');
    // Here you would navigate to your main app
    // navigation.replace('MainApp');
  };

  const updateIndex = (newIndex: number) => {
    setCurrentIndex(newIndex);
  };

  const gestureHandler = useAnimatedGestureHandler({
    onStart: (_, ctx: any) => {
      ctx.startX = translateX.value;
      isGestureActive.value = true;
    },
    onActive: (event, ctx) => {
      // Calculate resistance for boundary screens
      let delta = event.translationX;
      
      // Apply resistance when swiping past boundaries
      if ((currentIndex === 0 && delta > 0) || 
          (currentIndex === screens.length - 1 && delta < 0)) {
        delta = delta * 0.3; // High resistance at boundaries
      }
      
      translateX.value = ctx.startX + delta;
    },
    onEnd: (event) => {
      isGestureActive.value = false;
      
      const velocity = event.velocityX;
      const isQuickSwipe = Math.abs(velocity) > 800;
      
      if ((event.translationX < -SWIPE_THRESHOLD || 
           (isQuickSwipe && velocity < 0)) && 
          currentIndex < screens.length - 1) {
        // Swipe left to next screen
        translateX.value = withSpring(-width, { 
          velocity: velocity,
          damping: 20,
          stiffness: 90,
          mass: 1,
          overshootClamping: false,
        });
        
        // After animation, reset translateX and update index
        setTimeout(() => {
          translateX.value = 0;
          runOnJS(updateIndex)(currentIndex + 1);
        }, 300);
      } else if ((event.translationX > SWIPE_THRESHOLD || 
                 (isQuickSwipe && velocity > 0)) && 
                currentIndex > 0) {
        // Swipe right to previous screen
        translateX.value = withSpring(width, { 
          velocity: velocity,
          damping: 20,
          stiffness: 90,
          mass: 1,
          overshootClamping: false,
        });
        
        // After animation, reset translateX and update index
        setTimeout(() => {
          translateX.value = 0;
          runOnJS(updateIndex)(currentIndex - 1);
        }, 300);
      } else {
        // Return to current screen with a bounce-back animation
        translateX.value = withSpring(0, { 
          velocity: velocity / 2,
          damping: 20,
          stiffness: 90,
          mass: 1,
          overshootClamping: false,
        });
      }
    },
    onFinish: () => {
      isGestureActive.value = false;
    },
  });

  // Style for the current screen
  const currentScreenStyle = useAnimatedStyle(() => {
    return {
      transform: [{ translateX: translateX.value }],
    };
  });
  
  // Style for the previous screen (if any)
  const prevScreenStyle = useAnimatedStyle(() => {
    const opacity = interpolate(
      translateX.value,
      [0, width / 2, width],
      [0, 0.5, 1],
      Extrapolate.CLAMP
    );
    
    return {
      transform: [
        { translateX: interpolate(
            translateX.value,
            [0, width],
            [-width, 0],
            Extrapolate.CLAMP
          ) 
        }
      ],
      opacity,
      zIndex: translateX.value > 0 ? 1 : 0,
    };
  });
  
  // Style for the next screen (if any)
  const nextScreenStyle = useAnimatedStyle(() => {
    const opacity = interpolate(
      translateX.value,
      [-width, -width / 2, 0],
      [1, 0.5, 0],
      Extrapolate.CLAMP
    );
    
    return {
      transform: [
        { translateX: interpolate(
            translateX.value,
            [-width, 0],
            [0, width],
            Extrapolate.CLAMP
          ) 
        }
      ],
      opacity,
      zIndex: translateX.value < 0 ? 1 : 0,
    };
  });

  // Generate pagination dots
  const renderPaginationDots = () => {
    return screens.map((_, index) => (
      <View 
        key={index} 
        style={[
          styles.dot, 
          index === currentIndex && styles.activeDot
        ]} 
      />
    ));
  };

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
          {currentIndex < screens.length - 1 && (
            <Animated.View style={[styles.screenContainer, nextScreenStyle]}>
              {screens[currentIndex + 1]}
            </Animated.View>
          )}
          
          {/* Pagination dots */}
          <View style={styles.pagination}>
            {renderPaginationDots()}
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
    overflow: 'hidden',
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
    bottom: 180, // Adjust based on your button position
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
    backgroundColor: '#7B61FF',
    transform: [{ scale: 1.2 }],
  },
});

export default OnboardingNavigator;