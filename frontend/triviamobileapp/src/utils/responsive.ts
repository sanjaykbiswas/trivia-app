import { Dimensions, PixelRatio, Platform, StatusBar } from 'react-native';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Base dimensions for scaling calculations (based on iPhone 11)
const baseWidth = 375;
const baseHeight = 812;

// Scale factor for responsive sizing
const widthScaleFactor = SCREEN_WIDTH / baseWidth;
const heightScaleFactor = SCREEN_HEIGHT / baseHeight;

/**
 * Get responsive width based on screen size
 * @param size Size in pixels based on design (base device width: 375px)
 */
export const wp = (size: number): number => {
  return Math.round(size * widthScaleFactor);
};

/**
 * Get responsive height based on screen size
 * @param size Size in pixels based on design (base device height: 812px)
 */
export const hp = (size: number): number => {
  return Math.round(size * heightScaleFactor);
};

/**
 * Get responsive font size that scales with screen size
 * @param size Font size in pixels
 */
export const getFontSize = (size: number): number => {
  // Scale based on width but with a smaller factor to prevent too large fonts on tablets
  const scaleFactor = Math.min(widthScaleFactor, 1.2);
  const newSize = size * scaleFactor;
  
  // Use PixelRatio to adjust for pixel density
  return Math.round(PixelRatio.roundToNearestPixel(newSize));
};

/**
 * Get current device information
 */
export const getDeviceInfo = () => {
  return {
    width: SCREEN_WIDTH,
    height: SCREEN_HEIGHT,
    isIOS: Platform.OS === 'ios',
    isAndroid: Platform.OS === 'android',
    isSmallDevice: SCREEN_WIDTH < 375,
    isLargeDevice: SCREEN_WIDTH >= 768, // iPad/tablet size
    hasNotch: isDeviceWithNotch(),
    statusBarHeight: StatusBar.currentHeight || 0,
  };
};

/**
 * Check if device has a notch
 */
const isDeviceWithNotch = (): boolean => {
  // This is a simple check and might need refinement
  const { width, height } = Dimensions.get('window');
  
  // iOS devices with notch
  if (Platform.OS === 'ios') {
    return (
      // iPhone X, XS, 11 Pro
      (width === 375 && height === 812) ||
      // iPhone XS Max, XR, 11, 11 Pro Max
      (width === 414 && height === 896) ||
      // iPhone 12 mini
      (width === 360 && height === 780) ||
      // iPhone 12, 12 Pro
      (width === 390 && height === 844) ||
      // iPhone 12 Pro Max
      (width === 428 && height === 926)
    );
  }
  
  // On Android, we can't reliably detect a notch, so return false
  return false;
};