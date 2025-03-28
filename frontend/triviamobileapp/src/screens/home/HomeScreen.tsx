// frontend/triviamobileapp/src/screens/home/HomeScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, TouchableOpacity, Alert, Text } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { SelectionOption } from '../../components/layout';
import { BottomNavBar } from '../../components/navigation';
import { DisplayNameModal } from '../../components/auth';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';
import UserService from '../../services/UserService';
import AuthService from '../../services/AuthService';

type HomeScreenProps = StackScreenProps<RootStackParamList, 'Home'>;
type NavItemType = 'home' | 'packs' | 'create' | 'friends' | 'profile';

const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const [activeNavItem, setActiveNavItem] = useState<NavItemType>('home');
  const [displayNameModalVisible, setDisplayNameModalVisible] = useState(false);
  const [actionType, setActionType] = useState<'solo' | 'party'>('solo');
  
  // Get auth context to check user state
  const { user } = useAuth();

  const handleNavItemPress = (itemId: NavItemType) => {
    setActiveNavItem(itemId);
    // In a real app, this would navigate to different screens
    console.log(`Navigate to ${itemId}`);
  };

  // Handle Solo option press
  const handleSoloPress = async () => {
    setActionType('solo');
    
    // Check if user is authenticated or has a temporary user account
    const isTemporary = await UserService.isTemporaryUser();
    const hasUser = !!user || isTemporary;
    
    if (hasUser) {
      console.log('User exists, starting solo game');
      // Continue with solo game flow
      navigateToGameSetup();
    } else {
      console.log('No user exists, showing display name modal');
      // Show display name modal
      setDisplayNameModalVisible(true);
    }
  };

  // Handle Party option press
  const handlePartyPress = async () => {
    setActionType('party');
    
    // Check if user is authenticated or has a temporary user account
    const isTemporary = await UserService.isTemporaryUser();
    const hasUser = !!user || isTemporary;
    
    if (hasUser) {
      console.log('User exists, starting multiplayer game');
      // Continue with party game flow
      navigateToMultiplayer();
    } else {
      console.log('No user exists, showing display name modal');
      // Show display name modal
      setDisplayNameModalVisible(true);
    }
  };

  // Handle successful display name creation
  const handleDisplayNameSuccess = () => {
    // Close the modal
    setDisplayNameModalVisible(false);
    
    // Based on the action type, navigate to the appropriate screen
    if (actionType === 'solo') {
      navigateToGameSetup();
    } else {
      navigateToMultiplayer();
    }
  };
  
  // Navigation helpers
  const navigateToGameSetup = () => {
    navigation.navigate('GameSetup');
  };
  
  const navigateToMultiplayer = () => {
    navigation.navigate('Multiplayer');
  };

  const handleBackPress = () => {
    // Temporary back button for testing
    navigation.goBack();
  };

  // New debug function to clear temporary user data
  const handleClearUserData = async () => {
    try {
      // Clear temporary user from AsyncStorage
      await AuthService.clearTempUser();
      console.log('Temporary user data cleared successfully');
      
      // Show confirmation alert
      Alert.alert(
        'Debug Action',
        'Temporary user data has been cleared. The app will now ask for your nickname again.',
        [{ text: 'OK' }]
      );
    } catch (error) {
      console.error('Error clearing temporary user data:', error);
      Alert.alert('Error', 'Failed to clear user data. See console for details.');
    }
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

        {/* Debug Button - Added for temporary user debugging */}
        <TouchableOpacity 
          style={styles.debugButton} 
          onPress={handleClearUserData}
          activeOpacity={0.7}
        >
          <Text style={styles.debugButtonText}>Clear User Data</Text>
        </TouchableOpacity>

        <View style={styles.contentContainer}>
          {/* This area is empty in the design */}
          <View style={styles.emptySpace} />
        </View>

        {/* Pills Tray */}
        <View style={styles.pillsTray}>
          <SelectionOption
            title="Solo"
            subtitle="Play competitively or in relaxed mode"
            emoji="🧠"
            onPress={handleSoloPress}
            testID="solo-option"
          />
          <SelectionOption
            title="Party"
            subtitle="Play games with friends"
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
        
        {/* Display Name Modal */}
        <DisplayNameModal
          visible={displayNameModalVisible}
          onClose={() => setDisplayNameModalVisible(false)}
          onSuccess={handleDisplayNameSuccess}
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
  debugButton: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    backgroundColor: '#FF6B6B', // Bright red to make it obvious
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    zIndex: 10,
  },
  debugButtonText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
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