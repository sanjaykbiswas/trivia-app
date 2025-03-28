// frontend/triviamobileapp/src/services/AuthService.ts
import { createClient, SupabaseClient, Provider } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@env';
import { GoogleSignin, statusCodes } from '@react-native-google-signin/google-signin';
import { appleAuth } from '@invertase/react-native-apple-authentication';
import { Platform, Linking } from 'react-native';

// Make sure polyfills are processed first
import 'react-native-url-polyfill/auto';

class AuthService {
  private supabase: SupabaseClient;
  private readonly TEMP_USER_KEY = 'trivia_app_temp_user';
  private isGoogleConfigured: boolean = false;
  
  constructor() {
    // Check if environment variables are available
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
      console.error('Supabase credentials are missing. Make sure .env file is properly configured.');
    }
    
    try {
      this.supabase = createClient(
        SUPABASE_URL || '', 
        SUPABASE_ANON_KEY || '', 
        {
          auth: {
            storage: AsyncStorage,
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: false,
          },
        }
      );
      
      // Initialize Google Sign-In
      this.initializeGoogleSignIn();
      
    } catch (error) {
      console.error('Failed to initialize Supabase client:', error);
      // Initialize with a dummy client to prevent crashes
      this.supabase = {} as SupabaseClient;
    }
  }

  // Initialize Google Sign-In configuration
  private async initializeGoogleSignIn() {
    try {
      // Verify Google Sign-In is properly installed
      if (Platform.OS === 'android') {
        await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
      }
      
      // Configure Google Sign-In
      GoogleSignin.configure({
        // Your actual Web Client ID from Google Cloud Console
        webClientId: '945168523687-fiqetr8sqbsfb4sge23qureoj5j3c2g3.apps.googleusercontent.com',
        offlineAccess: true,
        iosClientId: '945168523687-4dvathak8sfh1ohg7rilm3n0lik5sobh.apps.googleusercontent.com',
        // Force user to select account each time (no silent login)
        forceCodeForRefreshToken: true,
      });
      
      this.isGoogleConfigured = true;
      console.log('Google Sign-In configured successfully');
      
    } catch (error) {
      this.isGoogleConfigured = false;
      console.error('Failed to configure Google Sign In:', error);
    }
  }
  
  // Save temporary user to storage
  async saveTempUser(userData: { id: string, username: string }): Promise<void> {
    try {
      await AsyncStorage.setItem(this.TEMP_USER_KEY, JSON.stringify(userData));
    } catch (error) {
      console.error('Failed to save temporary user data:', error);
    }
  }

  // Get temporary user from storage
  async getTempUser(): Promise<{ id: string, username: string } | null> {
    try {
      const userData = await AsyncStorage.getItem(this.TEMP_USER_KEY);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Failed to get temporary user data:', error);
      return null;
    }
  }

  // Clear temporary user from storage
  async clearTempUser(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.TEMP_USER_KEY);
    } catch (error) {
      console.error('Failed to clear temporary user data:', error);
    }
  }

  // Create temporary user with just a username
  async createTempUser(username: string): Promise<{ id: string, username: string } | null> {
    try {
      // Make API call to backend
      const response = await fetch(`${SUPABASE_URL}/auth/temp-user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create temporary user: ${response.statusText}`);
      }
      
      const userData = await response.json();
      
      // Save to local storage
      await this.saveTempUser(userData);
      
      return userData;
    } catch (error) {
      console.error('Failed to create temporary user:', error);
      return null;
    }
  }

  // Link temporary user to authenticated identity
  async linkIdentity(tempUserId: string, authProvider: string, email?: string): Promise<boolean> {
    try {
      // Get current session
      const { data: { session } } = await this.getSession();
      
      if (!session) {
        console.error('No active session for identity linking');
        return false;
      }
      
      // Make API call to backend with authentication
      const response = await fetch(`${SUPABASE_URL}/auth/link-identity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          temp_user_id: tempUserId,
          auth_provider: authProvider,
          email,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to link identity: ${response.statusText}`);
      }
      
      // Clear temporary user data since it's now linked
      await this.clearTempUser();
      
      return true;
    } catch (error) {
      console.error('Failed to link identity:', error);
      return false;
    }
  }
  
  async signUp(email: string) {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    
    const result = await this.supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: 'triviamobileapp://auth/callback',
      }
    });
    
    // If successful and we have a temporary user, attempt to link identities
    if (!result.error) {
      try {
        const tempUser = await this.getTempUser();
        if (tempUser) {
          // Store the intent to link identities after authentication completes
          await AsyncStorage.setItem('pending_link', JSON.stringify({
            tempUserId: tempUser.id,
            authProvider: 'email',
            email,
          }));
        }
      } catch (error) {
        console.error('Error preparing identity linking:', error);
      }
    }
    
    return result;
  }
  
  async signIn(email: string) {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    
    // For magic links, we use signInWithOtp method
    const result = await this.supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: 'triviamobileapp://auth/callback', // Your app's deep link URL with path
      }
    });
    
    // If successful and we have a temporary user, attempt to link identities
    if (!result.error) {
      try {
        const tempUser = await this.getTempUser();
        if (tempUser) {
          // Store the intent to link identities after authentication completes
          await AsyncStorage.setItem('pending_link', JSON.stringify({
            tempUserId: tempUser.id,
            authProvider: 'email',
            email,
          }));
        }
      } catch (error) {
        console.error('Error preparing identity linking:', error);
      }
    }
    
    return result;
  }
  
  async signOut() {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    
    // If signed in with Google, sign out from there too
    try {
      // Try to sign out from Google without checking if signed in first
      // This is safer as the check method might change between versions
      try {
        await GoogleSignin.signOut();
      } catch (error: any) {
        // Only log the error if it's not "No user signed in"
        if (error?.code !== statusCodes.SIGN_IN_REQUIRED) {
          console.error('Google Sign Out error:', error);
        }
      }
    } catch (error) {
      console.error('Google Sign Out handling error:', error);
    }
    
    // Sign out from Supabase
    return this.supabase.auth.signOut();
  }
  
  async signInWithApple() {
    try {
      // Check if Apple authentication is available (iOS 13+ only)
      if (!appleAuth.isSupported) {
        return { error: { message: 'Apple Sign In is only supported on iOS 13 and above' } };
      }
      
      // Perform the Apple sign-in request
      const appleAuthRequestResponse = await appleAuth.performRequest({
        requestedOperation: appleAuth.Operation.LOGIN,
        requestedScopes: [appleAuth.Scope.EMAIL, appleAuth.Scope.FULL_NAME],
      });
      
      // Get the credential state for the user
      const credentialState = await appleAuth.getCredentialStateForUser(appleAuthRequestResponse.user);
      
      // If authorized, sign in with Supabase using the Apple credentials
      if (credentialState === appleAuth.State.AUTHORIZED) {
        // Get the identity token
        const { identityToken } = appleAuthRequestResponse;
        
        if (!identityToken) {
          throw new Error('Apple Sign In failed - no identity token returned');
        }
        
        // Sign in with Supabase using the Apple token
        const response = await this.supabase.auth.signInWithIdToken({
          provider: 'apple' as Provider,
          token: identityToken,
        });
        
        // After successful sign-in, check if we have a temporary user to link
        const tempUser = await this.getTempUser();
        if (tempUser && !response.error) {
          // If we have both a temporary user and successful sign-in
          // Store the intent to link identities
          await AsyncStorage.setItem('pending_link', JSON.stringify({
            tempUserId: tempUser.id,
            authProvider: 'apple',
            email: response.data.user?.email,
          }));
        }
        
        return response;
      }
      
      return { error: { message: 'Apple Sign In failed - not authorized' } };
    } catch (error: any) {
      console.error('Apple Sign In error:', error);
      
      if (error.code === appleAuth.Error.CANCELED) {
        return { error: { message: 'Sign in was canceled' } };
      }
      
      return { error: { message: error.message || 'Apple Sign In failed' } };
    }
  }
  
  async signInWithGoogle() {
    try {
      // Check if Google Sign-In is properly configured
      if (!this.isGoogleConfigured) {
        // Try to initialize again
        await this.initializeGoogleSignIn();
        
        if (!this.isGoogleConfigured) {
          return { error: { message: 'Google Sign In is not properly configured' } };
        }
      }
      
      // Check if play services are available (Android specific)
      if (Platform.OS === 'android') {
        await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
      }
      
      console.log('Attempting Google sign-in using native flow...');
      
      // First make sure we're signed out of Google
      try {
        await GoogleSignin.signOut();
      } catch (signOutError) {
        // Ignore errors during sign out
        console.log('Sign out before sign in failed, continuing anyway:', signOutError);
      }
      
      // Use the native Google Sign-in flow
      const userInfo = await GoogleSignin.signIn();
      
      // Check if we have user info
      if (!userInfo) {
        throw new Error('Google Sign In failed - no user info returned');
      }
      
      console.log('Google Sign In successful, getting tokens...');
      
      // Get the ID token explicitly - this is the safe way regardless of version
      const tokens = await GoogleSignin.getTokens();
      
      if (!tokens || !tokens.idToken) {
        throw new Error('Failed to get Google ID token');
      }
      
      const idToken = tokens.idToken;
      
      console.log('Successfully got Google ID token, signing in with Supabase...');
      
      // Sign in with Supabase using the Google ID token
      const { data, error } = await this.supabase.auth.signInWithIdToken({
        provider: 'google',
        token: idToken,
      });
      
      if (error) {
        console.error('Supabase Google sign in error:', error);
        return { error };
      }
      
      // If successful and we have a temporary user, prepare to link identities
      if (data.user) {
        const tempUser = await this.getTempUser();
        if (tempUser) {
          await AsyncStorage.setItem('pending_link', JSON.stringify({
            tempUserId: tempUser.id,
            authProvider: 'google',
            email: data.user.email,
          }));
        }
      }
      
      return { data };
      
    } catch (error: any) {
      console.error('Google Sign In error:', error);
      
      // Provide more specific error messages based on error codes
      if (error.code === statusCodes.SIGN_IN_CANCELLED) {
        return { error: { message: 'Sign in was canceled' } };
      } else if (error.code === statusCodes.IN_PROGRESS) {
        return { error: { message: 'Google Sign In is already in progress' } };
      } else if (error.code === statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
        return { error: { message: 'Google Play Services is not available' } };
      }
      
      return { 
        error: { 
          message: error.message || 'Google Sign In failed',
          details: error.code ? `Error code: ${error.code}` : undefined
        }
      };
    }
  }
  
  // Helper method to check if specific OAuth providers are enabled in Supabase
  async getEnabledProviders() {
    try {
      const response = await fetch(`${SUPABASE_URL}/auth/v1/providers`, {
        method: 'GET',
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch providers: ${response.statusText}`);
      }
      
      const providers = await response.json();
      
      if (!Array.isArray(providers)) {
        throw new Error('Unexpected response format');
      }
      
      // Return array of enabled provider IDs
      return providers
        .filter((provider: any) => provider.enabled === true)
        .map((provider: any) => provider.id);
    } catch (error) {
      console.error('Error checking enabled providers:', error);
      return [];
    }
  }
  
  async getCurrentUser() {
    if (!this.supabase.auth) return { data: { user: null }, error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.getUser();
  }
  
  async getSession() {
    if (!this.supabase.auth) return { data: { session: null }, error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.getSession();
  }
  
  getSupabaseClient() {
    return this.supabase;
  }
}

export default new AuthService();