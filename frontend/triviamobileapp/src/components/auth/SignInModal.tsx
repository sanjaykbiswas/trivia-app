// frontend/triviamobileapp/src/components/auth/SignInModal.tsx
import React, { useRef, useEffect, useState } from 'react';
import { 
  View, 
  Modal,
  StyleSheet, 
  TouchableOpacity, 
  Text,
  TouchableWithoutFeedback,
  Pressable,
  Platform,
  Alert,
  Animated,
  ActivityIndicator
} from 'react-native';
import { Typography } from '../common';
import { colors, spacing } from '../../theme';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../../navigation/types';
import { useAuth } from '../../contexts/AuthContext';
import Svg, { Path } from 'react-native-svg';

interface SignInModalProps {
  visible: boolean;
  onClose: () => void;
  onContinueWithEmail: () => void;
  iconTextSpacing?: number; // Variable spacing between icon and text
  title?: string; // Add title prop
  isSignUp?: boolean; // Flag to indicate if this is for sign up
}

const SignInModal: React.FC<SignInModalProps> = ({ 
  visible, 
  onClose, 
  onContinueWithEmail,
  iconTextSpacing = 12, // Default spacing
  title = "Sign In", // Default title
  isSignUp = false // Default to sign in flow
}) => {
  const navigation = useNavigation<StackNavigationProp<RootStackParamList>>();
  const { signInWithApple, signInWithGoogle } = useAuth();
  
  // Loading states for buttons
  const [googleLoading, setGoogleLoading] = useState(false);
  const [appleLoading, setAppleLoading] = useState(false);
  
  // Animation for modal sliding up
  const slideAnimation = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      // Start the slide-up animation when modal becomes visible
      Animated.timing(slideAnimation, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    } else {
      // Slide down when closing
      Animated.timing(slideAnimation, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }
  }, [visible, slideAnimation]);
  
  // Calculate translateY based on animation value
  const translateY = slideAnimation.interpolate({
    inputRange: [0, 1],
    outputRange: [300, 0], // Start 300 pixels down, end at normal position
  });

  const handleAppleSignIn = async () => {
    if (Platform.OS !== 'ios') {
      Alert.alert('Error', 'Apple authentication is only available on iOS devices');
      return;
    }

    try {
      setAppleLoading(true);
      const { error } = await signInWithApple();
      
      if (error) {
        if (error.message !== 'Sign in was canceled') {
          Alert.alert('Sign In Error', error.message);
        }
      } else {
        // Sign in successful, close modal
        onClose();
      }
    } catch (error: any) {
      Alert.alert('Sign In Error', error.message || 'Failed to sign in with Apple');
      console.error(error);
    } finally {
      setAppleLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      setGoogleLoading(true);
      const { error } = await signInWithGoogle();
      
      if (error) {
        if (error.message !== 'Sign in was canceled') {
          // Format the error message nicely
          let errorMessage = error.message;
          if (error.details) {
            errorMessage += `\n\n${error.details}`;
          }
          Alert.alert('Sign In Error', errorMessage);
        }
      } else {
        // Sign in successful, close modal
        onClose();
      }
    } catch (error: any) {
      Alert.alert('Sign In Error', error.message || 'Failed to sign in with Google');
      console.error(error);
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleEmailContinue = () => {
    // Close the modal first
    onClose();
    
    // Use setTimeout to ensure modal is fully closed before navigation
    setTimeout(() => {
      // Then call the continuation handler that will navigate to SignInScreen
      onContinueWithEmail();
    }, 100);
  };

  return (
    <Modal
      animationType="fade" // Background changes instantly
      transparent={true}
      visible={visible}
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.modalOverlay}>
          <TouchableWithoutFeedback onPress={e => e.stopPropagation()}>
            <Animated.View 
              style={[
                styles.modalContent,
                { transform: [{ translateY }] }
              ]}
            >
              <View style={styles.header}>
                <Typography variant="heading2" style={styles.title}>
                  {title}
                </Typography>
                <Pressable onPress={onClose} style={styles.closeButton}>
                  <Text style={styles.closeButtonText}>✕</Text>
                </Pressable>
              </View>
              
              {/* Divider line */}
              <View style={styles.divider} />

              {/* Apple Sign In Button */}
              {Platform.OS === 'ios' && (
                <TouchableOpacity 
                  style={[styles.button, styles.appleButton]}
                  onPress={handleAppleSignIn}
                  disabled={appleLoading || googleLoading}
                >
                  <View style={[styles.buttonContent, {columnGap: iconTextSpacing}]}>
                    {appleLoading ? (
                      <ActivityIndicator size="small" color="white" />
                    ) : (
                      <Svg width={20} height={20} viewBox="0 0 24 24" fill="none">
                        <Path 
                          d="M17.543 12.084c-.03-2.751 2.251-4.088 2.354-4.155-1.287-1.884-3.287-2.141-3.987-2.163-1.677-.175-3.304 1.001-4.161 1.001-.878 0-2.201-.983-3.635-.955-1.843.027-3.57 1.093-4.521 2.745-1.954 3.39-.495 8.376 1.378 11.12.937 1.345 2.033 2.846 3.47 2.791 1.405-.059 1.93-.9 3.627-.9 1.678 0 2.168.9 3.633.864 1.507-.024 2.456-1.359 3.363-2.713 1.08-1.55 1.517-3.074 1.535-3.155-.035-.012-2.926-1.12-2.956-4.48zM14.955 3.65c.755-.944 1.27-2.232 1.127-3.54-1.092.049-2.456.757-3.242 1.683-.697.815-1.321 2.149-1.16 3.407 1.226.093 2.482-.627 3.275-1.55z" 
                          fill="white"
                        />
                      </Svg>
                    )}
                    <Text style={styles.appleButtonText}>
                      {isSignUp ? 'Sign up with Apple' : 'Sign in with Apple'}
                    </Text>
                  </View>
                </TouchableOpacity>
              )}

              {/* Google Sign In Button */}
              <TouchableOpacity 
                style={[styles.button, styles.googleButton]}
                onPress={handleGoogleSignIn}
                disabled={googleLoading || appleLoading}
              >
                <View style={[styles.buttonContent, {columnGap: iconTextSpacing}]}>
                  {googleLoading ? (
                    <ActivityIndicator size="small" color="#4285F4" />
                  ) : (
                    <Svg width={20} height={20} viewBox="0 0 24 24" fill="none">
                      <Path
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                        fill="#4285F4"
                      />
                      <Path
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                        fill="#34A853"
                      />
                      <Path
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                        fill="#FBBC05"
                      />
                      <Path
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                        fill="#EA4335"
                      />
                    </Svg>
                  )}
                  <Text style={styles.googleButtonText}>
                    {isSignUp ? 'Sign up with Google' : 'Sign in with Google'}
                  </Text>
                </View>
              </TouchableOpacity>

              {/* Email Continue Button */}
              <TouchableOpacity 
                style={[styles.button, styles.emailButton]}
                onPress={handleEmailContinue}
                disabled={googleLoading || appleLoading}
              >
                <View style={[styles.buttonContent, {columnGap: iconTextSpacing}]}>
                  <View style={styles.emailIconContainer}>
                    <Text style={styles.emailIcon}>✉️</Text>
                  </View>
                  <Text style={styles.emailButtonText}>Continue with email</Text>
                </View>
              </TouchableOpacity>

              {/* Terms and Conditions */}
              <View style={styles.termsContainer}>
                <Text style={styles.termsText}>
                  By continuing you agree to Cal AI's
                </Text>
                <View style={styles.termsLinksContainer}>
                  <Text 
                    style={styles.termsLink}
                    onPress={() => console.log('Terms and Conditions pressed')}
                  >
                    Terms and Conditions
                  </Text>
                  <Text style={styles.termsText}> and </Text>
                  <Text 
                    style={styles.termsLink}
                    onPress={() => console.log('Privacy Policy pressed')}
                  >
                    Privacy Policy
                  </Text>
                </View>
              </View>
            </Animated.View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.4)', // Lighter background opacity
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
    marginBottom: spacing.md, // Reduced margin to make room for divider
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
  divider: {
    height: 1,
    backgroundColor: colors.gray[200], // Light grey divider
    marginBottom: spacing.xl,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center', // Center the content
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: 100,
    marginBottom: spacing.md,
    height: 56, // Taller buttons as per screenshot
  },
  buttonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  appleButton: {
    backgroundColor: 'black',
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
    alignItems: 'center',
  },
  termsLinksContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    flexWrap: 'wrap',
    marginTop: 4,
  },
  termsText: {
    color: colors.text.secondary,
    fontSize: 14,
    textAlign: 'center',
  },
  termsLink: {
    color: colors.text.primary,
    fontSize: 14,
    textDecorationLine: 'underline',
    fontWeight: 'bold',
  },
});

export default SignInModal;