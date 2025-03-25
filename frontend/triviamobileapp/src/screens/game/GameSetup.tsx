// File: frontend/triviamobileapp/src/screens/game/GameSetup.tsx
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity, Share, Alert, Clipboard } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { PageTitle } from '../../components/layout';
import { Header } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import Svg, { Path } from 'react-native-svg';

type GameSetupScreenProps = StackScreenProps<RootStackParamList, 'GameSetup'>;

const GameSetupScreen: React.FC<GameSetupScreenProps> = ({ navigation }) => {
  // Generate a random room code (5 characters)
  const [roomCode] = useState(() => {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 5; i++) {
      result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
  });

  // We'll now just use the room code directly
  const [copySuccess, setCopySuccess] = useState(false);

  // Reset copy success message after 3 seconds
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (copySuccess) {
      timer = setTimeout(() => {
        setCopySuccess(false);
      }, 3000);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [copySuccess]);

  const handleBackPress = () => {
    navigation.goBack();
  };

  const handleShareRoomCode = async () => {
    try {
      await Share.share({
        message: `Join my trivia game with room code: ${roomCode}`
      });
    } catch (error) {
      console.error('Error sharing room code:', error);
    }
  };

  const handleStartGame = () => {
    console.log('Creating packs with AI');
    // TODO: Navigate to appropriate screen
  };

  const handleShareCode = async () => {
    try {
      await Share.share({
        message: `Join my trivia game with room code: ${roomCode}`
      });
      setCopySuccess(true);
    } catch (error) {
      console.error('Error sharing room code:', error);
    }
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
      backgroundColor={colors.background.default}
    >
      <ScrollView style={styles.scrollView}>
        <View style={styles.container}>
          <Header 
            showBackButton={true} 
            onBackPress={handleBackPress} 
          />

          <View style={styles.contentContainer}>
            <PageTitle title="Choose your pack" />

            <View style={styles.roomCodeSection}>
              <Typography variant="bodyMedium" style={styles.sectionLabel}>
                Room Code
              </Typography>
              <View style={styles.roomCodeContainer}>
                <Typography variant="heading2" style={styles.roomCode}>
                  {roomCode}
                </Typography>
                <TouchableOpacity 
                  style={styles.shareButton} 
                  onPress={handleShareRoomCode}
                >
                  <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <Path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                    <Path d="M16 6l-4-4-4 4" />
                    <Path d="M12 2v13" />
                  </Svg>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>

      <View style={styles.bottomButtons}>
        <Button
          title="Create Packs With AI"
          onPress={handleStartGame}
          variant="contained"
          size="large"
          fullWidth
          style={styles.startButton}
        />
        
        {/* Shareable Code Component */}
        <View style={styles.shareableLinkContainer}>
          <View style={styles.linkDisplay}>
            <Typography variant="bodyMedium" numberOfLines={1} style={styles.linkText}>
              {roomCode}
            </Typography>
          </View>
          <TouchableOpacity 
            style={styles.copyButton}
            onPress={handleShareCode}
          >
            <View style={styles.shareButtonContent}>
              <Svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={styles.shareIcon}>
                <Path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                <Path d="M16 6l-4-4-4 4" />
                <Path d="M12 2v13" />
              </Svg>
              <Typography variant="buttonMedium" style={styles.copyButtonText}>
                Share code
              </Typography>
            </View>
          </TouchableOpacity>
        </View>
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  contentContainer: {
    flex: 1,
    padding: spacing.page,
  },
  roomCodeSection: {
    marginBottom: spacing.xl,
  },
  sectionLabel: {
    marginBottom: spacing.xs,
    textAlign: 'center',
    color: colors.text.primary,
  },
  roomCodeContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.gray[100],
    borderRadius: 12,
    padding: spacing.md,
  },
  roomCode: {
    flex: 1,
    textAlign: 'center',
    letterSpacing: 2,
    color: '#9370DB', // Purple color for room code
  },
  shareButton: {
    padding: spacing.sm,
    borderRadius: 50,
    backgroundColor: colors.background.default,
  },
  bottomButtons: {
    padding: spacing.page,
    paddingBottom: spacing.page,
  },
  startButton: {
    backgroundColor: colors.primary.main, // Black button to match onboarding screen
  },
  // New styles for the shareable link component
  shareableLinkContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
    backgroundColor: colors.background.light,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.gray[200],
    height: 48, // Match the default height of large buttons
  },
  linkDisplay: {
    flex: 1,
    paddingHorizontal: spacing.md,
    justifyContent: 'center',
    height: '100%',
  },
  linkText: {
    color: colors.text.primary,
    fontSize: 18,
    fontWeight: '500',
    letterSpacing: 1,
  },
  copyButton: {
    backgroundColor: colors.background.default,
    paddingHorizontal: spacing.md,
    borderRadius: 8,
    marginRight: spacing.xs,
    height: '80%',
    justifyContent: 'center',
  },
  copyButtonText: {
    color: colors.text.primary,
    marginLeft: 4,
  },
  shareButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  shareIcon: {
    marginRight: 4,
  }
});

export default GameSetupScreen;