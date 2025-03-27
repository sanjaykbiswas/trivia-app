import React from 'react';
import { 
  View, 
  Modal, 
  StyleSheet, 
  TouchableOpacity, 
  Text, 
  TouchableWithoutFeedback,
  Pressable
} from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../../navigation/types';

interface SignInModalProps {
  visible: boolean;
  onClose: () => void;
  onContinueWithEmail: () => void;
}

const SignInModal: React.FC<SignInModalProps> = ({ 
  visible, 
  onClose, 
  onContinueWithEmail 
}) => {
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();

  // Placeholder functions for social sign-in
  const handleAppleSignIn = () => {
    // This would be implemented with @invertase/react-native-apple-authentication
    console.log('Apple Sign In pressed');
    // For now, just close the modal after "signing in"
    onClose();
  };

  const handleGoogleSignIn = () => {
    // This would be implemented with @react-native-google-signin/google-signin
    console.log('Google Sign In pressed');
    // For now, just close the modal after "signing in"
    onClose();
  };

  const handleEmailContinue = () => {
    onContinueWithEmail();
  };

  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.modalOverlay}>
          <TouchableWithoutFeedback onPress={e => e.stopPropagation()}>
            <View style={styles.modalContent}>
              <View style={styles.header}>
                <Typography variant="heading2" style={styles.title}>
                  Sign In
                </Typography>
                <Pressable onPress={onClose} style={styles.closeButton}>
                  <Text style={styles.closeButtonText}>✕</Text>
                </Pressable>
              </View>

              {/* Apple Sign In Button */}
              <TouchableOpacity 
                style={[styles.button, styles.appleButton]}
                onPress={handleAppleSignIn}
              >
                <View style={styles.buttonIconContainer}>
                  <Text style={styles.appleIcon}>􀣺</Text>
                </View>
                <Text style={styles.appleButtonText}>Sign in with Apple</Text>
              </TouchableOpacity>

              {/* Google Sign In Button */}
              <TouchableOpacity 
                style={[styles.button, styles.googleButton]}
                onPress={handleGoogleSignIn}
              >
                <View style={styles.googleIconContainer}>
                  <Text style={styles.googleIcon}>G</Text>
                </View>
                <Text style={styles.googleButtonText}>Sign in with Google</Text>
              </TouchableOpacity>

              {/* Email Continue Button */}
              <TouchableOpacity 
                style={[styles.button, styles.emailButton]}
                onPress={handleEmailContinue}
              >
                <View style={styles.emailIconContainer}>
                  <Text style={styles.emailIcon}>✉️</Text>
                </View>
                <Text style={styles.emailButtonText}>Continue with email</Text>
              </TouchableOpacity>

              {/* Terms and Conditions */}
              <View style={styles.termsContainer}>
                <Text style={styles.termsText}>
                  By continuing you agree to Cal AI's{' '}
                  <Text style={styles.termsLink}>Terms and Conditions</Text> and{' '}
                  <Text style={styles.termsLink}>Privacy Policy</Text>
                </Text>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: spacing.lg,
    paddingBottom: 34, // Extra padding for bottom safe area
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    marginBottom: spacing.xl,
  },
  title: {
    textAlign: 'center',
  },
  closeButton: {
    position: 'absolute',
    right: 0,
    top: 0,
    padding: spacing.sm,
  },
  closeButtonText: {
    fontSize: 18,
    color: colors.text.secondary,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
    borderRadius: 100,
    marginBottom: spacing.md,
    position: 'relative',
  },
  buttonIconContainer: {
    position: 'absolute',
    left: spacing.md,
  },
  appleButton: {
    backgroundColor: 'black',
  },
  appleIcon: {
    color: 'white',
    fontSize: 24,
  },
  appleButtonText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 16,
  },
  googleButton: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: colors.gray[300],
  },
  googleIconContainer: {
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  googleIcon: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'black',
  },
  googleButtonText: {
    color: 'black',
    fontWeight: '600',
    fontSize: 16,
  },
  emailButton: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: colors.gray[300],
  },
  emailIconContainer: {
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emailIcon: {
    fontSize: 16,
  },
  emailButtonText: {
    color: 'black',
    fontWeight: '600',
    fontSize: 16,
  },
  termsContainer: {
    marginTop: spacing.md,
  },
  termsText: {
    color: colors.text.secondary,
    fontSize: 14,
    textAlign: 'center',
  },
  termsLink: {
    color: colors.text.primary,
    textDecorationLine: 'underline',
  },
});

export default SignInModal;