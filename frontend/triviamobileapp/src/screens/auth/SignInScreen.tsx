// frontend/triviamobileapp/src/screens/auth/SignInScreen.tsx
import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Alert, Keyboard, TouchableWithoutFeedback } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { FormInput } from '../../components/form';
import { Header } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';

type SignInScreenProps = StackScreenProps<RootStackParamList, 'SignIn'>;

const SignInScreen: React.FC<SignInScreenProps> = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  
  const { signIn } = useAuth();
  
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
      const { error } = await signIn(email);
      
      if (error) {
        Alert.alert('Sign In Error', error.message);
      } else {
        setMagicLinkSent(true);
        Alert.alert(
          'Magic Link Sent',
          'We\'ve sent a sign-in link to your email. Please check your inbox and follow the instructions to sign in.',
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
    navigation.navigate('SignUp');
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
              {magicLinkSent ? 'Check Your Email' : 'Sign In'}
            </Typography>
            
            {magicLinkSent ? (
              <Typography variant="bodyMedium" style={styles.message}>
                We've sent a sign-in link to {email}. Please check your email and follow the instructions to sign in.
              </Typography>
            ) : (
              <>
                <Typography variant="bodyMedium" style={styles.message}>
                  Enter your email and we'll send you a magic link to sign in. No password required!
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
                    title="Send Magic Link"
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
          </View>
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