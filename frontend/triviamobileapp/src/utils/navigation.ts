/**
 * Navigation types and utilities
 */

// Define the available screens in the app
export enum AppScreens {
    Splash = 'Splash',
    Onboarding = 'Onboarding',
    // Add other screens here as you develop them
    // Auth screens
    SignIn = 'SignIn',
    SignUp = 'SignUp',
    // Main app screens
    Home = 'Home',
    Profile = 'Profile',
    Settings = 'Settings',
  }
  
  // Define the navigation parameters for each screen
  export type AppNavigatorParamList = {
    [AppScreens.Splash]: undefined;
    [AppScreens.Onboarding]: undefined;
    // Define parameters for other screens as needed
    [AppScreens.SignIn]: undefined;
    [AppScreens.SignUp]: undefined;
    [AppScreens.Home]: undefined;
    [AppScreens.Profile]: undefined;
    [AppScreens.Settings]: undefined;
  };
  
  // Utility to create navigation references (for later use with React Navigation)
  export const createNavigationRef = () => null;