import React, { useState, useRef } from 'react';
import { 
  View, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput, 
  Keyboard, 
  Platform, 
  KeyboardAvoidingView,
} from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { SelectionOption, BottomTray } from '../../components/layout';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useKeyboard } from '../../utils/keyboard';

type MultiplayerScreenProps = StackScreenProps<RootStackParamList, 'Multiplayer'>;

/**
 * MultiplayerScreen component
 * Allows users to host or join a multiplayer game session
 */
const MultiplayerScreen: React.FC<MultiplayerScreenProps> = ({ navigation }) => {
  const [roomCode, setRoomCode] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<TextInput>(null);
  const { isKeyboardVisible } = useKeyboard();
  
  const handleBackPress = () => {
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

  const handleJoinGame = () => {
    // Handle join game with room code
    if (roomCode.trim()) {
      console.log(`Join Game with code: ${roomCode}`);
      // Dismiss keyboard
      Keyboard.dismiss();
      // Navigate to game lobby
      // navigation.navigate('GameLobby', { roomCode });
    }
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
      <KeyboardAvoidingView 
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 64 : 0}
      >
        {/* Static back button - always visible */}
        <TouchableOpacity style={styles.backButton} onPress={handleBackPress}>
          <View style={styles.backButtonCircle}>
            <Typography variant="bodyMedium">←</Typography>
          </View>
        </TouchableOpacity>

        {/* Main Content */}
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
            onPress={() => inputRef.current?.focus()}
            testID="join-game-option"
            style={styles.gameOption}
          />
        </View>

        {/* Bottom Tray with Input and Join Button */}
        <BottomTray
          style={[
            styles.bottomTray,
            isKeyboardVisible && styles.keyboardVisibleTray
          ]}
        >
          <View style={styles.inputContainer}>
            {/* Room code input */}
            <TextInput
              ref={inputRef}
              style={[
                styles.input,
                isFocused && styles.inputFocused
              ]}
              placeholder="5 Digit Room Code"
              placeholderTextColor={colors.text.hint}
              value={roomCode}
              onChangeText={setRoomCode}
              autoCapitalize="characters"
              maxLength={6}
              keyboardType="number-pad"
              onFocus={handleFocus}
              onBlur={handleBlur}
              returnKeyType="done"
              onSubmitEditing={handleJoinGame}
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
        </BottomTray>
      </KeyboardAvoidingView>
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
  bottomTray: {
    paddingBottom: Platform.OS === 'ios' ? spacing.lg : spacing.md,
  },
  keyboardVisibleTray: {
    // When keyboard is visible, ensure tray sticks to the keyboard
    paddingBottom: 0,
  },
  inputContainer: {
    width: '100%',
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