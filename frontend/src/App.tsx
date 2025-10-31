import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/hooks/useAuth";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import SubmitClaim from "./pages/SubmitClaim";
import Reports from "./pages/Reports";
import UserPortal from "./pages/UserPortal";
// Enterprise Components (kept)
import EnterpriseIndex from "./pages/EnterpriseIndex";
import EnterpriseClaimDetails from "./pages/EnterpriseClaimDetails";
import EnhancedAdminPortal from "./pages/EnhancedAdminPortal";
import ClaimsManagementInterface from "./pages/ClaimsManagementInterface";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Main routes using cleaned up components */}
            <Route path="/" element={<EnterpriseIndex />} />
            <Route path="/login" element={<Login />} />
            <Route path="/user" element={<UserPortal />} />
            <Route path="/user/submit-claim" element={<SubmitClaim />} />
            <Route path="/user/claims" element={<ClaimsManagementInterface />} />
            <Route path="/user/claim/:claimId" element={<EnterpriseClaimDetails />} />
            <Route path="/user/claims/:claimId" element={<EnterpriseClaimDetails />} />
            <Route path="/user/reports" element={<Reports />} />
            <Route path="/admin" element={<EnhancedAdminPortal />} />
            <Route path="/admin/claims" element={<ClaimsManagementInterface />} />
            <Route path="/admin/claim/:claimId" element={<EnterpriseClaimDetails />} />
            <Route path="/admin/claims/:claimId" element={<EnterpriseClaimDetails />} />
            
            {/* Enterprise routes (primary) */}
            <Route path="/enterprise" element={<EnterpriseIndex />} />
            <Route path="/enterprise/user" element={<EnterpriseIndex />} />
            <Route path="/enterprise/user/submit-claim" element={<SubmitClaim />} />
            <Route path="/enterprise/user/claims" element={<ClaimsManagementInterface />} />
            <Route path="/enterprise/user/claim/:claimId" element={<EnterpriseClaimDetails />} />
            <Route path="/enterprise/admin" element={<EnhancedAdminPortal />} />
            <Route path="/enterprise/admin/claims" element={<ClaimsManagementInterface />} />
            <Route path="/enterprise/admin/claim/:claimId" element={<EnterpriseClaimDetails />} />
            
            {/* Catch-all route */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
