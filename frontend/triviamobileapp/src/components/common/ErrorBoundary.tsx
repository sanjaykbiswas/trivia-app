import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, StyleSheet, TouchableOpacity, Text } from 'react-native';
import { colors, spacing } from '../../theme';
import Typography from './Typography';

interface Props {
  children: ReactNode;
  fallbackComponent?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary component
 * Catches JavaScript errors in child components and displays a fallback UI
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { 
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // You can log the error to an error reporting service
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    
    // Call the optional onError callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  resetError = (): void => {
    this.setState({ hasError: false, error: null });
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // Render custom fallback UI if provided
      if (this.props.fallbackComponent) {
        return this.props.fallbackComponent;
      }

      // Default fallback UI
      return (
        <View style={styles.container}>
          <Typography variant="heading3" style={styles.title}>
            <Text>Something went wrong</Text>
          </Typography>
          
          <Typography variant="bodyMedium" style={styles.message}>
            <Text>The application encountered an unexpected error.</Text>
          </Typography>
          
          {__DEV__ && this.state.error && (
            <View style={styles.errorContainer}>
              <Typography variant="bodySmall" style={styles.errorText}>
                <Text>{this.state.error.toString()}</Text>
              </Typography>
            </View>
          )}
          
          <TouchableOpacity 
            style={styles.button}
            onPress={this.resetError}
          >
            <Typography variant="buttonMedium" style={styles.buttonText}>
              <Text>Try Again</Text>
            </Typography>
          </TouchableOpacity>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
    backgroundColor: colors.background.default,
  },
  title: {
    marginBottom: spacing.md,
    color: colors.error.main,
  },
  message: {
    marginBottom: spacing.lg,
    textAlign: 'center',
    color: colors.text.primary,
  },
  errorContainer: {
    padding: spacing.md,
    backgroundColor: colors.gray[100],
    borderRadius: 8,
    marginBottom: spacing.lg,
    width: '100%',
  },
  errorText: {
    color: colors.error.dark,
  },
  button: {
    backgroundColor: colors.primary.main,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: 100,
  },
  buttonText: {
    color: colors.primary.contrastText,
  },
});

export default ErrorBoundary;