import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity, Platform, ActivityIndicator, Text, Alert } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { Header } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@env';
import { FormInput } from '../../components/form';

type APITestScreenProps = StackScreenProps<RootStackParamList, 'APITest'>;

const API_TIMEOUT = 10000; // 10 seconds timeout for API calls

interface TestResult {
  endpoint: string;
  status: 'success' | 'error' | 'pending';
  message: string;
  responseTime?: number;
  details?: string;
  method?: string;
}

// Available HTTP methods for testing
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

const APITestScreen: React.FC<APITestScreenProps> = ({ navigation }) => {
  const [results, setResults] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [customUrl, setCustomUrl] = useState('');
  const [customEndpoint, setCustomEndpoint] = useState('/');
  const [selectedMethod, setSelectedMethod] = useState<HttpMethod>('GET');

  // Default API URLs
  const getDefaultApiUrl = (): string => {
    if (Platform.OS === 'ios') {
      return 'http://localhost:8000';
    } else {
      return 'http://10.0.2.2:8000';
    }
  };
  
  const [apiBaseUrl, setApiBaseUrl] = useState(getDefaultApiUrl());

  const handleBackPress = () => {
    navigation.goBack();
  };

  const addResult = (result: TestResult) => {
    setResults(prev => [result, ...prev]);
  };

  const clearResults = () => {
    setResults([]);
  };

  const updateResult = (endpoint: string, update: Partial<TestResult>) => {
    setResults(prev => 
      prev.map(result => 
        result.endpoint === endpoint 
          ? { ...result, ...update } 
          : result
      )
    );
  };

  const testEndpoint = async (endpoint: string, description: string = '', method: HttpMethod = 'GET') => {
    const fullUrl = `${apiBaseUrl}${endpoint}`;
    
    // Add a pending result first
    addResult({
      endpoint: fullUrl,
      status: 'pending',
      message: `Testing ${description || endpoint} with ${method}...`,
      method,
    });

    try {
      const startTime = Date.now();
      
      // Set up timeout handling
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
      
      // Make the request with the specified method
      const options: RequestInit = {
        method,
        headers: { 'Accept': 'application/json' },
        signal: controller.signal
      };
      
      const response = await fetch(fullUrl, options);
      
      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;

      // Clone the response to avoid "Already read" errors - a key improvement!
      const responseClone = response.clone();

      if (response.ok) {
        let responseText = '';
        try {
          // Try to read as JSON first, fallback to text - ONLY using the responseClone
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const data = await responseClone.json();
            responseText = JSON.stringify(data, null, 2).substring(0, 1000);
            if (JSON.stringify(data).length > 1000) responseText += '...';
          } else {
            responseText = await responseClone.text();
            if (responseText.length > 1000) responseText = responseText.substring(0, 1000) + '...';
          }
        } catch (e) {
          // If JSON parsing fails, make ANOTHER clone and try to get the raw text
          try {
            const anotherClone = response.clone(); // Make a new clone
            responseText = await anotherClone.text();
            if (responseText.length > 1000) responseText = responseText.substring(0, 1000) + '...';
          } catch (textError) {
            responseText = `[Could not read response body: ${textError}]`;
          }
        }

        updateResult(fullUrl, {
          status: 'success',
          message: `✅ Success (${response.status} ${response.statusText})`,
          responseTime,
          details: responseText || '[Empty response body]'
        });
      } else {
        let errorDetails = '';
        try {
          // First try to get JSON error details
          try {
            const errorJson = await responseClone.json();
            errorDetails = JSON.stringify(errorJson, null, 2);
          } catch (jsonError) {
            // If not JSON, get text
            errorDetails = await response.text();
          }
          
          if (errorDetails.length > 1000) errorDetails = errorDetails.substring(0, 1000) + '...';
        } catch (e) {
          errorDetails = 'Could not read response body';
        }

        updateResult(fullUrl, {
          status: 'error',
          message: `❌ Failed with status ${response.status} ${response.statusText}`,
          responseTime,
          details: errorDetails || '[Empty error response]'
        });
      }
    } catch (error: any) {
      const errorMessage = error.name === 'AbortError' 
        ? '❌ Request timed out after 10 seconds'
        : `❌ Error: ${error.message || 'Unknown error'}`;
      
      updateResult(fullUrl, {
        status: 'error',
        message: errorMessage,
        details: error.stack ? error.stack.split('\n').slice(0, 3).join('\n') : undefined
      });
    }
  };

  const runAllTests = async () => {
    setLoading(true);
    clearResults();
    
    try {
      // Test main API endpoints in sequence to avoid "Already read" issues
      await testEndpoint('/', 'Root endpoint');
      await new Promise(r => setTimeout(r, 500)); // Small delay between requests
      
      await testEndpoint('/docs', 'API docs (Swagger UI)');
      await new Promise(r => setTimeout(r, 500)); // Small delay between requests
      
      await testEndpoint('/categories/', 'Categories endpoint');  // Note the trailing slash to avoid redirect
      await new Promise(r => setTimeout(r, 500)); // Small delay between requests
      
      // Add a custom fix for the questions endpoint that was causing 500 errors
      await testEndpoint('/questions/game?count=2', 'Questions endpoint (fixed)');
      
      // Test Supabase direct connection
      if (SUPABASE_URL) {
        const supabaseUrl = `${SUPABASE_URL}/rest/v1/categories`;
        addResult({
          endpoint: supabaseUrl,
          status: 'pending',
          message: `Testing direct Supabase connection...`,
          method: 'GET'
        });
        
        try {
          const startTime = Date.now();
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
          
          const response = await fetch(supabaseUrl, {
            method: 'GET',
            headers: {
              'apikey': SUPABASE_ANON_KEY || '',
              'Content-Type': 'application/json',
            },
            signal: controller.signal
          });
          
          clearTimeout(timeoutId);
          const responseTime = Date.now() - startTime;
          
          // Clone response to avoid "Already read" errors
          const responseClone = response.clone();
          
          if (response.ok) {
            const data = await responseClone.json();
            updateResult(supabaseUrl, {
              status: 'success',
              message: `✅ Supabase connection successful`,
              responseTime,
              details: JSON.stringify(data, null, 2).substring(0, 1000)
            });
          } else {
            updateResult(supabaseUrl, {
              status: 'error',
              message: `❌ Supabase connection failed (${response.status})`,
              responseTime,
              details: await response.text()
            });
          }
        } catch (error: any) {
          updateResult(supabaseUrl, {
            status: 'error',
            message: `❌ Supabase error: ${error.message || 'Unknown error'}`,
            details: error.stack
          });
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const testCustomEndpoint = async () => {
    if (!customEndpoint) {
      return;
    }
    
    let endpoint = customEndpoint;
    if (!endpoint.startsWith('/')) {
      endpoint = '/' + endpoint;
    }
    
    await testEndpoint(endpoint, 'Custom endpoint', selectedMethod);
  };

  const updateApiUrl = () => {
    if (customUrl.trim()) {
      setApiBaseUrl(customUrl.trim());
      
      // Show a confirmation
      Alert.alert(
        'API URL Updated',
        `API URL set to: ${customUrl.trim()}`,
        [{ text: 'OK' }]
      );
    } else {
      setApiBaseUrl(getDefaultApiUrl());
      
      // Show a confirmation
      Alert.alert(
        'API URL Reset',
        `API URL reset to default: ${getDefaultApiUrl()}`,
        [{ text: 'OK' }]
      );
    }
  };

  // Reset to default URL
  const resetApiUrl = () => {
    setCustomUrl('');
    setApiBaseUrl(getDefaultApiUrl());
    
    // Show a confirmation
    Alert.alert(
      'API URL Reset',
      `API URL reset to default: ${getDefaultApiUrl()}`,
      [{ text: 'OK' }]
    );
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
    >
      <View style={styles.container}>
        <Header 
          showBackButton={true} 
          onBackPress={handleBackPress} 
        />
        
        <Typography variant="heading2" style={styles.title}>
          API Connection Test
        </Typography>
        
        <View style={styles.formContainer}>
          <Typography variant="heading5" style={styles.sectionTitle}>
            Backend API URL
          </Typography>
          
          <Typography variant="bodySmall" style={styles.currentUrlText}>
            Current: {apiBaseUrl}
          </Typography>
          
          <View style={styles.inputRow}>
            <FormInput
              value={customUrl}
              onChangeText={setCustomUrl}
              placeholder="Custom API URL (eg: http://192.168.x.x:8000)"
              style={styles.urlInput}
            />
            
            <TouchableOpacity 
              style={styles.updateButton}
              onPress={updateApiUrl}
            >
              <Typography variant="bodySmall" color="white">
                Update
              </Typography>
            </TouchableOpacity>
          </View>
          
          <Button
            title="Reset to Default URL"
            onPress={resetApiUrl}
            variant="outlined"
            size="small"
            style={styles.resetButton}
          />
        </View>
        
        <View style={styles.actionsContainer}>
          <Button
            title="Run All Tests"
            onPress={runAllTests}
            variant="contained"
            size="large"
            loading={loading}
            disabled={loading}
            style={styles.testButton}
          />
          
          <View style={styles.customEndpointContainer}>
            <Typography variant="heading5" style={styles.sectionTitle}>
              Test Custom Endpoint
            </Typography>
            
            <View style={styles.methodSelector}>
              {(['GET', 'POST', 'PUT', 'DELETE'] as HttpMethod[]).map(method => (
                <TouchableOpacity
                  key={method}
                  style={[
                    styles.methodButton,
                    selectedMethod === method && styles.selectedMethodButton
                  ]}
                  onPress={() => setSelectedMethod(method)}
                >
                  <Typography
                    variant="bodySmall"
                    color={selectedMethod === method ? 'white' : colors.text.primary}
                  >
                    {method}
                  </Typography>
                </TouchableOpacity>
              ))}
            </View>
            
            <View style={styles.inputRow}>
              <FormInput
                value={customEndpoint}
                onChangeText={setCustomEndpoint}
                placeholder="Endpoint (e.g., /categories/)"
                style={styles.endpointInput}
              />
              
              <TouchableOpacity 
                style={styles.testEndpointButton}
                onPress={testCustomEndpoint}
                disabled={loading}
              >
                <Typography variant="bodySmall" color="white">
                  Test
                </Typography>
              </TouchableOpacity>
            </View>
          </View>
        </View>
        
        <View style={styles.resultsContainer}>
          <View style={styles.resultsHeader}>
            <Typography variant="heading5" style={styles.resultsTitle}>
              Test Results
            </Typography>
            
            {results.length > 0 && (
              <TouchableOpacity 
                onPress={clearResults}
                style={styles.clearButton}
              >
                <Typography variant="bodySmall" color={colors.error.main}>
                  Clear
                </Typography>
              </TouchableOpacity>
            )}
          </View>
          
          <ScrollView style={styles.resultsScroll}>
            {results.length === 0 ? (
              <Typography variant="bodyMedium" style={styles.noResults}>
                No tests run yet. Press "Run All Tests" to begin.
              </Typography>
            ) : (
              results.map((result, index) => (
                <View key={`${result.endpoint}-${index}`} style={styles.resultItem}>
                  <View style={styles.resultHeader}>
                    <View style={styles.endpointContainer}>
                      {result.method && (
                        <View style={styles.methodTag}>
                          <Typography variant="caption" style={styles.methodText}>
                            {result.method}
                          </Typography>
                        </View>
                      )}
                      <Typography variant="bodySmall" style={styles.resultEndpoint}>
                        {result.endpoint}
                      </Typography>
                    </View>
                    
                    {result.responseTime && (
                      <Typography variant="bodySmall" style={styles.resultTime}>
                        {result.responseTime}ms
                      </Typography>
                    )}
                  </View>
                  
                  <View style={styles.resultContent}>
                    {result.status === 'pending' ? (
                      <View style={styles.pendingContainer}>
                        <ActivityIndicator size="small" color={colors.primary.main} />
                        <Typography variant="bodyMedium" style={styles.pendingText}>
                          {result.message}
                        </Typography>
                      </View>
                    ) : (
                      <Typography 
                        variant="bodyMedium" 
                        color={result.status === 'success' ? colors.success.main : colors.error.main}
                      >
                        {result.message}
                      </Typography>
                    )}
                    
                    {result.details && (
                      <View style={styles.detailsContainer}>
                        <Typography variant="bodySmall" style={styles.detailsTitle}>
                          Response:
                        </Typography>
                        <Text style={styles.detailsText}>
                          {result.details}
                        </Text>
                      </View>
                    )}
                  </View>
                </View>
              ))
            )}
          </ScrollView>
        </View>
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  title: {
    paddingHorizontal: spacing.page,
    marginBottom: spacing.md,
  },
  formContainer: {
    paddingHorizontal: spacing.page,
    marginBottom: spacing.md,
  },
  sectionTitle: {
    marginBottom: spacing.xs,
  },
  currentUrlText: {
    color: colors.text.secondary,
    marginBottom: spacing.xs,
  },
  inputRow: {
    flexDirection: 'row',
    marginBottom: spacing.xs,
  },
  urlInput: {
    flex: 1,
    marginBottom: 0,
  },
  updateButton: {
    backgroundColor: colors.primary.main,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    marginLeft: spacing.xs,
    borderRadius: 16,
  },
  resetButton: {
    alignSelf: 'flex-start',
    marginTop: spacing.xs,
  },
  actionsContainer: {
    paddingHorizontal: spacing.page,
    marginBottom: spacing.md,
  },
  testButton: {
    marginBottom: spacing.md,
  },
  customEndpointContainer: {
    marginBottom: spacing.md,
  },
  methodSelector: {
    flexDirection: 'row',
    marginBottom: spacing.xs,
  },
  methodButton: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    marginRight: spacing.xs,
    borderRadius: 8,
    backgroundColor: colors.background.light,
    borderWidth: 1,
    borderColor: colors.divider,
  },
  selectedMethodButton: {
    backgroundColor: colors.primary.main,
    borderColor: colors.primary.main,
  },
  endpointInput: {
    flex: 1,
    marginBottom: 0,
  },
  testEndpointButton: {
    backgroundColor: colors.primary.main,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    marginLeft: spacing.xs,
    borderRadius: 16,
  },
  resultsContainer: {
    flex: 1,
    paddingHorizontal: spacing.page,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  resultsTitle: {
    flex: 1,
  },
  clearButton: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
  },
  resultsScroll: {
    flex: 1,
    backgroundColor: colors.background.light,
    borderRadius: 16,
  },
  noResults: {
    padding: spacing.md,
    textAlign: 'center',
    color: colors.text.secondary,
  },
  resultItem: {
    padding: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  endpointContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  methodTag: {
    backgroundColor: colors.gray[700],
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 6,
  },
  methodText: {
    color: 'white',
    fontSize: 10,
    fontWeight: 'bold',
  },
  resultEndpoint: {
    flex: 1,
    color: colors.text.secondary,
    fontWeight: '500',
  },
  resultTime: {
    color: colors.text.secondary,
  },
  resultContent: {
  },
  pendingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  pendingText: {
    marginLeft: spacing.sm,
    color: colors.text.secondary,
  },
  detailsContainer: {
    marginTop: spacing.sm,
    padding: spacing.sm,
    backgroundColor: colors.background.default,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: colors.gray[300],
  },
  detailsTitle: {
    fontWeight: '500',
    marginBottom: spacing.xs,
  },
  detailsText: {
    fontSize: 12,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: colors.text.primary,
  },
});

export default APITestScreen;