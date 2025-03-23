import React from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  StyleProp,
  TouchableOpacity,
} from 'react-native';
import { Typography, Button } from '../common';
import { colors, spacing } from '../../theme';

interface BottomTrayProps {
  title?: string;
  primaryButtonText: string;
  primaryButtonAction: () => void;
  secondaryText?: string;
  secondaryAction?: () => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/**
 * BottomTray component
 * A reusable tray that appears at the bottom of the screen with actions
 */
const BottomTray: React.FC<BottomTrayProps> = ({
  title,
  primaryButtonText,
  primaryButtonAction,
  secondaryText,
  secondaryAction,
  style,
  testID,
}) => {
  return (
    <View style={[styles.container, style]} testID={testID}>
      {title && (
        <Typography
          variant="heading5"
          align="center"
          style={styles.title}
        >
          {title}
        </Typography>
      )}

      <Button
        title={primaryButtonText}
        onPress={primaryButtonAction}
        variant="contained"
        size="large"
        fullWidth
        style={styles.primaryButton}
      />

      {secondaryText && (
        <TouchableOpacity
          onPress={secondaryAction}
          style={styles.secondaryButton}
          disabled={!secondaryAction}
        >
          <Typography
            variant="bodyMedium"
            color={colors.text.secondary}
            align="center"
          >
            {secondaryText}
          </Typography>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background.default,
    paddingHorizontal: spacing.page,
    paddingVertical: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
  },
  title: {
    marginBottom: spacing.md,
  },
  primaryButton: {
    marginBottom: spacing.md,
  },
  secondaryButton: {
    paddingVertical: spacing.xs,
  },
});

export default BottomTray;