import React, { useState, useRef, useEffect } from 'react';
import { 
  View, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput, 
  Keyboard,
  Modal as RNModal,
} from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { SelectionOption } from '../../components/layout';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type MultiplayerScreenProps = StackScreenProps<RootStackParamList, 'Multiplayer'>;

/**
 * MultiplayerScreen component
 * Allows users to host or join a multiplayer game session
 */
const MultiplayerScreen: React.FC<MultiplayerScreenProps> = ({ navigation }) => {
  const [roomCode, setRoomCode] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isJoinModalVisible, setIsJoinModalVisible] = useState(false);
  const inputRef = useRef<TextInput>(null);
  
  // Focus input when modal becomes visible
  useEffect(() => {
    if (isJoinModalVisible && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
    }
  }, [isJoinModalVisible]);

  const handleBackPress = () => {
    // If modal is visible, dismiss it; otherwise go back
    if (isJoinModalVisible) {
      setIsJoinModalVisible(false);
      Keyboard.dismiss();
      return;
    }
    
    // Dismiss keyboard if visible before navigating back
    Keyboard.dismiss();
    navigation.goBack();
  };

  const handleHostGame = () => {
    // Handle host game logic
    console.log('Host Game pressed');
    // Navigate to game setup or lobby creation screen
    // navigation.navigate('GameSetup');
  };

  const handleJoinPillPress = () => {
    // Show the join modal
    setIsJoinModalVisible(true);
  };

  const handleJoinGame = () => {
    // Handle join game with room code
    if (roomCode.trim()) {
      console.log(`Join Game with code: ${roomCode}`);
      // Dismiss keyboard and modal
      Keyboard.dismiss();
      setIsJoinModalVisible(false);
      // Navigate to game lobby
      // navigation.navigate('GameLobby', { roomCode });
    }
  };

  const handleCloseModal = () => {
    setIsJoinModalVisible(false);
    Keyboard.dismiss();
  };

  const handleFocus = () => {
    setIsFocused(true);
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  const isJoinButtonDisabled = !roomCode.trim();

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        {/* Static back button - always visible */}
        <TouchableOpacity style={styles.backButton} onPress={handleBackPress}>
          <View style={styles.backButtonCircle}>
            <Typography variant="bodyMedium">←</Typography>
          </View>
        </TouchableOpacity>

        <View style={styles.contentContainer}>
          {/* Left-aligned title */}
          <Typography variant="heading1" style={styles.title}>
            Multiplayer
          </Typography>

          {/* Host Game option */}
          <SelectionOption
            title="Host"
            subtitle="Create a new game room"
            emoji="👑"
            onPress={handleHostGame}
            testID="host-game-option"
            style={styles.gameOption}
          />

          {/* Join Game option */}
          <SelectionOption
            title="Join"
            subtitle="Enter a game room code"
            emoji="🎮"
            onPress={handleJoinPillPress}
            testID="join-game-option"
            style={styles.gameOption}
          />
        </View>

        {/* Join Game Modal - Using React Native's built-in Modal */}
        <RNModal
          visible={isJoinModalVisible}
          transparent={true}
          animationType="fade"
          onRequestClose={handleCloseModal}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContainer}>
              <Typography variant="heading4" style={styles.modalTitle}>
                Enter 5-digit game code
              </Typography>
              
              {/* Room code input */}
              <TextInput
                ref={inputRef}
                style={[
                  styles.input,
                  isFocused && styles.inputFocused
                ]}
                value={roomCode}
                onChangeText={setRoomCode}
                autoCapitalize="none"
                maxLength={5}
                keyboardType="number-pad"
                onFocus={handleFocus}
                onBlur={handleBlur}
                returnKeyType="done"
                onSubmitEditing={handleJoinGame}
                autoFocus={true}
                testID="room-code-input"
              />
              
              {/* Join Game Button */}
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
        </RNModal>
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
  gameOption: {
    marginBottom: spacing.md,
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContainer: {
    width: '85%',
    backgroundColor: colors.background.default,
    borderRadius: 20,
    padding: spacing.lg,
    shadowColor: colors.gray[900],
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 10,
  },
  modalTitle: {
    marginBottom: spacing.md,
    textAlign: 'left',
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
    marginBottom: spacing.lg,
    textAlign: 'left',
    paddingLeft: spacing.md + 4, // Add extra left padding for text
  },
  inputFocused: {
    borderColor: colors.primary.main,
    backgroundColor: colors.background.default,
    shadowColor: colors.primary.main,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  joinButton: {
    marginTop: spacing.sm,
  },
});

export default MultiplayerScreen;