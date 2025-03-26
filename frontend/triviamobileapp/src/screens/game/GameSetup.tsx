import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, ScrollView, Share, TouchableOpacity, ScrollView as RNScrollView } from 'react-native';
import { StackScreenProps } from '@react-navigation/stack';
import { Container, Typography, Button } from '../../components/common';
import { PageTitle, BottomActions } from '../../components/layout';
import { Header } from '../../components/navigation';
import { ShareableCode, CategoryBubble, PackCard, SectionHeader } from '../../components/game';
import { colors, spacing } from '../../theme';
import { RootStackParamList } from '../../navigation/types';

type GameSetupScreenProps = StackScreenProps<RootStackParamList, 'GameSetup'>;

// Define category types
type CategoryType = 'All' | 'My Packs' | 'Popular' | 'Free' | 'Shop';

// Mock data for packs
const myPacks = [
  { id: 'mp1', title: 'Geography Expert', variant: 'myPack' },
  { id: 'mp2', title: 'Geography Buff', variant: 'myPack' },
  { id: 'mp3', title: 'Odds and Ends', variant: 'myPack' },
  { id: 'mp4', title: 'Science Quiz', variant: 'myPack' },
];

const freshPacks = [
  { id: 'fp1', title: 'Shabirky Quiz', author: 'shabirky', variant: 'freshPack' },
  { id: 'fp2', title: 'Do you even know Aiden?', author: 'Aiden_Galbraith_', variant: 'freshPack' },
  { id: 'fp3', title: 'Meeee', author: 'Alyssa', variant: 'freshPack' },
  { id: 'fp4', title: 'Fun Facts', author: 'Jasmine', variant: 'freshPack' },
];

const popularPacks = [
  { id: 'pp1', title: 'Pop Culture', variant: 'popularPack' },
  { id: 'pp2', title: 'Movie Trivia', variant: 'popularPack' },
  { id: 'pp3', title: 'Sports', variant: 'popularPack' },
  { id: 'pp4', title: 'Music Legends', variant: 'popularPack' },
];

const freePacks = [
  { id: 'frp1', title: 'General Knowledge', variant: 'freePack' },
  { id: 'frp2', title: 'Science', variant: 'freePack' },
  { id: 'frp3', title: 'History', variant: 'freePack' },
  { id: 'frp4', title: 'Food & Drink', variant: 'freePack' },
];

const shopPacks = [
  { id: 'sp1', title: 'Premium Quiz', variant: 'shopPack' },
  { id: 'sp2', title: 'Movie Masters', variant: 'shopPack' },
  { id: 'sp3', title: 'Sports Elite', variant: 'shopPack' },
  { id: 'sp4', title: 'Brain Teasers', variant: 'shopPack' },
];

/**
 * GameSetupScreen component
 * Allows users to configure game settings and select packs before starting a game
 */
const GameSetupScreen: React.FC<GameSetupScreenProps> = ({ navigation }) => {
  // Active category state
  const [activeCategory, setActiveCategory] = useState<CategoryType>('All');
  
  // Generate a random 6-digit room code
  const [roomCode] = useState(() => {
    // Generate a random 6-digit number as a string
    const min = 100000; // Smallest 6-digit number
    const max = 999999; // Largest 6-digit number
    return Math.floor(min + Math.random() * (max - min + 1)).toString();
  });

  const [copySuccess, setCopySuccess] = useState(false);
  
  // References
  const categoriesScrollViewRef = useRef<RNScrollView>(null);

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

  const handlePackPress = (packId: string) => {
    console.log(`Pack selected: ${packId}`);
    // TODO: Handle pack selection
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
    packs: { id: string; title: string; variant: string; author?: string }[],
    variant: 'myPack' | 'freshPack' | 'popularPack' | 'freePack' | 'shopPack'
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
            variant={variant as any}
            onPress={() => handlePackPress(pack.id)}
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
          {/* My Packs Section */}
          {shouldShowSection('My Packs') && (
            <View style={styles.section}>
              <SectionHeader title="My Packs" testID="section-my-packs" />
              {renderPackRow(myPacks, 'myPack')}
            </View>
          )}

          {/* Fresh Packs Section */}
          {shouldShowSection('Popular') && (
            <View style={styles.section}>
              <SectionHeader title="Fresh Packs" testID="section-fresh-packs" />
              {renderPackRow(freshPacks, 'freshPack')}
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
              {renderPackRow(freePacks, 'freePack')}
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
});

export default GameSetupScreen;