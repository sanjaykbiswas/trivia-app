import React, { useMemo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  Platform,
  Dimensions,
  Alert,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import LinearGradient from 'react-native-linear-gradient';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withSequence,
  withDelay,
  Easing,
} from 'react-native-reanimated';
import { normalize, spacing } from '../utils/scaling';
import LogoCard from '../components/LogoCard.tsx';

// Get screen dimensions
const { width, height } = Dimensions.get('window');

interface HomeScreenProps {
  navigation?: any;
}

const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  // Get safe area insets
  const insets = useSafeAreaInsets();
  
  // Animation values for buttons
  const joinButtonScale = useSharedValue(1);
  const hostButtonScale = useSharedValue(1);
  
  // Memoize the padding for the home indicator
  const bottomPadding = useMemo(() => Math.max(insets.bottom, 10), [insets.bottom]);
  
  // Button press animations
  const handleJoinPress = useCallback(() => {
    // Apply bounce animation
    joinButtonScale.value = withSequence(
      withSpring(0.9, { damping: 10, stiffness: 300 }),
      withDelay(100, withSpring(1, { damping: 15, stiffness: 200 }))
    );
    
    // Handle join game logic
    Alert.alert('Join Game', 'Enter game code to join a game');
  }, [joinButtonScale]);
  
  const handleHostPress = useCallback(() => {
    // Apply bounce animation
    hostButtonScale.value = withSequence(
      withSpring(0.9, { damping: 10, stiffness: 300 }),
      withDelay(100, withSpring(1, { damping: 15, stiffness: 200 }))
    );
    
    // Handle host game logic
    Alert.alert('Host Game', 'Create a new game and invite friends');
  }, [hostButtonScale]);
  
  // Animated styles for buttons
  const joinButtonStyle = useAnimatedStyle(() => ({
    transform: [{ scale: joinButtonScale.value }]
  }));
  
  const hostButtonStyle = useAnimatedStyle(() => ({
    transform: [{ scale: hostButtonScale.value }]
  }));
  
  return (
    <View style={styles.container}>
      <StatusBar
        barStyle="light-content"
        backgroundColor="transparent"
        translucent={true}
      />
      
      {/* Top section with gradient background and logo */}
      <LinearGradient
        colors={['#7B61FF', '#6154CD']}
        start={{x: 0, y: 0}}
        end={{x: 1, y: 1}}
        style={[styles.topSection, { paddingTop: insets.top || 10 }]}
      >
        {/* Navigation buttons */}
        <View style={styles.navButtons}>
          <TouchableOpacity
            style={styles.navButton}
            activeOpacity={0.8}
            onPress={() => console.log('Settings pressed')}
          >
            <Text style={styles.navButtonText}>⚙️</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.navButton}
            activeOpacity={0.8}
            onPress={() => console.log('Help pressed')}
          >
            <Text style={styles.navButtonText}>❓</Text>
          </TouchableOpacity>
        </View>
        
        {/* Logo card */}
        <View style={styles.logoContainer}>
          <LogoCard />
        </View>
      </LinearGradient>
      
      {/* Bottom section with buttons */}
      <View style={[styles.bottomSection, { paddingBottom: bottomPadding + spacing(20) }]}>
        <Animated.View style={[styles.buttonContainer, joinButtonStyle]}>
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={handleJoinPress}
            style={styles.touchableFullWidth}
          >
            <LinearGradient
              colors={['#7B61FF', '#6154CD']}
              start={{x: 0, y: 0}}
              end={{x: 1, y: 1}}
              style={styles.partyButton}
            >
              <Text style={styles.buttonText}>JOIN GAME</Text>
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>
        
        <Animated.View style={[styles.buttonContainer, hostButtonStyle]}>
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={handleHostPress}
            style={styles.touchableFullWidth}
          >
            <LinearGradient
              colors={['#FF4E9D', '#FF0076']}
              start={{x: 0, y: 0}}
              end={{x: 1, y: 1}}
              style={styles.partyButton}
            >
              <Text style={styles.buttonText}>HOST GAME</Text>
            </LinearGradient>
          </TouchableOpacity>
        </Animated.View>
        
        {/* Home indicator */}
        {Platform.OS === 'ios' && insets.bottom === 0 && (
          <View style={styles.homeIndicator} />
        )}
      </View>
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
  },
  bottomSection: {
    backgroundColor: 'white',
    height: '30%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'space-evenly',
    padding: spacing(20),
    position: 'relative',
    zIndex: 5,
    borderTopLeftRadius: spacing(30),
    borderTopRightRadius: spacing(30),
    marginTop: -spacing(30),
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: -spacing(10) },
        shadowOpacity: 0.1,
        shadowRadius: spacing(20),
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
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing(10),
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: spacing(4) },
        shadowOpacity: 0.2,
        shadowRadius: spacing(10),
      },
      android: {
        elevation: 4,
      },
    }),
  },
  navButtonText: {
    fontSize: normalize(24),
  },
  logoContainer: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -width * 0.4 }, { translateY: -width * 0.25 }],
    width: '80%',
    height: 'auto',
    zIndex: 4,
  },
  buttonContainer: {
    width: '100%',
    maxWidth: spacing(300),
    marginVertical: spacing(10),
  },
  partyButton: {
    width: '100%',
    borderRadius: spacing(30),
    padding: spacing(18),
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
    ...Platform.select({
      ios: {
        shadowColor: '#7B61FF',
        shadowOffset: { width: 0, height: spacing(8) },
        shadowOpacity: 0.3,
        shadowRadius: spacing(15),
      },
      android: {
        elevation: 8,
      },
    }),
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
    alignSelf: 'center',
    width: spacing(120),
    height: spacing(5),
    backgroundColor: '#000',
    borderRadius: spacing(3),
  },
  touchableFullWidth: {
    width: '100%',
  },
});

export default HomeScreen;