// frontend/triviamobileapp/src/components/auth/DisplayNameModal.tsx
import React, { useState, useRef, useEffect } from 'react';
import { View, StyleSheet, TextInput } from 'react-native';
import { Typography, Button, Modal } from '../common';
import { FormInput } from '../form';
import { colors, spacing } from '../../theme';
import { useAuth } from '../../contexts/AuthContext';

interface DisplayNameModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const DisplayNameModal: React.FC<DisplayNameModalProps> = ({ 
  visible, 
  onClose, 
  onSuccess
}) => {
  const [displayName, setDisplayName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<TextInput>(null);
  
  const { createTemporaryUser } = useAuth();

  // Focus input when modal becomes visible
  useEffect(() => {
    if (visible && inputRef.current) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 300);
    }
  }, [visible]);
  
  // Reset state when modal closes
  useEffect(() => {
    if (!visible) {
      setDisplayName('');
      setError(null);
    }
  }, [visible]);

  const handleSubmit = async () => {
    // Validate display name
    if (!displayName.trim()) {
      setError('Please enter a name to continue');
      return;
    }
    
    // Clear any previous errors
    setError(null);
    setLoading(true);
    
    try {
      // Create temporary user with the provided display name
      const userData = await createTemporaryUser(displayName.trim());
      
      if (userData) {
        // Success - close modal and continue
        setLoading(false);
        onSuccess();
      } else {
        // Error creating user
        setError('Failed to create user. Please try again.');
        setLoading(false);
      }
    } catch (error: any) {
      console.error('Error creating temporary user:', error);
      setError(error.message || 'An unexpected error occurred');
      setLoading(false);
    }
  };

  return (
    <Modal
      visible={visible}
      onClose={onClose}
    >
      <Typography variant="heading4" style={styles.modalTitle}>
        Enter a nickname
      </Typography>
      
      <Typography variant="bodyMedium" style={styles.modalDescription}>
        You can change this as often as you'd like
      </Typography>
      
      {/* Display Name Input */}
      <FormInput
        ref={inputRef}
        value={displayName}
        onChangeText={setDisplayName}
        placeholder="Your nickname"
        autoCapitalize="words"
        testID="display-name-input"
        autoFocus={true}
      />
      
      {/* Error message */}
      {error && (
        <Typography 
          variant="bodySmall" 
          color={colors.error.main} 
          style={styles.errorText}
        >
          {error}
        </Typography>
      )}
      
      {/* Submit Button */}
      <Button
        title="Continue"
        onPress={handleSubmit}
        variant="contained"
        size="large"
        fullWidth
        loading={loading}
        disabled={loading || !displayName.trim()}
        testID="continue-button"
        style={styles.continueButton}
      />
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalTitle: {
    marginBottom: spacing.xs,
  },
  modalDescription: {
    marginBottom: spacing.md,
    color: colors.text.secondary,
  },
  errorText: {
    marginTop: -spacing.sm,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  continueButton: {
    marginTop: spacing.sm,
  },
});

export default DisplayNameModal;