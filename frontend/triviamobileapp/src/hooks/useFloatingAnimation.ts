// src/hooks/useFloatingAnimation.ts
import { useRef, useEffect } from 'react';
import { Animated, Easing } from 'react-native';

export const useFloatingAnimation = (
  duration = 1500,
  displacement = 10
) => {
  const floatAnim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    const createAnimation = (toValue: number) => {
      return Animated.timing(floatAnim, {
        toValue,
        duration,
        easing: Easing.inOut(Easing.sin),
        useNativeDriver: true,
      });
    };

    Animated.loop(
      Animated.sequence([
        createAnimation(1),
        createAnimation(0),
      ])
    ).start();
    
    return () => {
      floatAnim.stopAnimation();
    };
  }, [floatAnim, duration]);
  
  return floatAnim;
};