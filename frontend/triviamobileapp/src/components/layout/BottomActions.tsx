import React, { ReactNode } from 'react';
import { View, StyleSheet, ViewStyle, StyleProp } from 'react-native';
import { colors, spacing } from '../../theme';

interface BottomActionsProps {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/**
 * BottomActions component
 * A container for action buttons fixed at the bottom of the screen
 */
const BottomActions: React.FC<BottomActionsProps> = ({
  children,
  style,
  testID,
}) => {
  return (
    <View style={[styles.container, style]} testID={testID}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: spacing.page,
    paddingVertical: spacing.md, // Standardized padding
    backgroundColor: colors.background.default,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
  },
});

export default BottomActions;