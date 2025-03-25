// File: frontend/triviamobileapp/src/components/layout/PageTitle.tsx
import React from 'react';
import { View, StyleSheet, ViewStyle, StyleProp } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';

interface PageTitleProps {
  title: string;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/**
 * PageTitle component
 * Provides a consistent main title for screens
 */
const PageTitle: React.FC<PageTitleProps> = ({
  title,
  style,
  testID,
}) => {
  return (
    <View style={[styles.container, style]} testID={testID}>
      <Typography variant="heading1" style={styles.title}>
        {title}
      </Typography>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.xl,
    paddingHorizontal: spacing.sm,
  },
  title: {
    textAlign: 'left',
  },
});

export default PageTitle;