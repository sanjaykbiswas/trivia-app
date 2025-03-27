import React, { useState } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { FormInput } from '../../components/form';
import { BackButton } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';

type ForgotPasswordScreenProps = StackScreenProps<RootStackParamList, 'ForgotPassword'>;

const ForgotPasswordScreen: React.FC<ForgotPasswordScreenProps> = ({ navigation, route }) => {
  const [email, setEmail] = useState(route.params?.email || '');
  const [loading, setLoading] = useState(false);
  const [sentEmail, setSentEmail] = useState(false);
  
  const { resetPassword } = useAuth();
  
  const handleResetPassword = async () => {
    if (!email) {
      Alert.alert('Error', 'Please enter your email address');
      return;
    }
    
    try {
      setLoading(true);
      const { error } = await resetPassword(email);
      
      if (error) {
        Alert.alert('Error', error.message);
      } else {
        setSentEmail(true);
      }
    } catch (error) {
      Alert.alert('Error', 'An unexpected error occurred');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleBack = () => {
    navigation.goBack();
  };
  
  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <BackButton onPress={handleBack} />
      
      <View style={styles.container}>
        <View style={styles.contentContainer}>
          <Typography variant="heading2" style={styles.title}>
            {sentEmail ? 'Check Your Email' : 'Reset Password'}
          </Typography>
          
          {sentEmail ? (
            <Typography variant="bodyMedium" style={styles.message}>
              We've sent password reset instructions to {email}. Please check your email inbox.
            </Typography>
          ) : (
            <>
              <Typography variant="bodyMedium" style={styles.message}>
                Enter your email address and we'll send you a link to reset your password.
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
                  title="Send Reset Link"
                  onPress={handleResetPassword}
                  variant="contained"
                  size="large"
                  loading={loading}
                  disabled={loading}
                  fullWidth
                  style={styles.resetButton}
                />
              </View>
            </>
          )}
        </View>
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
  },
  contentContainer: {
    paddingHorizontal: spacing.page,
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
  resetButton: {
    marginTop: spacing.md,
  },
});

export default ForgotPasswordScreen;