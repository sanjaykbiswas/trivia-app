import React, { useMemo } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, { 
  useAnimatedStyle, 
  interpolate,
  Extrapolate 
} from 'react-native-reanimated';
import { normalize, spacing } from '../../utils/scaling';
import { FloatingElement } from './types';
import { useMultipleFloatingAnimations } from '../../hooks/useFloatingAnimation';

interface FloatingElementsProps {
  elements: FloatingElement[];
}

const FloatingElements: React.FC<FloatingElementsProps> = ({ elements }) => {
  // Use optimized hook for multiple animations with staggered timing
  const animations = useMultipleFloatingAnimations(elements.length, {
    duration: 4000, // Base duration (will be varied per element)
  });
  
  // Precalculate rotation offsets for elements
  const rotationOffsets = useMemo(() => 
    elements.map((_, index) => (index * 90) % 360), 
    [elements]
  );
  
  // Pre-compute spacing values for animations
  const spacingValues = useMemo(() => {
    return {
      x: {
        p5: spacing(5),
        n5: -spacing(5)
      },
      y: {
        p3: -spacing(3),
        p5: -spacing(5)
      }
    };
  }, []);
  
  return (
    <View style={styles.container}>
      {elements.map((element, index) => {
        // Skip rendering if out of bounds (safety check)
        if (index >= animations.length) return null;
        
        const { value } = animations[index];
        const rotationOffset = rotationOffsets[index];
        
        // Create animated style for this element
        const animatedStyle = useAnimatedStyle(() => {
          // Calculate translation with a circular path
          const translateX = interpolate(
            value.value,
            [0, 0.25, 0.5, 0.75, 1],
            [0, spacingValues.x.p5, 0, spacingValues.x.n5, 0],
            Extrapolate.CLAMP
          );
          
          const translateY = interpolate(
            value.value,
            [0, 0.25, 0.5, 0.75, 1],
            [0, spacingValues.y.p3, spacingValues.y.p5, spacingValues.y.p3, 0],
            Extrapolate.CLAMP
          );
          
          // Calculate rotation
          const rotate = `${
            interpolate(
              value.value,
              [0, 1],
              [rotationOffset, rotationOffset + 40], // Smaller rotation range
              Extrapolate.CLAMP
            )
          }deg`;
          
          return {
            transform: [
              { translateX },
              { translateY },
              { rotate },
            ],
            opacity: interpolate(
              value.value,
              [0, 0.5, 1],
              [0.3, 0.5, 0.3], // Subtle opacity changes
              Extrapolate.CLAMP
            ),
          };
        });
        
        // Create a position style object
        const positionStyle: { [key: string]: number | string | undefined } = {};
        
        // Only add valid position properties with type casting for string values
        if (element.position.top !== undefined) positionStyle.top = element.position.top as string | number;
        if (element.position.bottom !== undefined) positionStyle.bottom = element.position.bottom as string | number;
        if (element.position.left !== undefined) positionStyle.left = element.position.left as string | number;
        if (element.position.right !== undefined) positionStyle.right = element.position.right as string | number;
        
        return (
          <Animated.Text 
            key={index}
            style={[
              styles.element,
              positionStyle,
              animatedStyle
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
    pointerEvents: 'none', // Don't interfere with touch events
  },
  element: {
    position: 'absolute',
    fontSize: normalize(24),
  },
});

export default FloatingElements;