import React from 'react';
import { View, StyleSheet, TouchableOpacity, StyleProp, ViewStyle } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';

interface AnswerOptionProps {
  letter: string;
  text: string;
  isSelected?: boolean;
  isCorrect?: boolean;
  isIncorrect?: boolean;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  disabled?: boolean;
  testID?: string;
}

export const AnswerOption: React.FC<AnswerOptionProps> = ({
  letter,
  text,
  isSelected = false,
  isCorrect = false,
  isIncorrect = false,
  onPress,
  style,
  disabled = false,
  testID,
}) => {
  // Determine the style based on the current state
  const getContainerStyle = () => {
    if (isCorrect) {
      return [styles.container, styles.correctContainer];
    }
    if (isIncorrect) {
      return [styles.container, styles.incorrectContainer];
    }
    if (isSelected) {
      return [styles.container, styles.selectedContainer];
    }
    return styles.container;
  };

  return (
    <TouchableOpacity
      style={[getContainerStyle(), style]}
      onPress={onPress}
      activeOpacity={0.7}
      disabled={disabled}
      testID={testID}
    >
      <View
        style={[
          styles.letterContainer,
          isSelected && styles.selectedLetterContainer,
          isCorrect && styles.correctLetterContainer,
          isIncorrect && styles.incorrectLetterContainer,
        ]}
      >
        <Typography
          variant="bodyMedium"
          style={styles.letter}
          color={isSelected || isCorrect || isIncorrect ? colors.text.primary : colors.text.primary}
        >
          {letter}
        </Typography>
      </View>
      <Typography
        variant="bodyMedium"
        style={styles.text}
        color={
          isSelected || isCorrect || isIncorrect
            ? colors.primary.contrastText
            : colors.text.primary
        }
      >
        {text}
      </Typography>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: 16,
    backgroundColor: colors.background.light,
    borderWidth: 1,
    borderColor: colors.divider,
  },
  selectedContainer: {
    backgroundColor: colors.primary.main,
    borderColor: colors.primary.main,
  },
  correctContainer: {
    backgroundColor: colors.success.main,
    borderColor: colors.success.main,
  },
  incorrectContainer: {
    backgroundColor: colors.error.main,
    borderColor: colors.error.main,
  },
  letterContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.background.default,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  selectedLetterContainer: {
    backgroundColor: colors.background.default,
  },
  correctLetterContainer: {
    backgroundColor: colors.background.default,
  },
  incorrectLetterContainer: {
    backgroundColor: colors.background.default,
  },
  letter: {
    fontWeight: 'bold',
  },
  text: {
    flex: 1,
    fontWeight: '500',
  },
});