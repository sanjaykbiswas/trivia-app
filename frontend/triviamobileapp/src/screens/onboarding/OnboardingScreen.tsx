import React from 'react';
import { View, StyleSheet } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container } from '../../components/common';
import { BottomTray } from '../../components/layout';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type OnboardingScreenProps = StackScreenProps<RootStackParamList, 'Onboarding'>;

/**
 * OnboardingScreen component
 * Displays the app introduction and initial call-to-actions
 */
const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ navigation }) => {
  const handleGetStarted = () => {
    // Navigate to SignUp when implemented
    console.log('Get Started pressed');
    // Example: navigation.navigate('SignUp');
  };

  const handleSignIn = () => {
    // Navigate to SignIn when implemented
    console.log('Sign In pressed');
    // Example: navigation.navigate('SignIn');
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        <View style={styles.contentContainer}>
          {/* Main content area - now empty or could contain other elements */}
        </View>

        {/* Bottom tray with customized title */}
        <BottomTray
          title="Trivia for game nights with friends"
          primaryButtonText="Start Playing"
          primaryButtonAction={handleGetStarted}
          secondaryText="Already have an account? Sign In"
          secondaryAction={handleSignIn}
          hideBorder={true}
          style={styles.bottomTray}
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
  bottomTray: {
    paddingTop: spacing.xl,
  },
});

export default OnboardingScreen;