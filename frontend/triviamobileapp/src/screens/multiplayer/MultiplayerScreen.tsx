// frontend/triviamobileapp/src/screens/multiplayer/MultiplayerScreen.tsx
import React, { useState, useRef, useEffect } from 'react';
import { 
  View, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput, 
  Keyboard,
  Modal as RNModal,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Animated,
} from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { SelectionOption } from '../../components/layout';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useKeyboardManager } from '../../utils/keyboard';

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
  
  // Use our enhanced keyboard manager
  const { isKeyboardVisible, keyboardHeight, dismissKeyboard } = useKeyboardManager();
  
  // Animation value for the floating button
  const buttonAnimatedValue = useRef(new Animated.Value(0)).current;

  // Animate the button when keyboard visibility changes
  useEffect(() => {
    Animated.timing(buttonAnimatedValue, {
      toValue: isKeyboardVisible ? 1 : 0,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [isKeyboardVisible, buttonAnimatedValue]);

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
      setIsJoinModalVisible(false);
    }, 50);
  };

  const handleFocus = () => {
    setIsFocused(true);
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  // Close the modal when tapping outside of it
  const handleModalBackgroundPress = () => {
    handleCloseModal();
  };

  // Button is enabled only when exactly 5 digits are entered
  const isJoinButtonDisabled = roomCode.trim().length !== 5;

  // Calculate the button's bottom position based on keyboard height
  const buttonBottomPosition = buttonAnimatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [-100, keyboardHeight > 0 ? keyboardHeight : 0]
  });

  // Calculate the button's opacity
  const buttonOpacity = buttonAnimatedValue.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0, 0.7, 1]
  });

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

        {/* Join Game Modal */}
        <RNModal
          visible={isJoinModalVisible}
          transparent={true}
          animationType="fade"
          onRequestClose={handleCloseModal}
        >
          <TouchableWithoutFeedback onPress={handleModalBackgroundPress}>
            <View style={styles.modalOverlay}>
              <KeyboardAvoidingView 
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
                style={styles.keyboardAvoidingView}
                keyboardVerticalOffset={Platform.OS === 'ios' ? 10 : 0}
              >
                <TouchableWithoutFeedback>
                  <View style={styles.modalContainer}>
                    <Typography variant="heading4" style={styles.modalTitle}>
                      Ask host for your code
                    </Typography>
                    
                    {/* Room code input */}
                    <TextInput
                      ref={inputRef}
                      style={[
                        styles.input,
                        isFocused && styles.inputFocused
                      ]}
                      value={roomCode}
                      onChangeText={(text) => {
                        // Only allow digits
                        const digitsOnly = text.replace(/[^0-9]/g, '');
                        setRoomCode(digitsOnly);
                      }}
                      autoCapitalize="none"
                      maxLength={5}
                      keyboardType="number-pad"
                      onFocus={handleFocus}
                      onBlur={handleBlur}
                      autoFocus={true}
                      testID="room-code-input"
                      onSubmitEditing={isJoinButtonDisabled ? undefined : handleJoinGame}
                      returnKeyType="done"
                      placeholder="5 digit game code"
                      placeholderTextColor={colors.gray[400]}
                    />
                  </View>
                </TouchableWithoutFeedback>
              </KeyboardAvoidingView>

              {/* Animated Floating Join Game button that appears above keyboard */}
              <Animated.View 
                style={[
                  styles.floatingButtonContainer, 
                  { 
                    bottom: buttonBottomPosition,
                    opacity: buttonOpacity,
                  }
                ]}
                pointerEvents={isKeyboardVisible ? "auto" : "none"}
              >
                <Button
                  title="Join Game"
                  onPress={handleJoinGame}
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={isJoinButtonDisabled}
                  testID="floating-join-button"
                />
              </Animated.View>
            </View>
          </TouchableWithoutFeedback>
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
  keyboardAvoidingView: {
    flex: 1,
    width: '100%',
    justifyContent: 'center',
    alignItems: 'center',
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
    marginBottom: spacing.md,
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
  floatingButtonContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    padding: spacing.md,
    backgroundColor: colors.background.default,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    zIndex: 1000, // Ensure it appears in the foreground
    elevation: 30, // Higher elevation for Android
    shadowColor: colors.gray[900],
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
});

export default MultiplayerScreen;