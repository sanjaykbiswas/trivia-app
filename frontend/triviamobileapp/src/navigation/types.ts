// frontend/triviamobileapp/src/navigation/types.ts
// Updated to add categoryId to navigation params
export type RootStackParamList = {
  Splash: undefined;
  Onboarding: undefined;
  SignIn: {
    isSignUp?: boolean;
  };
  Home: undefined;
  Multiplayer: undefined;
  GameSetup: undefined;
  GameOptions: {
    packTitle?: string;
    categoryId?: string;
  };
  GamePlay: {
    categoryId?: string; 
    difficulty?: string; 
    roomCode?: string; 
    categories?: string[];
    packTitle?: string;
    questionCount?: number;
    timerSeconds?: number;
  };
  QuestionScreen: {
    categoryId?: string;
    packTitle?: string;
    questionCount?: number;
    timerSeconds?: number;
    roomCode?: string;
  };
  Profile: undefined;
  Settings: undefined;
  APITest: undefined; // Added for API testing
};