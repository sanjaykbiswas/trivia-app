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
 * Card displaying a trivia pack with title and optional author
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
      <View style={[styles.imageContainer, styles[`${variant}Background`]]} />
      <View style={styles.contentContainer}>
        <Typography variant="bodySmall" style={styles.title} numberOfLines={2}>
          {title}
        </Typography>
      </View>
      
      {author && (
        <View style={styles.authorStrip}>
          <Typography variant="caption" color="white">
            By {author}
          </Typography>
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    width: 130,
    backgroundColor: colors.background.default,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: colors.gray[900],
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  imageContainer: {
    height: 130,
    width: '100%',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
  },
  contentContainer: {
    padding: 12,
    minHeight: 50,
    justifyContent: 'center',
  },
  title: {
    fontWeight: '600',
    textAlign: 'center',
  },
  authorStrip: {
    backgroundColor: '#6b4afb',
    paddingVertical: 8,
    alignItems: 'center',
  },
  myPackBackground: {
    backgroundColor: '#ff7373',
  },
  freshPackBackground: {
    backgroundColor: '#ffa64d',
  },
  popularPackBackground: {
    backgroundColor: '#6b4afb',
  },
  freePackBackground: {
    backgroundColor: '#33cc5a',
  },
  shopPackBackground: {
    backgroundColor: '#ff9500',
  },
});

export default PackCard;