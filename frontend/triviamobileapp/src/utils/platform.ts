import { Platform, NativeModules, Dimensions, StatusBar } from 'react-native';

const { StatusBarManager } = NativeModules;

/**
 * Get the status bar height for iOS
 */
export const getStatusBarHeight = (skipAndroid = false): number => {
  if (Platform.OS === 'ios') {
    return StatusBarManager?.height || 20;
  }
  
  if (skipAndroid) {
    return 0;
  }
  
  return StatusBar.currentHeight || 0;
};

/**
 * Get the bottom inset for devices with home indicator (notched devices)
 */
export const getBottomInset = (): number => {
  if (Platform.OS === 'ios') {
    // These values are estimates for common iOS devices
    const { height, width } = Dimensions.get('window');
    const aspectRatio = height / width;
    
    // iPhone X or newer
    if (aspectRatio > 2) {
      return 34;
    }
    
    return 0;
  }
  
  // No bottom inset for Android
  return 0;
};

/**
 * Check if the device is a tablet
 */
export const isTablet = (): boolean => {
  const { width, height } = Dimensions.get('window');
  const aspectRatio = height / width;
  
  // iPad typically has aspect ratio less than 1.6
  return aspectRatio < 1.6 && Math.max(width, height) >= 768;
};

/**
 * Helper to conditionally apply styles based on platform
 */
export const platformSpecific = <T>(ios: T, android: T): T => {
  return Platform.select({
    ios,
    android,
  }) as T;
};