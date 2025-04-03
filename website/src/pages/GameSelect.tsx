import React, { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, BookOpen, Globe, Lightbulb, Film, Dices, Users, Copy, Search, Music, Map, Trophy, Utensils, BriefcaseMedical, Building2, PenTool, Landmark, Languages, LucideIcon, Ship, BookText } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { toast } from 'sonner';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import GameSettings from '@/components/GameSettings';

interface CategoryCardProps {
  title: string;
  icon: React.ReactNode;
  description: string;
  onClick: () => void;
}

const CategoryCard: React.FC<CategoryCardProps> = ({ title, icon, description, onClick }) => {
  return (
    <div onClick={onClick} className="cursor-pointer">
      <Card className="h-full border-pirate-navy/20 hover:border-pirate-gold transition-colors p-6 flex flex-col items-center text-center hover:shadow-md">
        <div className="bg-pirate-navy/10 p-3 rounded-full mb-4">
          {icon}
        </div>
        <h3 className="font-pirate text-xl text-pirate-navy mb-2">{title}</h3>
        <p className="text-pirate-navy/70 text-sm">{description}</p>
      </Card>
    </div>
  );
};

interface Category {
  title: string;
  icon: React.ReactNode;
  description: string;
  slug: string;
  focuses: string[];
}

interface GameSelectProps {
  mode: 'solo' | 'crew';
}

