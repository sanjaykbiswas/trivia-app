// src/components/LinearGradientCircle.tsx
// Simplified version that doesn't try to handle animated styles

import React from 'react';
import { StyleSheet, ViewStyle } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { spacing } from '../utils/scaling';

interface LinearGradientCircleProps {
  size: number;
  colors: string[];
  style?: ViewStyle; 
  children?: React.ReactNode;
}

const LinearGradientCircle: React.FC<LinearGradientCircleProps> = ({
  size,
  colors,
  style,
  children,
}) => {
  const circleStyle: ViewStyle = {
    width: spacing(size),
    height: spacing(size),
    borderRadius: spacing(size / 2),
  };

  return (
    <LinearGradient
      colors={colors}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[circleStyle, styles.gradient, style]}
    >
      {children}
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  gradient: {
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
});

export default LinearGradientCircle;