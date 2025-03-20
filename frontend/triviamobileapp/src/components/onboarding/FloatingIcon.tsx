import React, { useRef, useEffect } from 'react';
import { Animated, StyleSheet, View, Text, Easing } from 'react-native';
import { spacing, normalize } from '../../utils/scaling.ts';

interface FloatingIconProps {
  icon: string;
  primaryColor: string;
}

const FloatingIcon: React.FC<FloatingIconProps> = ({ icon, primaryColor }) => {
  const floatAnim = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    const createAnimation = (toValue: number) => {
      return Animated.timing(floatAnim, {
        toValue,
        duration: 1500,
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
  }, [floatAnim]);

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
                opacity: floatAnim.interpolate({
                  inputRange: [0, 0.5, 1],
                  outputRange: [0.2, 0.8, 0.2]
                })
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
                opacity: floatAnim.interpolate({
                  inputRange: [0, 0.5, 1],
                  outputRange: [0.8, 0.2, 0.8]
                })
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
                opacity: floatAnim.interpolate({
                  inputRange: [0, 0.5, 1],
                  outputRange: [0.4, 0.9, 0.4]
                })
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