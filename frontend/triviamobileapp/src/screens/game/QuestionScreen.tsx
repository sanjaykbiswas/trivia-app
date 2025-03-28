import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, TouchableOpacity, Animated, BackHandler, Alert, ActivityIndicator } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { QuestionTimer } from '../../components/game/QuestionTimer';
import { AnswerOption } from '../../components/game/AnswerOption';
import { FeedbackPanel } from '../../components/game/FeedbackPanel';
import QuestionService, { Question } from '../../services/QuestionService';

type QuestionScreenProps = StackScreenProps<RootStackParamList, 'QuestionScreen'>;

interface QuestionItem extends Question {
  options: string[];
  correctAnswer: number; // Index of correct answer
}

const QuestionScreen: React.FC<QuestionScreenProps> = ({ navigation, route }) => {
  // Extract parameters from route or use defaults
  const categoryId = route.params?.categoryId;
  const packTitle = route.params?.packTitle || 'Trivia Pack';
  const questionCount = route.params?.questionCount || 5;
  const timerSeconds = route.params?.timerSeconds || 30;

  // State management
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswerIndex, setSelectedAnswerIndex] = useState<number | null>(null);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [isCorrectAnswer, setIsCorrectAnswer] = useState(false);
  const [isTimerActive, setIsTimerActive] = useState(false); // Start when questions are ready
  const [score, setScore] = useState(0);
  const [timeLeft, setTimeLeft] = useState(timerSeconds);

  // Loading state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Questions state
  const [questions, setQuestions] = useState<QuestionItem[]>([]);

  // Current question
  const currentQuestion = questions[currentQuestionIndex];

  // Animation for feedback panel
  const feedbackAnimation = useRef(new Animated.Value(100)).current;

  // Load questions from the API when component mounts
  useEffect(() => {
    const loadQuestions = async () => {
      setLoading(true);
      setError(null);
      
      try {
        console.log(`Loading questions for category ${categoryId}, count: ${questionCount}`);
        
        let apiQuestions: Question[] = [];
        
        if (categoryId) {
          // Fetch questions for the specific category
          apiQuestions = await QuestionService.getQuestionsByCategory(categoryId, questionCount);
        } else {
          // Fetch general questions if no category ID provided
          apiQuestions = await QuestionService.getGameQuestions(undefined, questionCount);
        }
        
        console.log(`Loaded ${apiQuestions.length} questions`);
        
        if (apiQuestions.length === 0) {
          setError("No questions available. Please try a different category.");
          setLoading(false);
          return;
        }
        
        // Transform the API questions into our QuestionItem format
        const transformedQuestions: QuestionItem[] = apiQuestions.map(q => {
          // Create array with correct answer and incorrect answers
          const allOptions = [q.correct_answer, ...q.incorrect_answers];
          
          // Shuffle options (Fisher-Yates algorithm)
          for (let i = allOptions.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [allOptions[i], allOptions[j]] = [allOptions[j], allOptions[i]];
          }
          
          // Find the index of the correct answer in the shuffled array
          const correctAnswerIndex = allOptions.findIndex(option => option === q.correct_answer);
          
          return {
            ...q,
            options: allOptions,
            correctAnswer: correctAnswerIndex
          };
        });
        
        setQuestions(transformedQuestions);
      } catch (err) {
        console.error('Error loading questions:', err);
        setError("Failed to load questions. Please try again later.");
      } finally {
        setLoading(false);
        // Start the timer after questions are loaded
        setTimeLeft(timerSeconds);
        setIsTimerActive(true);
      }
    };
    
    loadQuestions();
  }, [categoryId, questionCount, timerSeconds]);

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
    const isCorrect = selectedAnswerIndex === currentQuestion?.correctAnswer;
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
        // End of quiz - display final results
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

        {/* Loading state */}
        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary.main} />
            <Typography variant="bodyMedium" style={styles.loadingText}>
              Loading questions...
            </Typography>
          </View>
        )}

        {/* Error state */}
        {error && !loading && (
          <View style={styles.errorContainer}>
            <Typography variant="bodyMedium" color={colors.error.main} style={styles.errorText}>
              {error}
            </Typography>
            <Button
              title="Go Back"
              onPress={() => navigation.goBack()}
              variant="outlined"
              size="medium"
            />
          </View>
        )}

        {/* Question content area - only show when questions are loaded and no error */}
        {!loading && !error && currentQuestion && (
          <View style={styles.questionContainer}>
            {/* Question progress */}
            <Typography 
              variant="bodyMedium" 
              color={colors.text.secondary}
              style={styles.progress}
            >
              Question {currentQuestionIndex + 1} of {questions.length}
            </Typography>

            {/* Question text */}
            <Typography variant="heading2" style={styles.question}>
              {currentQuestion.content}
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
        )}

        {/* Bottom action button - only show when questions are loaded and no error */}
        {!loading && !error && currentQuestion && (
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
        )}

        {/* Feedback panel (conditionally rendered) */}
        {isAnswerSubmitted && currentQuestion && (
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  loadingText: {
    marginTop: spacing.lg,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  errorText: {
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
});

export default QuestionScreen;