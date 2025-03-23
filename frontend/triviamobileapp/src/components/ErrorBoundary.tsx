// src/components/ErrorBoundary.tsx
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { normalize, spacing } from '../utils/scaling';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.log('Error caught by boundary:', error, errorInfo);
  }

  resetError = (): void => {
    this.setState({ hasError: false, error: undefined });
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <View style={styles.container}>
          <Text style={styles.title}>Something went wrong</Text>
          <Text style={styles.message}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </Text>
          <TouchableOpacity style={styles.button} onPress={this.resetError}>
            <Text style={styles.buttonText}>Try Again</Text>
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
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing(20),
    backgroundColor: '#F8F9FF',
  },
  title: {
    fontSize: normalize(24),
    fontWeight: 'bold',
    marginBottom: spacing(10),
    color: '#333',
  },
  message: {
    fontSize: normalize(16),
    textAlign: 'center',
    marginBottom: spacing(30),
    color: '#666',
  },
  button: {
    backgroundColor: '#7B61FF',
    paddingHorizontal: spacing(30),
    paddingVertical: spacing(15),
    borderRadius: spacing(30),
  },
  buttonText: {
    color: 'white',
    fontSize: normalize(16),
    fontWeight: 'bold',
  },
});

export default ErrorBoundary;