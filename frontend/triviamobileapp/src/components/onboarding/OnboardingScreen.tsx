import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  Dimensions,
  Platform,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { normalize, spacing } from '../../utils/scaling';
import FloatingElements from './FloatingElements';
import FloatingIcon from './FloatingIcon';

const { width } = Dimensions.get('window');

export interface OnboardingScreenProps {
    // Content props
    icon: string;
    title: string;
    subtitle: string;
    
    // Style props
    primaryColor: string;
    secondaryColor: string;
    
    // Navigation props
    currentStep: number;
    totalSteps: number;
    onContinue: () => void;
    
    // Optional props
    buttonText?: string;
    floatingEmojis?: Array<{
      emoji: string;
      position: {
        top?: string | number;
        bottom?: string | number;
        left?: string | number;
        right?: string | number;
      }
    }>;
    
    // Added prop to control pagination visibility
    paginationVisibility?: boolean;
  }

const OnboardingScreen: React.FC<OnboardingScreenProps> = ({
  icon,
  title,
  subtitle,
  primaryColor,
  secondaryColor,
  currentStep,
  totalSteps,
  onContinue,
  buttonText = "Continue",
  floatingEmojis = [
    {emoji: '❓', position: {top: '15%', left: '10%'}},
    {emoji: '💡', position: {top: '25%', right: '10%'}},
    {emoji: '🧠', position: {bottom: '30%', left: '15%'}},
    {emoji: '🎓', position: {bottom: '25%', right: '20%'}}
  ],
  paginationVisibility = true
}) => {
  const insets = useSafeAreaInsets();
  
  // Generate dots for pagination
  const renderPaginationDots = () => {
    const dots = [];
    for (let i = 0; i < totalSteps; i++) {
      dots.push(
        <View 
          key={i} 
          style={[
            styles.dot, 
            i === currentStep ? 
              [styles.activeDot, {backgroundColor: primaryColor}] : 
              null
          ]} 
        />
      );
    }
    return dots;
  };

  return (
    <View style={styles.container}>
      <StatusBar 
        barStyle="dark-content" 
        backgroundColor="#f8f9ff" 
        translucent={Platform.OS === 'android'}
      />
      
      <View style={styles.backgroundFill} />
      
      <FloatingElements 
        elements={floatingEmojis}
      />
      
      <SafeAreaView edges={['right', 'left', 'top']} style={styles.safeContainer}>
        <View style={styles.mainContent}>
          <FloatingIcon 
            icon={icon}
            primaryColor={primaryColor}
          />
          
          <Text style={[styles.title, {color: primaryColor}]}>{title}</Text>
          <Text style={styles.subtitle}>{subtitle}</Text>
          
          {/* Only render pagination dots if paginationVisibility is true */}
          {paginationVisibility && (
            <View style={styles.pagination}>
              {renderPaginationDots()}
            </View>
          )}
        </View>
      </SafeAreaView>

      <View 
        style={[
          styles.buttonContainer, 
          { 
            paddingBottom: Math.max(insets.bottom, spacing(20)),
            paddingTop: spacing(20) 
          }
        ]}
      >
        <TouchableOpacity
          style={styles.touchableWrapper}
          activeOpacity={0.8}
          onPress={onContinue}
        >
          <LinearGradient
            colors={[primaryColor, secondaryColor]}
            start={{x: 0, y: 0}}
            end={{x: 1, y: 1}}
            style={styles.gradientButton}
          >
            <Text style={styles.buttonText}>{buttonText}</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9ff',
  },
  backgroundFill: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#f8f9ff',
  },
  safeContainer: {
    flex: 1,
  },
  mainContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing(20),
  },
  title: {
    fontSize: normalize(32),
    fontWeight: '800',
    marginBottom: spacing(20),
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subtitle: {
    fontSize: normalize(18),
    textAlign: 'center',
    color: '#555',
    marginBottom: spacing(60),
    maxWidth: width * 0.8,
    lineHeight: normalize(24),
  },
  pagination: {
    flexDirection: 'row',
    marginBottom: spacing(40),
  },
  dot: {
    width: spacing(10),
    height: spacing(10),
    borderRadius: spacing(5),
    backgroundColor: '#ddd',
    marginHorizontal: spacing(6),
  },
  activeDot: {
    transform: [{ scale: 1.2 }],
  },
  buttonContainer: {
    width: '100%',
    paddingHorizontal: spacing(20),
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9ff',
  },
  touchableWrapper: {
    width: '100%',
    alignItems: 'center',
  },
  gradientButton: {
    width: '100%',
    maxWidth: spacing(320),
    height: spacing(60),
    borderRadius: spacing(30),
    alignItems: 'center',
    justifyContent: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#7B61FF',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.5,
        shadowRadius: 15,
      },
      android: {
        elevation: 8,
      }
    }),
  },
  buttonText: {
    color: 'white',
    fontSize: normalize(20),
    fontWeight: 'bold',
    textAlign: 'center',
  },
});

export default OnboardingScreen;