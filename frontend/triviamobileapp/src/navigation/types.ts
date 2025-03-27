export type RootStackParamList = {
  Splash: undefined;
  Onboarding: undefined;
  SignIn: undefined;
  SignUp: undefined;
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
  Profile: undefined;
  Settings: undefined;
};