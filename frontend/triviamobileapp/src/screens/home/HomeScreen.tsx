import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography } from '../../components/common';
import { SelectionOption } from '../../components/layout';
import { BottomNavBar } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type HomeScreenProps = StackScreenProps<RootStackParamList, 'Home'>;
type NavItemType = 'home' | 'packs' | 'create' | 'friends' | 'profile';

const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const [activeNavItem, setActiveNavItem] = useState<NavItemType>('home');

  const handleNavItemPress = (itemId: NavItemType) => {
    setActiveNavItem(itemId);
    // In a real app, this would navigate to different screens
    console.log(`Navigate to ${itemId}`);
  };

  const handleSoloPress = () => {
    // Handle Solo option press
    console.log('Solo pressed');
  };

  const handlePartyPress = () => {
    // Handle Party option press
    console.log('Party pressed');
  };

  const handleBackPress = () => {
    // Temporary back button for testing
    navigation.goBack();
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        {/* Temporary back button for testing */}
        <TouchableOpacity style={styles.backButton} onPress={handleBackPress}>
          <View style={styles.backButtonCircle}>
            <Typography variant="bodyMedium">←</Typography>
          </View>
        </TouchableOpacity>

        <View style={styles.contentContainer}>
          {/* This area is empty in the design */}
          <View style={styles.emptySpace} />
        </View>

        {/* Pills Tray */}
        <View style={styles.pillsTray}>
          <SelectionOption
            title="Solo"
            subtitle="Daily challenges and competitive play"
            emoji="🧠"
            onPress={handleSoloPress}
            testID="solo-option"
          />
          <SelectionOption
            title="Party"
            subtitle="Host or join a game with friends"
            emoji="🎉"
            onPress={handlePartyPress}
            testID="party-option"
          />
        </View>

        {/* Bottom Navigation Bar */}
        <BottomNavBar
          activeItemId={activeNavItem}
          onItemPress={handleNavItemPress}
        />
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
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
  contentContainer: {
    flex: 1,
    padding: spacing.page,
  },
  emptySpace: {
    flex: 1,
  },
  pillsTray: {
    padding: spacing.page,
    paddingBottom: spacing.xs,
    backgroundColor: colors.background.default,
  },
});

export default HomeScreen;