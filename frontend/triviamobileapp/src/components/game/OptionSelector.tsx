import React from 'react';
import { View, StyleSheet, TouchableOpacity, StyleProp, ViewStyle } from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';

interface OptionSelectorProps {
  title: string;
  options: string[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}

/**
 * OptionSelector component
 * A selector with multiple options for game settings
 */
const OptionSelector: React.FC<OptionSelectorProps> = ({
  title,
  options,
  selectedIndex,
  onSelect,
  style,
  testID,
}) => {
  return (
    <View style={[styles.container, style]} testID={testID}>
      <Typography variant="heading5" style={styles.title}>
        {title}
      </Typography>
      
      <View style={styles.optionsContainer}>
        {options.map((option, index) => (
          <TouchableOpacity
            key={index}
            style={[
              styles.optionButton,
              selectedIndex === index && styles.selectedOption
            ]}
            onPress={() => onSelect(index)}
            activeOpacity={0.8}
            testID={`${testID}-option-${index}`}
          >
            <Typography 
              variant="bodyMedium" 
              color={selectedIndex === index ? colors.primary.contrastText : colors.text.primary}
            >
              {option}
            </Typography>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.lg,
  },
  title: {
    marginBottom: spacing.sm,
    fontWeight: 'bold',
  },
  optionsContainer: {
    flexDirection: 'row',
    backgroundColor: colors.gray[200],
    borderRadius: 100,
    padding: 4,
  },
  optionButton: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 100,
  },
  selectedOption: {
    backgroundColor: colors.primary.main,
  },
});

export default OptionSelector;