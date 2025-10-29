import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Activity, TrendingUp, CheckCircle, AlertTriangle, Clock, LogOut, Loader2, RefreshCw } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { 
  apiClient, 
  DashboardMetrics, 
  Claim, 
  getStatusColor, 
  getStatusLabel, 
  formatCurrency, 
  formatDateTime 
} from "@/lib/api";

const AdminPortal = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { isAuthenticated, userType, logout } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentClaims, setRecentClaims] = useState<Claim[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || userType !== 'admin') {
      navigate('/login?type=admin');
    } else {
      loadDashboardData();
    }
  }, [isAuthenticated, userType, navigate]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      
      // Load metrics and recent claims in parallel
      const [metricsData, claimsData] = await Promise.all([
        apiClient.getDashboardMetrics(),
        apiClient.getClaims()
      ]);
      
      setMetrics(metricsData);
      // Get the 5 most recent claims
      setRecentClaims(claimsData.claims.slice(0, 5));
    } catch (error) {
      toast({
        title: "Error Loading Dashboard",
        description: error instanceof Error ? error.message : "Failed to load dashboard data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

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
                <p className="text-xs text-muted-foreground">Admin Portal</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="info">Administrator</Badge>
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
        {/* Metrics Dashboard */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-foreground mb-6">Dashboard Overview</h2>
          
          {metrics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Total Claims */}
              <Card className="p-6 bg-gradient-to-br from-card to-primary/5 border-primary/20">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Activity className="w-6 h-6 text-primary" />
                  </div>
                  <TrendingUp className="w-5 h-5 text-success" />
                </div>
                <p className="text-sm text-muted-foreground mb-1">Total Claims</p>
                <p className="text-3xl font-bold text-foreground">{metrics.total_claims}</p>
              </Card>

              {/* Approval Rate */}
              <Card className="p-6 bg-gradient-to-br from-card to-success/5 border-success/20">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg bg-success/10 flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-success" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-1">Approval Rate</p>
                <p className="text-3xl font-bold text-foreground">{metrics.approval_rate.toFixed(1)}%</p>
              </Card>

              {/* Avg Processing Time */}
              <Card className="p-6 bg-gradient-to-br from-card to-info/5 border-info/20">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg bg-info/10 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-info" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-1">Avg Processing Time</p>
                <p className="text-3xl font-bold text-foreground">
                  {(metrics.avg_processing_time_seconds / 3600).toFixed(1)}h
                </p>
              </Card>

              {/* Flagged Claims */}
              <Card className="p-6 bg-gradient-to-br from-card to-destructive/5 border-destructive/20">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg bg-destructive/10 flex items-center justify-center">
                    <AlertTriangle className="w-6 h-6 text-destructive" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-1">Fraud Flagged</p>
                <p className="text-3xl font-bold text-foreground">{metrics.fraud_flagged_claims}</p>
              </Card>

              {/* Pending Claims */}
              <Card className="p-6 bg-gradient-to-br from-card to-warning/5 border-warning/20">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg bg-warning/10 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-warning" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-1">Pending Review</p>
                <p className="text-3xl font-bold text-foreground">{metrics.pending_claims}</p>
              </Card>

              {/* Approved Claims */}
              <Card className="p-6 bg-gradient-to-br from-card to-primary/5 border-primary/20">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <CheckCircle className="w-6 h-6 text-primary" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-1">Approved</p>
                <p className="text-3xl font-bold text-foreground">{metrics.approved_claims}</p>
              </Card>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="p-6 animate-pulse">
                  <div className="h-16 bg-muted rounded mb-4"></div>
                  <div className="h-4 bg-muted rounded mb-2"></div>
                  <div className="h-8 bg-muted rounded"></div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Recent Claims Table */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-foreground">Recent Submissions</h3>
            <Link to="/admin/claims">
              <Button variant="outline">View All Claims</Button>
            </Link>
          </div>
          
          {recentClaims.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Claim ID</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Patient</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Insurer</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Amount</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Date</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {recentClaims.map((claim) => (
                    <tr key={claim.claim_id} className="border-b hover:bg-accent/30 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-medium text-foreground">{claim.claim_id}</span>
                      </td>
                      <td className="py-3 px-4 text-foreground">{claim.patient_name}</td>
                      <td className="py-3 px-4 text-foreground">{claim.insurance_provider}</td>
                      <td className="py-3 px-4 font-semibold text-foreground">{formatCurrency(claim.claim_amount)}</td>
                      <td className="py-3 px-4">
                        <Badge variant={getStatusColor(claim.status) as any}>
                          {getStatusLabel(claim.status)}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-sm text-muted-foreground">
                        {formatDateTime(claim.created_at)}
                      </td>
                      <td className="py-3 px-4">
                        <Link to={`/admin/claim/${claim.claim_id}`}>
                          <Button size="sm" variant="ghost">View</Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No recent claims found</p>
            </div>
          )}
        </Card>
      </main>
    </div>
  );
};

export default AdminPortal;
