import React, { useState, useRef, useEffect } from 'react';
import { 
  View, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput, 
  Keyboard, 
  Platform, 
  KeyboardAvoidingView,
  Dimensions
} from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { SelectionOption } from '../../components/layout';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useKeyboard } from '../../utils/keyboard';

type MultiplayerScreenProps = StackScreenProps<RootStackParamList, 'Multiplayer'>;

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

/**
 * MultiplayerScreen component
 * Allows users to host or join a multiplayer game session
 */
const MultiplayerScreen: React.FC<MultiplayerScreenProps> = ({ navigation }) => {
  const [roomCode, setRoomCode] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<TextInput>(null);
  const { isKeyboardVisible, keyboardHeight } = useKeyboard();
  
  // Calculate appropriate bottom padding for the content container
  const getContentPadding = () => {
    if (isKeyboardVisible) {
      // When keyboard is visible, ensure enough space for the input and button
      // The additional padding ensures the elements are fully visible above the keyboard
      return keyboardHeight + (Platform.OS === 'ios' ? 80 : 100);
    }
    return 0;
  };

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

        {/* Main Content - Scrollable if needed */}
        <View 
          style={[
            styles.contentContainer,
            { paddingBottom: getContentPadding() }
          ]}
        >
          {/* Left-aligned title */}
          <Typography variant="heading1" style={styles.title}>
            Multiplayer
          </Typography>

          <View style={styles.spacer} />

          {/* Host Game option */}
          <SelectionOption
            title="Host"
            subtitle="Create a new game room"
            emoji="👑"
            onPress={handleHostGame}
            testID="host-game-option"
            style={styles.hostGameOption}
          />
          
          {/* Divider with text */}
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

          {/* Input and Button Container - Always visible at bottom */}
          <View style={styles.inputContainer}>
            {/* Room code input */}
            <TextInput
              ref={inputRef}
              style={[
                styles.input,
                isFocused && styles.inputFocused
              ]}
              placeholder="Room Code"
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
        </View>
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
  spacer: {
    flex: 1,
  },
  hostGameOption: {
    marginBottom: spacing.md,
  },
  dividerContainer: {
    width: '100%',
    paddingVertical: spacing.sm,
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
  inputContainer: {
    width: '100%',
    backgroundColor: colors.background.default,
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
    marginBottom: spacing.lg,
  },
});

export default MultiplayerScreen;