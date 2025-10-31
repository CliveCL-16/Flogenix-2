import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  FileText, 
  ClipboardList, 
  User, 
  Bell, 
  ArrowLeft, 
  Activity, 
  LogOut, 
  Loader2, 
  RefreshCw,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  DollarSign,
  BarChart3,
  Brain,
  Eye,
  Download,
  MessageCircle,
  Shield
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { 
  apiClient, 
  Claim, 
  DashboardMetrics,
  formatCurrency, 
  formatDateTime 
} from "@/lib/api";

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  created_at: string;
  action_url?: string;
}

// Helper functions for status display
const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
  switch (status.toUpperCase()) {
    case 'APPROVED':
      return 'default'; // Green in most themes
    case 'DENIED':
      return 'destructive';
    case 'PENDING':
      return 'secondary';
    case 'PROCESSING':
      return 'outline';
    case 'PENDING_REVIEW':
      return 'secondary';
    case 'FRAUD_FLAGGED':
      return 'destructive';
    default:
      return 'outline';
  }
};

const getStatusLabel = (status: string): string => {
  switch (status.toUpperCase()) {
    case 'PENDING':
      return 'Pending';
    case 'PROCESSING':
      return 'Processing';
    case 'APPROVED':
      return 'Approved';
    case 'DENIED':
      return 'Denied';
    case 'PENDING_REVIEW':
      return 'Pending Review';
    case 'FRAUD_FLAGGED':
      return 'Fraud Flagged';
    default:
      return status;
  }
};

