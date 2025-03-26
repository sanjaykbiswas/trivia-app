import React from 'react';
import { View, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';

interface SectionHeaderProps {
  title: string;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/**
 * SectionHeader component
 * Header for content sections that displays a title
 */
const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  style,
  testID,
}) => {
  return (
    <View style={[styles.container, style]} testID={testID}>
      <Typography variant="heading5" style={styles.title}>
        {title}
      </Typography>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  title: {
    fontWeight: 'bold',
  },
});

export default SectionHeader;