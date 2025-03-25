import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  StyleSheet,
  Animated,
  TouchableWithoutFeedback,
  Keyboard,
  Dimensions,
  ViewStyle,
  StyleProp,
  Platform,
} from 'react-native';
import { colors, spacing } from '../../theme';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

interface SlidingTrayProps {
  isVisible: boolean;
  onDismiss: () => void;
  children: React.ReactNode;
  height?: number | string;
  style?: StyleProp<ViewStyle>;
  overlayColor?: string;
  overlayOpacity?: number;
  animationDuration?: number;
}

/**
 * A sliding tray component that animates from the bottom of the screen
 * Can be used for input forms, selections, or any content that should appear on demand
 */
const SlidingTray: React.FC<SlidingTrayProps> = ({
  isVisible,
  onDismiss,
  children,
  height = '50%',
  style,
  overlayColor = colors.gray[900],
  overlayOpacity = 0.5,
  animationDuration = 300,
}) => {
  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const insets = useSafeAreaInsets();
  
  // Track animation completion state
  const [animationComplete, setAnimationComplete] = useState(!isVisible);

  // Calculate the height value based on percentage or absolute
  const calculateHeight = () => {
    if (typeof height === 'string' && height.includes('%')) {
      const percentage = parseInt(height, 10) / 100;
      return SCREEN_HEIGHT * percentage;
    }
    return typeof height === 'number' ? height : SCREEN_HEIGHT * 0.5;
  };

  const actualHeight = calculateHeight();

  useEffect(() => {
    if (isVisible) {
      // Show the tray with animation
      setAnimationComplete(false);
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 1,
          duration: animationDuration,
          useNativeDriver: true,
        }),
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: animationDuration,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      // Hide the tray with animation
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: 0,
          duration: animationDuration,
          useNativeDriver: true,
        }),
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: animationDuration,
          useNativeDriver: true,
        }),
      ]).start(() => {
        // Mark animation as complete after it finishes
        setAnimationComplete(true);
      });
    }
  }, [isVisible, slideAnim, fadeAnim, animationDuration]);

  // If not visible and animation is complete, don't render
  if (!isVisible && animationComplete) return null;

  return (
    <View style={styles.container} pointerEvents={isVisible ? 'auto' : 'none'}>
      {/* Background overlay */}
      <TouchableWithoutFeedback onPress={() => {
        Keyboard.dismiss();
        onDismiss();
      }}>
        <Animated.View
          style={[
            styles.overlay,
            {
              backgroundColor: overlayColor,
              opacity: fadeAnim.interpolate({
                inputRange: [0, 1],
                outputRange: [0, overlayOpacity],
              }),
            },
          ]}
        />
      </TouchableWithoutFeedback>

      {/* Sliding tray */}
      <Animated.View
        style={[
          styles.tray,
          style,
          {
            height: actualHeight,
            paddingBottom: Platform.OS === 'ios' ? insets.bottom : spacing.md,
            transform: [
              {
                translateY: slideAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: [actualHeight, 0],
                }),
              },
            ],
          },
        ]}
      >
        <View style={styles.handle} />
        <View style={styles.content}>{children}</View>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'flex-end',
    zIndex: 1000,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
  },
  tray: {
    backgroundColor: colors.background.default,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingHorizontal: spacing.page,
    paddingTop: spacing.md,
    shadowColor: colors.gray[900],
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 10,
  },
  handle: {
    width: 40,
    height: 5,
    backgroundColor: colors.gray[300],
    borderRadius: 3,
    alignSelf: 'center',
    marginBottom: spacing.md,
  },
  content: {
    flex: 1,
  },
});

export default SlidingTray;