import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/hooks/useAuth";
import Index from "./pages/Index";
import UserPortal from "./pages/UserPortal";
import AdminPortal from "./pages/AdminPortal";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import SubmitClaim from "./pages/SubmitClaim";
import ViewClaims from "./pages/ViewClaims";
import ClaimDetails from "./pages/ClaimDetails";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/login" element={<Login />} />
            <Route path="/user" element={<UserPortal />} />
            <Route path="/user/submit-claim" element={<SubmitClaim />} />
            <Route path="/user/claims" element={<ViewClaims />} />
            <Route path="/user/claim/:claimId" element={<ClaimDetails />} />
            <Route path="/admin" element={<AdminPortal />} />
            <Route path="/admin/claims" element={<ViewClaims />} />
            <Route path="/admin/claim/:claimId" element={<ClaimDetails />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
