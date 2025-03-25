import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, TextInput, TouchableOpacity, Share } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { BackButton } from '../../components/navigation';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import Svg, { Path, Circle, Rect } from 'react-native-svg';

type GameSetupScreenProps = StackScreenProps<RootStackParamList, 'GameSetup'>;

// Define category option interface
interface CategoryOption {
  id: string;
  name: string;
  icon: React.ReactNode;
  selected?: boolean;
}

const GameSetupScreen: React.FC<GameSetupScreenProps> = ({ navigation }) => {
  // Generate a random room code (5 characters)
  const [roomCode] = useState(() => {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 5; i++) {
      result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return result;
  });

  // Categories state
  const [categories, setCategories] = useState<CategoryOption[]>([
    {
      id: 'general',
      name: 'General Knowledge',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Path d="M12 2a8 8 0 0 0-8 8v12l6.5-4 6.5 4V10a8 8 0 0 0-8-8z" />
        </Svg>
      ),
      selected: true,
    },
    {
      id: 'science',
      name: 'Science',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Circle cx="12" cy="12" r="8" />
          <Path d="M12 2v2M12 20v2M20 12h2M2 12h2M17.5 6.5l1.4-1.4M5.1 18.9l1.4-1.4M17.5 17.5l1.4 1.4M5.1 5.1l1.4 1.4" />
        </Svg>
      ),
    },
    {
      id: 'history',
      name: 'History',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Path d="M12 8v4l3 3" />
          <Circle cx="12" cy="12" r="10" />
        </Svg>
      ),
    },
    {
      id: 'geography',
      name: 'Geography',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Circle cx="12" cy="12" r="10" />
          <Path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10z" />
          <Path d="M2 12h20" />
        </Svg>
      ),
    },
    {
      id: 'entertainment',
      name: 'Entertainment',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Rect x="2" y="7" width="20" height="15" rx="2" ry="2" />
          <Path d="M17 2l-5 5-5-5" />
        </Svg>
      ),
    },
    {
      id: 'sports',
      name: 'Sports',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Path d="M19 7c0-3-2-5-5-5S9 4 9 7M12 12l9.1-1.2M12 12L2.9 9.8M12 12v10M6.5 14.2l-.9 3.8M18.9 16.8l-1.5 5.8" />
        </Svg>
      ),
    },
    {
      id: 'technology',
      name: 'Technology',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
          <Path d="M9 9h.01M15 9h.01M9 15h.01M15 15h.01M5 9h.01M19 9h.01M5 15h.01M19 15h.01" />
        </Svg>
      ),
    },
    {
      id: 'art',
      name: 'Art & Literature',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Path d="M12 19l7-7 3 3-7 7-3-3z" />
          <Path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" />
          <Path d="M2 2l7.586 7.586" />
          <Path d="M11 11L15.5 6.5" />
        </Svg>
      ),
    },
    {
      id: 'music',
      name: 'Music',
      icon: (
        <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <Path d="M9 18V5l12-2v13" />
          <Circle cx="6" cy="18" r="3" />
          <Circle cx="18" cy="16" r="3" />
        </Svg>
      ),
    }
  ]);

  // Custom category input state
  const [customCategory, setCustomCategory] = useState('');

  const handleBackPress = () => {
    navigation.goBack();
  };

  const handleCategoryPress = (id: string) => {
    setCategories(prevCategories => 
      prevCategories.map(category => ({
        ...category,
        selected: category.id === id ? !category.selected : category.selected
      }))
    );
  };

  const handleShareRoomCode = async () => {
    try {
      await Share.share({
        message: `Join my trivia game with room code: ${roomCode}`
      });
    } catch (error) {
      console.error('Error sharing room code:', error);
    }
  };

  const handleStartGame = () => {
    const selectedCategories = categories.filter(c => c.selected).map(c => c.name);
    console.log('Starting game with categories:', selectedCategories);
    // TODO: Navigate to game screen
    // navigation.navigate('GamePlay', { roomCode, categories: selectedCategories });
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
      backgroundColor={colors.background.default}
    >
      <ScrollView style={styles.scrollView}>
        <View style={styles.container}>
          <BackButton onPress={handleBackPress} />

          <View style={styles.header}>
            <Typography variant="heading1" style={styles.title}>
              Game Room
            </Typography>
          </View>

          <View style={styles.roomCodeSection}>
            <Typography variant="bodyMedium" style={styles.sectionLabel}>
              Room Code
            </Typography>
            <View style={styles.roomCodeContainer}>
              <Typography variant="heading2" style={styles.roomCode}>
                {roomCode}
              </Typography>
              <TouchableOpacity 
                style={styles.shareButton} 
                onPress={handleShareRoomCode}
              >
                <Svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <Path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                  <Path d="M16 6l-4-4-4 4" />
                  <Path d="M12 2v13" />
                </Svg>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.gameSettingsSection}>
            <Typography variant="heading2" style={styles.gameSettingsTitle}>
              Game Settings
            </Typography>
            
            <Typography variant="bodyLarge" style={styles.categoryTitle}>
              Popular Categories
            </Typography>
            
            <View style={styles.categoryGrid}>
              {categories.map((category) => (
                <TouchableOpacity
                  key={category.id}
                  style={[
                    styles.categoryItem,
                    category.selected && styles.categoryItemSelected
                  ]}
                  onPress={() => handleCategoryPress(category.id)}
                >
                  <View style={styles.categoryIcon}>
                    {category.icon}
                  </View>
                  <Typography 
                    variant="bodySmall" 
                    style={styles.categoryName}
                  >
                    {category.name}
                  </Typography>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.customCategorySection}>
              <Typography variant="bodyLarge" style={styles.categoryTitle}>
                Custom Category
              </Typography>
              
              <TouchableOpacity style={styles.customCategoryButton}>
                <Svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9370DB" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <Path d="M12 5v14M5 12h14" />
                </Svg>
                <Typography 
                  variant="bodyMedium" 
                  color="#9370DB"
                  style={styles.customCategoryButtonText}
                >
                  Create Your Own Category!
                </Typography>
              </TouchableOpacity>

              <TextInput
                style={styles.customCategoryInput}
                placeholder="Enter any topic (e.g., 'Marvel Movies', 'Classic Cars'...)"
                placeholderTextColor={colors.gray[400]}
                value={customCategory}
                onChangeText={setCustomCategory}
              />
            </View>
          </View>
        </View>
      </ScrollView>

      <View style={styles.bottomButtons}>
        <Button
          title="Start Game"
          onPress={handleStartGame}
          variant="contained"
          size="large"
          fullWidth
          style={styles.startButton}
        />
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
  },
  container: {
    flex: 1,
    padding: spacing.page,
    paddingTop: spacing.xxl + spacing.md, // Extra padding for back button
  },
  header: {
    marginBottom: spacing.lg,
    alignItems: 'center',
  },
  title: {
    marginTop: spacing.md,
    color: colors.text.primary,
  },
  roomCodeSection: {
    marginBottom: spacing.xl,
  },
  sectionLabel: {
    marginBottom: spacing.xs,
    textAlign: 'center',
    color: colors.text.primary,
  },
  roomCodeContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.gray[100],
    borderRadius: 12,
    padding: spacing.md,
  },
  roomCode: {
    flex: 1,
    textAlign: 'center',
    letterSpacing: 2,
    color: '#9370DB', // Purple color for room code
  },
  shareButton: {
    padding: spacing.sm,
    borderRadius: 50,
    backgroundColor: colors.background.default,
  },
  gameSettingsSection: {
    marginBottom: spacing.xl,
  },
  gameSettingsTitle: {
    marginBottom: spacing.lg,
    textAlign: 'center',
    color: '#9370DB', // Purple for game settings title
  },
  categoryTitle: {
    marginBottom: spacing.md,
    color: colors.text.primary,
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: spacing.xl,
  },
  categoryItem: {
    width: '30%',
    aspectRatio: 1,
    backgroundColor: colors.gray[100],
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.sm,
    marginBottom: spacing.md,
  },
  categoryItemSelected: {
    backgroundColor: '#E6E0FA', // Light purple background for selected items
    borderWidth: 2,
    borderColor: '#9370DB',
  },
  categoryIcon: {
    marginBottom: spacing.xs,
  },
  categoryName: {
    textAlign: 'center',
    color: colors.text.primary,
  },
  customCategorySection: {
    marginBottom: spacing.md,
  },
  customCategoryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 2,
    borderColor: '#9370DB',
    borderRadius: 12,
    borderStyle: 'dashed',
  },
  customCategoryButtonText: {
    marginLeft: spacing.sm,
  },
  customCategoryInput: {
    backgroundColor: colors.gray[100],
    borderRadius: 16,
    padding: spacing.md,
    fontSize: 16,
    color: colors.text.primary,
  },
  bottomButtons: {
    padding: spacing.page,
    paddingBottom: spacing.page,
  },
  startButton: {
    backgroundColor: '#9370DB', // Purple button
  },
});

export default GameSetupScreen;