import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container } from '../../components/common';
import { BottomTray } from '../../components/layout';
import { SignInModal } from '../../components/auth';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type OnboardingScreenProps = StackScreenProps<RootStackParamList, 'Onboarding'>;

/**
 * OnboardingScreen component
 * Displays the app introduction and initial call-to-actions
 */
const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ navigation }) => {
  const [signInModalVisible, setSignInModalVisible] = useState(false);

  const handleGetStarted = () => {
    // Navigate to Home screen (which will be accessible without login now)
    navigation.navigate('Home');
  };

  const handleSignIn = () => {
    // Show sign-in modal
    setSignInModalVisible(true);
  };

  const handleCloseModal = () => {
    setSignInModalVisible(false);
  };

  const handleContinueWithEmail = () => {
    // Close modal first
    setSignInModalVisible(false);
    
    // Navigate to SignIn screen for email login
    navigation.navigate('SignIn');
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
          title="Trivia tailored for friends"
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
          onClose={handleCloseModal}
          onContinueWithEmail={handleContinueWithEmail}
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