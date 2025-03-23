// src/components/onboarding/FloatingElements.tsx
// Fixed version with safer animation handling

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
  // Specify 'floatingEmoji' animation type to use the correct speed factor
  const animations = useMultipleFloatingAnimations(elements.length, {
    duration: 4000,
    animationType: 'floatingEmoji' // Use the floating emoji speed factor
  });
  
  // Precalculate rotation offsets for elements with more variety
  const rotationOffsets = useMemo(() => 
    elements.map((_, index) => (index * 90 + Math.floor(Math.random() * 45)) % 360), 
    [elements]
  );
  
  // Pre-compute spacing values for animations with larger movement range
  const spacingValues = useMemo(() => {
    return {
      x: {
        p20: spacing(20),
        n20: -spacing(20)
      },
      y: {
        p10: -spacing(10),
        p20: -spacing(20)
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
        
        // Create animated style for this element with explicit numeric values
        const animatedStyle = useAnimatedStyle(() => {
          // Calculate translation with a much larger circular path
          const translateX = interpolate(
            value.value,
            [0, 0.25, 0.5, 0.75, 1],
            [0, spacingValues.x.p20, 0, spacingValues.x.n20, 0],
            Extrapolate.CLAMP
          );
          
          const translateY = interpolate(
            value.value,
            [0, 0.25, 0.5, 0.75, 1],
            [0, spacingValues.y.p10, spacingValues.y.p20, spacingValues.y.p10, 0],
            Extrapolate.CLAMP
          );
          
          // Calculate rotation with larger range - ensure numeric values
          const rotateValue = interpolate(
            value.value,
            [0, 1],
            [rotationOffset, rotationOffset + 120], // Much larger rotation range
            Extrapolate.CLAMP
          );
          
          return {
            transform: [
              { translateX }, // Now a pure number
              { translateY }, // Now a pure number
              { rotate: `${rotateValue}deg` }, // Now correctly formatted
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