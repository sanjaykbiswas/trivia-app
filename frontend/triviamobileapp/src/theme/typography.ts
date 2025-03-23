/**
 * Application typography system
 * Defines consistent text styles across the app
 */

export const fontFamily = {
    primary: 'System',      // System font as primary
    secondary: 'System',    // System font as secondary
    // Add custom fonts as needed
  };
  
  export const fontWeights = {
    light: '300' as const,
    regular: '400' as const,
    medium: '500' as const,
    semiBold: '600' as const,
    bold: '700' as const,
    extraBold: '800' as const,
  };
  
  export const typography = {
    // Font families
    fontFamily,
    
    // Font weights
    fontWeights,
    
    // Predefined text styles
    heading1: {
      fontFamily: fontFamily.primary,
      fontSize: 32,
      fontWeight: fontWeights.bold,
      lineHeight: 40,
      letterSpacing: 0.25,
    },
    
    heading2: {
      fontFamily: fontFamily.primary,
      fontSize: 28,
      fontWeight: fontWeights.bold,
      lineHeight: 36,
      letterSpacing: 0.25,
    },
    
    heading3: {
      fontFamily: fontFamily.primary,
      fontSize: 24,
      fontWeight: fontWeights.semiBold,
      lineHeight: 32,
      letterSpacing: 0.15,
    },
    
    heading4: {
      fontFamily: fontFamily.primary,
      fontSize: 20,
      fontWeight: fontWeights.semiBold,
      lineHeight: 28,
      letterSpacing: 0.15,
    },
    
    heading5: {
      fontFamily: fontFamily.primary,
      fontSize: 18,
      fontWeight: fontWeights.medium,
      lineHeight: 24,
      letterSpacing: 0.15,
    },
    
    // Body text styles
    bodyLarge: {
      fontFamily: fontFamily.primary,
      fontSize: 18,
      fontWeight: fontWeights.regular,
      lineHeight: 28,
      letterSpacing: 0.5,
    },
    
    bodyMedium: {
      fontFamily: fontFamily.primary,
      fontSize: 16,
      fontWeight: fontWeights.regular,
      lineHeight: 24,
      letterSpacing: 0.5,
    },
    
    bodySmall: {
      fontFamily: fontFamily.primary,
      fontSize: 14,
      fontWeight: fontWeights.regular,
      lineHeight: 20,
      letterSpacing: 0.25,
    },
    
    // Button text styles
    buttonLarge: {
      fontFamily: fontFamily.primary,
      fontSize: 16,
      fontWeight: fontWeights.bold,
      lineHeight: 24,
      letterSpacing: 0.5,
    },
    
    buttonMedium: {
      fontFamily: fontFamily.primary,
      fontSize: 16,
      fontWeight: fontWeights.medium,
      lineHeight: 24,
      letterSpacing: 0.5,
    },
    
    buttonSmall: {
      fontFamily: fontFamily.primary,
      fontSize: 14,
      fontWeight: fontWeights.medium,
      lineHeight: 20,
      letterSpacing: 0.25,
    },
    
    // Caption and small text
    caption: {
      fontFamily: fontFamily.primary,
      fontSize: 12,
      fontWeight: fontWeights.regular,
      lineHeight: 16,
      letterSpacing: 0.4,
    },
    
    overline: {
      fontFamily: fontFamily.primary,
      fontSize: 10,
      fontWeight: fontWeights.medium,
      lineHeight: 16,
      letterSpacing: 1.5,
      textTransform: 'uppercase',
    },
  };
  
  export type TypographyTheme = typeof typography;
  
  export default typography;