import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, TextInput } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { SelectionOption, BottomTray } from '../../components/layout';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type MultiplayerScreenProps = StackScreenProps<RootStackParamList, 'Multiplayer'>;

/**
 * MultiplayerScreen component
 * Allows users to host or join a multiplayer game session
 */
const MultiplayerScreen: React.FC<MultiplayerScreenProps> = ({ navigation }) => {
  const [roomCode, setRoomCode] = useState('');

  const handleBackPress = () => {
    navigation.goBack();
  };

  const handleHostGame = () => {
    // Handle host game logic
    console.log('Host Game pressed');
    // Navigate to game setup or lobby creation screen
    // navigation.navigate('GameSetup');
  };

  const handleJoinGame = () => {
    // Handle join game with room code
    if (roomCode.trim()) {
      console.log(`Join Game with code: ${roomCode}`);
      // Navigate to game lobby
      // navigation.navigate('GameLobby', { roomCode });
    }
  };

  const isJoinButtonDisabled = !roomCode.trim();

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        {/* Back button */}
        <TouchableOpacity style={styles.backButton} onPress={handleBackPress}>
          <View style={styles.backButtonCircle}>
            <Typography variant="bodyMedium">←</Typography>
          </View>
        </TouchableOpacity>

        <View style={styles.contentContainer}>
          {/* Left-aligned title in-line with back button */}
          <Typography variant="heading1" style={styles.title}>
            Multiplayer
          </Typography>

          <View style={styles.spacer} />

          {/* Host Game option positioned at the bottom of main content */}
          <SelectionOption
            title="Host"
            subtitle="Create a new game room"
            emoji="👑"
            onPress={handleHostGame}
            testID="host-game-option"
            style={styles.hostGameOption}
          />
        </View>

        {/* Divider with text - positioned above the bottom tray */}
        <View style={styles.dividerContainer}>
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Typography 
              variant="bodySmall" 
              color={colors.text.secondary}
              style={styles.dividerText}
            >
              Or join with code
            </Typography>
            <View style={styles.dividerLine} />
          </View>
        </View>

        {/* Bottom Tray with Join Game functionality */}
        <View style={styles.bottomTrayContainer}>
          {/* Room code input */}
          <TextInput
            style={styles.input}
            placeholder="Enter Room Code"
            placeholderTextColor={colors.text.hint}
            value={roomCode}
            onChangeText={setRoomCode}
            autoCapitalize="characters"
            maxLength={6}
            testID="room-code-input"
          />
          
          {/* Use full width button instead of BottomTray for consistent width */}
          <Button
            title="Join Game"
            onPress={handleJoinGame}
            variant="contained"
            size="large"
            fullWidth
            disabled={isJoinButtonDisabled}
            style={styles.joinButton}
            testID="join-game-button"
          />
        </View>
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
    paddingTop: spacing.xxl + spacing.md, // Extra padding for back button
  },
  title: {
    marginBottom: spacing.xl,
    textAlign: 'left',
    marginLeft: spacing.sm, // Align with back button
  },
  spacer: {
    flex: 1,
  },
  hostGameOption: {
    marginBottom: spacing.sm,
  },
  dividerContainer: {
    paddingHorizontal: spacing.page,
    backgroundColor: colors.background.default,
  },
  divider: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.divider,
  },
  dividerText: {
    marginHorizontal: spacing.md,
  },
  bottomTrayContainer: {
    backgroundColor: colors.background.default,
    padding: spacing.page,
    paddingTop: 0,
    paddingBottom: spacing.xl,
  },
  input: {
    width: '100%',
    padding: spacing.md,
    borderRadius: 16,
    backgroundColor: colors.gray[100],
    borderWidth: 1,
    borderColor: colors.border,
    color: colors.text.primary,
    fontSize: 16,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  joinButton: {
    marginTop: spacing.sm,
    // Match the styling from OnboardingScreen's button
  },
});

export default MultiplayerScreen;