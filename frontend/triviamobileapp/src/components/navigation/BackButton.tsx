import React from 'react';
import { TouchableOpacity, View, StyleSheet } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';

interface BackButtonProps {
  onPress: () => void;
  style?: any;
}

const BackButton: React.FC<BackButtonProps> = ({ onPress, style }) => (
  <TouchableOpacity style={[styles.backButton, style]} onPress={onPress}>
    <View style={styles.backButtonCircle}>
      <Typography variant="bodyMedium">←</Typography>
    </View>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  backButton: {
    position: 'absolute',
    top: spacing.md,
    left: spacing.md,
    zIndex: 10,
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

export default BackButton;