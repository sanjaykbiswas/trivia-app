// frontend/triviamobileapp/src/screens/auth/SignInScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, StyleSheet, TouchableOpacity, Alert, Keyboard, TouchableWithoutFeedback } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { FormInput } from '../../components/form';
import { Header } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';
import { SignInModal } from '../../components/auth';

type SignInScreenProps = StackScreenProps<RootStackParamList, 'SignIn'>;

const SignInScreen: React.FC<SignInScreenProps> = ({ navigation, route }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  const [signUpModalVisible, setSignUpModalVisible] = useState(false);
  
  // Check if this is a sign-up flow from route params
  const isSignUp = route.params?.isSignUp === true;
  
  const { signIn, signUp } = useAuth();
  
  const handleBackPress = () => {
    navigation.goBack();
  };
  
  const handleSignIn = async () => {
    if (!email) {
      Alert.alert('Error', 'Please enter your email address');
      return;
    }
    
    try {
      setLoading(true);
      // Use signUp if we're in sign up flow, otherwise use signIn
      const { error } = isSignUp ? await signUp(email) : await signIn(email);
      
      if (error) {
        Alert.alert(isSignUp ? 'Sign Up Error' : 'Sign In Error', error.message);
      } else {
        setMagicLinkSent(true);
        Alert.alert(
          'Magic Link Sent',
          `We've sent a ${isSignUp ? 'sign-up' : 'sign-in'} link to your email. Please check your inbox and follow the instructions.`,
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      Alert.alert('Error', 'An unexpected error occurred');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSignUp = () => {
    // Instead of navigation, show the modal
    setSignUpModalVisible(true);
  };
  
  const handleContinueWithEmailSignUp = () => {
    setSignUpModalVisible(false);
    // Navigate to SignIn screen with isSignUp parameter
    navigation.navigate('SignIn', { isSignUp: true });
  };
  
  const dismissKeyboard = () => {
    Keyboard.dismiss();
  };
  
  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <TouchableWithoutFeedback onPress={dismissKeyboard}>
        <View style={styles.container}>
          <Header 
            showBackButton={true} 
            onBackPress={handleBackPress} 
          />
        
          <View style={styles.contentContainer}>
            <Typography variant="heading1" style={styles.title}>
              {magicLinkSent ? 'Check Your Email' : 'Enter your email'}
            </Typography>
            
            {magicLinkSent ? (
              <Typography variant="bodyMedium" style={styles.message}>
                We've sent a {isSignUp ? 'sign-up' : 'sign-in'} link to {email}. Please check your email and follow the instructions.
              </Typography>
            ) : (
              <>
                <Typography variant="bodyMedium" style={styles.message}>
                  {isSignUp 
                    ? 'We\'ll send you a link to create your account!'
                    : 'We\'ll send you a magic link to sign in!'}
                </Typography>
                
                <View style={styles.formContainer}>
                  <FormInput
                    value={email}
                    onChangeText={setEmail}
                    placeholder="Email"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    testID="email-input"
                  />
                  
                  <Button
                    title={isSignUp ? "Create Account" : "Send Magic Link"}
                    onPress={handleSignIn}
                    variant="contained"
                    size="large"
                    loading={loading}
                    disabled={loading}
                    fullWidth
                    style={styles.signInButton}
                  />
                </View>
              </>
            )}
          </View>
          
          <View style={styles.footer}>
            {!isSignUp ? (
              <TouchableOpacity onPress={handleSignUp}>
                <Typography variant="bodyMedium" style={styles.signUpText}>
                  Don't have an account? <Typography
                    variant="bodyMedium"
                    color={colors.primary.main}
                    style={styles.signUpLink}
                  >
                    Sign Up
                  </Typography>
                </Typography>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity onPress={() => navigation.navigate('SignIn', { isSignUp: false })}>
                <Typography variant="bodyMedium" style={styles.signUpText}>
                  Already have an account? <Typography
                    variant="bodyMedium"
                    color={colors.primary.main}
                    style={styles.signUpLink}
                  >
                    Sign In
                  </Typography>
                </Typography>
              </TouchableOpacity>
            )}
          </View>
          
          {/* Sign Up Modal */}
          <SignInModal
            visible={signUpModalVisible}
            onClose={() => setSignUpModalVisible(false)}
            onContinueWithEmail={handleContinueWithEmailSignUp}
            title="Create an account"
            isSignUp={true}
          />
        </View>
      </TouchableWithoutFeedback>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.page,
    paddingBottom: spacing.xl,
  },
  title: {
    marginBottom: spacing.xl,
  },
  message: {
    marginBottom: spacing.xl,
  },
  formContainer: {
    width: '100%',
  },
  signInButton: {
    marginTop: spacing.md,
  },
  footer: {
    paddingVertical: spacing.xl,
    alignItems: 'center',
  },
  signUpText: {
    textAlign: 'center',
  },
  signUpLink: {
    fontWeight: '600',
  },
});

export default SignInScreen;