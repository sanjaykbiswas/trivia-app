// src/screens/HomeScreen.tsx
import React, { useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  Platform,
  Animated,
  Easing,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { normalize, spacing } from '../utils/scaling';
import LinearGradientCircle from '../components/LinearGradientCircle';

interface HomeScreenProps {
  onJoinGame?: () => void;
  onHostGame?: () => void;
}

const { width, height } = Dimensions.get('window');

const characters = [
  { emoji: '🦊', colors: ['#FFC107', '#FF9800'], size: 100 },
  { emoji: '🦉', colors: ['#FF4E9D', '#FF0076'], size: 120 },
  { emoji: '🐙', colors: ['#00E5E8', '#00BCD4'], size: 90 },
  { emoji: '🦄', colors: ['#76FF03', '#64DD17'], size: 90 },
];

const positions = [
  { bottom: '15%', left: '5%' },
  { top: '20%', right: '8%' },
  { bottom: '8%', right: '12%' },
  { top: '40%', left: '8%' },
];

const animationConfig = {
  duration: 8000,
  easing: Easing.inOut(Easing.sin),
  useNativeDriver: true,
};

const HomeScreen: React.FC<HomeScreenProps> = ({
  onJoinGame = () => console.log('Join game pressed'),
  onHostGame = () => console.log('Host game pressed'),
}) => {
  const insets = useSafeAreaInsets();
  
  // Animation values with initial values
  const logoAnimation = useRef(new Animated.Value(0)).current;
  const circleAnimations = useRef(
    characters.map(() => new Animated.Value(0))
  ).current;
  const blobAnimation1 = useRef(new Animated.Value(0)).current;
  const blobAnimation2 = useRef(new Animated.Value(0)).current;
  const emojiAnimation = useRef(new Animated.Value(0)).current;
  
  // Track mount state to prevent animations after unmount
  const isMounted = useRef(true);
  
  // Animation timeouts refs for cleanup
  const timeoutRefs = useRef<NodeJS.Timeout[]>([]);
  
  // Store animation handles for cleanup
  const animationHandles = useRef<Animated.CompositeAnimation[]>([]);
  
  useEffect(() => {
    // For cleanup - set mounted flag
    isMounted.current = true;
    
    // Initialize with a staggered approach - with increased delay
    const initialDelay = 500; // Increased initial delay for component to fully mount
    
    // Logo animation
    const logoAnimationTimeout = setTimeout(() => {
      if (!isMounted.current) return;
      
      const logoAnim = Animated.loop(
        Animated.sequence([
          Animated.timing(logoAnimation, {
            toValue: 1,
            ...animationConfig,
          }),
          Animated.timing(logoAnimation, {
            toValue: 0,
            ...animationConfig,
          }),
        ])
      );
      
      logoAnim.start();
      animationHandles.current.push(logoAnim);
    }, initialDelay);
    
    timeoutRefs.current.push(logoAnimationTimeout);

    // Circle animations with staggered start
    circleAnimations.forEach((anim, index) => {
      const circleTimeout = setTimeout(() => {
        if (!isMounted.current) return;
        
        const circleAnim = Animated.loop(
          Animated.sequence([
            Animated.timing(anim, {
              toValue: 1,
              duration: 6000 + (index * 1000), // Staggered durations
              easing: Easing.inOut(Easing.sin),
              useNativeDriver: true,
            }),
            Animated.timing(anim, {
              toValue: 0,
              duration: 6000 + (index * 1000),
              easing: Easing.inOut(Easing.sin),
              useNativeDriver: true,
            }),
          ])
        );
        
        circleAnim.start();
        animationHandles.current.push(circleAnim);
      }, initialDelay + (index * 150)); // Increased stagger
      
      timeoutRefs.current.push(circleTimeout);
    });

    // Blob animations - start after circles
    const blobTimeout = setTimeout(() => {
      if (!isMounted.current) return;
      
      const blobAnim1 = Animated.loop(
        Animated.sequence([
          Animated.timing(blobAnimation1, {
            toValue: 1,
            duration: 10000,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(blobAnimation1, {
            toValue: 0,
            duration: 10000,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      );
      
      const blobAnim2 = Animated.loop(
        Animated.sequence([
          Animated.timing(blobAnimation2, {
            toValue: 1,
            duration: 12000,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(blobAnimation2, {
            toValue: 0,
            duration: 12000,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      );
      
      blobAnim1.start();
      blobAnim2.start();
      animationHandles.current.push(blobAnim1, blobAnim2);
    }, initialDelay + 600); // Increased delay
    
    timeoutRefs.current.push(blobTimeout);

    // Emoji animation - start last
    const emojiTimeout = setTimeout(() => {
      if (!isMounted.current) return;
      
      const emojiAnim = Animated.loop(
        Animated.timing(emojiAnimation, {
          toValue: 1,
          duration: 15000,
          easing: Easing.linear,
          useNativeDriver: true,
        })
      );
      
      emojiAnim.start();
      animationHandles.current.push(emojiAnim);
    }, initialDelay + 800); // Increased delay
    
    timeoutRefs.current.push(emojiTimeout);

    // Cleanup animations and timeouts on unmount
    return () => {
      // Set mounted flag to false to prevent starting new animations
      isMounted.current = false;
      
      // Clear all pending timeouts
      timeoutRefs.current.forEach(timeout => clearTimeout(timeout));
      
      // Stop all running animations
      animationHandles.current.forEach(anim => anim.stop());
      
      // Reset animation values
      [logoAnimation, ...circleAnimations, blobAnimation1, blobAnimation2, emojiAnimation].forEach(
        anim => anim.setValue(0)
      );
    };
  }, [logoAnimation, circleAnimations, blobAnimation1, blobAnimation2, emojiAnimation]);

  // Animated styles - fixed to ensure they're properly formatted
  const logoStyle = {
    transform: [
      {
        translateY: logoAnimation.interpolate({
          inputRange: [0, 1],
          outputRange: [0, -15],
        }),
      },
      {
        rotate: logoAnimation.interpolate({
          inputRange: [0, 1],
          outputRange: ['0deg', '5deg'],
        }),
      },
    ],
  };

  // Emoji rotation style
  const emojiStyle = {
    transform: [
      {
        rotate: emojiAnimation.interpolate({
          inputRange: [0, 1],
          outputRange: ['0deg', '360deg'],
        }),
      },
    ],
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#7B61FF', '#6154CD']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.topSection}
      >
        {/* Navigation buttons */}
        <View style={styles.navButtons}>
          <TouchableOpacity style={styles.navButton}>
            <Text style={styles.navButtonIcon}>⚙️</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.navButton, { marginLeft: spacing(10) }]}>
            <Text style={styles.navButtonIcon}>❓</Text>
          </TouchableOpacity>
        </View>
        
        {/* Decorative circles with characters - FIXED CODE */}
        {characters.map((character, index) => {
          // Create a plain object style for animation
          const animationStyle = {
            transform: [
              {
                translateY: circleAnimations[index].interpolate({
                  inputRange: [0, 1],
                  outputRange: [0, -20],
                }),
              },
            ],
          };
          
          // Extract position styles from positions array
          const positionStyle = positions[index];
          
          return (
            <Animated.View
              key={`circle-container-${index}`}
              style={[
                styles.decorativeCircle,
                positionStyle,
                animationStyle
              ]}
            >
              <LinearGradientCircle
                size={character.size}
                colors={character.colors}
              >
                <View style={styles.character}>
                  <Text style={styles.characterText}>{character.emoji}</Text>
                </View>
              </LinearGradientCircle>
            </Animated.View>
          );
        })}
        
        {/* Emoji */}
        <Animated.Text 
          style={[
            styles.emojiSmall,
            styles.emoji2,
            emojiStyle,
          ]}
        >
          🎯
        </Animated.Text>
        
        {/* Background blobs */}
        <Animated.View 
          style={[
            styles.blob1,
            {
              transform: [
                {
                  scale: blobAnimation1.interpolate({
                    inputRange: [0, 1],
                    outputRange: [1, 1.2],
                  }),
                },
                {
                  rotate: blobAnimation1.interpolate({
                    inputRange: [0, 1],
                    outputRange: ['0deg', '30deg'],
                  }),
                },
              ],
            },
          ]} 
        />
        <Animated.View 
          style={[
            styles.blob2,
            {
              transform: [
                {
                  scale: blobAnimation2.interpolate({
                    inputRange: [0, 1],
                    outputRange: [1, 1.3],
                  }),
                },
                {
                  rotate: blobAnimation2.interpolate({
                    inputRange: [0, 1],
                    outputRange: ['0deg', '-25deg'],
                  }),
                },
              ],
            },
          ]} 
        />
        
        {/* Logo */}
        <Animated.View style={[styles.logoContainer, logoStyle]}>
          <LinearGradient
            colors={['#333333', '#111111']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.logoCard}
          >
            <LinearGradient
              colors={['#00E5E8', '#FF00FF', '#FFC100']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.logoBorder}
            />
            <View style={styles.logoContent}>
              <Text style={styles.logoText}>open</Text>
              <Text style={styles.logoTextLarge}>trivia</Text>
            </View>
          </LinearGradient>
        </Animated.View>
      </LinearGradient>
      
      <View style={[
        styles.bottomSection,
        { paddingBottom: Math.max(insets.bottom, spacing(20)) }
      ]}>
        <TouchableOpacity
          style={styles.touchableWrapper}
          activeOpacity={0.8}
          onPress={onJoinGame}
        >
          <LinearGradient
            colors={['#7B61FF', '#6154CD']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.partyButton}
          >
            <Text style={styles.buttonText}>JOIN GAME</Text>
          </LinearGradient>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.touchableWrapper}
          activeOpacity={0.8}
          onPress={onHostGame}
        >
          <LinearGradient
            colors={['#FF4E9D', '#FF0076']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.partyButton}
          >
            <Text style={styles.buttonText}>HOST GAME</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
      
      {/* iOS Home Indicator */}
      {Platform.OS === 'ios' && (
        <View style={styles.homeIndicator} />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f8f8',
  },
  topSection: {
    height: '70%',
    position: 'relative',
    overflow: 'visible',
    padding: spacing(10),
    // Using a component rather than a style property
  },
  bottomSection: {
    height: '30%',
    backgroundColor: 'white',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'space-evenly',
    padding: spacing(20),
    position: 'relative',
    zIndex: 5,
    borderTopLeftRadius: spacing(30),
    borderTopRightRadius: spacing(30),
    marginTop: spacing(-30),
    // Shadow effect
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -10 },
        shadowOpacity: 0.1,
        shadowRadius: 20,
      },
      android: {
        elevation: 10,
      },
    }),
  },
  navButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    zIndex: 10,
    position: 'relative',
    padding: spacing(10),
  },
  navButton: {
    width: spacing(50),
    height: spacing(50),
    backgroundColor: 'white',
    borderRadius: spacing(25),
    alignItems: 'center',
    justifyContent: 'center',
    // Shadow effect
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 10,
      },
      android: {
        elevation: 5,
      },
    }),
  },
  navButtonIcon: {
    fontSize: normalize(24),
  },
  decorativeCircle: {
    position: 'absolute',
    overflow: 'hidden',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
    // Shadow effect
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 5 },
        shadowOpacity: 0.2,
        shadowRadius: 15,
      },
      android: {
        elevation: 8,
      },
    }),
  },
  character: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  characterText: {
    fontSize: normalize(50),
  },
  emojiSmall: {
    fontSize: normalize(30),
    position: 'absolute',
    zIndex: 3,
    // Shadow effect
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: 3 },
    textShadowRadius: 5,
  },
  emoji2: {
    bottom: '25%',
    right: '25%',
  },
  blob1: {
    position: 'absolute',
    width: spacing(300),
    height: spacing(300),
    backgroundColor: 'rgba(255, 0, 255, 0.5)',
    borderRadius: spacing(150),
    bottom: spacing(-150),
    left: spacing(-100),
    zIndex: 0,
    opacity: 0.5,
  },
  blob2: {
    position: 'absolute',
    width: spacing(350),
    height: spacing(350),
    backgroundColor: 'rgba(0, 229, 232, 0.5)',
    borderRadius: spacing(175),
    bottom: spacing(-200),
    right: spacing(-150),
    zIndex: 0,
    opacity: 0.5,
  },
  logoContainer: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: '80%',
    height: 'auto',
    zIndex: 4,
    transform: [
      { translateX: -width * 0.8 * 0.5 },
      { translateY: -100 }, // Approximately half the height
    ],
  },
  logoCard: {
    width: '100%',
    borderRadius: spacing(25),
    padding: spacing(25),
    // Shadow effect
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 15 },
        shadowOpacity: 0.5,
        shadowRadius: 35,
      },
      android: {
        elevation: 20,
      },
    }),
    paddingLeft: spacing(10), // Reduced left padding to move content left
    position: 'relative',
    overflow: 'hidden',
  },
  logoBorder: {
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    borderRadius: spacing(27),
    opacity: 0.7,
    zIndex: -1,
  },
  logoContent: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    justifyContent: 'center',
    marginLeft: spacing(15),
  },
  logoText: {
    color: 'white',
    fontSize: normalize(45),
    textAlign: 'left',
    fontWeight: '800',
    lineHeight: normalize(40),
    letterSpacing: -1,
    // Shadow effect
    textShadowColor: 'rgba(0,0,0,0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 10,
    paddingLeft: spacing(10),
  },
  logoTextLarge: {
    fontSize: normalize(72),
    fontWeight: '900',
    color: 'white',
    marginTop: spacing(-5),
    letterSpacing: -2,
    marginLeft: spacing(-8),
    // Extra thick black outline for better visibility
    textShadowColor: '#000',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 10,
  },
  touchableWrapper: {
    width: '100%',
    alignItems: 'center',
  },
  partyButton: {
    width: '100%',
    maxWidth: spacing(300),
    borderRadius: spacing(30),
    padding: spacing(18),
    alignItems: 'center',
    justifyContent: 'center',
    // Shadow effect
    ...Platform.select({
      ios: {
        shadowColor: 'rgba(123, 97, 255, 0.5)',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 1,
        shadowRadius: 15,
      },
      android: {
        elevation: 10,
      },
    }),
    overflow: 'hidden',
    position: 'relative',
  },
  buttonText: {
    color: 'white',
    fontSize: normalize(20),
    fontWeight: '800',
    textAlign: 'center',
  },
  homeIndicator: {
    position: 'absolute',
    bottom: spacing(5),
    left: '50%',
    width: spacing(120),
    height: spacing(5),
    backgroundColor: '#000',
    borderRadius: spacing(3),
    transform: [{ translateX: -spacing(60) }],
  },
});

export default HomeScreen;