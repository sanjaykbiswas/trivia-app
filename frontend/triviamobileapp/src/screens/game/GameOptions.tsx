import React, { useState } from 'react';
import { View, StyleSheet, Share } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { BottomActions, PageTitle } from '../../components/layout';
import { Header } from '../../components/navigation';
import { ShareableCode, OptionSelector } from '../../components/game';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type GameOptionsScreenProps = StackScreenProps<RootStackParamList, 'GameOptions'>;

const GameOptionsScreen: React.FC<GameOptionsScreenProps> = ({ navigation, route }) => {
  // Pack details from route params or defaults
  const packTitle = route.params?.packTitle || 'Geography Expert';
  
  // Game options state
  const [questionsPerGame, setQuestionsPerGame] = useState(1); // 0-based index (5, 10, 15, 20)
  const [questionTimer, setQuestionTimer] = useState(2); // 0-based index (15s, 30s, 45s, 60s)
  
  // Generate a random 6-digit room code
  const [roomCode] = useState(() => {
    const min = 100000; // Smallest 6-digit number
    const max = 999999; // Largest 6-digit number
    return Math.floor(min + Math.random() * (max - min + 1)).toString();
  });

  const handleBackPress = () => {
    navigation.goBack();
  };

  const handleStartGame = () => {
    console.log('Starting the party!');
    // Get selected values from the indices
    const questionCounts = [5, 10, 15, 20];
    const timerOptions = [15, 30, 45, 60];
    
    const selectedQuestionCount = questionCounts[questionsPerGame];
    const selectedTimer = timerOptions[questionTimer];
    
    console.log(`Questions: ${selectedQuestionCount}, Timer: ${selectedTimer}s`);
    
    // Navigate to question screen with options
    navigation.navigate('QuestionScreen', {
      categoryId: route.params?.categoryId, // Pass the category ID
      packTitle,
      questionCount: selectedQuestionCount,
      timerSeconds: selectedTimer,
      roomCode
    });
  };

  const handleShareCode = async () => {
    try {
      const formattedCode = `${roomCode.substring(0, 3)}-${roomCode.substring(3)}`;
      await Share.share({
        message: `Join my trivia game with room code: ${formattedCode}`
      });
    } catch (error) {
      console.error('Error sharing room code:', error);
    }
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
        
        {/* Page Title */}
        <PageTitle title={packTitle} style={styles.pageTitle} />
        
        {/* Content */}
        <View style={styles.contentContainer}>
          {/* Options section */}
          <View style={styles.optionsSection}>
            <OptionSelector
              title="Questions Per Game"
              options={["5", "10", "15", "20"]}
              selectedIndex={questionsPerGame}
              onSelect={setQuestionsPerGame}
              testID="questions-selector"
            />
            
            <OptionSelector
              title="Question Timer"
              options={["15s", "30s", "45s", "60s"]}
              selectedIndex={questionTimer}
              onSelect={setQuestionTimer}
              testID="timer-selector"
            />
          </View>
        </View>
        
        {/* Footer */}
        <BottomActions style={styles.footer}>
          <Button
            title="Start the Party!"
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
  },
  pageTitle: {
    paddingTop: spacing.xs,
  },
  contentContainer: {
    flex: 1,
    paddingHorizontal: spacing.page,
  },
  optionsSection: {
    marginTop: spacing.xl,
  },
  footer: {
    backgroundColor: colors.background.default,
  },
  startButton: {
    backgroundColor: colors.primary.main,
    marginBottom: spacing.md,
  },
  shareableCode: {
    marginTop: 0,
  },
});

export default GameOptionsScreen;