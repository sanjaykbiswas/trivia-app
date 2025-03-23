// Update the LinearGradientCircle.tsx component:

import React from 'react';
import { StyleSheet, View, Text, ViewStyle, TextStyle } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import Animated from 'react-native-reanimated';
import { spacing } from '../utils/scaling';

interface LinearGradientCircleProps {
  size: number;
  colors: string[];
  style?: any; // Change this to 'any' to accept any style props
  animatedStyle?: any;
  children?: React.ReactNode;
}

const LinearGradientCircle: React.FC<LinearGradientCircleProps> = ({
  size,
  colors,
  style,
  animatedStyle,
  children,
}) => {
  const circleStyle: ViewStyle = {
    width: spacing(size),
    height: spacing(size),
    borderRadius: spacing(size / 2),
  };

  return (
    <Animated.View style={[circleStyle, style, animatedStyle]}>
      <LinearGradient
        colors={colors}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[circleStyle, styles.gradient]}
      >
        {children}
      </LinearGradient>
    </Animated.View>
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