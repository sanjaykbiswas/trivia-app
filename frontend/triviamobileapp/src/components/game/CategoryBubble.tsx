import React from 'react';
import { StyleSheet, TouchableOpacity, StyleProp, ViewStyle } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';

interface CategoryBubbleProps {
  title: string;
  isActive?: boolean;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/**
 * CategoryBubble component
 * A selectable bubble filter used in category selection
 */
const CategoryBubble: React.FC<CategoryBubbleProps> = ({
  title,
  isActive = false,
  onPress,
  style,
  testID,
}) => {
  return (
    <TouchableOpacity
      style={[styles.bubble, isActive && styles.activeBubble, style]}
      onPress={onPress}
      activeOpacity={0.7}
      testID={testID}
    >
      <Typography
        variant="bodySmall"
        color={isActive ? colors.primary.contrastText : colors.text.secondary}
        style={styles.text}
      >
        {title}
      </Typography>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  bubble: {
    paddingVertical: 6,
    paddingHorizontal: 16,
    backgroundColor: colors.background.light,
    borderRadius: 16,
    marginRight: 8,
    height: 32, // Fixed height for consistency
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.background.light, // Adding border to prevent shifting when active
  },
  activeBubble: {
    backgroundColor: colors.primary.main,
    borderColor: colors.primary.main,
  },
  text: {
    fontWeight: '500',
    fontSize: 14,
  },
});

export default CategoryBubble;