import React, { useState, useRef, useEffect } from 'react';
import { 
  View, 
  StyleSheet, 
  TouchableOpacity, 
  TextInput, 
  Keyboard, 
  Animated, 
  Dimensions,
} from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { SelectionOption, SlidingTray } from '../../components/layout';
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
  const [isJoinTrayVisible, setIsJoinTrayVisible] = useState(false);
  const inputRef = useRef<TextInput>(null);
  const { isKeyboardVisible, keyboardHeight } = useKeyboard();
  
  // Animation value for content opacity when tray is visible
  const contentOpacity = useRef(new Animated.Value(1)).current;
  
  // Screen dimensions for responsive calculations
  const { height: SCREEN_HEIGHT } = Dimensions.get('window');

  // Animate content opacity when tray visibility changes
  useEffect(() => {
    Animated.timing(contentOpacity, {
      toValue: isJoinTrayVisible ? 0.3 : 1,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, [isJoinTrayVisible, contentOpacity]);

  const handleBackPress = () => {
    // If tray is visible, dismiss it; otherwise go back
    if (isJoinTrayVisible) {
      setIsJoinTrayVisible(false);
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
    // Show the join tray and focus the input
    setIsJoinTrayVisible(true);
    
    // Short delay to ensure the input is focused after the tray appears
    setTimeout(() => {
      inputRef.current?.focus();
    }, 300);
  };

  const handleJoinGame = () => {
    // Handle join game with room code
    if (roomCode.trim()) {
      console.log(`Join Game with code: ${roomCode}`);
      // Dismiss keyboard and tray
      Keyboard.dismiss();
      setIsJoinTrayVisible(false);
      // Navigate to game lobby
      // navigation.navigate('GameLobby', { roomCode });
    }
  };

  const handleDismissTray = () => {
    setIsJoinTrayVisible(false);
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

        {/* Main Content - Animated to fade when tray is active */}
        <Animated.View 
          style={[
            styles.contentContainer,
            { opacity: contentOpacity }
          ]}
        >
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
        </Animated.View>

        {/* Sliding Join Tray */}
        <SlidingTray
          isVisible={isJoinTrayVisible}
          onDismiss={handleDismissTray}
          height={isKeyboardVisible ? keyboardHeight + 180 : '40%'}
        >
          <View style={styles.trayContent}>
            <Typography variant="heading3" style={styles.trayTitle}>
              Join Game
            </Typography>
            
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
        </SlidingTray>
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
  trayContent: {
    flex: 1,
    width: '100%',
  },
  trayTitle: {
    marginBottom: spacing.md,
    textAlign: 'center',
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