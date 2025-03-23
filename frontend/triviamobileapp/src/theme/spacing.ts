/**
 * Application spacing system
 * Centralized spacing units to maintain consistent layout throughout the app
 */

// Base spacing unit (in pixels)
const baseUnit = 8;

export const spacing = {
  // Named spacing values
  none: 0,
  xs: baseUnit / 2,       // 4px
  sm: baseUnit,           // 8px
  md: baseUnit * 2,       // 16px
  lg: baseUnit * 3,       // 24px
  xl: baseUnit * 4,       // 32px
  xxl: baseUnit * 6,      // 48px
  xxxl: baseUnit * 8,     // 64px
  
  // Function to get custom spacing
  custom: (multiplier: number) => baseUnit * multiplier,
  
  // Common layout spacing
  page: baseUnit * 2,     // 16px - Standard page padding
  section: baseUnit * 3,  // 24px - Spacing between sections
  item: baseUnit,         // 8px - Spacing between items in a list
  stack: baseUnit * 2,    // 16px - Vertical spacing between stacked elements
  
  // Button spacing
  buttonPadding: {
    vertical: baseUnit * 1.5,   // 12px
    horizontal: baseUnit * 2.5, // 20px
  },
};

export type SpacingTheme = typeof spacing;

export default spacing;