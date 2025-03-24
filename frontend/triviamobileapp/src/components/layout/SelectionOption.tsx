import React from 'react';
import { View, StyleSheet, TouchableOpacity, StyleProp, ViewStyle, Text } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';

interface SelectionOptionProps {
  title: string;
  subtitle: string;
  emoji?: string;
  icon?: React.ReactNode;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

const SelectionOption: React.FC<SelectionOptionProps> = ({
  title,
  subtitle,
  emoji,
  icon,
  onPress,
  style,
  testID,
}) => {
  return (
    <TouchableOpacity
      style={[styles.container, style]}
      onPress={onPress}
      testID={testID}
      activeOpacity={0.7}
    >
      {emoji ? (
        <View style={styles.emojiContainer}>
          <Text style={styles.emoji}>{emoji}</Text>
        </View>
      ) : icon ? (
        <View style={styles.iconContainer}>{icon}</View>
      ) : null}
      
      <View style={styles.content}>
        <Typography variant="heading5" style={styles.title}>
          {title}
        </Typography>
        <Typography variant="bodySmall" color={colors.text.secondary} style={styles.subtitle}>
          {subtitle}
        </Typography>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8F9FF',
    borderRadius: 16,
    padding: spacing.md,
    marginBottom: spacing.md,
    shadowColor: colors.gray[900],
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  emojiContainer: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  emoji: {
    fontSize: 32,
  },
  iconContainer: {
    width: 48,
    height: 48,
    backgroundColor: colors.background.default,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
    shadowColor: colors.gray[900],
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  content: {
    flex: 1,
  },
  title: {
    marginBottom: 4,
  },
  subtitle: {
    lineHeight: 20,
  },
});

export default SelectionOption;