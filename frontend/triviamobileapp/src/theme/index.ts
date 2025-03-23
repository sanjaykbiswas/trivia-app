/**
 * Theme exports and configuration
 * Centralizes all theme elements
 */

import colors, { ColorTheme } from './colors';
import spacing, { SpacingTheme } from './spacing';
import typography, { TypographyTheme } from './typography';

export type Theme = {
  colors: ColorTheme;
  spacing: SpacingTheme;
  typography: TypographyTheme;
};

// Default theme configuration
export const theme: Theme = {
  colors,
  spacing,
  typography,
};

export { colors, spacing, typography };
export default theme;