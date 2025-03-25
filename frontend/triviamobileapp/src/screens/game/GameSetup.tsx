import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, TextInput, TouchableOpacity, Share } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { BackButton } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import Svg, { Path, Circle, Rect } from 'react-native-svg';

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

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
      backgroundColor={colors.background.default}
    >
      <ScrollView style={styles.scrollView}>
        <View style={styles.container}>
          <BackButton onPress={handleBackPress} />

          <View style={styles.header}>
            <Typography variant="heading1" style={styles.title}>
              Choose your pack
            </Typography>
          </View>

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
    padding: spacing.page,
    paddingTop: spacing.xxl + spacing.md, // Extra padding for back button
  },
  header: {
    marginBottom: spacing.lg,
    alignItems: 'flex-start', // Left align the title
  },
  title: {
    marginTop: spacing.md,
    color: colors.text.primary,
    textAlign: 'left', // Ensure left alignment
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
});

export default GameSetupScreen;