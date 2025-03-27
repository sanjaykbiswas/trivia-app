import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Animated, Easing } from 'react-native';
import { Typography } from '../common';
import { colors } from '../../theme';

interface QuestionTimerProps {
  timeLeft: number;
  totalTime: number;
  active: boolean;
}

export const QuestionTimer: React.FC<QuestionTimerProps> = ({ timeLeft, totalTime, active }) => {
  const [spinAnimation] = useState(new Animated.Value(0));
  
  // Percentage of time left for visual feedback
  const percentLeft = timeLeft / totalTime;
  
  // Change color based on time left
  const getTimerColor = () => {
    if (percentLeft > 0.6) return colors.primary.main;
    if (percentLeft > 0.3) return colors.warning.main;
    return colors.error.main;
  };
  
  useEffect(() => {
    // Reset animation when timer is reset
    if (timeLeft === totalTime) {
      spinAnimation.setValue(0);
    }
    
    if (active) {
      // Animate timer rotation for visual countdown
      Animated.timing(spinAnimation, {
        toValue: 1,
        duration: timeLeft * 1000,
        easing: Easing.linear,
        useNativeDriver: true,
      }).start();
    } else {
      // Pause animation when timer is paused
      spinAnimation.stopAnimation();
    }
  }, [timeLeft, active, totalTime]);
  
  // Calculate rotation for the progress indicator
  const rotate = spinAnimation.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={styles.container}>
      {/* Static circle background */}
      <View style={[styles.timerCircle, { borderColor: colors.gray[200] }]} />
      
      {/* Animated progress circle */}
      <Animated.View
        style={[
          styles.timerProgress,
          {
            borderColor: getTimerColor(),
            transform: [{ rotate }],
          },
        ]}
      />
      
      {/* Timer text */}
      <Typography
        variant="bodyLarge"
        style={styles.timerText}
        color={timeLeft <= 10 ? colors.error.main : colors.text.primary}
      >
        {timeLeft}
      </Typography>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: 48,
    height: 48,
    position: 'absolute',
    left: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  timerCircle: {
    position: 'absolute',
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 3,
    borderColor: '#EEEEEE',
  },
  timerProgress: {
    position: 'absolute',
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 3,
    borderLeftColor: 'transparent',
    borderBottomColor: 'transparent',
    transform: [{ rotate: '-90deg' }],
  },
  timerText: {
    fontWeight: 'bold',
    fontSize: 18,
  },
});