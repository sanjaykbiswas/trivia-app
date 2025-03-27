import React from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { Typography, Button } from '../common';
import { colors, spacing } from '../../theme';

interface FeedbackPanelProps {
  isCorrect: boolean;
  correctAnswer: string;
  animationValue: Animated.Value;
  onNextPress: () => void;
  isLastQuestion: boolean;
}

export const FeedbackPanel: React.FC<FeedbackPanelProps> = ({
  isCorrect,
  correctAnswer,
  animationValue,
  onNextPress,
  isLastQuestion,
}) => {
  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [
            {
              translateY: animationValue.interpolate({
                inputRange: [0, 100],
                outputRange: [0, 300], // Fully off-screen
              }),
            },
          ],
        },
      ]}
    >
      <Typography
        variant="heading3"
        style={styles.title}
        color={isCorrect ? colors.success.main : colors.error.main}
      >
        {isCorrect ? 'Correct!' : 'Incorrect'}
      </Typography>

      <Typography
        variant="bodyMedium"
        style={styles.message}
        color={colors.text.primary}
      >
        {isCorrect
          ? 'Great job!'
          : `The correct answer is: ${correctAnswer}`}
      </Typography>

      <Button
        title={isLastQuestion ? 'Finish Quiz' : 'Next Question'}
        onPress={onNextPress}
        variant="contained"
        size="large"
        fullWidth
        style={styles.button}
      />
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: colors.background.default,
    padding: spacing.lg,
    paddingBottom: spacing.xl,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    shadowColor: colors.gray[900],
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 10,
  },
  title: {
    textAlign: 'center',
    marginBottom: spacing.xs,
    fontWeight: 'bold',
  },
  message: {
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  button: {
    marginTop: spacing.md,
  },
});