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
const SWIPE_THRESHOLD = 120; // minimum distance to trigger swipe

const OnboardingNavigator: React.FC = () => {
  const [currentScreen, setCurrentScreen] = useState(0);
  const translateX = useRef(new Animated.Value(0)).current;
  
  // Navigate to the next screen
  const handleContinue = () => {
    if (currentScreen < 3) {
      navigateToScreen(currentScreen + 1);
    } else {
      // Navigate to main app or login
      console.log('Onboarding complete');
    }
  };
  
  // Navigate to a specific screen with animation
  const navigateToScreen = (screenIndex: number) => {
    Animated.timing(translateX, {
      toValue: 0,
      duration: 300,
      useNativeDriver: true,
    }).start(() => {
      setCurrentScreen(screenIndex);
    });
  };
  
  // Configure the pan responder for swipe gestures
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: (_, gestureState) => 
        Math.abs(gestureState.dx) > 10,
      
      onPanResponderMove: (_, gestureState) => {
        // Only allow swiping if we're not at the edge screens, or
        // we're swiping in the allowed direction at edge screens
        const canSwipeLeft = currentScreen < 3;
        const canSwipeRight = currentScreen > 0;
        
        if ((gestureState.dx < 0 && canSwipeLeft) || 
            (gestureState.dx > 0 && canSwipeRight)) {
          translateX.setValue(gestureState.dx);
        }
      },
      
      onPanResponderRelease: (_, gestureState) => {
        if (gestureState.dx < -SWIPE_THRESHOLD && currentScreen < 3) {
          // Swiped left -> go to next screen
          Animated.timing(translateX, {
            toValue: -width,
            duration: 200,
            useNativeDriver: true,
          }).start(() => {
            translateX.setValue(0);
            setCurrentScreen(currentScreen + 1);
          });
        } else if (gestureState.dx > SWIPE_THRESHOLD && currentScreen > 0) {
          // Swiped right -> go to previous screen
          Animated.timing(translateX, {
            toValue: width,
            duration: 200,
            useNativeDriver: true,
          }).start(() => {
            translateX.setValue(0);
            setCurrentScreen(currentScreen - 1);
          });
        } else {
          // Not enough swipe distance, reset position
          Animated.spring(translateX, {
            toValue: 0,
            useNativeDriver: true,
          }).start();
        }
      },
    })
  ).current;
  
  // Render the current screen
  const renderCurrentScreen = () => {
    switch (currentScreen) {
      case 0:
        return <Screen1 onContinue={handleContinue} />;
      case 1:
        return <Screen2 onContinue={handleContinue} />;
      case 2:
        return <Screen3 onContinue={handleContinue} />;
      case 3:
        return <Screen4 onContinue={handleContinue} />;
      default:
        return <Screen1 onContinue={handleContinue} />;
    }
  };
  
  return (
    <View style={styles.container} {...panResponder.panHandlers}>
      <Animated.View
        style={[
          styles.screenContainer,
          { transform: [{ translateX }] }
        ]}
      >
        {renderCurrentScreen()}
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  screenContainer: {
    flex: 1,
  },
});

export default OnboardingNavigator;