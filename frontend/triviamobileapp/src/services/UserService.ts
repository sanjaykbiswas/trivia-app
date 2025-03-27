// frontend/triviamobileapp/src/services/UserService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import AuthService from './AuthService';
import { SUPABASE_URL } from '@env';

class UserService {
  private readonly TEMP_USER_KEY = 'trivia_app_temp_user';
  
  /**
   * Create a temporary user with just a display name
   */
  async createTemporaryUser(username: string): Promise<{ id: string; username: string } | null> {
    // Use AuthService's method
    return AuthService.createTempUser(username);
  }
  
  /**
   * Check if the current user is a temporary user
   */
  async isTemporaryUser(): Promise<boolean> {
    const tempUser = await this.getTemporaryUser();
    if (!tempUser) return false;
    
    // Check if user has been linked already (has auth session but still has temp data)
    const { data } = await AuthService.getSession();
    return !data.session;
  }
  
  /**
   * Get the temporary user data
   */
  async getTemporaryUser(): Promise<{ id: string; username: string } | null> {
    return AuthService.getTempUser();
  }
  
  /**
   * Handle post-authentication identity linking
   * Call this after successful authentication to link identities if needed
   */
  async handlePostAuthLinking(): Promise<boolean> {
    try {
      // Check if we have pending link information
      const pendingLinkData = await AsyncStorage.getItem('pending_link');
      if (!pendingLinkData) return false;
      
      const { tempUserId, authProvider, email } = JSON.parse(pendingLinkData);
      
      // Attempt to link identities
      const linked = await AuthService.linkIdentity(tempUserId, authProvider, email);
      
      // Clean up pending link data regardless of result
      await AsyncStorage.removeItem('pending_link');
      
      return linked;
    } catch (error) {
      console.error('Error handling post-authentication linking:', error);
      // Clean up to prevent future errors
      await AsyncStorage.removeItem('pending_link');
      return false;
    }
  }
  
  /**
   * Get the current username (either from auth or temporary user)
   */
  async getCurrentUsername(): Promise<string | null> {
    // Check authenticated user first
    const { data } = await AuthService.getCurrentUser();
    if (data.user?.user_metadata?.username) {
      return data.user.user_metadata.username;
    }
    
    // User might be in the custom users table (created by the trigger)
    // Get session for authentication token
    const sessionData = await AuthService.getSession();
    const token = sessionData.data.session?.access_token;
    
    if (token && data.user?.id) {
      try {
        // Fetch user from custom table using authenticated API call
        const response = await fetch(`${SUPABASE_URL}/api/users/${data.user.id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const userData = await response.json();
          if (userData.username) {
            return userData.username;
          }
        }
      } catch (error) {
        console.error('Error fetching user data:', error);
      }
    }
    
    // Fall back to temporary user
    const tempUser = await this.getTemporaryUser();
    return tempUser?.username || null;
  }
}

export default new UserService();