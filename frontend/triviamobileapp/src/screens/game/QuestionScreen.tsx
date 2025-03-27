import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, TouchableOpacity, Animated, BackHandler, Alert } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { QuestionTimer } from '../../components/game/QuestionTimer';
import { AnswerOption } from '../../components/game/AnswerOption';
import { FeedbackPanel } from '../../components/game/FeedbackPanel';

// Mock data for questions
const mockQuestions = [
  {
    id: 'q1',
    question: 'What is the capital city of Australia?',
    options: ['Sydney', 'Canberra', 'Melbourne', 'Perth'],
    correctAnswer: 1, // Index of correct answer (Canberra)
  },
  {
    id: 'q2',
    question: 'Which planet is known as the Red Planet?',
    options: ['Venus', 'Mars', 'Jupiter', 'Saturn'],
    correctAnswer: 1, // Mars
  },
  {
    id: 'q3',
    question: 'What is the largest ocean on Earth?',
    options: ['Atlantic Ocean', 'Indian Ocean', 'Arctic Ocean', 'Pacific Ocean'],
    correctAnswer: 3, // Pacific Ocean
  },
  {
    id: 'q4',
    question: 'Which country is known as the Land of the Rising Sun?',
    options: ['China', 'Thailand', 'Japan', 'South Korea'],
    correctAnswer: 2, // Japan
  },
  {
    id: 'q5',
    question: 'What is the smallest prime number?',
    options: ['0', '1', '2', '3'],
    correctAnswer: 2, // 2
  }
];

type QuestionScreenProps = StackScreenProps<RootStackParamList, 'QuestionScreen'>;

