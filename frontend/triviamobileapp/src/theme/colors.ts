/**
 * Application color palette
 * Centralized color definitions to maintain consistency throughout the app
 */

export const colors = {
    // Primary brand colors
    primary: {
      main: '#000000',          // Primary black
      light: '#333333',
      dark: '#000000',
      contrastText: '#FFFFFF',  // White text on primary color
    },
    
    // Secondary colors
    secondary: {
      main: '#FFFFFF',
      dark: '#F5F5F5',
      light: '#FFFFFF',
      contrastText: '#000000',
    },
    
    // Semantic colors for states and feedback
    success: {
      main: '#4CAF50',
      light: '#81C784',
      dark: '#388E3C',
      contrastText: '#FFFFFF',
    },
    
    error: {
      main: '#F44336',
      light: '#E57373',
      dark: '#D32F2F',
      contrastText: '#FFFFFF',
    },
    
    warning: {
      main: '#FF9800',
      light: '#FFB74D',
      dark: '#F57C00',
      contrastText: '#000000',
    },
    
    info: {
      main: '#2196F3',
      light: '#64B5F6',
      dark: '#1976D2',
      contrastText: '#FFFFFF',
    },
    
    // Grayscale
    gray: {
      50: '#FAFAFA',
      100: '#F5F5F5',
      200: '#EEEEEE',
      300: '#E0E0E0',
      400: '#BDBDBD',
      500: '#9E9E9E',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },
    
    // Text colors
    text: {
      primary: '#000000',
      secondary: '#757575',
      disabled: '#9E9E9E',
      hint: '#9E9E9E',
    },
    
    // Background colors
    background: {
      default: '#FFFFFF',
      paper: '#FFFFFF',
      light: '#F5F5F5',
    },
    
    // Divider and border colors
    divider: '#E0E0E0',
    border: '#E0E0E0',
  };
  
  export type ColorTheme = typeof colors;
  
  export default colors;