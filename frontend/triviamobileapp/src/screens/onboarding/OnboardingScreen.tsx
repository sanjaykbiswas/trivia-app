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
          <Typography variant="heading2" align="center">
            Calorie tracking
          </Typography>
          <Typography variant="heading2" align="center">
            made easy
          </Typography>
        </View>

        {/* Bottom tray with actions - now with hideBorder set to true */}
        <BottomTray
          primaryButtonText="Get Started"
          primaryButtonAction={onGetStarted}
          secondaryText="Purchased on the web? Sign In"
          secondaryAction={onSignIn}
          hideBorder={true} // Add this line to hide the border
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
});

export default OnboardingScreen;