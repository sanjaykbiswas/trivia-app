import React from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  StyleProp,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { colors } from '../../theme';

interface ContainerProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  useSafeArea?: boolean;
  statusBarColor?: string;
  statusBarStyle?: 'default' | 'light-content' | 'dark-content';
  backgroundColor?: string;
  edges?: Array<'top' | 'right' | 'bottom' | 'left'>;
  testID?: string;
}

/**
 * Container component for screens
 * Provides consistent screen layout with proper safe area handling
 */
const Container: React.FC<ContainerProps> = ({
  children,
  style,
  useSafeArea = true,
  statusBarColor = colors.background.default,
  statusBarStyle = 'dark-content',
  backgroundColor = colors.background.default,
  edges = ['top', 'right', 'bottom', 'left'],
  testID,
}) => {
  // Base styles for the container
  const containerStyle: ViewStyle = {
    flex: 1,
    backgroundColor,
  };

  // Render with or without SafeAreaView
  if (useSafeArea) {
    return (
      <>
        <StatusBar
          backgroundColor={statusBarColor}
          barStyle={statusBarStyle}
          translucent
        />
        <SafeAreaView style={[containerStyle, style]} testID={testID}>
          {children}
        </SafeAreaView>
      </>
    );
  }

  return (
    <>
      <StatusBar
        backgroundColor={statusBarColor}
        barStyle={statusBarStyle}
        translucent
      />
      <View style={[containerStyle, style]} testID={testID}>
        {children}
      </View>
    </>
  );
};

export default Container;