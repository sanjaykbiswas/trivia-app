import React, { useRef, useEffect, useMemo } from 'react';
import { Animated, StyleSheet, Easing, View, DimensionValue } from 'react-native';
import { normalize, spacing } from '../../utils/scaling';
import { FloatingElement } from './types';

interface FloatingElementsProps {
  elements: FloatingElement[];
}

const FloatingElements: React.FC<FloatingElementsProps> = ({ elements }) => {
  // Create animation refs for each element
  const animationsRef = useRef<Animated.Value[]>([]);
  
  // Initialize animations with proper cleanup
  useEffect(() => {
    // Create new animation values if needed
    if (animationsRef.current.length !== elements.length) {
      animationsRef.current = elements.map(() => new Animated.Value(0));
    }
    
    // Store animation references for cleanup
    const animations = animationsRef.current;
    
    // Create and start animations
    const animationHandlers = animations.map((anim, index) => {
      // Reset animation value
      anim.setValue(0);
      
      // Stagger durations between 10-17 seconds to avoid synchronization
      const duration = 10000 + (index * 1500);
      
      // Create the animation
      return Animated.timing(anim, {
        toValue: 1,
        duration: duration,
        easing: Easing.linear,
        useNativeDriver: true,
      });
    });
    
    // Start all animations in a loop
    const loopedAnimations = animationHandlers.map((anim) => 
      Animated.loop(anim)
    );
    
    // Start all animations
    loopedAnimations.forEach(anim => anim.start());
    
    // Cleanup function to stop animations
    return () => {
      animations.forEach(anim => anim.stopAnimation());
      loopedAnimations.forEach(anim => anim.stop());
    };
  }, [elements.length]); // Only re-run if the number of elements changes
  
  // Generate transform functions for each element (memoized for performance)
  const getElementTransforms = useMemo(() => {
    return elements.map((_, index) => {
      const startRotation = index * 90; // Different start rotation for each element
      
      return (animValue: Animated.Value) => {
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
    });
  }, [elements]);

  return (
    <View style={styles.container}>
      {elements.map((element, index) => {
        // Ensure we have a valid animation value
        const animValue = index < animationsRef.current.length ? 
                         animationsRef.current[index] : 
                         new Animated.Value(0);
        
        // Create a position style object
        const positionStyle: { [key: string]: DimensionValue } = {};
        
        // Only add valid position properties
        if (element.position.top !== undefined) positionStyle.top = element.position.top as DimensionValue;
        if (element.position.bottom !== undefined) positionStyle.bottom = element.position.bottom as DimensionValue;
        if (element.position.left !== undefined) positionStyle.left = element.position.left as DimensionValue;
        if (element.position.right !== undefined) positionStyle.right = element.position.right as DimensionValue;
        
        // Get transform for this element
        const transforms = getElementTransforms[index](animValue);
        
        return (
          <Animated.Text 
            key={index}
            style={[
              styles.element,
              positionStyle,
              transforms
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