import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Container, Typography } from '../../components';
import { BottomTray } from '../../components/layout';
import { colors, spacing } from '../../theme';

interface OnboardingScreenProps {
  onGetStarted: () => void;
  onSignIn: () => void;
}

/**
 * OnboardingScreen component
 * Displays the app introduction and initial call-to-actions
 */
const OnboardingScreen: React.FC<OnboardingScreenProps> = ({
  onGetStarted,
  onSignIn,
}) => {
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
          title="Endless trivia.  No repeats." // Will be split into two lines in the BottomTray component
          primaryButtonText="Start Playing"
          primaryButtonAction={onGetStarted}
          secondaryText="Already have an account? Sign In"
          secondaryAction={onSignIn}
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
    paddingTop: spacing.xl, // Add extra padding at the top for the larger title
  },
});

export default OnboardingScreen;