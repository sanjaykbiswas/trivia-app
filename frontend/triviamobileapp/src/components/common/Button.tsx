import React from 'react';
import {
  TouchableOpacity,
  StyleSheet,
  ViewStyle,
  TextStyle,
  StyleProp,
  ActivityIndicator,
  View,
} from 'react-native';
import Typography from './Typography';
import { colors, spacing, typography } from '../../theme';

type ButtonVariant = 'contained' | 'outlined' | 'text';
type ButtonSize = 'small' | 'medium' | 'large';

interface ButtonProps {
  onPress: () => void;
  title: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
  testID?: string;
}

/**
 * Button component
 * Reusable button with different variants and states
 */
const Button: React.FC<ButtonProps> = ({
  onPress,
  title,
  variant = 'contained',
  size = 'medium',
  disabled = false,
  loading = false,
  fullWidth = false,
  style,
  textStyle,
  testID,
}) => {
  // Determine button container styles based on variant and size
  const getContainerStyle = (): ViewStyle => {
    const baseStyle: ViewStyle = {
      borderRadius: 16, // For fully rounded use 100
      justifyContent: 'center',
      alignItems: 'center',
      flexDirection: 'row',
      width: fullWidth ? '100%' : 'auto',
      opacity: disabled ? 0.7 : 1,
    };

    // Apply padding based on size
    switch (size) {
      case 'small':
        baseStyle.paddingVertical = spacing.buttonPadding.vertical - 4;
        baseStyle.paddingHorizontal = spacing.buttonPadding.horizontal - 4;
        break;
      case 'large':
        baseStyle.paddingVertical = spacing.buttonPadding.vertical + 4;
        baseStyle.paddingHorizontal = spacing.buttonPadding.horizontal + 4;
        break;
      default: // medium
        baseStyle.paddingVertical = spacing.buttonPadding.vertical;
        baseStyle.paddingHorizontal = spacing.buttonPadding.horizontal;
        break;
    }

    // Apply styles based on variant
    switch (variant) {
      case 'outlined':
        return {
          ...baseStyle,
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderColor: disabled ? colors.text.disabled : colors.primary.main,
        };
      case 'text':
        return {
          ...baseStyle,
          backgroundColor: 'transparent',
          paddingVertical: spacing.sm,
          paddingHorizontal: spacing.sm,
        };
      default: // contained
        return {
          ...baseStyle,
          backgroundColor: disabled ? colors.gray[300] : colors.primary.main,
        };
    }
  };

  // Determine text style based on variant and size
  const getTextStyle = (): TextStyle => {
    // Choose typography variant based on size
    let textVariant: 'buttonSmall' | 'buttonMedium' | 'buttonLarge';
    
    switch (size) {
      case 'small':
        textVariant = 'buttonSmall';
        break;
      case 'large':
        textVariant = 'buttonLarge';
        break;
      default: // medium
        textVariant = 'buttonMedium';
        break;
    }

    // Base text style
    const baseTextStyle: TextStyle = {
      fontFamily: typography[textVariant].fontFamily,
      fontSize: typography[textVariant].fontSize,
      fontWeight: typography[textVariant].fontWeight as TextStyle['fontWeight'],
      lineHeight: typography[textVariant].lineHeight,
      letterSpacing: typography[textVariant].letterSpacing,
    };

    // Apply color based on variant
    switch (variant) {
      case 'outlined':
        baseTextStyle.color = disabled ? colors.text.disabled : colors.primary.main;
        break;
      case 'text':
        baseTextStyle.color = disabled ? colors.text.disabled : colors.primary.main;
        break;
      default: // contained
        baseTextStyle.color = colors.primary.contrastText;
        break;
    }

    return baseTextStyle;
  };

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      style={[getContainerStyle(), style]}
      testID={testID}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={
            variant === 'contained'
              ? colors.primary.contrastText
              : colors.primary.main
          }
        />
      ) : (
        <Typography style={[getTextStyle(), textStyle]}>{title}</Typography>
      )}
    </TouchableOpacity>
  );
};

export default Button;