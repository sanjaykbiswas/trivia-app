import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { FormInput } from '../../components/form';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';

type SignInScreenProps = StackScreenProps<RootStackParamList, 'SignIn'>;

const SignInScreen: React.FC<SignInScreenProps> = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { signIn } = useAuth();
  
  const handleSignIn = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password');
      return;
    }
    
    try {
      setLoading(true);
      const { error } = await signIn(email, password);
      
      if (error) {
        Alert.alert('Sign In Error', error.message);
      } else {
        // Successful login will trigger the auth state change
        // and navigate automatically via the auth state provider
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
  
  const handleForgotPassword = () => {
    navigation.navigate('ForgotPassword');
  };
  
  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        <View style={styles.contentContainer}>
          <Typography variant="heading1" style={styles.title}>
            Sign In
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
            
            <FormInput
              value={password}
              onChangeText={setPassword}
              placeholder="Password"
              secureTextEntry
              testID="password-input"
            />
            
            <TouchableOpacity
              onPress={handleForgotPassword}
              style={styles.forgotPasswordContainer}
            >
              <Typography
                variant="bodySmall"
                color={colors.primary.main}
                style={styles.forgotPasswordText}
              >
                Forgot Password?
              </Typography>
            </TouchableOpacity>
            
            <Button
              title="Sign In"
              onPress={handleSignIn}
              variant="contained"
              size="large"
              loading={loading}
              disabled={loading}
              fullWidth
              style={styles.signInButton}
            />
          </View>
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
    paddingHorizontal: spacing.page,
  },
  title: {
    marginBottom: spacing.xl,
  },
  formContainer: {
    width: '100%',
  },
  forgotPasswordContainer: {
    alignItems: 'flex-end',
    marginBottom: spacing.md,
  },
  forgotPasswordText: {
    fontWeight: '500',
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