export type RootStackParamList = {
  Splash: undefined;
  Onboarding: undefined;
  SignIn: undefined;
  SignUp: undefined;
  Home: undefined;
  Multiplayer: undefined;
  GameSetup: undefined;
  GamePlay: { categoryId?: string; difficulty?: string; roomCode?: string; categories?: string[] };
  Profile: undefined;
  Settings: undefined;
};