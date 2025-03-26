import React from 'react';
import { View, StyleSheet, TouchableOpacity, StyleProp, ViewStyle } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';

type CardVariant = 'myPack' | 'freshPack' | 'popularPack' | 'freePack' | 'shopPack';

interface PackCardProps {
  title: string;
  author?: string;
  variant?: CardVariant;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/**
 * PackCard component
 * Card displaying a trivia pack with title
 */
const PackCard: React.FC<PackCardProps> = ({
  title,
  author,
  variant = 'myPack',
  onPress,
  style,
  testID,
}) => {
  return (
    <TouchableOpacity
      style={[styles.card, style]}
      onPress={onPress}
      activeOpacity={0.8}
      testID={testID}
    >
      <View style={styles.contentContainer}>
        <Typography 
          variant="bodySmall" 
          style={styles.title} 
          numberOfLines={2}
          color={colors.text.primary}
        >
          {title}
        </Typography>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    width: 130,
    height: 130,
    backgroundColor: colors.gray[200], // Using a grey background for all packs
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: colors.gray[900],
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  contentContainer: {
    flex: 1,
    padding: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default PackCard;