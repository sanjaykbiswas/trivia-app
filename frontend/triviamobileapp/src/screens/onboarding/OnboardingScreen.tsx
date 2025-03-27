import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Text } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography } from '../../components/common';
import { BottomTray } from '../../components/layout';
import { SignInModal } from '../../components/auth';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type OnboardingScreenProps = StackScreenProps<RootStackParamList, 'Onboarding'>;

/**
 * OnboardingScreen component
 * Displays the app introduction with animated typing effect
 */
const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ navigation }) => {
  // Modals state
  const [signInModalVisible, setSignInModalVisible] = useState(false);
  const [signUpModalVisible, setSignUpModalVisible] = useState(false);
  
  // Animation state
  const [typedText, setTypedText] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);
  
  // Animation for the initial title fade-in
  const fadeAnim = useState(new Animated.Value(0))[0];
  const translateYAnim = useState(new Animated.Value(20))[0];
  
  // Animation configuration constants
  const TYPING_SPEED = 100;          // Time between typing each character
  const PHRASE_DISPLAY_TIME = 1500;  // Time to display completed phrase
  const DELETION_SPEED = 50;         // Time between deleting each character
  
  // Phrases to cycle through - easy to add or remove items
  const PHRASES = [
    "game nights",
    "daily fixes",
    "competitive spirits",
    "rainy days",
    "tickling your brain",
    "bathroom breaks",
    "dinners with friends"
  ];

  // Animation controller reference
  const animationRef = useRef({
    phrases: PHRASES,
    currentPhraseIndex: 0,
    currentText: '',
    isTyping: true,
    isRunning: false,
    timerId: null as NodeJS.Timeout | null,
    
    getCurrentPhrase() {
      return this.phrases[this.currentPhraseIndex];
    },
    
    start(updateTextFn: (text: string) => void) {
      if (this.isRunning) return;
      this.isRunning = true;
      this.step(updateTextFn);
    },
    
    stop() {
      this.isRunning = false;
      if (this.timerId) {
        clearTimeout(this.timerId);
        this.timerId = null;
      }
    },
    
    step(updateTextFn: (text: string) => void) {
      if (!this.isRunning) return;
      
      const currentPhrase = this.getCurrentPhrase();
      
      // Typing phase
      if (this.isTyping) {
        if (this.currentText.length < currentPhrase.length) {
          // Add next character
          this.currentText = currentPhrase.substring(0, this.currentText.length + 1);
          updateTextFn(this.currentText);
          this.timerId = setTimeout(() => this.step(updateTextFn), TYPING_SPEED);
        } else {
          // Full phrase typed - pause before deleting
          this.timerId = setTimeout(() => {
            this.isTyping = false;
            this.step(updateTextFn);
          }, PHRASE_DISPLAY_TIME);
        }
      } 
      // Deletion phase
      else {
        if (this.currentText.length > 0) {
          // Remove last character
          this.currentText = currentPhrase.substring(0, this.currentText.length - 1);
          updateTextFn(this.currentText);
          this.timerId = setTimeout(() => this.step(updateTextFn), DELETION_SPEED);
        } else {
          // Fully deleted - move to next phrase
          this.currentPhraseIndex = (this.currentPhraseIndex + 1) % this.phrases.length;
          this.isTyping = true;
          this.step(updateTextFn);
        }
      }
    }
  });

  // Cursor blinking effect
  useEffect(() => {
    const cursorInterval = setInterval(() => {
      setCursorVisible(prev => !prev);
    }, 500);
    
    return () => clearInterval(cursorInterval);
  }, []);
  
  // Initial fade-in and start typing animation
  useEffect(() => {
    // Fade in animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.timing(translateYAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start();
    
    // Start typing animation after a delay
    const startTimer = setTimeout(() => {
      animationRef.current.start(setTypedText);
    }, 1000);
    
    // Cleanup function
    return () => {
      clearTimeout(startTimer);
      animationRef.current.stop();
    };
  }, []);

  const handleGetStarted = () => {
    setSignUpModalVisible(true);
  };

  const handleSignIn = () => {
    setSignInModalVisible(true);
  };

  const handleCloseSignInModal = () => {
    setSignInModalVisible(false);
  };

  const handleCloseSignUpModal = () => {
    setSignUpModalVisible(false);
  };

  const handleContinueWithEmail = (isSignUp = false) => {
    navigation.navigate('SignIn', { isSignUp });
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        <View style={styles.contentContainer}>
          {/* Centered title with animation */}
          <Animated.View 
            style={[
              styles.titleContainer,
              {
                opacity: fadeAnim,
                transform: [{ translateY: translateYAnim }]
              }
            ]}
          >
            <Typography variant="heading1" style={styles.titleText}>
              Trivia for
            </Typography>
            <View style={styles.typingContainer}>
              <Typography variant="heading1" style={[styles.titleText, styles.typingText]}>
                {typedText}
                <Text style={[styles.cursor, {opacity: cursorVisible ? 1 : 0}]}>|</Text>
              </Typography>
            </View>
          </Animated.View>
        </View>

        {/* Bottom tray with call-to-action buttons */}
        <BottomTray
          primaryButtonText="Start Playing"
          primaryButtonAction={handleGetStarted}
          secondaryText="Already have an account? Sign In"
          secondaryAction={handleSignIn}
          hideBorder={true}
          style={styles.bottomTray}
        />

        {/* Sign In Modal */}
        <SignInModal
          visible={signInModalVisible}
          onClose={handleCloseSignInModal}
          onContinueWithEmail={() => handleContinueWithEmail(false)}
          title="Sign In"
          isSignUp={false}
        />

        {/* Sign Up Modal */}
        <SignInModal
          visible={signUpModalVisible}
          onClose={handleCloseSignUpModal}
          onContinueWithEmail={() => handleContinueWithEmail(true)}
          title="Create an account"
          isSignUp={true}
        />
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'space-between',
  },
  contentContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing.page,
  },
  titleContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  titleText: {
    textAlign: 'center',
    fontWeight: 'bold',
    fontSize: 34,
    lineHeight: 44,
  },
  typingContainer: {
    minHeight: 44, // Ensures consistent height as phrases change
    justifyContent: 'center',
  },
  typingText: {
    color: colors.primary.main, // Makes the typing text stand out
  },
  cursor: {
    color: colors.primary.main,
    fontWeight: 'bold',
  },
  bottomTray: {
    paddingTop: spacing.xl,
  },
});

export default OnboardingScreen;