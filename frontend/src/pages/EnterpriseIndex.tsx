import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  TrendingUp, 
  Users, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock,
  Shield,
  DollarSign,
  BarChart3,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, DashboardMetrics, Claim, formatCurrency, formatDateTime, getStatusColor } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

export default function EnterpriseIndex() {
  const { user, hasRole, login, logout } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentClaims, setRecentClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Auto-login with demo credentials for development
  useEffect(() => {
    const autoLogin = async () => {
      if (!user && process.env.NODE_ENV === 'development') {
        try {
          await login({
            email_or_username: 'user@demo.com',
            password: 'user123'
          });
          toast({
            title: 'Demo Login',
            description: 'Automatically logged in with demo user credentials.',
          });
        } catch (error) {
          console.error('Auto-login failed:', error);
        }
      }
    };
    autoLogin();
  }, [user, login, toast]);

  const loadDashboardData = async () => {
    try {
      setRefreshing(true);
      
      // Load metrics
      const metricsData = await apiClient.getDashboardMetrics();
      setMetrics(metricsData);

      // Load recent claims
      const claimsData = await apiClient.getClaims({ limit: 10 });
      setRecentClaims(claimsData.claims);

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const handleRefresh = () => {
    loadDashboardData();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Welcome back, {user?.first_name}!
              </h1>
              <p className="text-gray-600 mt-1">
                {hasRole(['ADMIN', 'SUPER_ADMIN']) 
                  ? 'Enterprise claims management dashboard'
                  : 'Your healthcare claims dashboard'
                }
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button 
                variant="outline" 
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Badge variant="secondary" className="text-sm">
                {user?.role}
              </Badge>
              <Button 
                variant="outline" 
                onClick={async () => {
                  await logout();
                  navigate('/login');
                }}
                className="flex items-center gap-2"
              >
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Debug/Login Section for Development */}
      {process.env.NODE_ENV === 'development' && !user && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Card className="bg-blue-50 border-blue-200">
            <CardHeader>
              <CardTitle className="text-blue-800">Demo Authentication</CardTitle>
              <CardDescription className="text-blue-600">
                Choose a demo user to test the system
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-3">
                <Button 
                  onClick={async () => {
                    try {
                      await login({ email_or_username: 'user@demo.com', password: 'user123' });
                      toast({ title: 'Success', description: 'Logged in as demo user' });
                    } catch (error) {
                      toast({ title: 'Error', description: 'Login failed', variant: 'destructive' });
                    }
                  }}
                  className="flex-1"
                >
                  Login as User (Sarah Johnson)
                </Button>
                <Button 
                  onClick={async () => {
                    try {
                      await login({ email_or_username: 'admin@demo.com', password: 'admin123' });
                      toast({ title: 'Success', description: 'Logged in as demo admin' });
                    } catch (error) {
                      toast({ title: 'Error', description: 'Login failed', variant: 'destructive' });
                    }
                  }}
                  variant="destructive"
                  className="flex-1"
                >
                  Login as Admin
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Portal Selection Section */}
      <div className="bg-gray-50 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* User Portal Card */}
            <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/enterprise/user/submit-claim')}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  User Portal
                </CardTitle>
                <CardDescription>
                  Submit and manage your healthcare claims
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button className="w-full" onClick={(e) => { 
                    e.stopPropagation(); 
                    console.log('Portal card: Navigating to submit claim');
                    navigate('/enterprise/user/submit-claim'); 
                  }}>
                    Submit New Claim
                  </Button>
                  <Button variant="outline" className="w-full" onClick={(e) => { 
                    e.stopPropagation(); 
                    console.log('Portal card: Navigating to view claims');
                    navigate('/enterprise/user/claims'); 
                  }}>
                    View My Claims
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Admin Portal Card - Only for Admins */}
            {hasRole(['ADMIN', 'SUPER_ADMIN', 'PROCESSOR']) && (
              <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/enterprise/admin')}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-red-600" />
                    Admin Portal
                  </CardTitle>
                  <CardDescription>
                    Process claims and manage system operations
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Button className="w-full" variant="destructive" onClick={(e) => { e.stopPropagation(); navigate('/enterprise/admin'); }}>
                      Admin Dashboard
                    </Button>
                    <Button variant="outline" className="w-full" onClick={(e) => { e.stopPropagation(); navigate('/enterprise/admin/claims'); }}>
                      Process Claims
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Metrics Cards */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Claims</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.total_claims.toLocaleString()}</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.claims_today} new today
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Approval Rate</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metrics.approval_rate.toFixed(1)}%</div>
                <p className="text-xs text-muted-foreground">
                  {metrics.approved_claims} of {metrics.approved_claims + metrics.denied_claims} processed
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Revenue Today</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(metrics.revenue_approved_today)}
                </div>
                <p className="text-xs text-muted-foreground">
                  Approved claims value
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="claims">Recent Claims</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="alerts">Alerts</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Claims Status Distribution */}
              {metrics && (
                <Card>
                  <CardHeader>
                    <CardTitle>Claims by Status</CardTitle>
                    <CardDescription>Current distribution of claim statuses</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span className="text-sm">Approved</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{metrics.approved_claims}</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full" 
                            style={{ width: `${(metrics.approved_claims / metrics.total_claims) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <XCircle className="h-4 w-4 text-red-500" />
                        <span className="text-sm">Denied</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{metrics.denied_claims}</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-red-500 h-2 rounded-full" 
                            style={{ width: `${(metrics.denied_claims / metrics.total_claims) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-yellow-500" />
                        <span className="text-sm">Pending</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{metrics.pending_claims}</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-yellow-500 h-2 rounded-full" 
                            style={{ width: `${(metrics.pending_claims / metrics.total_claims) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-purple-500" />
                        <span className="text-sm">Fraud Flagged</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{metrics.fraud_flagged_claims}</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-purple-500 h-2 rounded-full" 
                            style={{ width: `${(metrics.fraud_flagged_claims / metrics.total_claims) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <CardDescription>Common tasks and shortcuts</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button 
                    className="w-full justify-start" 
                    variant="outline"
                    onClick={() => {
                      console.log('Navigating to submit claim');
                      navigate('/enterprise/user/submit-claim');
                    }}
                  >
                    <Users className="h-4 w-4 mr-2" />
                    Submit New Claim
                  </Button>
                  <Button 
                    className="w-full justify-start" 
                    variant="outline"
                    onClick={() => {
                      console.log('Navigating to view claims');
                      navigate('/enterprise/user/claims');
                    }}
                  >
                    <BarChart3 className="h-4 w-4 mr-2" />
                    View All Claims
                  </Button>
                  {hasRole(['ADMIN', 'SUPER_ADMIN', 'PROCESSOR']) && (
                    <>
                      <Button 
                        className="w-full justify-start" 
                        variant="outline"
                        onClick={() => navigate('/enterprise/admin')}
                      >
                        <Shield className="h-4 w-4 mr-2" />
                        Admin Portal
                      </Button>
                      <Button 
                        className="w-full justify-start" 
                        variant="outline"
                        onClick={() => navigate('/enterprise/admin/claims')}
                      >
                        <Activity className="h-4 w-4 mr-2" />
                        Process Pending Claims
                      </Button>
                      <Button className="w-full justify-start" variant="outline">
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Review Fraud Alerts
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="claims" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Claims</CardTitle>
                <CardDescription>Latest claim submissions and updates</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentClaims.map((claim) => (
                    <div key={claim.claim_id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="font-medium">{claim.claim_id}</span>
                          <Badge className={getStatusColor(claim.status)}>
                            {claim.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {claim.patient_name} • {formatCurrency(claim.claim_amount)}
                        </p>
                        <p className="text-xs text-gray-500">
                          Created {formatDateTime(claim.created_at)}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {claim.confidence_score && (
                          <Badge variant="outline">
                            {claim.confidence_score.toFixed(0)}% confidence
                          </Badge>
                        )}
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => navigate(`/enterprise/user/claim/${claim.claim_id}`)}
                        >
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Performance Metrics</CardTitle>
                  <CardDescription>System performance indicators</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">AI Processing Accuracy</span>
                      <span className="font-medium">94.2%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Fraud Detection Rate</span>
                      <span className="font-medium">98.7%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Average Agent Response Time</span>
                      <span className="font-medium">1.3s</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">System Uptime</span>
                      <span className="font-medium">99.9%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Multi-Agent Insights</CardTitle>
                  <CardDescription>AI agent collaboration statistics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Intake Agent Success</span>
                      <span className="font-medium">99.1%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Eligibility Agent Success</span>
                      <span className="font-medium">97.8%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Clinical Review Success</span>
                      <span className="font-medium">96.4%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Fraud Detection Success</span>
                      <span className="font-medium">98.7%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="alerts" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>System Alerts</CardTitle>
                <CardDescription>Important notifications and warnings</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-yellow-800">High Volume Alert</p>
                      <p className="text-sm text-yellow-700">
                        Claims volume is 23% higher than usual today. Consider allocating additional processing resources.
                      </p>
                      <p className="text-xs text-yellow-600 mt-1">2 hours ago</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <Shield className="h-5 w-5 text-red-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-red-800">Fraud Detection Alert</p>
                      <p className="text-sm text-red-700">
                        3 high-risk claims detected in the last hour. Manual review recommended.
                      </p>
                      <p className="text-xs text-red-600 mt-1">45 minutes ago</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                    <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-green-800">System Update Complete</p>
                      <p className="text-sm text-green-700">
                        Multi-agent system updated successfully. Performance improvements deployed.
                      </p>
                      <p className="text-xs text-green-600 mt-1">6 hours ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}