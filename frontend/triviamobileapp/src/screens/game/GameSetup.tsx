import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Share } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { PageTitle, BottomActions } from '../../components/layout';
import { Header } from '../../components/navigation';
import { ShareableCode } from '../../components/game';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type GameSetupScreenProps = StackScreenProps<RootStackParamList, 'GameSetup'>;

/**
 * GameSetupScreen component
 * Allows users to configure game settings before starting a game
 */
const GameSetupScreen: React.FC<GameSetupScreenProps> = ({ navigation }) => {
  // Generate a random 6-digit room code
  const [roomCode] = useState(() => {
    // Generate a random 6-digit number as a string
    const min = 100000; // Smallest 6-digit number
    const max = 999999; // Largest 6-digit number
    return Math.floor(min + Math.random() * (max - min + 1)).toString();
  });

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

  const handleStartGame = () => {
    console.log('Creating packs with AI');
    // TODO: Navigate to appropriate screen
  };

  // Format the room code for sharing (including the hyphen)
  const formattedRoomCode = () => {
    if (roomCode.length === 6) {
      return `${roomCode.substring(0, 3)}-${roomCode.substring(3)}`;
    }
    return roomCode;
  };

  const handleShareCode = async () => {
    try {
      await Share.share({
        message: `Join my trivia game with room code: ${formattedRoomCode()}`
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
      <View style={styles.container}>
        <Header 
          showBackButton={true} 
          onBackPress={handleBackPress} 
        />

        <ScrollView style={styles.scrollView}>
          <View style={styles.contentContainer}>
            <PageTitle title="Choose your pack" />
            
            {/* Pack selection content will go here */}
            <View style={styles.placeholderContent}>
              <Typography variant="bodyMedium" color={colors.text.secondary}>
                Pack selection options will be displayed here
              </Typography>
            </View>
          </View>
        </ScrollView>

        <BottomActions>
          <Button
            title="Create Packs With AI"
            onPress={handleStartGame}
            variant="contained"
            size="large"
            fullWidth
            style={styles.startButton}
          />
          
          <ShareableCode 
            code={roomCode}
            onShare={handleShareCode}
            style={styles.shareableCode}
            testID="game-code-share"
          />
        </BottomActions>
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    padding: spacing.page,
    paddingBottom: spacing.xxl, // Add extra padding at the bottom for scrolling
  },
  placeholderContent: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    backgroundColor: colors.gray[100],
    borderRadius: 12,
    height: 200,
  },
  startButton: {
    backgroundColor: colors.primary.main, // Black button to match onboarding screen
    marginBottom: spacing.md,
  },
  shareableCode: {
    marginTop: spacing.xs,
  },
});

export default GameSetupScreen;