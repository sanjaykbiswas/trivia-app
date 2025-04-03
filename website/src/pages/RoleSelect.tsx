// src/pages/RoleSelect.tsx
// --- START OF MODIFIED FILE ---
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Anchor, User, UserPlus, Ship, Loader2 } from 'lucide-react';
import Header from '@/components/Header';
import PirateButton from '@/components/PirateButton';
import { Card } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
// --- IMPORT updateUser ---
import { createTemporaryUser, updateUser } from '@/services/userApi';
// --- END IMPORT updateUser ---
import { ApiUserResponse } from '@/types/apiTypes';
import { getPirateNameForUserId } from '@/utils/gamePlayUtils';

interface RoleFormValues {
  role: 'captain' | 'scallywag';
  gameCode?: string;
}

const RoleSelect: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<RoleFormValues>({
    defaultValues: {
      role: 'captain',
      gameCode: '',
    },
  });

  const selectedRole = form.watch('role');

  // --- MODIFIED onSubmit ---
  const onSubmit = async (data: RoleFormValues) => {
    setIsLoading(true);
    let user: ApiUserResponse | null = null;
    let userId: string | null = null;
    let assignedName: string | null = null;

    try {
      // --- Step 1: Create Temporary User (pass null for name) ---
      console.log(`Creating temporary user record...`);
      user = await createTemporaryUser(null); // Pass null for displayName initially
      console.log("Temporary user created (backend):", user);

      if (!user?.id) {
         throw new Error("Failed to get valid ID after user creation.");
      }
      userId = user.id; // Store the ID

      // --- Step 2: Assign and Store Name LOCALLY ---
      assignedName = getPirateNameForUserId(userId); // Assign name based on the retrieved ID
      console.log(`Assigned name '${assignedName}' to user ${userId}`);
      localStorage.setItem('tempUserId', userId);
      localStorage.setItem('tempUserDisplayName', assignedName); // Store the *assigned* name

      // --- Step 3: UPDATE User Record on BACKEND with the Assigned Name ---
      console.log(`Updating backend user record ${userId} with name '${assignedName}'...`);
      try {
          await updateUser(userId, { displayname: assignedName }); // Send update request
          console.log(`Successfully updated user ${userId} displayname on backend.`);
      } catch (updateError) {
          // Log the error but proceed - game creation might still work using fallback name
          console.error(`Failed to update user ${userId} displayname on backend:`, updateError);
          toast.warning("Name Update Failed", { description: "Could not save your pirate name to the server, using a default." });
      }

      // --- Step 4: Navigate Based on Role ---
      if (data.role === 'captain') {
        console.log("Navigating Captain to Game Select...");
        navigate(`/crew/captain`); // Proceed to game creation

      } else { // Scallywag Flow
        console.log("Validating game code and navigating Scallywag to Waiting Room...");
        if (!data.gameCode?.trim()) {
             toast.warning("Missing Game Code", { description: "Please provide the game code." });
             setIsLoading(false);
             return; // Stop execution
         }
         const gameCodeValue = data.gameCode.toUpperCase().trim();
         console.log(`Navigating Scallywag (User ID: ${userId}, Name: ${assignedName}) to Waiting Room for game code: ${gameCodeValue}`);
         // Scallywag will send their name during the join request anyway
         navigate(`/crew/waiting/scallywag?gameCode=${gameCodeValue}`);
      }

    } catch (error) {
      console.error("Error during role selection flow:", error);
      const action = data.role === 'captain' ? 'proceed' : 'continue';
      const baseMessage = `Failed to ${action}.`;
      let description = "An unknown error occurred.";
      if (error instanceof Error) {
          description = error.message.startsWith('Failed to')
              ? error.message
              : `${baseMessage} ${error.message}`;
      }
      toast.error("Action Failed", { description });
    } finally {
      setIsLoading(false);
    }
  };
  // --- END MODIFIED onSubmit ---

  // --- JSX (No changes needed from the previous version) ---
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8">
        <Link to="/" className="flex items-center text-pirate-navy hover:text-pirate-accent mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          <span>Back to Home</span>
        </Link>
        <div className="map-container p-6 md:p-8 mb-10 max-w-md mx-auto relative">
          <h1 className="pirate-heading text-3xl md:text-4xl mb-3 text-center">Join a Crew</h1>
          <p className="text-pirate-navy/80 mb-8 text-center">Choose your role in this voyage!</p>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              {/* Role Selection RadioGroup */}
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem className="space-y-3">
                    <FormControl>
                       <RadioGroup
                        onValueChange={field.onChange}
                        value={field.value}
                        className="grid grid-cols-1 gap-4"
                      >
                        {/* Captain Card */}
                        <FormLabel htmlFor="captain" className="cursor-pointer">
                            <Card className={`p-4 transition-all ${ field.value === 'captain' ? 'border-pirate-gold shadow-md bg-gradient-to-r from-pirate-navy to-pirate-navy/90 text-white' : 'border-pirate-navy/20 hover:border-pirate-navy/50' }`}>
                                <div className="flex items-start space-x-3">
                                    <RadioGroupItem value="captain" id="captain" className={`mt-1 ${field.value === 'captain' ? 'border-white text-white focus-visible:ring-pirate-gold' : 'focus-visible:ring-pirate-gold'}`}/>
                                    <div className="flex-1">
                                        <div className="flex items-center mb-1">
                                            <Anchor className={`h-5 w-5 mr-2 ${field.value === 'captain' ? 'text-pirate-gold' : 'text-pirate-navy'}`} />
                                            <span className="font-bold text-lg">Captain</span>
                                        </div>
                                        <p className={`text-sm ${field.value === 'captain' ? 'text-white/80' : 'text-pirate-navy/70'}`}> Start a new game and invite your crew. </p>
                                    </div>
                                </div>
                            </Card>
                        </FormLabel>
                        {/* Scallywag Card */}
                        <FormLabel htmlFor="scallywag" className="cursor-pointer">
                             <Card className={`p-4 transition-all ${ field.value === 'scallywag' ? 'border-pirate-gold shadow-md bg-gradient-to-r from-pirate-navy to-pirate-navy/90 text-white' : 'border-pirate-navy/20 hover:border-pirate-navy/50' }`}>
                               <div className="flex items-start space-x-3">
                                 <RadioGroupItem value="scallywag" id="scallywag" className={`mt-1 ${field.value === 'scallywag' ? 'border-white text-white focus-visible:ring-pirate-gold' : 'focus-visible:ring-pirate-gold'}`}/>
                                 <div className="flex-1">
                                   <div className="flex items-center mb-1">
                                     <User className={`h-5 w-5 mr-2 ${field.value === 'scallywag' ? 'text-pirate-gold' : 'text-pirate-navy'}`} />
                                     <span className="font-bold text-lg">Scallywag</span>
                                   </div>
                                   <p className={`text-sm ${field.value === 'scallywag' ? 'text-white/80' : 'text-pirate-navy/70'}`}> Join an existing game with a game code. </p>
                                 </div>
                               </div>
                             </Card>
                        </FormLabel>
                      </RadioGroup>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {/* Game Code Input (only for Scallywag) */}
              {selectedRole === 'scallywag' && (
                <div className="space-y-4 pt-2">
                  <FormField
                    control={form.control}
                    name="gameCode"
                    rules={{ required: "Need the Captain's code!", pattern: { value: /^[A-Z0-9]{6}$/, message: "Code must be 6 uppercase letters/numbers"} }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel htmlFor='gameCode' className="text-pirate-navy/90">Game Code</FormLabel>
                        <FormControl>
                           <Input id='gameCode' placeholder="Enter 6-character code" className="text-center uppercase tracking-widest border-pirate-navy/30 focus-visible:ring-pirate-gold font-mono" maxLength={6} {...field} onChange={(e) => field.onChange(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''))} autoComplete="off" />
                        </FormControl>
                         <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              )}
              {/* Submit Button */}
              <div className="pt-4">
                <PirateButton type="submit" className="w-full" disabled={isLoading} icon={selectedRole === 'captain' ? <Anchor className="h-5 w-5" /> : <UserPlus className="h-5 w-5" />} >
                  {isLoading ? (selectedRole === 'captain' ? 'Setting Course...' : 'Joining Crew...') : (selectedRole === 'captain' ? 'Start New Game' : 'Join Crew')}
                </PirateButton>
              </div>
            </form>
          </Form>
           {/* Loading Overlay */}
            {isLoading && (
                <div className="absolute inset-0 bg-pirate-parchment/80 flex items-center justify-center rounded-xl z-20">
                    <Loader2 className="h-8 w-8 animate-spin text-pirate-navy" />
                    <span className="ml-2 font-semibold text-pirate-navy">
                      Setting up your identity...
                    </span>
                </div>
            )}
        </div>
      </main>
      {/* Footer */}
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
// --- END OF MODIFIED FILE ---