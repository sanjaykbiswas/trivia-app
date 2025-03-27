import React, { ReactNode } from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  StyleProp,
  TouchableOpacity,
  Text,
} from 'react-native';
import { Typography, Button } from '../common';
import { colors, spacing } from '../../theme';

interface BottomTrayProps {
  title?: string;
  primaryButtonText?: string;
  primaryButtonAction?: () => void;
  secondaryText?: string;
  secondaryAction?: () => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
  hideBorder?: boolean;
  children?: React.ReactNode; // New prop for custom content
}

/**
 * BottomTray component
 * A reusable tray that appears at the bottom of the screen with actions
 * Now supports custom content through children prop
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
  children,
}) => {
  // Function to render secondary text with "Sign In" part in bold
  const renderSecondaryText = () => {
    if (!secondaryText) return null;
    
    if (secondaryText.includes("Sign In")) {
      const parts = secondaryText.split("Sign In");
      return (
        <View style={styles.secondaryTextContainer}>
          <Typography
            variant="bodyMedium"
            color={colors.text.secondary}
            align="center"
          >
            <Text>{parts[0]}</Text>
            <Text style={{ fontWeight: 'bold' }}>Sign In</Text>
            {parts.length > 1 && <Text>{parts[1]}</Text>}
          </Typography>
        </View>
      );
    } else {
      return (
        <Typography
          variant="bodyMedium"
          color={colors.text.secondary}
          align="center"
        >
          <Text>{secondaryText}</Text>
        </Typography>
      );
    }
  };

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
            <Text>{title.split(' ').slice(0, 2).join(' ')}</Text>
          </Typography>
          <Typography
            variant="heading2"
            align="center"
            style={styles.title}
          >
            <Text>{title.split(' ').slice(2).join(' ')}</Text>
          </Typography>
        </View>
      )}

      {/* Render custom content if provided */}
      {children}

      {/* Render primary button only if text and action are provided */}
      {primaryButtonText && primaryButtonAction && (
        <Button
          title={primaryButtonText}
          onPress={primaryButtonAction}
          variant="contained"
          size="large"
          fullWidth
          style={styles.primaryButton}
        />
      )}

      {secondaryText && (
        <TouchableOpacity
          onPress={secondaryAction}
          style={styles.secondaryButton}
          disabled={!secondaryAction}
        >
          {renderSecondaryText()}
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
    marginTop: -4, // Reduced spacing between the two lines
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