const UserPortal = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { isAuthenticated, userType, logout, userName } = useAuth();
  
  // State management
  const [recentClaims, setRecentClaims] = useState<Claim[]>([]);
  const [dashboardStats, setDashboardStats] = useState<DashboardMetrics | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!isAuthenticated || userType !== 'user') {
      navigate('/login?type=user');
    } else {
      loadDashboardData();
      // Set up periodic refresh for real-time updates
      const interval = setInterval(loadNotifications, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, userType, navigate]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      await Promise.all([
        loadRecentClaims(),
        loadDashboardStats(),
        loadNotifications()
      ]);
    } catch (error) {
      toast({
        title: "Error Loading Dashboard",
        description: "Failed to load dashboard data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadRecentClaims = async () => {
    try {
      const claimsData = await apiClient.getClaims({ limit: 5 });
      setRecentClaims(claimsData.claims);
    } catch (error) {
      console.error('Failed to load recent claims:', error);
    }
  };

  const loadDashboardStats = async () => {
    try {
      // Calculate metrics from actual claims data
      const claimsData = await apiClient.getClaims();
      const claims = claimsData.claims;
      
      const totalClaims = claims.length;
      const approvedClaims = claims.filter(claim => claim.status === 'APPROVED').length;
      const pendingClaims = claims.filter(claim => claim.status === 'PENDING').length;
      const processingClaims = claims.filter(claim => claim.status === 'PROCESSING').length;
      
      const approvalRate = totalClaims > 0 ? (approvedClaims / totalClaims) : 0;
      const totalApprovedAmount = claims
        .filter(claim => claim.status === 'APPROVED')
        .reduce((sum, claim) => sum + claim.claim_amount, 0);
      
      // Calculate average processing time (mock for now since we don't have processing times)
      const avgProcessingTimeHours = totalClaims > 0 ? Math.floor(Math.random() * 24) + 1 : 0;
      
      setDashboardStats({
        total_claims: totalClaims,
        pending_claims: pendingClaims,
        processing_claims: processingClaims,
        approved_claims: approvedClaims,
        denied_claims: claims.filter(claim => claim.status === 'DENIED').length,
        fraud_flagged_claims: claims.filter(claim => claim.status === 'FRAUD_FLAGGED').length,
        approval_rate: approvalRate,
        avg_processing_time_seconds: avgProcessingTimeHours * 3600,
        claims_today: claims.filter(claim => {
          const today = new Date().toISOString().split('T')[0];
          return claim.created_at.startsWith(today);
        }).length,
        revenue_approved_today: totalApprovedAmount
      } as DashboardMetrics);
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const notificationsData = await apiClient.getNotifications({ limit: 10 });
      setNotifications(notificationsData.notifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadDashboardData();
    setIsRefreshing(false);
    toast({
      title: "Dashboard Refreshed",
      description: "All data has been updated",
    });
  };

  const markNotificationAsRead = async (notificationId: string) => {
    try {
      await apiClient.markNotificationRead(notificationId);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading your dashboard...</span>
        </div>
      </div>
    );
  }

  const unreadNotifications = notifications.filter(n => !n.read).length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                Welcome back, User
              </h1>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <div className="relative">
                <Button variant="ghost" size="sm" className="relative">
                  <Bell className="h-5 w-5" />
                  {unreadNotifications > 0 && (
                    <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs">
                      {unreadNotifications}
                    </Badge>
                  )}
                </Button>
              </div>
              
              <Button variant="ghost" size="sm" onClick={() => navigate('/user/profile')}>
                <User className="h-5 w-5" />
                Profile
              </Button>
              
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-5 w-5" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Key Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Claims</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardStats?.total_claims || 0}</div>
              <p className="text-xs text-muted-foreground">
                All time submissions
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Approval Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashboardStats?.approval_rate ? `${(dashboardStats.approval_rate * 100).toFixed(1)}%` : '0%'}
              </div>
              <p className="text-xs text-muted-foreground">
                Success rate
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Approved</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(dashboardStats?.revenue_approved_today || 0)}
              </div>
              <p className="text-xs text-muted-foreground">
                Approved amount
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Common tasks and shortcuts</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Link to="/user/submit-claim">
                    <Button className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                      <FileText className="h-6 w-6" />
                      <span>Submit New Claim</span>
                    </Button>
                  </Link>
                  
                  <Link to="/user/claims">
                    <Button variant="outline" className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                      <ClipboardList className="h-6 w-6" />
                      <span>Track Claims</span>
                    </Button>
                  </Link>
                  
                  <Link to="/user/reports">
                    <Button variant="outline" className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                      <Brain className="h-6 w-6" />
                      <span>Processing Analytics</span>
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Recent Claims */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Recent Claims</CardTitle>
                  <CardDescription>Your latest claim submissions</CardDescription>
                </div>
                <Link to="/user/claims">
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4 mr-2" />
                    View All
                  </Button>
                </Link>
              </CardHeader>
              <CardContent>
                {recentClaims.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No claims submitted yet</p>
                    <Link to="/user/submit-claim" className="inline-block mt-2">
                      <Button size="sm">Submit Your First Claim</Button>
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {recentClaims.map((claim) => (
                      <div key={claim.claim_id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <div>
                              <p className="font-medium">Claim #{claim.claim_id}</p>
                              <p className="text-sm text-gray-600">{claim.patient_name}</p>
                            </div>
                            <Badge variant={getStatusVariant(claim.status)}>
                              {getStatusLabel(claim.status)}
                            </Badge>
                          </div>
                          <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                            <span>{formatCurrency(claim.claim_amount)}</span>
                            <span>{formatDateTime(claim.created_at)}</span>
                            {claim.confidence_score && (
                              <span className="flex items-center space-x-1">
                                <Brain className="h-3 w-3" />
                                <span>{(claim.confidence_score * 100).toFixed(0)}% confidence</span>
                              </span>
                            )}
                          </div>
                        </div>
                        <Link to={`/user/claims/${claim.claim_id}`}>
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Notifications */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Notifications</span>
                  <Badge variant="secondary">{unreadNotifications}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="text-sm text-gray-500 text-center py-4">
                      No notifications yet
                    </p>
                  ) : (
                    notifications.slice(0, 5).map((notification) => (
                      <div 
                        key={notification.id}
                        className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                          notification.read ? 'bg-gray-50' : 'bg-blue-50 border-blue-200'
                        }`}
                        onClick={() => markNotificationAsRead(notification.id)}
                      >
                        <div className="flex items-start space-x-2">
                          <div className={`w-2 h-2 rounded-full mt-2 ${
                            notification.read ? 'bg-gray-300' : 'bg-blue-500'
                          }`} />
                          <div className="flex-1">
                            <h5 className="font-medium text-sm">{notification.title}</h5>
                            <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              {formatDateTime(notification.created_at)}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                {notifications.length > 5 && (
                  <div className="text-center mt-4">
                    <Button variant="ghost" size="sm">
                      View All Notifications
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* System Status */}
            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">AI Processing</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-green-600">Online</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Document OCR</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-green-600">Online</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Fraud Detection</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-sm text-green-600">Active</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Help & Support */}
            <Card>
              <CardHeader>
                <CardTitle>Need Help?</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Contact Support
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <Download className="h-4 w-4 mr-2" />
                    User Guide
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <Shield className="h-4 w-4 mr-2" />
                    Privacy Policy
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserPortal;