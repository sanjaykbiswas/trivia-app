// src/pages/RoleSelect.tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Anchor, User, UserPlus } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormField, FormItem, FormLabel } from '@/components/ui/form';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';

interface RoleFormValues {
  role: 'captain' | 'scallywag';
  gameCode?: string;
}

const RoleSelect: React.FC = () => {
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState<'captain' | 'scallywag' | null>(null);

  const form = useForm<RoleFormValues>({
    defaultValues: {
      role: 'captain', // Default to Captain selection visually
      gameCode: '',
    },
  });

  const onSubmit = (data: RoleFormValues) => {
    if (data.role === 'captain') {
      // Captain Flow: Generate code, navigate to GameSelect
      const gameCode = Math.random().toString(36).substring(2, 8).toUpperCase();
      navigate(`/crew/captain?gameCode=${gameCode}`); // Captain goes to setup
      toast(`Game code: ${gameCode}`, {
        description: "Share this code with your crew!",
      });
    } else { // Scallywag Flow
      // Validate game code
      if (!data.gameCode || data.gameCode.length < 4) { // Keep validation
        toast("Please enter a valid game code", {
          description: "Ask your Captain for the code",
        });
        return;
      }

      // --- CHANGE HERE ---
      // Navigate Scallywag DIRECTLY to Waiting Room
      navigate(`/crew/waiting/scallywag?gameCode=${data.gameCode.toUpperCase()}`);
      // No need for toast here, they are joining
    }
  };

  // Set initial role state based on defaultValues if needed for UI logic
  useState(() => {
      setSelectedRole(form.getValues('role'));
  })

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <Link to="/" className="flex items-center text-pirate-navy hover:text-pirate-accent mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          <span>Back to Home</span>
        </Link>

        <div className="map-container p-6 md:p-8 mb-10 max-w-md mx-auto">
          <h1 className="pirate-heading text-3xl md:text-4xl mb-3 text-center">Join a Crew</h1>
          <p className="text-pirate-navy/80 mb-8 text-center">Choose your role in this voyage!</p>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem className="space-y-3">
                    <FormControl>
                      <RadioGroup
                        onValueChange={(value: 'captain' | 'scallywag') => {
                          field.onChange(value);
                          setSelectedRole(value); // Update local state for UI changes
                        }}
                        defaultValue={field.value}
                        className="grid grid-cols-1 gap-4"
                      >
                        {/* Captain Card */}
                        <Card className={`p-4 cursor-pointer transition-all ${
                          field.value === 'captain'
                            ? 'border-pirate-gold shadow-md bg-gradient-to-r from-pirate-navy to-pirate-navy/90 text-white'
                            : 'border-pirate-navy/20 hover:border-pirate-navy/50'
                        }`}>
                           <div className="flex items-start space-x-3">
                             <RadioGroupItem
                               value="captain"
                               id="captain"
                               className={`mt-1 ${field.value === 'captain' ? 'border-white text-white focus-visible:ring-pirate-gold' : 'focus-visible:ring-pirate-gold'}`}
                             />
                             <FormLabel htmlFor="captain" className="flex-1 cursor-pointer">
                               <div className="flex items-center mb-1">
                                 <Anchor className={`h-5 w-5 mr-2 ${field.value === 'captain' ? 'text-pirate-gold' : 'text-pirate-navy'}`} />
                                 <span className="font-bold text-lg">Captain</span>
                               </div>
                               <p className={`text-sm ${field.value === 'captain' ? 'text-white/80' : 'text-pirate-navy/70'}`}>
                                 Create a new game and invite your crew.
                               </p>
                             </FormLabel>
                           </div>
                         </Card>

                        {/* Scallywag Card */}
                         <Card className={`p-4 cursor-pointer transition-all ${
                           field.value === 'scallywag'
                             ? 'border-pirate-gold shadow-md bg-gradient-to-r from-pirate-navy to-pirate-navy/90 text-white'
                             : 'border-pirate-navy/20 hover:border-pirate-navy/50'
                         }`}>
                           <div className="flex items-start space-x-3">
                             <RadioGroupItem
                               value="scallywag"
                               id="scallywag"
                               className={`mt-1 ${field.value === 'scallywag' ? 'border-white text-white focus-visible:ring-pirate-gold' : 'focus-visible:ring-pirate-gold'}`}
                             />
                             <FormLabel htmlFor="scallywag" className="flex-1 cursor-pointer">
                               <div className="flex items-center mb-1">
                                 <User className={`h-5 w-5 mr-2 ${field.value === 'scallywag' ? 'text-pirate-gold' : 'text-pirate-navy'}`} />
                                 <span className="font-bold text-lg">Scallywag</span>
                               </div>
                               <p className={`text-sm ${field.value === 'scallywag' ? 'text-white/80' : 'text-pirate-navy/70'}`}>
                                 Join an existing game with a game code.
                               </p>
                             </FormLabel>
                           </div>
                         </Card>
                      </RadioGroup>
                    </FormControl>
                  </FormItem>
                )}
              />

              {/* Show Game Code input only when Scallywag is selected */}
              {selectedRole === 'scallywag' && (
                <FormField
                  control={form.control}
                  name="gameCode"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Game Code</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Enter the Captain's code"
                          className="text-center uppercase tracking-widest" // Make code stand out
                          maxLength={6} // Standard length
                          {...field}
                          onChange={(e) => field.onChange(e.target.value.toUpperCase())} // Force uppercase
                          autoComplete="off"
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              )}

              <div className="pt-4">
                <PirateButton
                  type="submit"
                  className="w-full"
                  icon={selectedRole === 'captain' ? <Anchor className="h-5 w-5" /> : <UserPlus className="h-5 w-5" />}
                >
                  {selectedRole === 'captain' ? 'Create Game' : 'Join Game'}
                </PirateButton>
              </div>
            </form>
          </Form>
        </div>
      </main>

      <footer className="ocean-bg py-8">
        <div className="container mx-auto text-center text-white relative z-10">
          <p className="font-pirate text-xl mb-2">Choose yer role, matey!</p>
          <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
};

export default RoleSelect;