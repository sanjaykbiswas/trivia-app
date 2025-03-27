// frontend/triviamobileapp/src/screens/auth/SignUpScreen.tsx
import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Alert, Keyboard, TouchableWithoutFeedback } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { FormInput } from '../../components/form';
import { Header } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';

type SignUpScreenProps = StackScreenProps<RootStackParamList, 'SignUp'>;

const SignUpScreen: React.FC<SignUpScreenProps> = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { signUp } = useAuth();
  
  const handleBackPress = () => {
    navigation.goBack();
  };
  
  const handleSignUp = async () => {
    if (!email) {
      Alert.alert('Error', 'Please enter your email address');
      return;
    }
    
    try {
      setLoading(true);
      const { error } = await signUp(email);
      
      if (error) {
        Alert.alert('Sign Up Error', error.message);
      } else {
        Alert.alert(
          'Confirmation Link Sent',
          'We\'ve sent a confirmation link to your email. Please check your inbox and follow the instructions to complete your registration.',
          [
            {
              text: 'OK',
              onPress: () => navigation.navigate('SignIn'),
            },
          ]
        );
      }
    } catch (error) {
      Alert.alert('Error', 'An unexpected error occurred');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSignIn = () => {
    navigation.navigate('SignIn');
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
              Sign Up
            </Typography>
            
            <Typography variant="bodyMedium" style={styles.message}>
              Enter your email and we'll send you a confirmation link to complete your registration. No password required!
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
                title="Sign Up"
                onPress={handleSignUp}
                variant="contained"
                size="large"
                loading={loading}
                disabled={loading}
                fullWidth
                style={styles.signUpButton}
              />
            </View>
          </View>
          
          <View style={styles.footer}>
            <TouchableOpacity onPress={handleSignIn}>
              <Typography variant="bodyMedium" style={styles.signInText}>
                Already have an account? <Typography
                  variant="bodyMedium"
                  color={colors.primary.main}
                  style={styles.signInLink}
                >
                  Sign In
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
    marginBottom: spacing.md,
  },
  message: {
    marginBottom: spacing.xl,
  },
  formContainer: {
    width: '100%',
  },
  signUpButton: {
    marginTop: spacing.md,
  },
  footer: {
    paddingVertical: spacing.xl,
    alignItems: 'center',
  },
  signInText: {
    textAlign: 'center',
  },
  signInLink: {
    fontWeight: '600',
  },
});

export default SignUpScreen;