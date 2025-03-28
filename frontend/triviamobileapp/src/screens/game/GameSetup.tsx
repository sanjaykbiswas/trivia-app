// frontend/triviamobileapp/src/screens/game/GameSetup.tsx
import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, ScrollView, Share, TouchableOpacity, ScrollView as RNScrollView, ActivityIndicator } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { PageTitle, BottomActions } from '../../components/layout';
import { Header } from '../../components/navigation';
import { ShareableCode, CategoryBubble, PackCard, SectionHeader } from '../../components/game';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';
import CategoryService, { Category } from '../../services/CategoryService';

type GameSetupScreenProps = StackScreenProps<RootStackParamList, 'GameSetup'>;

// Define category types
type CategoryType = 'All' | 'My Packs' | 'Popular' | 'Free' | 'Shop';

// Interface for pack data
interface Pack {
  id: string;
  title: string;
  variant: string;
  author?: string;
}

const GameSetupScreen: React.FC<GameSetupScreenProps> = ({ navigation }) => {
  // Active category state
  const [activeCategory, setActiveCategory] = useState<CategoryType>('All');
  
  // State for real categories from backend
  const [freeCategories, setFreeCategories] = useState<Pack[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Generate a random 6-digit room code
  const [roomCode] = useState(() => {
    // Generate a random 6-digit number as a string
    const min = 100000; // Smallest 6-digit number
    const max = 999999; // Largest 6-digit number
    return Math.floor(min + Math.random() * (max - min + 1)).toString();
  });

  const [copySuccess, setCopySuccess] = useState(false);
  
  // Create placeholder packs for other sections
  const myPacks = Array(5).fill(0).map((_, index) => ({
    id: `mp${index + 1}`,
    title: `Placeholder ${index + 1}`,
    variant: 'myPack'
  }));

  const popularPacks = Array(5).fill(0).map((_, index) => ({
    id: `pp${index + 1}`,
    title: `Placeholder ${index + 1}`,
    variant: 'popularPack'
  }));

  const shopPacks = Array(5).fill(0).map((_, index) => ({
    id: `sp${index + 1}`,
    title: `Placeholder ${index + 1}`,
    variant: 'shopPack'
  }));
  
  // References
  const categoriesScrollViewRef = useRef<RNScrollView>(null);

  // Fetch categories from backend on component mount
  useEffect(() => {
    fetchCategories();
  }, []);

  // Fetch categories from the backend
  const fetchCategories = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Fetching categories...');
      const categories = await CategoryService.getAllCategories();
      console.log('Fetched categories:', categories);
      
      if (!categories || categories.length === 0) {
        console.warn('No categories returned from service');
        setError('No categories found. The database might be empty.');
        setFreeCategories([]);
        return;
      }
      
      // Convert backend categories to pack format
      const freePacks = categories.map(category => ({
        id: category.id, // Use the category ID directly
        title: category.name,
        variant: 'freePack',
      }));
      
      console.log('Created free packs:', freePacks);
      setFreeCategories(freePacks);
    } catch (err) {
      console.error('Failed to fetch categories:', err);
      setError('Failed to load categories. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Reset copy success message after 3 seconds
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (copySuccess) {
      timer = setTimeout(() => {
        setCopySuccess(false);
      }, 3000);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [copySuccess]);

  const handleBackPress = () => {
    navigation.goBack();
  };

  const handleStartGame = () => {
    console.log('Creating packs with AI');
    // TODO: Navigate to appropriate screen
  };

  const handlePackPress = (packId: string, packTitle: string, variant: string) => {
    console.log(`Pack selected: ${packId}, ${packTitle}`);
    
    // Simplified pack data for navigation
    const packData = {
      packTitle: packTitle,
      categoryId: packId // Pass the category ID directly
    };
    
    // Navigate to GameOptions with pack data
    navigation.navigate('GameOptions', packData);
  };

  const handleCategoryPress = (category: CategoryType) => {
    setActiveCategory(category);
    // Optional: Scroll to relevant section
  };

  // Format the room code for sharing (including the hyphen)
  const formattedRoomCode = () => {
    if (roomCode.length === 6) {
      return `${roomCode.substring(0, 3)}-${roomCode.substring(3)}`;
    }
    return roomCode;
  };

  const handleShareCode = async () => {
    try {
      await Share.share({
        message: `Join my trivia game with room code: ${formattedRoomCode()}`
      });
      setCopySuccess(true);
    } catch (error) {
      console.error('Error sharing room code:', error);
    }
  };

  // Render a horizontal pack list
  const renderPackRow = (
    packs: Pack[],
    variant: 'myPack' | 'popularPack' | 'freePack' | 'shopPack'
  ) => {
    return (
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.packRow}
      >
        {packs.map((pack) => (
          <PackCard
            key={pack.id}
            title={pack.title}
            author={pack.author}
            variant={variant}
            onPress={() => handlePackPress(pack.id, pack.title, variant)}
            style={styles.packCard}
            testID={`pack-${pack.id}`}
          />
        ))}
      </ScrollView>
    );
  };

  // Filter content based on active category
  const shouldShowSection = (sectionCategory: string) => {
    if (activeCategory === 'All') return true;
    return activeCategory === sectionCategory;
  };

  return (
    <Container
      useSafeArea={true}
      statusBarColor={colors.background.default}
      statusBarStyle="dark-content"
      backgroundColor={colors.background.default}
    >
      <View style={styles.container}>
        <Header 
          showBackButton={true} 
          onBackPress={handleBackPress} 
        />

        <PageTitle title="Choose your pack" />

        {/* Category Filters */}
        <View style={styles.categoryWrapper}>
          <ScrollView
            ref={categoriesScrollViewRef}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoryContainer}
          >
            <CategoryBubble
              title="All"
              isActive={activeCategory === 'All'}
              onPress={() => handleCategoryPress('All')}
              testID="category-all"
            />
            <CategoryBubble
              title="My Packs"
              isActive={activeCategory === 'My Packs'}
              onPress={() => handleCategoryPress('My Packs')}
              testID="category-my-packs"
            />
            <CategoryBubble
              title="Popular"
              isActive={activeCategory === 'Popular'}
              onPress={() => handleCategoryPress('Popular')}
              testID="category-popular"
            />
            <CategoryBubble
              title="Free"
              isActive={activeCategory === 'Free'}
              onPress={() => handleCategoryPress('Free')}
              testID="category-free"
            />
            <CategoryBubble
              title="Shop"
              isActive={activeCategory === 'Shop'}
              onPress={() => handleCategoryPress('Shop')}
              testID="category-shop"
            />
          </ScrollView>
        </View>

        {/* Main Content */}
        <ScrollView 
          style={styles.scrollView} 
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollViewContent}
        >
          {/* Loading Indicator */}
          {loading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.primary.main} />
              <Typography variant="bodyMedium" style={styles.loadingText}>
                Loading categories...
              </Typography>
            </View>
          )}

          {/* Error Message */}
          {error && (
            <View style={styles.errorContainer}>
              <Typography variant="bodyMedium" color={colors.error.main} style={styles.errorText}>
                {error}
              </Typography>
              <Button
                title="Retry"
                onPress={fetchCategories}
                variant="outlined"
                size="small"
                style={styles.retryButton}
              />
            </View>
          )}

          {/* My Packs Section */}
          {shouldShowSection('My Packs') && (
            <View style={styles.section}>
              <SectionHeader title="My Packs" testID="section-my-packs" />
              {renderPackRow(myPacks, 'myPack')}
            </View>
          )}

          {/* Popular Packs Section */}
          {shouldShowSection('Popular') && (
            <View style={styles.section}>
              <SectionHeader title="Popular Packs" testID="section-popular-packs" />
              {renderPackRow(popularPacks, 'popularPack')}
            </View>
          )}

          {/* Free Packs Section */}
          {shouldShowSection('Free') && (
            <View style={styles.section}>
              <SectionHeader title="Free Packs" testID="section-free-packs" />
              {!loading && freeCategories.length > 0 ? (
                renderPackRow(freeCategories, 'freePack')
              ) : !loading && !error ? (
                <Typography variant="bodyMedium" style={styles.emptyText}>
                  No free packs available.
                </Typography>
              ) : null}
            </View>
          )}

          {/* Shop Section */}
          {shouldShowSection('Shop') && (
            <View style={styles.section}>
              <SectionHeader title="Shop" testID="section-shop" />
              {renderPackRow(shopPacks, 'shopPack')}
            </View>
          )}
        </ScrollView>

        <BottomActions>
          <Button
            title="Create Packs With AI"
            onPress={handleStartGame}
            variant="contained"
            size="large"
            fullWidth
            style={styles.startButton}
          />
          
          <ShareableCode 
            code={roomCode}
            onShare={handleShareCode}
            style={styles.shareableCode}
            testID="game-code-share"
          />
        </BottomActions>
      </View>
    </Container>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  categoryWrapper: {
    height: 40, // Fixed height for category section
    marginBottom: spacing.xs, // Reduced spacing
  },
  categoryContainer: {
    paddingHorizontal: spacing.page,
  },
  scrollView: {
    flex: 1,
  },
  scrollViewContent: {
    padding: spacing.page,
    paddingBottom: spacing.lg, // Reduced padding at bottom
  },
  section: {
    marginBottom: spacing.md, // Reduced from xl to md
  },
  packRow: {
    paddingBottom: spacing.xs,
  },
  packCard: {
    marginRight: spacing.md,
  },
  startButton: {
    backgroundColor: colors.primary.main,
    marginBottom: spacing.md,
  },
  shareableCode: {
    marginTop: 0, // Reset margin
  },
  loadingContainer: {
    padding: spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: spacing.md,
  },
  errorContainer: {
    padding: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  errorText: {
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: spacing.sm,
  },
  emptyText: {
    textAlign: 'center',
    padding: spacing.md,
  },
});

export default GameSetupScreen;