const QuestionScreen: React.FC<QuestionScreenProps> = ({ navigation, route }) => {
  // Extract parameters from route or use defaults
  const packTitle = route.params?.packTitle || 'Trivia Pack';
  const questionCount = route.params?.questionCount || 5;
  const timerSeconds = route.params?.timerSeconds || 30;

  // State management
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswerIndex, setSelectedAnswerIndex] = useState<number | null>(null);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [isCorrectAnswer, setIsCorrectAnswer] = useState(false);
  const [isTimerActive, setIsTimerActive] = useState(true);
  const [score, setScore] = useState(0);
  const [timeLeft, setTimeLeft] = useState(timerSeconds);

  // Questions state - in a real app, this would come from an API
  const [questions, setQuestions] = useState(mockQuestions);

  // Current question
  const currentQuestion = questions[currentQuestionIndex];

  // Animation for feedback panel
  const feedbackAnimation = useRef(new Animated.Value(100)).current;

  // Handle back button press
  useEffect(() => {
    const backHandler = BackHandler.addEventListener('hardwareBackPress', () => {
      // If in the middle of a question, show confirmation dialog
      Alert.alert(
        'Quit Game',
        'Are you sure you want to quit this game?',
        [
          { text: 'Cancel', style: 'cancel', onPress: () => {} },
          { text: 'Quit', style: 'destructive', onPress: () => navigation.goBack() }
        ]
      );
      return true; // Prevent default back behavior
    });

    return () => backHandler.remove();
  }, [navigation]);

  // Timer effect
  useEffect(() => {
    let timerId: NodeJS.Timeout | undefined;

    if (isTimerActive && timeLeft > 0) {
      timerId = setTimeout(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
    } else if (timeLeft === 0 && isTimerActive) {
      // Auto-submit when time runs out
      handleSubmitAnswer();
    }

    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, [timeLeft, isTimerActive]);

  // Handle option selection
  const handleSelectOption = (index: number) => {
    if (isAnswerSubmitted) return;
    setSelectedAnswerIndex(index);
  };

  // Submit answer
  const handleSubmitAnswer = () => {
    if (isAnswerSubmitted) {
      // If already submitted, proceed to next question
      handleNextQuestion();
      return;
    }

    setIsTimerActive(false);
    setIsAnswerSubmitted(true);

    // Check if answer is correct
    const isCorrect = selectedAnswerIndex === currentQuestion.correctAnswer;
    setIsCorrectAnswer(isCorrect);

    // Update score if correct
    if (isCorrect) {
      setScore(prevScore => prevScore + 1);
    }

    // Show feedback panel
    Animated.timing(feedbackAnimation, {
      toValue: 0,
      duration: 300,
      useNativeDriver: true,
    }).start();
  };

  // Proceed to next question
  const handleNextQuestion = () => {
    // Hide feedback panel
    Animated.timing(feedbackAnimation, {
      toValue: 100,
      duration: 200,
      useNativeDriver: true,
    }).start(() => {
      if (currentQuestionIndex < questions.length - 1) {
        // Move to next question
        setCurrentQuestionIndex(prevIndex => prevIndex + 1);
        setSelectedAnswerIndex(null);
        setIsAnswerSubmitted(false);
        setTimeLeft(timerSeconds);
        setIsTimerActive(true);
      } else {
        // End of quiz - navigate to results screen
        // In a real app, you would navigate to a results screen
        navigation.goBack();
        Alert.alert('Game Over', `Your score: ${score}/${questions.length}`);
      }
    });
  };

  // Close/exit the game
  const handleCloseGame = () => {
    Alert.alert(
      'Quit Game',
      'Are you sure you want to quit this game?',
      [
        { text: 'Cancel', style: 'cancel', onPress: () => {} },
        { text: 'Quit', style: 'destructive', onPress: () => navigation.goBack() }
      ]
    );
  };

  // Get button text based on state
  const getButtonText = () => {
    if (isAnswerSubmitted) {
      if (currentQuestionIndex < questions.length - 1) {
        return 'Next Question';
      } else {
        return 'Finish Quiz';
      }
    }
    return 'Submit Answer';
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        {/* Header with timer and title */}
        <View style={styles.header}>
          <QuestionTimer
            timeLeft={timeLeft}
            totalTime={timerSeconds}
            active={isTimerActive}
          />
          <Typography variant="bodyMedium" style={styles.packTitle}>
            {packTitle}
          </Typography>
          <TouchableOpacity style={styles.closeButton} onPress={handleCloseGame}>
            <Typography variant="bodyMedium">✕</Typography>
          </TouchableOpacity>
        </View>

        {/* Question content area */}
        <View style={styles.questionContainer}>
          {/* Question progress */}
          <Typography 
            variant="bodyMedium" 
            color={colors.text.secondary}
            style={styles.progress}
          >
            Question {currentQuestionIndex + 1} of {Math.min(questionCount, questions.length)}
          </Typography>

          {/* Question text */}
          <Typography variant="heading2" style={styles.question}>
            {currentQuestion.question}
          </Typography>

          {/* Answer options */}
          <View style={styles.optionsContainer}>
            {currentQuestion.options.map((option, index) => (
              <AnswerOption
                key={index}
                letter={String.fromCharCode(65 + index)} // A, B, C, D
                text={option}
                isSelected={selectedAnswerIndex === index}
                isCorrect={isAnswerSubmitted && index === currentQuestion.correctAnswer}
                isIncorrect={isAnswerSubmitted && selectedAnswerIndex === index && index !== currentQuestion.correctAnswer}
                onPress={() => handleSelectOption(index)}
                disabled={isAnswerSubmitted}
              />
            ))}
          </View>
        </View>

        {/* Bottom action button */}
        <View style={styles.bottomActions}>
          <Button
            title={getButtonText()}
            onPress={handleSubmitAnswer}
            disabled={selectedAnswerIndex === null && !isAnswerSubmitted}
            variant="contained"
            size="large"
            fullWidth
          />
        </View>

        {/* Feedback panel (conditionally rendered) */}
        {isAnswerSubmitted && (
          <FeedbackPanel
            isCorrect={isCorrectAnswer}
            correctAnswer={currentQuestion.options[currentQuestion.correctAnswer]}
            animationValue={feedbackAnimation}
            onNextPress={handleNextQuestion}
            isLastQuestion={currentQuestionIndex === questions.length - 1}
          />
        )}
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    position: 'relative',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
    position: 'relative',
  },
  packTitle: {
    fontWeight: '500',
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.background.light,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'absolute',
    right: spacing.md,
  },
  questionContainer: {
    flex: 1,
    padding: spacing.md,
  },
  progress: {
    fontSize: 16,
    fontWeight: '500',
    paddingTop: spacing.sm,
    paddingBottom: spacing.xs,
  },
  question: {
    marginBottom: spacing.xl,
    lineHeight: 40,
  },
  optionsContainer: {
    gap: spacing.md,
  },
  bottomActions: {
    padding: spacing.page,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
  },
});

export default QuestionScreen;