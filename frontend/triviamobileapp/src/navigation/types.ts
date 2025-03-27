// frontend/triviamobileapp/src/navigation/types.ts
export type RootStackParamList = {
  Splash: undefined;
  Onboarding: undefined;
  SignIn: undefined;
  // SignUp removed
  Home: undefined;
  Multiplayer: undefined;
  GameSetup: undefined;
  GameOptions: {
    packTitle?: string;
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
    packTitle?: string;
    questionCount?: number;
    timerSeconds?: number;
    roomCode?: string;
  };
  Profile: undefined;
  Settings: undefined;
};