// src/utils/scaling.ts
import { Dimensions, PixelRatio, Platform } from 'react-native';

// Get screen dimensions
const { width, height } = Dimensions.get('window');

// Create a scale based on screen size
const scale = Math.min(width, height) / 375; // Base scale on iPhone 8 dimensions

// Function to normalize font sizes for different screen densities
export const normalize = (size: number): number => {
  const newSize = size * scale;
  if (Platform.OS === 'ios') {
    return Math.round(PixelRatio.roundToNearestPixel(newSize));
  }
  return Math.round(PixelRatio.roundToNearestPixel(newSize)) - 2; // Slightly smaller text on Android
};

// Function to create responsive spacing
export const spacing = (size: number): number => {
  return Math.round(size * scale);
};