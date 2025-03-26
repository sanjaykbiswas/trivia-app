import React, { useRef, useEffect } from 'react';
import { View, StyleSheet, TextInput } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { 
  Container, 
  Typography, 
  Button,
  Modal 
} from '../../components/common';
import { SelectionOption, PageTitle } from '../../components/layout';
import { Header } from '../../components/navigation';
import { FormInput } from '../../components/form';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useKeyboardManager } from '../../utils/keyboard';
import { useModal } from '../../hooks/useModal';
import { useRoomCode } from '../../hooks/useRoomCode';

type MultiplayerScreenProps = StackScreenProps<RootStackParamList, 'Multiplayer'>;

/**
 * MultiplayerScreen component
 * Allows users to host or join a multiplayer game session
 */
const MultiplayerScreen: React.FC<MultiplayerScreenProps> = ({ navigation }) => {
  const { roomCode, displayValue, setRoomCode, isValidRoomCode, resetRoomCode } = useRoomCode();
  const { isVisible, showModal, hideModal } = useModal();
  const { dismissKeyboard } = useKeyboardManager();
  const inputRef = useRef<TextInput>(null);

  // Focus input when modal becomes visible
  useEffect(() => {
    if (isVisible && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
    }
  }, [isVisible]);

  const handleBackPress = () => {
    // If modal is visible, dismiss it; otherwise go back
    if (isVisible) {
      handleCloseModal();
      return;
    }
    
    // Dismiss keyboard if visible before navigating back
    dismissKeyboard();
    navigation.goBack();
  };

  const handleHostGame = () => {
    // Handle host game logic
    console.log('Host Game pressed');
    navigation.navigate('GameSetup');
  };

  const handleJoinGame = () => {
    // Handle join game with room code
    if (isValidRoomCode) {
      console.log(`Join Game with code: ${roomCode}`);
      // Dismiss modal
      handleCloseModal();
      // Navigate to game lobby
      // navigation.navigate('GameLobby', { roomCode });
    }
  };

  const handleCloseModal = () => {
    // Dismiss keyboard first, then hide the modal to prevent visual jump
    dismissKeyboard();
    
    // Use a small timeout to ensure keyboard dismissal is processed before modal animation
    setTimeout(() => {
      hideModal();
      
      // Reset the input state after the modal is closed
      setTimeout(() => {
        resetRoomCode();
      }, 100);
    }, 50);
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        <Header 
          showBackButton={true} 
          onBackPress={handleBackPress} 
        />

        <View style={styles.contentContainer}>
          {/* Page Title */}
          <PageTitle title="Multiplayer" />

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
            onPress={showModal}
            testID="join-game-option"
            style={styles.gameOption}
          />
        </View>

        {/* Join Game Modal */}
        <Modal
          visible={isVisible}
          onClose={handleCloseModal}
        >
          <Typography variant="heading4" style={styles.modalTitle}>
            Ask your host for a game code
          </Typography>
          
          {/* Room code input */}
          <FormInput
            ref={inputRef}
            value={displayValue}
            onChangeText={setRoomCode}
            autoCapitalize="none"
            maxLength={7}
            keyboardType="number-pad"
            autoFocus={true}
            testID="room-code-input"
            placeholder="Enter 6 digit code"
          />
          
          {/* Join Game Button inside modal */}
          <Button
            title="Join Game"
            onPress={handleJoinGame}
            variant="contained"
            size="large"
            fullWidth
            disabled={!isValidRoomCode}
            testID="join-button"
            style={styles.joinButton}
          />
        </Modal>
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    flex: 1,
    padding: spacing.page,
  },
  gameOption: {
    marginBottom: spacing.md,
  },
  modalTitle: {
    marginBottom: spacing.md,
    textAlign: 'left',
  },
  joinButton: {
    marginTop: spacing.sm, 
  },
});

export default MultiplayerScreen;