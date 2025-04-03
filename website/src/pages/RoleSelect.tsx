// website/src/pages/RoleSelect.tsx
// --- START OF FILE ---
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
// REMOVED createGameSession import - it's not called here anymore for Captain
import { joinGameSession } from '@/services/gameApi';
import { createTemporaryUser } from '@/services/userApi';
// REMOVED GameCreationPayload import
import { ApiGameJoinRequest, ApiGameSessionResponse, ApiUserResponse } from '@/types/apiTypes';

interface RoleFormValues {
  role: 'captain' | 'scallywag';
  gameCode?: string;
  displayName?: string;
}

const RoleSelect: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<RoleFormValues>({
    defaultValues: {
      role: 'captain',
      gameCode: '',
      displayName: '',
    },
  });

  const selectedRole = form.watch('role');

  const onSubmit = async (data: RoleFormValues) => {
    setIsLoading(true);
    let user: ApiUserResponse | null = null;

    try {
      // --- Step 1: Create Temporary User (for BOTH roles) ---
      const displayNameForCreation = data.role === 'scallywag'
        ? data.displayName?.trim() || `Scallywag_${Math.random().toString(36).substring(2, 7)}` // Use entered name or generate one
        : `Captain_${Math.random().toString(36).substring(2, 7)}`; // Generate Captain name

      console.log(`Creating temporary user for role: ${data.role} with name: ${displayNameForCreation}`);
      user = await createTemporaryUser(displayNameForCreation);
      console.log("Temporary user created:", user);

      if (!user?.id) {
         throw new Error("Failed to get valid ID after user creation.");
      }
      const userId = user.id;

      // --- Step 2: Navigate or Join Game ---
      if (data.role === 'captain') {
        // Captain Flow: JUST NAVIGATE to Game Select screen
        // Game creation happens AFTER selecting pack/settings there.
        console.log("Navigating Captain to Game Select...");
        // We don't have a game code yet, so no need to pass it here.
        // GameSelect will handle game creation later.
        navigate(`/crew/captain`); // Navigate to the route where captain selects game options
        // Optional: Store the temporary captain user ID somewhere accessible
        // (e.g., local storage, state management) so GameSelect can use it later.
        // For now, we'll rely on GameSelect generating another temp user if needed,
        // or ideally implementing proper auth soon.
         localStorage.setItem('tempUserId', userId); // <<< Store temporary user ID
         localStorage.setItem('tempUserDisplayName', displayNameForCreation); // <<< Store temporary user name

      } else {
        // Scallywag Flow: Join Game
        console.log("Proceeding to join game as Scallywag...");
        if (!data.gameCode || !data.displayName) {
             toast.warning("Missing Information", { description: "Please provide your name and the game code." });
             setIsLoading(false);
             return;
         }

        const joinPayload: ApiGameJoinRequest = {
            game_code: data.gameCode.toUpperCase().trim(),
            // Use the name they entered *and* that was used for user creation
            display_name: data.displayName.trim(),
        };
        const joinedGame = await joinGameSession(joinPayload, userId); // Pass dynamic userId
        console.log("Successfully joined game:", joinedGame);
        toast.success("Joined the Crew!", {
             description: `Now entering the waiting room for game ${joinedGame.code}.`,
        });
         localStorage.setItem('tempUserId', userId); // <<< Store temporary user ID
         localStorage.setItem('tempUserDisplayName', data.displayName.trim()); // <<< Store temporary user name
        // Navigate Scallywag directly to Waiting Room
        navigate(`/crew/waiting/scallywag?gameCode=${joinedGame.code}`);
      }

    } catch (error) {
      console.error("Error during role selection flow:", error);
      const action = data.role === 'captain' ? 'proceed' : 'join game'; // Adjusted message
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

 // --- REST OF THE COMPONENT REMAINS THE SAME (JSX) ---
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <Link to="/" className="flex items-center text-pirate-navy hover:text-pirate-accent mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          <span>Back to Home</span>
        </Link>

        <div className="map-container p-6 md:p-8 mb-10 max-w-md mx-auto relative"> {/* Added relative */}
          <h1 className="pirate-heading text-3xl md:text-4xl mb-3 text-center">Join a Crew</h1>
          <p className="text-pirate-navy/80 mb-8 text-center">Choose your role in this voyage!</p>

          <Form {...form}>
            {/* Use form element to wrap everything */}
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              {/* Role Selection */}
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem className="space-y-3">
                    <FormControl>
                       <RadioGroup
                        onValueChange={field.onChange} // Let RHF handle the change
                        value={field.value} // Controlled by RHF
                        className="grid grid-cols-1 gap-4"
                      >
                        {/* Captain Card */}
                        <FormLabel htmlFor="captain" className="cursor-pointer">
                            <Card className={`p-4 transition-all ${
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
                                    <div className="flex-1">
                                        <div className="flex items-center mb-1">
                                            <Anchor className={`h-5 w-5 mr-2 ${field.value === 'captain' ? 'text-pirate-gold' : 'text-pirate-navy'}`} />
                                            <span className="font-bold text-lg">Captain</span>
                                        </div>
                                        <p className={`text-sm ${field.value === 'captain' ? 'text-white/80' : 'text-pirate-navy/70'}`}>
                                            Start a new game and invite your crew.
                                        </p>
                                    </div>
                                </div>
                            </Card>
                        </FormLabel>

                        {/* Scallywag Card */}
                        <FormLabel htmlFor="scallywag" className="cursor-pointer">
                             <Card className={`p-4 transition-all ${
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
                                 <div className="flex-1">
                                   <div className="flex items-center mb-1">
                                     <User className={`h-5 w-5 mr-2 ${field.value === 'scallywag' ? 'text-pirate-gold' : 'text-pirate-navy'}`} />
                                     <span className="font-bold text-lg">Scallywag</span>
                                   </div>
                                   <p className={`text-sm ${field.value === 'scallywag' ? 'text-white/80' : 'text-pirate-navy/70'}`}>
                                     Join an existing game with a game code.
                                   </p>
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

              {/* Show Details only when Scallywag is selected */}
              {selectedRole === 'scallywag' && (
                <div className="space-y-4 pt-2">
                   {/* Display Name Input */}
                   <FormField
                     control={form.control}
                     name="displayName"
                     rules={{ required: "Enter yer pirate name!", minLength: { value: 2, message: "Name needs more letters!" } }}
                     render={({ field }) => (
                       <FormItem>
                         <FormLabel htmlFor='displayName' className="text-pirate-navy/90">Pirate Name</FormLabel>
                         <FormControl>
                           <div className="relative">
                             <Ship className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-pirate-navy/40" />
                             <Input
                               id='displayName'
                               placeholder="E.g., One-Eyed Jack"
                               className="pl-10 border-pirate-navy/30 focus-visible:ring-pirate-gold"
                               {...field}
                               autoComplete="off"
                             />
                           </div>
                         </FormControl>
                         <FormMessage />
                       </FormItem>
                     )}
                   />

                  {/* Game Code Input */}
                  <FormField
                    control={form.control}
                    name="gameCode"
                    rules={{ required: "Need the Captain's code!", pattern: { value: /^[A-Z0-9]{6}$/, message: "Code must be 6 uppercase letters/numbers"} }} // Updated validation
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel htmlFor='gameCode' className="text-pirate-navy/90">Game Code</FormLabel>
                        <FormControl>
                           <Input
                              id='gameCode'
                              placeholder="Enter 6-character code"
                              className="text-center uppercase tracking-widest border-pirate-navy/30 focus-visible:ring-pirate-gold font-mono" // Added font-mono
                              maxLength={6}
                              {...field}
                              onChange={(e) => field.onChange(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''))} // Force uppercase alphanumeric
                              autoComplete="off"
                            />
                        </FormControl>
                         <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              )}

              <div className="pt-4">
                {/* Button type is submit, handled by form onSubmit */}
                <PirateButton
                  type="submit"
                  className="w-full"
                  disabled={isLoading}
                  icon={selectedRole === 'captain' ? <Anchor className="h-5 w-5" /> : <UserPlus className="h-5 w-5" />}
                >
                  {/* Changed Captain button text */}
                  {selectedRole === 'captain' ? 'Start New Game' : 'Join Crew'}
                </PirateButton>
              </div>
            </form>
          </Form>

           {/* Loading Overlay */}
            {isLoading && (
                <div className="absolute inset-0 bg-pirate-parchment/80 flex items-center justify-center rounded-xl z-20">
                    <Loader2 className="h-8 w-8 animate-spin text-pirate-navy" />
                    <span className="ml-2 font-semibold text-pirate-navy">
                        {/* Dynamic loading message */}
                        {form.formState.isSubmitting ? (selectedRole === 'captain' ? 'Setting up...' : 'Joining Crew...') : 'Setting up...'}
                    </span>
                </div>
            )}

        </div>
      </main>

      {/* Footer remains the same */}
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
// --- END OF FILE ---