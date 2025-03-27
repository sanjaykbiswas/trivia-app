import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { FormInput } from '../../components/form';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';

type SignUpScreenProps = StackScreenProps<RootStackParamList, 'SignUp'>;

const SignUpScreen: React.FC<SignUpScreenProps> = ({ navigation }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { signUp } = useAuth();
  
  const handleSignUp = async () => {
    if (!email || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }
    
    try {
      setLoading(true);
      const { error } = await signUp(email, password);
      
      if (error) {
        Alert.alert('Sign Up Error', error.message);
      } else {
        Alert.alert(
          'Account Created',
          'Please check your email for a confirmation link, then sign in.',
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
  
  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        <View style={styles.contentContainer}>
          <Typography variant="heading1" style={styles.title}>
            Sign Up
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
            
            <FormInput
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="Confirm Password"
              secureTextEntry
              testID="confirm-password-input"
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