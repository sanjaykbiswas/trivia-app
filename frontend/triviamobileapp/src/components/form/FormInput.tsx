// File: frontend/triviamobileapp/src/components/form/FormInput.tsx
import React, { forwardRef, useState } from 'react';
import { TextInput, StyleSheet, TextInputProps } from 'react-native';
import { colors, spacing } from '../../theme';

interface FormInputProps extends TextInputProps {
  error?: string;
}

const FormInput = forwardRef<TextInput, FormInputProps>(
  ({ style, error, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);

    const handleFocus = (e: any) => {
      setIsFocused(true);
      props.onFocus?.(e);
    };

    const handleBlur = (e: any) => {
      setIsFocused(false);
      props.onBlur?.(e);
    };

    return (
      <TextInput
        ref={ref}
        style={[
          styles.input,
          isFocused && styles.inputFocused,
          error && styles.inputError,
          style
        ]}
        placeholderTextColor={colors.gray[400]}
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...props}
      />
    );
  }
);

const styles = StyleSheet.create({
  input: {
    width: '100%',
    padding: spacing.md,
    borderRadius: 16,
    backgroundColor: colors.gray[100],
    borderWidth: 1,
    borderColor: colors.border,
    color: colors.text.primary,
    fontSize: 16,
    marginBottom: spacing.md,
    textAlign: 'left',
    paddingLeft: spacing.md + 4, // Add extra left padding for text
  },
  inputFocused: {
    borderColor: colors.primary.main,
    backgroundColor: colors.background.default,
    shadowColor: colors.primary.main,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  inputError: {
    borderColor: colors.error.main,
  },
});

export default FormInput;