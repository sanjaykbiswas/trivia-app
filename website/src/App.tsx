// src/App.tsx
// --- START OF FILE ---
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import GameSelect from "./pages/GameSelect";
import RoleSelect from "./pages/RoleSelect";
import WaitingRoom from "./pages/WaitingRoom";
import NotFound from "./pages/NotFound";
import CountdownScreen from "./pages/CountdownScreen";
import GameplayScreen from "./pages/GameplayScreen";
import ResultsScreen from "./pages/ResultsScreen";
import AuthScreen from "./pages/AuthScreen"; // Import the new screen

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/auth" element={<AuthScreen />} /> {/* Add Auth route */}
          <Route path="/solo" element={<GameSelect mode="solo" />} />
          <Route path="/crew" element={<RoleSelect />} />
          <Route path="/crew/:role" element={<GameSelect mode="crew" />} />
          <Route path="/solo/waiting" element={<WaitingRoom />} />
          <Route path="/crew/waiting/:role" element={<WaitingRoom />} />
          <Route path="/countdown" element={<CountdownScreen />} />
          <Route path="/gameplay" element={<GameplayScreen />} />
          <Route path="/results" element={<ResultsScreen />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
// --- END OF FILE ---