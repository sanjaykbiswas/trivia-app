// src/pages/AuthScreen.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mail } from 'lucide-react';
import Header from '@/components/Header'; // Assuming you want the standard header

// Inline SVG for Google Logo (simple version)
const GoogleIcon = () => (
  <svg viewBox="0 0 48 48" width="24px" height="24px">
    <path fill="#EA4335" d="M24 9.5c3.49 0 6.6 1.2 9.01 3.19l6.89-6.89C35.76 2.34 30.2 0 24 0 14.9 0 7.09 5.44 4.12 13.09l7.64 5.94C13.64 13.08 18.44 9.5 24 9.5z"></path>
    <path fill="#4285F4" d="M46.17 24.98c0-1.66-.15-3.29-.43-4.88H24v9.32h12.48c-.54 3.03-2.09 5.58-4.58 7.31l7.39 5.72C43.36 37.88 46.17 31.91 46.17 24.98z"></path>
    <path fill="#FBBC05" d="M11.76 19.03c-.47-1.4-.74-2.89-.74-4.43s.27-3.03.74-4.43l-7.64-5.94C1.96 10.16 0 14.89 0 20c0 5.11 1.96 9.84 4.12 13.11l7.64-5.94z"></path>
    <path fill="#34A853" d="M24 48c6.2 0 11.76-2.07 15.68-5.58l-7.39-5.72c-2.04 1.37-4.65 2.19-7.29 2.19-5.56 0-10.36-3.58-12.24-8.41l-7.64 5.94C7.09 42.56 14.9 48 24 48z"></path>
    <path fill="none" d="M0 0h48v48H0z"></path>
  </svg>
);


const AuthScreen: React.FC = () => {

  const handleGoogleSignIn = () => {
    console.log("Attempting Google Sign In...");
    // Add actual Google Sign In logic here (e.g., using Firebase, Supabase, etc.)
    alert("Google Sign In (Not Implemented)");
  };

  const handleEmailSignIn = () => {
    console.log("Attempting Email Sign In...");
    // Add actual Email Sign In logic here
    alert("Email Sign In (Not Implemented)");
  };


  return (
    <div className="min-h-screen flex flex-col">
      {/* Use the standard header */}
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 flex flex-col items-center justify-center">

        {/* Back link (optional, depends on where user comes from) */}
         {/* <Link to="/" className="absolute top-24 left-6 flex items-center text-pirate-navy hover:text-pirate-accent mb-6">
           <ArrowLeft className="h-4 w-4 mr-2" />
           <span>Back</span>
         </Link> */}

        <div className="map-container p-6 md:p-10 mb-10 w-full max-w-md">
          <h1 className="pirate-heading text-3xl md:text-4xl mb-8 text-center">
            Sign Up or Log In
          </h1>

          <div className="flex flex-col items-center gap-4 w-full">
             {/* --- Google Button --- */}
             <button
              onClick={handleGoogleSignIn}
              className="w-full flex items-center justify-center gap-3 bg-white text-black border border-gray-300 rounded-full px-4 py-3 text-base font-medium hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pirate-gold"
            >
              <GoogleIcon />
              Sign in with Google
            </button>

             {/* --- Email Button --- */}
             <button
               onClick={handleEmailSignIn}
               className="w-full flex items-center justify-center gap-3 bg-pirate-navy text-white rounded-full px-4 py-3 text-base font-medium hover:bg-pirate-navy/90 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pirate-gold"
             >
               <Mail className="h-5 w-5" />
               Sign in with Email
             </button>

             {/* Optional: Divider */}
             {/* <div className="my-4 flex items-center w-full">
               <hr className="flex-grow border-t border-pirate-navy/20"/>
               <span className="mx-4 text-xs text-pirate-navy/60">OR</span>
               <hr className="flex-grow border-t border-pirate-navy/20"/>
             </div> */}

             {/* Optional: Link to traditional email/password form */}
             {/* <p className="text-sm text-pirate-navy/80">
               Use your <Link to="/login-email" className="underline hover:text-pirate-accent">email and password</Link>.
             </p> */}

          </div>
        </div>
      </main>

      <footer className="ocean-bg py-8">
        <div className="container mx-auto text-center text-white relative z-10">
          <p className="font-pirate text-xl mb-2">Join the Crew!</p>
          <p className="text-sm opacity-75">© 2023 Trivia Trove - All Rights Reserved</p>
        </div>
      </footer>
    </div>
  );
};

export default AuthScreen;