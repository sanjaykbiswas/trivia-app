import React from 'react';
import { View, StyleSheet, TouchableOpacity, Text } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';
import Svg, { Path } from 'react-native-svg';

interface ShareableCodeProps {
  code: string;
  onShare: () => void;
  label?: string;
  style?: any;
  testID?: string;
}

/**
 * ShareableCode component
 * Displays a code with a share button that allows users to share the code
 * Formats 6-digit codes with a hyphen between the 3rd and 4th digits (e.g., 123-456)
 */
const ShareableCode: React.FC<ShareableCodeProps> = ({
  code,
  onShare,
  label = 'Game Code:',
  style,
  testID,
}) => {
  // Format the code if it's 6 digits
  const formattedCode = () => {
    if (code.length === 6) {
      return `${code.substring(0, 3)}-${code.substring(3)}`;
    }
    return code;
  };

  return (
    <TouchableOpacity 
      style={[styles.container, style]}
      onPress={onShare}
      activeOpacity={0.7}
      testID={testID}
    >
      <View style={styles.linkDisplay}>
        <Typography variant="bodyMedium" numberOfLines={1} style={styles.linkText}>
          {label} <Text style={styles.codeText}>{formattedCode()}</Text>
        </Typography>
      </View>
      <View style={styles.copyButtonContainer}>
        <Svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
          <Path d="M16 6l-4-4-4 4" />
          <Path d="M12 2v13" />
        </Svg>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    backgroundColor: colors.background.light,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.gray[200],
    height: 48, // Match the default height of large buttons
    width: '100%',
    flexDirection: 'row',
  },
  linkDisplay: {
    flex: 1,
    justifyContent: 'center',
    height: '100%',
    alignItems: 'center',
  },
  linkText: {
    color: colors.text.primary,
    fontSize: 16,
    textAlign: 'center',
  },
  codeText: {
    fontWeight: 'bold',
    color: colors.text.primary,
    letterSpacing: 1,
  },
  copyButtonContainer: {
    position: 'absolute',
    right: 0,
    top: 0,
    backgroundColor: colors.background.default,
    padding: spacing.md,
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    borderTopRightRadius: 12,
    borderBottomRightRadius: 12,
    zIndex: 1, // Ensure icon is above other elements
  },
});

export default ShareableCode;