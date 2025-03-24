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
  hideBorder?: boolean;
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
  hideBorder = false,
}) => {
  return (
    <View 
      style={[
        styles.container, 
        hideBorder && styles.noBorder,
        style
      ]} 
      testID={testID}
    >
      {title && (
        <View style={styles.titleContainer}>
          <Typography
            variant="heading2"
            align="center"
          >
            {title.split(' ').slice(0, 2).join(' ')}
          </Typography>
          <Typography
            variant="heading2"
            align="center"
            style={styles.title}
          >
            {title.split(' ').slice(2).join(' ')}
          </Typography>
        </View>
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
          <View style={styles.secondaryTextContainer}>
            <Typography
              variant="bodyMedium"
              color={colors.text.secondary}
              align="center"
            >
              {secondaryText.split("Sign In")[0]}
            </Typography>
            <Typography
              variant="bodyMedium"
              color={colors.text.secondary}
              align="center"
              style={{ fontWeight: 'bold' }}
            >
              Sign In
            </Typography>
          </View>
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
  noBorder: {
    borderTopWidth: 0,
  },
  titleContainer: {
    marginBottom: spacing.sm,
  },
  title: {
    marginTop: -4, // Reduced spacing between the two lines (negative value to bring lines closer)
  },
  primaryButton: {
    marginBottom: spacing.xs,
  },
  secondaryButton: {
    paddingVertical: spacing.xs,
  },
  secondaryTextContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default BottomTray;