import React, { ReactNode } from 'react';
import { View, StyleSheet, ViewStyle, StyleProp, TouchableOpacity } from 'react-native';
import { colors, spacing } from '../../theme';
import { Typography } from '../../components/common';

interface HeaderProps {
  showBackButton?: boolean;
  onBackPress?: () => void;
  rightContent?: ReactNode;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/**
 * Header component
 * Provides a consistent header across screens with optional back button
 */
const Header: React.FC<HeaderProps> = ({
  showBackButton = true,
  onBackPress,
  rightContent,
  style,
  testID,
}) => {
  return (
    <View style={[styles.container, style]} testID={testID}>
      <View style={styles.leftContainer}>
        {showBackButton && onBackPress && (
          <TouchableOpacity style={styles.backButton} onPress={onBackPress}>
            <View style={styles.backButtonCircle}>
              <Typography variant="bodyMedium">←</Typography>
            </View>
          </TouchableOpacity>
        )}
      </View>
      
      {rightContent && (
        <View style={styles.rightContainer}>
          {rightContent}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.page,
    height: 60, // Fixed height for consistency
  },
  leftContainer: {
    flex: 1,
    alignItems: 'flex-start',
  },
  rightContainer: {
    flex: 1,
    alignItems: 'flex-end',
  },
  backButton: {
    // Removed extra padding to ensure consistent alignment
  },
  backButtonCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.background.light,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default Header;