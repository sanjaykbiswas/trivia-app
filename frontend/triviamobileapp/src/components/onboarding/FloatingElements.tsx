import React, { useRef, useEffect } from 'react';
import { Animated, StyleSheet, Easing, View, TextStyle, DimensionValue } from 'react-native';
import { normalize, spacing } from '../../utils/scaling';

// Updated interface with more specific types for position values
interface FloatingElementsProps {
  elements: Array<{
    emoji: string;
    position: {
      top?: string | number;
      bottom?: string | number;
      left?: string | number;
      right?: string | number;
    };
  }>;
}

const FloatingElements: React.FC<FloatingElementsProps> = ({ elements }) => {
  // Create animation refs for each element
  const animationsRef = useRef<Animated.Value[]>([]);
  
  // Initialize animations if needed
  if (animationsRef.current.length !== elements.length) {
    animationsRef.current = elements.map(() => new Animated.Value(0));
  }
  
  useEffect(() => {
    // Function to animate a single element
    const animateFloatingElement = (animValue: Animated.Value, duration: number) => {
      // Reset the animation value
      animValue.setValue(0);
      
      // Create and start the animation
      Animated.timing(animValue, {
        toValue: 1,
        duration: duration,
        easing: Easing.linear,
        useNativeDriver: true,
      }).start((result) => {
        // Only restart if component is still mounted and animation completed normally
        if (result.finished) {
          animateFloatingElement(animValue, duration);
        }
      });
    };
    
    // Start all animations with different durations
    const animations = animationsRef.current;
    animations.forEach((anim, index) => {
      // Stagger durations between 10-17 seconds
      const duration = 10000 + (index * 2000);
      animateFloatingElement(anim, duration);
    });
    
    // Cleanup function to stop animations
    return () => {
      animations.forEach(anim => anim.stopAnimation());
    };
  }, [elements.length]); // Only re-run if the number of elements changes
  
  // Function to get transform styles for floating elements
  const getFloatingElementTransforms = (animValue: Animated.Value, startRotation = 0) => {
    const translateX = animValue.interpolate({
      inputRange: [0, 0.25, 0.5, 0.75, 1],
      outputRange: [0, spacing(8), 0, -spacing(8), 0],
    });
    
    const translateY = animValue.interpolate({
      inputRange: [0, 0.25, 0.5, 0.75, 1],
      outputRange: [0, -spacing(5), -spacing(10), -spacing(5), 0],
    });
    
    const rotate = animValue.interpolate({
      inputRange: [0, 1],
      outputRange: [`${startRotation}deg`, `${startRotation + 360}deg`],
    });
    
    return {
      transform: [
        { translateX },
        { translateY },
        { rotate },
      ],
    };
  };

  return (
    <View style={styles.container}>
      {elements.map((element, index) => {
        // Ensure we have a valid animation value
        const animValue = index < animationsRef.current.length ? 
                         animationsRef.current[index] : 
                         new Animated.Value(0);
        
        // Create a valid style object from the position
        const positionStyle: { [key: string]: DimensionValue } = {};
        
        // Only add valid position properties
        if (element.position.top !== undefined) positionStyle.top = element.position.top as DimensionValue;
        if (element.position.bottom !== undefined) positionStyle.bottom = element.position.bottom as DimensionValue;
        if (element.position.left !== undefined) positionStyle.left = element.position.left as DimensionValue;
        if (element.position.right !== undefined) positionStyle.right = element.position.right as DimensionValue;
        
        return (
          <Animated.Text 
            key={index}
            style={[
              styles.element,
              positionStyle,
              getFloatingElementTransforms(animValue, index * 90)
            ]}>
            {element.emoji}
          </Animated.Text>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 0,
  },
  element: {
    position: 'absolute',
    fontSize: normalize(24),
    opacity: 0.4,
  },
});

export default FloatingElements;