import { createRef } from 'react';
import { NavigationContainerRef } from '@react-navigation/native';
import { StackActions } from '@react-navigation/native';
import { RootStackParamList } from './types';

// Create a navigation reference that can be used outside of components
export const navigationRef = createRef<NavigationContainerRef<RootStackParamList>>();

/**
 * Navigate to a screen
 * @param name Screen name
 * @param params Screen parameters
 */
export function navigate<RouteName extends keyof RootStackParamList>(
  name: RouteName, 
  params?: RootStackParamList[RouteName]
) {
  if (navigationRef.current) {
    // Use type assertion to handle the navigation
    navigationRef.current.navigate(name as any, params as any);
  } else {
    console.warn('Navigation attempted before navigator was ready');
  }
}

/**
 * Go back to the previous screen
 */
export function goBack() {
  if (navigationRef.current) {
    navigationRef.current.goBack();
  }
}

/**
 * Reset the navigation state to the provided state
 * @param routes New route stack
 * @param index Index of the active route
 */
export function reset(routes: { name: keyof RootStackParamList, params?: any }[], index = 0) {
  if (navigationRef.current) {
    navigationRef.current.reset({
      index,
      routes: routes as any[],
    });
  }
}

/**
 * Replace the current screen with a new one
 * @param name Screen name
 * @param params Screen parameters
 */
export function replace<RouteName extends keyof RootStackParamList>(
  name: RouteName, 
  params?: RootStackParamList[RouteName]
) {
  if (navigationRef.current) {
    navigationRef.current.dispatch(
      StackActions.replace(name as string, params as any)
    );
  }
}