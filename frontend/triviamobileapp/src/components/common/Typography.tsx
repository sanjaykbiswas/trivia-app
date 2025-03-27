import React from 'react';
import {
  Text,
  StyleSheet,
  TextStyle,
  StyleProp,
  TextProps as RNTextProps,
} from 'react-native';
import { typography, colors } from '../../theme';

// Available typography variants
type TypographyVariant =
  | 'heading1'
  | 'heading2'
  | 'heading3'
  | 'heading4'
  | 'heading5'
  | 'bodyLarge'
  | 'bodyMedium'
  | 'bodySmall'
  | 'buttonLarge'
  | 'buttonMedium'
  | 'buttonSmall'
  | 'caption'
  | 'overline';

interface TypographyProps extends RNTextProps {
  children: React.ReactNode;
  variant?: TypographyVariant;
  style?: StyleProp<TextStyle>;
  color?: string;
  align?: 'auto' | 'left' | 'right' | 'center' | 'justify';
  testID?: string;
}

/**
 * Typography component
 * Renders text with predefined styles based on the design system
 */
const Typography: React.FC<TypographyProps> = ({
  children,
  variant = 'bodyMedium',
  style,
  color = colors.text.primary,
  align = 'left',
  testID,
  ...rest
}) => {
  // Get the style for the specified variant
  const variantStyle = typography[variant];

  // Apply text styles
  const textStyle: TextStyle = {
    // Take only the properties from variantStyle that are compatible with TextStyle
    fontFamily: variantStyle.fontFamily,
    fontSize: variantStyle.fontSize,
    fontWeight: variantStyle.fontWeight as TextStyle['fontWeight'],
    lineHeight: variantStyle.lineHeight,
    letterSpacing: variantStyle.letterSpacing,
    color,
    textAlign: align,
  };
  
  // Add textTransform if available (only present in some typography variants)
  if ('textTransform' in variantStyle) {
    textStyle.textTransform = variantStyle.textTransform as TextStyle['textTransform'];
  }

  // Safely render children
  const renderChildren = () => {
    // Direct string is fine
    if (typeof children === 'string' || typeof children === 'number') {
      return children;
    }
    
    // React elements are fine
    if (React.isValidElement(children)) {
      return children;
    }
    
    // If it's an array, we need to handle each item
    if (Array.isArray(children)) {
      return children;
    }
    
    // For other types (like undefined, null, boolean), convert to string or return empty
    if (children === null || children === undefined || typeof children === 'boolean') {
      return '';
    }
    
    // Fallback for other types
    return String(children);
  };

  return (
    <Text style={[textStyle, style]} testID={testID} {...rest}>
      {renderChildren()}
    </Text>
  );
};

export default Typography;