// src/navigation/OnboardingNavigator.tsx
import React, { useState, useRef } from 'react';
import { 
  View, 
  StyleSheet, 
  Dimensions, 
  PanResponder, 
  Animated 
} from 'react-native';
import Screen1 from '../screens/onboarding/Screen1';
import Screen2 from '../screens/onboarding/Screen2';
import Screen3 from '../screens/onboarding/Screen3';
import Screen4 from '../screens/onboarding/Screen4';

const { width } = Dimensions.get('window');
const SWIPE_THRESHOLD = 80;

const OnboardingNavigator: React.FC = () => {
  // Track current screen index
  const [currentScreen, setCurrentScreen] = useState(0);
  
  // Slide position for all screens
  const slidePosition = useRef(new Animated.Value(0)).current;
  
  // Track if animation is in progress
  const isAnimating = useRef(false);
  
  // Continue button handler - instant transition
  const handleContinue = () => {
    if (currentScreen < 3) {
      setCurrentScreen(currentScreen + 1);
    } else {
      console.log('Onboarding complete');
    }
  };
  
  // Create pan responder for swipe gestures
  const panResponder = PanResponder.create({
    onStartShouldSetPanResponder: () => false,
    onMoveShouldSetPanResponder: (_, { dx, dy }) => {
      return !isAnimating.current && 
             Math.abs(dx) > 10 && 
             Math.abs(dx) > Math.abs(dy);
    },
    
    onPanResponderMove: (_, { dx }) => {
      // Check boundaries
      const canSwipeLeft = currentScreen < 3;
      const canSwipeRight = currentScreen > 0;
      
      if ((dx < 0 && canSwipeLeft) || (dx > 0 && canSwipeRight)) {
        slidePosition.setValue(dx);
      }
    },
    
    onPanResponderRelease: (_, { dx, vx }) => {
      if (isAnimating.current) return;
      
      const swipeDistance = Math.abs(dx);
      const swipeVelocity = Math.abs(vx);
      const isQuickSwipe = swipeVelocity > 0.5;
      
      if ((dx < 0 && currentScreen < 3) && 
          (swipeDistance > SWIPE_THRESHOLD || isQuickSwipe)) {
        // Swipe left to next screen
        isAnimating.current = true;
        
        Animated.timing(slidePosition, {
          toValue: -width,
          duration: 300,
          useNativeDriver: true
        }).start(() => {
          slidePosition.setValue(0);
          setCurrentScreen(currentScreen + 1);
          isAnimating.current = false;
        });
      } 
      else if ((dx > 0 && currentScreen > 0) && 
               (swipeDistance > SWIPE_THRESHOLD || isQuickSwipe)) {
        // Swipe right to previous screen
        isAnimating.current = true;
        
        Animated.timing(slidePosition, {
          toValue: width,
          duration: 300,
          useNativeDriver: true
        }).start(() => {
          slidePosition.setValue(0);
          setCurrentScreen(currentScreen - 1);
          isAnimating.current = false;
        });
      } 
      else {
        // Return to current screen
        Animated.spring(slidePosition, {
          toValue: 0,
          friction: 6,
          tension: 40,
          useNativeDriver: true
        }).start();
      }
    },
    
    onPanResponderTerminationRequest: () => false,
    
    onPanResponderTerminate: () => {
      Animated.spring(slidePosition, {
        toValue: 0,
        useNativeDriver: true
      }).start();
    }
  });
  
  // Create screen transforms based on position
  const getPreviousScreenStyles = () => {
    // For previous screen, it should slide in from the left
    const translateX = slidePosition.interpolate({
      inputRange: [0, width],
      outputRange: [-width, 0],
      extrapolate: 'clamp'
    });
    
    return {
      transform: [{ translateX }]
    };
  };
  
  const getCurrentScreenStyles = () => {
    // Current screen moves with the finger
    return {
      transform: [{ translateX: slidePosition }]
    };
  };
  
  const getNextScreenStyles = () => {
    // For next screen, it should slide in from the right
    const translateX = slidePosition.interpolate({
      inputRange: [-width, 0],
      outputRange: [0, width],
      extrapolate: 'clamp'
    });
    
    return {
      transform: [{ translateX }]
    };
  };
  
  // Get the appropriate screen component
  const getScreenComponent = (index) => {
    switch (index) {
      case 0: return <Screen1 onContinue={handleContinue} />;
      case 1: return <Screen2 onContinue={handleContinue} />;
      case 2: return <Screen3 onContinue={handleContinue} />;
      case 3: return <Screen4 onContinue={handleContinue} />;
      default: return null;
    }
  };
  
  return (
    <View style={styles.container} {...panResponder.panHandlers}>
      {/* Previous Screen (if not on first screen) */}
      {currentScreen > 0 && (
        <Animated.View style={[styles.screenContainer, getPreviousScreenStyles()]}>
          {getScreenComponent(currentScreen - 1)}
        </Animated.View>
      )}
      
      {/* Current Screen */}
      <Animated.View style={[styles.screenContainer, getCurrentScreenStyles()]}>
        {getScreenComponent(currentScreen)}
      </Animated.View>
      
      {/* Next Screen (if not on last screen) */}
      {currentScreen < 3 && (
        <Animated.View style={[styles.screenContainer, getNextScreenStyles()]}>
          {getScreenComponent(currentScreen + 1)}
        </Animated.View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9ff',
    overflow: 'hidden',
  },
  screenContainer: {
    ...StyleSheet.absoluteFillObject,
    width: width,
  },
});

export default OnboardingNavigator;