const GameSelect: React.FC<GameSelectProps> = ({ mode }) => {
  const { role } = useParams<{ role?: string }>();
  const [searchParams] = useSearchParams();
  const gameCode = searchParams.get('gameCode');
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  
  useEffect(() => {
    if (mode === 'crew' && (!role || !gameCode)) {
      navigate('/crew');
    }
  }, [mode, role, gameCode, navigate]);

  const getPageTitle = () => {
    if (mode === 'solo') return 'Solo Journey';
    return '';
  };

  const getPageDescription = () => {
    if (mode === 'solo') return 'Test your knowledge on a solo adventure!';
    return '';
  };

  const getBackLink = () => {
    if (mode === 'solo') return '/';
    return '/crew';
  };

  const copyGameCodeToClipboard = () => {
    if (gameCode) {
      navigator.clipboard.writeText(gameCode)
        .then(() => {
          toast('Copied to clipboard', {
            description: 'Game code copied successfully!',
          });
        })
        .catch(() => {
          toast('Failed to copy', {
            description: 'Please try copying manually',
          });
        });
    }
  };

  const handleCategorySelect = (category: Category) => {
    setSelectedCategory(category);
  };

  const handleBackToCategories = () => {
    setSelectedCategory(null);
  };

  const navigateToWaitingRoom = (gameSettings: {
    numberOfQuestions: number;
    timePerQuestion: number;
    focus: string;
  }) => {
    if (selectedCategory) {
      navigate(
        `/${mode}/waiting${role ? `/${role}` : ''}?gameCode=${gameCode || ''}&category=${selectedCategory.slug}&questions=${gameSettings.numberOfQuestions}&time=${gameSettings.timePerQuestion}&focus=${gameSettings.focus}`
      );
    }
  };

  const categories: Category[] = [
    {
      title: "General Knowledge",
      icon: <Globe className="h-6 w-6 text-pirate-navy" />,
      description: "Test your knowledge across a variety of subjects.",
      slug: "general",
      focuses: ["General", "Trivia", "Facts", "World Records"]
    },
    {
      title: "History",
      icon: <BookOpen className="h-6 w-6 text-pirate-navy" />,
      description: "Voyage through time with historical questions.",
      slug: "history",
      focuses: ["General", "Ancient Civilizations", "World Wars", "Modern History", "American History"]
    },
    {
      title: "Science",
      icon: <Lightbulb className="h-6 w-6 text-pirate-navy" />,
      description: "Discover the mysteries of science and nature.",
      slug: "science",
      focuses: ["General", "Biology", "Chemistry", "Physics", "Astronomy"]
    },
    {
      title: "Entertainment",
      icon: <Film className="h-6 w-6 text-pirate-navy" />,
      description: "Questions about movies, TV, music, and more.",
      slug: "entertainment",
      focuses: ["General", "Movies", "Television", "Video Games", "Theater"]
    },
    {
      title: "Music",
      icon: <Music className="h-6 w-6 text-pirate-navy" />,
      description: "Test your knowledge of songs, artists, and melodies.",
      slug: "music",
      focuses: ["General", "Classical", "Rock", "Pop", "Hip-Hop", "Jazz"]
    },
    {
      title: "Geography",
      icon: <Map className="h-6 w-6 text-pirate-navy" />,
      description: "Navigate the world with questions about locations and landmarks.",
      slug: "geography",
      focuses: ["General", "Countries", "Capitals", "Landmarks", "Oceans & Rivers"]
    },
    {
      title: "Sports",
      icon: <Trophy className="h-6 w-6 text-pirate-navy" />,
      description: "Compete with questions about athletes, teams, and events.",
      slug: "sports",
      focuses: ["General", "Football", "Basketball", "Baseball", "Soccer", "Olympics"]
    },
    {
      title: "Food & Drink",
      icon: <Utensils className="h-6 w-6 text-pirate-navy" />,
      description: "Savor questions about culinary delights and beverages.",
      slug: "food",
      focuses: ["General", "Cuisine", "Drinks", "Cooking Techniques", "Famous Chefs"]
    },
    {
      title: "Medicine",
      icon: <BriefcaseMedical className="h-6 w-6 text-pirate-navy" />,
      description: "Diagnose your knowledge of health and medicine.",
      slug: "medicine",
      focuses: ["General", "Anatomy", "Diseases", "Medical History", "Treatments"]
    },
    {
      title: "Architecture",
      icon: <Building2 className="h-6 w-6 text-pirate-navy" />,
      description: "Build your knowledge of famous structures and designs.",
      slug: "architecture",
      focuses: ["General", "Ancient Structures", "Modern Buildings", "Architects", "Styles"]
    },
    {
      title: "Art",
      icon: <PenTool className="h-6 w-6 text-pirate-navy" />,
      description: "Paint a masterpiece with your art knowledge.",
      slug: "art",
      focuses: ["General", "Paintings", "Sculpture", "Photography", "Modern Art"]
    },
    {
      title: "Politics",
      icon: <Landmark className="h-6 w-6 text-pirate-navy" />,
      description: "Debate your knowledge of governments and political systems.",
      slug: "politics",
      focuses: ["General", "World Leaders", "Systems of Government", "Political History", "International Relations"]
    },
    {
      title: "Languages",
      icon: <Languages className="h-6 w-6 text-pirate-navy" />,
      description: "Translate your way through linguistic questions.",
      slug: "languages",
      focuses: ["General", "Etymology", "World Languages", "Grammar", "Language History"]
    },
    {
      title: "Maritime",
      icon: <Ship className="h-6 w-6 text-pirate-navy" />,
      description: "Set sail with questions about ships and the sea.",
      slug: "maritime",
      focuses: ["General", "Ships", "Navigation", "Sea Exploration", "Pirates"]
    },
    {
      title: "Literature",
      icon: <BookText className="h-6 w-6 text-pirate-navy" />,
      description: "Turn the page with questions about books and authors.",
      slug: "literature",
      focuses: ["General", "Classic Literature", "Modern Fiction", "Poetry", "Authors"]
    },
    {
      title: "Random Mix",
      icon: <Dices className="h-6 w-6 text-pirate-navy" />,
      description: "A treasure chest of questions from all categories.",
      slug: "random",
      focuses: ["General"]
    },
    {
      title: "Sports Trivia",
      icon: <Trophy className="h-6 w-6 text-pirate-navy" />,
      description: "Challenge yourself with sports facts and trivia.",
      slug: "sports-trivia",
      focuses: ["General", "Records", "Championships", "Player Facts", "Team Histories"]
    }
  ];

  const filteredCategories = categories.filter(category => 
    category.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    category.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          {!selectedCategory ? (
            <Link to={getBackLink()} className="flex items-center text-pirate-navy hover:text-pirate-accent">
              <ArrowLeft className="h-4 w-4 mr-2" />
              <span>Back</span>
            </Link>
          ) : (
            <button 
              onClick={handleBackToCategories}
              className="flex items-center text-pirate-navy hover:text-pirate-accent"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              <span>Back to Categories</span>
            </button>
          )}
          
          {mode === 'crew' && gameCode && (
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-2 text-pirate-navy" />
              <span className="text-sm font-mono bg-pirate-navy/10 px-2 py-1 rounded">
                {gameCode}
              </span>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button 
                      onClick={copyGameCodeToClipboard}
                      className="ml-2 p-1 text-pirate-navy hover:text-pirate-gold transition-colors rounded-full hover:bg-pirate-navy/10"
                      aria-label="Copy game code"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Copy game code</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          )}
        </div>
        
        <div className="map-container p-6 md:p-8 mb-10">
          {getPageTitle() && <h1 className="pirate-heading text-3xl md:text-4xl mb-3">{getPageTitle()}</h1>}
          {getPageDescription() && <p className="text-pirate-navy/80 mb-8">{getPageDescription()}</p>}
          
          {!selectedCategory ? (
            <>
              <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-pirate-navy/50" />
                <Input 
                  placeholder="Search categories..." 
                  className="pl-10 border-pirate-navy/20 focus-visible:ring-pirate-gold"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <ScrollArea className="h-[calc(100vh-300px)] pr-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredCategories.map((category, index) => (
                    <CategoryCard
                      key={index}
                      title={category.title}
                      icon={category.icon}
                      description={category.description}
                      onClick={() => handleCategorySelect(category)}
                    />
                  ))}
                  
                  {filteredCategories.length === 0 && (
                    <div className="col-span-full text-center py-10">
                      <p className="text-pirate-navy/60 text-lg">No categories match your search</p>
                      <p className="text-pirate-navy/40">Try a different search term</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </>
          ) : (
            <GameSettings 
              category={selectedCategory} 
              onSubmit={navigateToWaitingRoom}
              mode={mode}
              role={role}
            />
          )}
        </div>
      </main>
      
      <footer className="ocean-bg py-8">
        <div className="container mx-auto text-center text-white relative z-10">
          <p className="font-pirate text-xl mb-2">Choose yer category, matey!</p>
          <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
};

export default GameSelect;
