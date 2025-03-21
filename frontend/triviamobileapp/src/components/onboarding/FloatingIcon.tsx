import React, { useRef, useEffect } from 'react';
import { Animated, StyleSheet, View, Text, Easing } from 'react-native';
import { spacing, normalize } from '../../utils/scaling';

interface FloatingIconProps {
  icon: string;
  primaryColor: string;
}

const FloatingIcon: React.FC<FloatingIconProps> = ({ icon, primaryColor }) => {
  // Animation value for the main floating effect
  const floatAnim = useRef(new Animated.Value(0)).current;
  
  // Animation values for the sparkles
  const sparkle1Anim = useRef(new Animated.Value(0)).current;
  const sparkle2Anim = useRef(new Animated.Value(0)).current;
  const sparkle3Anim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    // Create the looping animation for the icon
    const createFloatAnimation = () => {
      Animated.loop(
        Animated.sequence([
          Animated.timing(floatAnim, {
            toValue: 1,
            duration: 1500,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(floatAnim, {
            toValue: 0,
            duration: 1500,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      ).start();
    };
    
    // Create animations for the sparkles with different durations
    const createSparkleAnimation = (
      animValue: Animated.Value, 
      duration: number, 
      delay: number = 0
    ) => {
      Animated.loop(
        Animated.sequence([
          Animated.timing(animValue, {
            toValue: 1,
            duration: duration,
            delay: delay,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(animValue, {
            toValue: 0,
            duration: duration,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      ).start();
    };
    
    // Start all animations
    createFloatAnimation();
    createSparkleAnimation(sparkle1Anim, 2000);
    createSparkleAnimation(sparkle2Anim, 2500, 500);
    createSparkleAnimation(sparkle3Anim, 1800, 1000);
    
    // Return cleanup function to stop animations
    return () => {
      floatAnim.stopAnimation();
      sparkle1Anim.stopAnimation();
      sparkle2Anim.stopAnimation();
      sparkle3Anim.stopAnimation();
    };
  }, [floatAnim, sparkle1Anim, sparkle2Anim, sparkle3Anim]);

  // Movement transform for the floating effect
  const floatTransform = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -spacing(10)],
  });

  return (
    <Animated.View 
      style={[
        styles.iconContainer, 
        { 
          transform: [{ translateY: floatTransform }],
          backgroundColor: `${primaryColor}20` // 12% opacity
        }
      ]}
    >
      <View style={[
        styles.iconInner,
        { backgroundColor: `${primaryColor}40` } // 25% opacity
      ]}>
        <View style={[
          styles.icon,
          { backgroundColor: primaryColor }
        ]}>
          <Animated.View 
            style={[
              styles.sparkle, 
              { 
                width: spacing(8), 
                height: spacing(8), 
                top: '20%', 
                left: '20%',
                opacity: sparkle1Anim,
              }
            ]} 
          />
          <Animated.View 
            style={[
              styles.sparkle, 
              { 
                width: spacing(6), 
                height: spacing(6), 
                top: '30%', 
                right: '20%',
                opacity: sparkle2Anim,
              }
            ]} 
          />
          <Animated.View 
            style={[
              styles.sparkle, 
              { 
                width: spacing(10), 
                height: spacing(10), 
                bottom: '20%', 
                right: '30%',
                opacity: sparkle3Anim,
              }
            ]} 
          />
          <Text style={styles.iconText}>{icon}</Text>
        </View>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  iconContainer: {
    width: spacing(160),
    height: spacing(160),
    borderRadius: spacing(80),
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing(40),
  },
  iconInner: {
    width: spacing(130),
    height: spacing(130),
    borderRadius: spacing(65),
    justifyContent: 'center',
    alignItems: 'center',
  },
  icon: {
    width: spacing(100),
    height: spacing(100),
    borderRadius: spacing(50),
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  iconText: {
    fontSize: normalize(40),
  },
  sparkle: {
    position: 'absolute',
    borderRadius: spacing(25),
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
  },
});

export default FloatingIcon;