import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FileText, ClipboardList, User, Bell, ArrowLeft, Activity, LogOut, Loader2, RefreshCw } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { 
  apiClient, 
  Claim, 
  getStatusColor, 
  getStatusLabel, 
  formatCurrency, 
  formatDateTime 
} from "@/lib/api";

const UserPortal = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { isAuthenticated, userType, logout, userName } = useAuth();
  const [recentClaims, setRecentClaims] = useState<Claim[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || userType !== 'user') {
      navigate('/login?type=user');
    } else {
      loadRecentClaims();
    }
  }, [isAuthenticated, userType, navigate]);

  const loadRecentClaims = async () => {
    try {
      setIsLoading(true);
      const claimsData = await apiClient.getClaims();
      // Get the 3 most recent claims for the user
      setRecentClaims(claimsData.claims.slice(0, 3));
    } catch (error) {
      toast({
        title: "Error Loading Claims",
        description: error instanceof Error ? error.message : "Failed to load recent claims",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const [user] = useState({
    name: userName || "Sarah Johnson",
    memberId: "MEM-2024-789456",
    activeCoverage: "Premium Health Plan",
    status: "Active"
  });

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleRefresh = () => {
    loadRecentClaims();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2" />
                Back
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
                <Activity className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">Flowgenix</h1>
                <p className="text-xs text-muted-foreground">User Portal</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon">
              <Bell className="w-5 h-5" />
            </Button>
            <Button onClick={handleRefresh} variant="ghost" size="sm">
              <RefreshCw className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Welcome Card */}
        <Card className="p-6 mb-8 bg-gradient-hero border-primary/20">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Welcome back, {user.name}</h2>
              <p className="text-muted-foreground mb-4">Member ID: {user.memberId}</p>
              <div className="flex gap-4 items-center">
                <div>
                  <p className="text-sm text-muted-foreground">Active Coverage</p>
                  <p className="font-semibold text-foreground">{user.activeCoverage}</p>
                </div>
                <Badge variant="success">{user.status}</Badge>
              </div>
            </div>
            <User className="w-16 h-16 text-primary/30" />
          </div>
        </Card>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Link to="/user/submit-claim">
            <Card className="p-6 hover:shadow-lg transition-all duration-200 cursor-pointer border-primary/20 hover:border-primary/40 bg-card group">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <FileText className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">Submit New Claim</h3>
                  <p className="text-sm text-muted-foreground">File a new healthcare claim</p>
                </div>
              </div>
            </Card>
          </Link>

          <Link to="/user/claims">
            <Card className="p-6 hover:shadow-lg transition-all duration-200 cursor-pointer border-primary/20 hover:border-primary/40 bg-card group">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-info/10 flex items-center justify-center group-hover:bg-info/20 transition-colors">
                  <ClipboardList className="w-6 h-6 text-info" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">View All Claims</h3>
                  <p className="text-sm text-muted-foreground">Track your claim history</p>
                </div>
              </div>
            </Card>
          </Link>
        </div>

        {/* Recent Claims */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-foreground mb-4">Recent Claims</h3>
          
          {isLoading ? (
            <div className="text-center py-8">
              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Loading recent claims...</p>
            </div>
          ) : recentClaims.length > 0 ? (
            <div className="space-y-3">
              {recentClaims.map((claim) => (
                <div key={claim.claim_id} className="flex items-center justify-between p-4 rounded-lg bg-accent/30 hover:bg-accent/50 transition-colors">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-medium text-foreground">{claim.claim_id}</span>
                      <Badge variant={getStatusColor(claim.status) as any}>
                        {getStatusLabel(claim.status)}
                      </Badge>
                    </div>
                    <p className="text-sm text-foreground">{claim.provider_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateTime(claim.created_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-foreground">{formatCurrency(claim.claim_amount)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">No claims found</p>
              <Link to="/user/submit-claim">
                <Button>Submit Your First Claim</Button>
              </Link>
            </div>
          )}
          
          {recentClaims.length > 0 && (
            <div className="mt-4 text-center">
              <Link to="/user/claims">
                <Button variant="outline">View All Claims</Button>
              </Link>
            </div>
          )}
        </Card>
      </main>
    </div>
  );
};

export default UserPortal;
