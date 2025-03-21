// src/navigation/OnboardingNavigator.tsx
import React, { useState } from 'react';
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
  const isAnimating = useSharedValue(false);
  
  // Create screen components with the proper props
  const renderScreen = (index: number) => {
    // Hide pagination dots from individual screens by passing empty function
    const dummyPaginationHandler = () => {};
    
    switch(index) {
      case 0:
        return <Screen1 
          onContinue={() => handleContinue()} 
          // Pass null to hide pagination in the screen component
          paginationVisibility={false}
        />;
      case 1:
        return <Screen2 
          onContinue={() => handleContinue()} 
          paginationVisibility={false}
        />;
      case 2:
        return <Screen3 
          onContinue={() => handleContinue()} 
          paginationVisibility={false}
        />;
      case 3:
        return <Screen4 
          onContinue={() => handleComplete()} 
          paginationVisibility={false}
        />;
      default:
        return null;
    }
  };
  
  const handleContinue = () => {
    if (currentIndex < 3 && !isAnimating.value) {
      isAnimating.value = true;
      
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
        isAnimating.value = false;
      }, 300);
    }
  };

  const handleComplete = () => {
    console.log('Onboarding complete');
    // Here you would navigate to your main app
    // navigation.replace('MainApp');
  };

  const updateIndex = (newIndex: number) => {
    if (newIndex >= 0 && newIndex <= 3) {
      setCurrentIndex(newIndex);
    }
  };

  const gestureHandler = useAnimatedGestureHandler({
    onStart: (_, ctx: any) => {
      if (isAnimating.value) return;
      ctx.startX = translateX.value;
    },
    onActive: (event, ctx) => {
      if (isAnimating.value) return;
      
      // Calculate resistance for boundary screens
      let delta = event.translationX;
      
      // Apply resistance when swiping past boundaries
      if ((currentIndex === 0 && delta > 0) || 
          (currentIndex === 3 && delta < 0)) {
        delta = delta * 0.3; // High resistance at boundaries
      }
      
      translateX.value = ctx.startX + delta;
    },
    onEnd: (event) => {
      if (isAnimating.value) return;
      
      const velocity = event.velocityX;
      const isQuickSwipe = Math.abs(velocity) > 800;
      
      if ((event.translationX < -SWIPE_THRESHOLD || 
           (isQuickSwipe && velocity < 0)) && 
          currentIndex < 3) {
        
        // Prevent additional gesture handling during animation
        isAnimating.value = true;
        
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
          isAnimating.value = false;
        }, 300);
      } else if ((event.translationX > SWIPE_THRESHOLD || 
                 (isQuickSwipe && velocity > 0)) && 
                currentIndex > 0) {
        
        // Prevent additional gesture handling during animation
        isAnimating.value = true;
        
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
          isAnimating.value = false;
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

  return (
    <View style={styles.container}>
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Animated.View style={styles.gestureContainer}>
          {/* Current Screen */}
          <Animated.View style={[styles.screenContainer, currentScreenStyle]}>
            {renderScreen(currentIndex)}
          </Animated.View>
          
          {/* Previous Screen (if not on first screen) */}
          {currentIndex > 0 && (
            <Animated.View style={[styles.screenContainer, prevScreenStyle]}>
              {renderScreen(currentIndex - 1)}
            </Animated.View>
          )}
          
          {/* Next Screen (if not on last screen) */}
          {currentIndex < 3 && (
            <Animated.View style={[styles.screenContainer, nextScreenStyle]}>
              {renderScreen(currentIndex + 1)}
            </Animated.View>
          )}
          
          {/* Pagination dots */}
          <View style={styles.pagination}>
            {[0, 1, 2, 3].map((index) => (
              <View 
                key={index} 
                style={[
                  styles.dot, 
                  index === currentIndex && styles.activeDot
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
    backgroundColor: '#7B61FF',
    transform: [{ scale: 1.2 }],
  },
});

export default OnboardingNavigator;