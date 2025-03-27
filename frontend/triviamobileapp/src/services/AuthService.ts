// frontend/triviamobileapp/src/services/AuthService.ts
import { createClient, SupabaseClient, Provider } from '@supabase/supabase-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@env';
import { GoogleSignin, statusCodes } from '@react-native-google-signin/google-signin';
import { appleAuth } from '@invertase/react-native-apple-authentication';
import { Platform } from 'react-native';

// Make sure polyfills are processed first
import 'react-native-url-polyfill/auto';

class AuthService {
  private supabase: SupabaseClient;
  
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
  private initializeGoogleSignIn() {
    try {
      GoogleSignin.configure({
        // You need to replace this with your actual Web Client ID from Google Cloud Console
        webClientId: '123456789-example.apps.googleusercontent.com', // Replace with actual Client ID
        offlineAccess: true,
      });
    } catch (error) {
      console.error('Failed to configure Google Sign In:', error);
    }
  }
  
  async signUp(email: string) {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    
    // With magic links, signUp is just sending a magic link
    return this.supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: 'triviamobileapp://', // Your app's deep link URL
      }
    });
  }
  
  async signIn(email: string) {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    
    // For magic links, we use signInWithOtp method
    return this.supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: 'triviamobileapp://', // Your app's deep link URL
      }
    });
  }
  
  async signOut() {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    
    // If signed in with Google, sign out from there too
    try {
      // Check if the user is signed in with Google
      const isGoogleSignedIn = await GoogleSignin.isSignedIn();
      if (isGoogleSignedIn) {
        await GoogleSignin.signOut();
      }
    } catch (error) {
      console.error('Google Sign Out error:', error);
    }
    
    // Sign out from Supabase
    return this.supabase.auth.signOut();
  }
  
  async getCurrentUser() {
    if (!this.supabase.auth) return { error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.getUser();
  }
  
  async getSession() {
    if (!this.supabase.auth) return { data: { session: null }, error: { message: 'Supabase client not initialized properly' } };
    return this.supabase.auth.getSession();
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
        return this.supabase.auth.signInWithIdToken({
          provider: 'apple' as Provider,
          token: identityToken,
        });
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
      // Check if play services are available
      await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
      
      // Perform the Google sign-in
      await GoogleSignin.signIn();
      
      // Get the auth tokens - this is a separate step with the newer Google Sign-In API
      const tokens = await GoogleSignin.getTokens();
      
      if (!tokens.idToken) {
        throw new Error('Google Sign In failed - no ID token returned');
      }
      
      // Sign in with Supabase using the Google token
      return this.supabase.auth.signInWithIdToken({
        provider: 'google' as Provider,
        token: tokens.idToken,
      });
    } catch (error: any) {
      console.error('Google Sign In error:', error);
      
      if (error.code === statusCodes.SIGN_IN_CANCELLED) {
        return { error: { message: 'Sign in was canceled' } };
      }
      
      return { error: { message: error.message || 'Google Sign In failed' } };
    }
  }
  
  getSupabaseClient() {
    return this.supabase;
  }
}

export default new AuthService();