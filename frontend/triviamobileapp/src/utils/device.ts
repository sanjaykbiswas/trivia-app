import { Dimensions, Platform, NativeModules, PixelRatio } from 'react-native';
import { isTablet } from './platform';

const { width, height } = Dimensions.get('window');

/**
 * Device utility for handling device-specific metrics and capabilities
 */
export const Device = {
  /**
   * Screen dimensions
   */
  screen: {
    width,
    height,
    /**
     * Get the screen width or height depending on orientation
     */
    get widthInCurrentOrientation() {
      const { width, height } = Dimensions.get('window');
      return width < height ? width : height;
    },
    get heightInCurrentOrientation() {
      const { width, height } = Dimensions.get('window');
      return width < height ? height : width;
    },
  },

  /**
   * OS-specific properties
   */
  os: {
    isAndroid: Platform.OS === 'android',
    isIOS: Platform.OS === 'ios',
    version: Platform.Version,
    /**
     * Check if the device is running iOS 11 or higher
     */
    isIphoneX: () => {
      if (Platform.OS === 'ios') {
        const dimension = Dimensions.get('window');
        return (
          (dimension.height === 812 || dimension.width === 812) || // iPhone X, XS, 11 Pro
          (dimension.height === 896 || dimension.width === 896) || // iPhone XR, XS Max, 11, 11 Pro Max
          (dimension.height === 844 || dimension.width === 844) || // iPhone 12, 12 Pro
          (dimension.height === 926 || dimension.width === 926)    // iPhone 12 Pro Max
        );
      }
      return false;
    },
  },

  /**
   * Device type classification
   */
  type: {
    isPhone: !isTablet(),
    isTablet: isTablet(),
  },

  /**
   * Pixel density
   */
  pixelDensity: PixelRatio.get(),

  /**
   * Convert DP (Device Independent Pixels) to PX (Pixels)
   */
  dpToPx: (dp: number) => PixelRatio.getPixelSizeForLayoutSize(dp),

  /**
   * Convert PX (Pixels) to DP (Device Independent Pixels)
   */
  pxToDp: (px: number) => px / PixelRatio.get(),
};