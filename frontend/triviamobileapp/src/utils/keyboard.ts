import { useEffect, useState, useCallback } from 'react';
import { Keyboard, KeyboardEvent, Platform, Dimensions } from 'react-native';

/**
 * Hook to track keyboard visibility and height
 * @returns Object with isKeyboardVisible state and keyboardHeight
 */
export function useKeyboard() {
  const [isKeyboardVisible, setKeyboardVisible] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);

  useEffect(() => {
    const keyboardDidShowListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
      (event: KeyboardEvent) => {
        setKeyboardVisible(true);
        setKeyboardHeight(event.endCoordinates.height);
      }
    );

    const keyboardDidHideListener = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
      () => {
        setKeyboardVisible(false);
        setKeyboardHeight(0);
      }
    );

    // Clean up event listeners
    return () => {
      keyboardDidShowListener.remove();
      keyboardDidHideListener.remove();
    };
  }, []);

  return { isKeyboardVisible, keyboardHeight };
}

/**
 * Enhanced hook for keyboard management with additional utilities
 * @returns Object with keyboard state, height, and helper functions
 */
export function useKeyboardManager() {
  const { isKeyboardVisible, keyboardHeight } = useKeyboard();
  
  // Calculate available screen height (minus keyboard)
  const screenHeight = Dimensions.get('window').height;
  const availableHeight = isKeyboardVisible 
    ? screenHeight - keyboardHeight 
    : screenHeight;

  // Dismiss keyboard helper
  const dismissKeyboard = useCallback(() => {
    Keyboard.dismiss();
  }, []);

  return { 
    isKeyboardVisible, 
    keyboardHeight, 
    availableHeight,
    dismissKeyboard
  };
}

/**
 * Dismiss keyboard helper function
 */
export const dismissKeyboard = () => {
  Keyboard.dismiss();
};

/**
 * Utility to avoid keyboard overlapping text inputs
 * Use this when you need specific actions on keyboard show/hide
 * @param onShow Function to run when keyboard shows
 * @param onHide Function to run when keyboard hides
 * @returns Cleanup function to remove listeners
 */
export const setupKeyboardListeners = (
  onShow?: (event: KeyboardEvent) => void,
  onHide?: () => void
): (() => void) => {
  const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
  const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

  const keyboardDidShowListener = onShow
    ? Keyboard.addListener(showEvent, onShow)
    : null;

  const keyboardDidHideListener = onHide
    ? Keyboard.addListener(hideEvent, onHide)
    : null;

  return () => {
    if (keyboardDidShowListener) keyboardDidShowListener.remove();
    if (keyboardDidHideListener) keyboardDidHideListener.remove();
  };
};