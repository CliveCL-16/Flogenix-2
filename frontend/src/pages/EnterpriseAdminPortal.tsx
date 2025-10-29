import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Users, 
  FileText, 
  TrendingUp, 
  Shield, 
  Settings, 
  Search,
  Filter,
  Download,
  RefreshCw,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  MoreVertical,
  UserPlus,
  Ban,
  Play,
  Pause,
  BarChart3,
  PieChart,
  Activity,
  Database,
  Bot,
  Zap,
  Bell,
  BellRing,
  Globe,
  Lock,
  Unlock,
  Edit,
  Trash2
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import NotificationSystem from '@/components/NotificationSystem';

interface AdminStats {
  total_users: number;
  active_users: number;
  total_claims: number;
  pending_claims: number;
  processing_claims: number;
  approved_claims: number;
  denied_claims: number;
  fraud_flagged: number;
  avg_processing_time: number;
  system_uptime: string;
  ai_agents_active: number;
  queue_size: number;
}

interface QueuedClaim {
  claim_id: string;
  patient_name: string;
  priority: number;
  status: string;
  submitted_at: string;
  estimated_completion: string;
  assigned_processor?: string;
}

interface SystemUser {
  id: number;
  user_id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  last_login_at: string;
  created_at: string;
  failed_login_attempts: number;
}

interface AgentMetrics {
  agent_name: string;
  status: 'active' | 'idle' | 'error';
  processed_today: number;
  avg_confidence: number;
  avg_processing_time: number;
  success_rate: number;
  last_activity: string;
}

const PRIORITY_COLORS = {
  1: 'bg-gray-100 text-gray-800',
  2: 'bg-yellow-100 text-yellow-800',
  3: 'bg-red-100 text-red-800',
};

const STATUS_COLORS = {
  pending: 'bg-blue-100 text-blue-800',
  processing: 'bg-yellow-100 text-yellow-800',
  reviewed: 'bg-purple-100 text-purple-800',
  approved: 'bg-green-100 text-green-800',
  denied: 'bg-red-100 text-red-800',
  fraud_flagged: 'bg-red-100 text-red-800',
};

const ROLE_COLORS = {
  USER: 'bg-gray-100 text-gray-800',
  PROCESSOR: 'bg-blue-100 text-blue-800',
  ADMIN: 'bg-purple-100 text-purple-800',
  SUPER_ADMIN: 'bg-red-100 text-red-800',
};

export default function EnterpriseAdminPortal() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [queuedClaims, setQueuedClaims] = useState<QueuedClaim[]>([]);
  const [users, setUsers] = useState<SystemUser[]>([]);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);

  // Search and filter states
  const [claimSearch, setClaimSearch] = useState('');
  const [claimStatusFilter, setClaimStatusFilter] = useState('all');
  const [userSearch, setUserSearch] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState('all');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch admin dashboard metrics
      const metricsResponse = await apiClient.getDashboardMetrics();
      
      // Mock admin-specific data (in production, these would be separate API calls)
      setStats({
        total_users: 1247,
        active_users: 892,
        total_claims: 15623,
        pending_claims: metricsResponse.pending_claims,
        processing_claims: metricsResponse.processing_claims,
        approved_claims: metricsResponse.approved_claims,
        denied_claims: metricsResponse.denied_claims,
        fraud_flagged: metricsResponse.fraud_flagged_claims,
        avg_processing_time: metricsResponse.avg_processing_time_seconds,
        system_uptime: '99.7%',
        ai_agents_active: 5,
        queue_size: 23,
      });

      // Mock queued claims
      setQueuedClaims([
        {
          claim_id: 'CLM-2024-001',
          patient_name: 'John Smith',
          priority: 3,
          status: 'pending',
          submitted_at: '2024-01-15T10:30:00Z',
          estimated_completion: '2024-01-15T12:00:00Z',
          assigned_processor: 'Dr. Johnson'
        },
        {
          claim_id: 'CLM-2024-002',
          patient_name: 'Sarah Davis',
          priority: 2,
          status: 'processing',
          submitted_at: '2024-01-15T09:45:00Z',
          estimated_completion: '2024-01-15T11:30:00Z'
        },
        {
          claim_id: 'CLM-2024-003',
          patient_name: 'Michael Brown',
          priority: 1,
          status: 'pending',
          submitted_at: '2024-01-15T08:20:00Z',
          estimated_completion: '2024-01-15T10:50:00Z'
        }
      ]);

      // Mock agent metrics
      setAgentMetrics([
        {
          agent_name: 'Intake Agent',
          status: 'active',
          processed_today: 156,
          avg_confidence: 94.5,
          avg_processing_time: 12.3,
          success_rate: 98.2,
          last_activity: '2024-01-15T11:45:00Z'
        },
        {
          agent_name: 'Eligibility Agent',
          status: 'active',
          processed_today: 142,
          avg_confidence: 91.8,
          avg_processing_time: 18.7,
          success_rate: 96.5,
          last_activity: '2024-01-15T11:44:00Z'
        },
        {
          agent_name: 'Clinical Review Agent',
          status: 'idle',
          processed_today: 89,
          avg_confidence: 88.3,
          avg_processing_time: 45.2,
          success_rate: 94.1,
          last_activity: '2024-01-15T11:30:00Z'
        },
        {
          agent_name: 'Fraud Detection Agent',
          status: 'active',
          processed_today: 156,
          avg_confidence: 96.7,
          avg_processing_time: 8.9,
          success_rate: 99.1,
          last_activity: '2024-01-15T11:45:00Z'
        },
        {
          agent_name: 'Adjudication Agent',
          status: 'active',
          processed_today: 134,
          avg_confidence: 92.4,
          avg_processing_time: 22.1,
          success_rate: 97.8,
          last_activity: '2024-01-15T11:43:00Z'
        }
      ]);

      // Mock users data
      setUsers([
        {
          id: 1,
          user_id: 'USR-001',
          email: 'admin@flogenix.com',
          username: 'admin',
          first_name: 'System',
          last_name: 'Administrator',
          role: 'SUPER_ADMIN',
          is_active: true,
          last_login_at: '2024-01-15T11:30:00Z',
          created_at: '2024-01-01T00:00:00Z',
          failed_login_attempts: 0
        },
        {
          id: 2,
          user_id: 'USR-002',
          email: 'processor@flogenix.com',
          username: 'processor1',
          first_name: 'Jane',
          last_name: 'Processor',
          role: 'PROCESSOR',
          is_active: true,
          last_login_at: '2024-01-15T10:15:00Z',
          created_at: '2024-01-02T00:00:00Z',
          failed_login_attempts: 0
        },
        {
          id: 3,
          user_id: 'USR-003',
          email: 'user@example.com',
          username: 'user1',
          first_name: 'John',
          last_name: 'User',
          role: 'USER',
          is_active: true,
          last_login_at: '2024-01-15T09:30:00Z',
          created_at: '2024-01-03T00:00:00Z',
          failed_login_attempts: 1
        }
      ]);

    } catch (error) {
      toast({
        title: 'Error Loading Dashboard',
        description: 'Failed to fetch admin dashboard data.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getAgentStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <Activity className="h-4 w-4 text-green-600" />;
      case 'idle':
        return <Pause className="h-4 w-4 text-yellow-600" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const filteredClaims = queuedClaims.filter(claim => {
    const matchesSearch = claim.claim_id.toLowerCase().includes(claimSearch.toLowerCase()) ||
                         claim.patient_name.toLowerCase().includes(claimSearch.toLowerCase());
    const matchesStatus = claimStatusFilter === 'all' || claim.status === claimStatusFilter;
    return matchesSearch && matchesStatus;
  });

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(userSearch.toLowerCase()) ||
                         user.username.toLowerCase().includes(userSearch.toLowerCase()) ||
                         `${user.first_name} ${user.last_name}`.toLowerCase().includes(userSearch.toLowerCase());
    const matchesRole = userRoleFilter === 'all' || user.role === userRoleFilter;
    return matchesSearch && matchesRole;
  });

  if (!user || (user.role !== 'ADMIN' && user.role !== 'SUPER_ADMIN' && user.role !== 'PROCESSOR')) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Shield className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">You don't have permission to access the admin portal.</p>
          <Button onClick={() => navigate('/enterprise')}>
            Return to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Admin Portal</h1>
              <p className="text-gray-600 mt-1">Enterprise system management and monitoring</p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <Activity className="h-3 w-3 mr-1" />
                System Operational
              </Badge>
              <Button
                variant="outline"
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative"
              >
                <BellRing className="h-4 w-4 mr-2" />
                Notifications
                <Badge 
                  variant="destructive" 
                  className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
                >
                  3
                </Badge>
              </Button>
              <Button variant="outline" onClick={fetchDashboardData} disabled={loading}>
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="queue" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Claims Queue
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center gap-2">
              <Bot className="h-4 w-4" />
              AI Agents
            </TabsTrigger>
            <TabsTrigger value="users" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              User Management
            </TabsTrigger>
            <TabsTrigger value="system" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              System Settings
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Users</p>
                      <p className="text-3xl font-bold text-gray-900">{stats?.total_users || 0}</p>
                      <p className="text-sm text-green-600">
                        {stats?.active_users || 0} active
                      </p>
                    </div>
                    <Users className="h-8 w-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Queue Size</p>
                      <p className="text-3xl font-bold text-gray-900">{stats?.queue_size || 0}</p>
                      <p className="text-sm text-blue-600">
                        {stats?.processing_claims || 0} processing
                      </p>
                    </div>
                    <Clock className="h-8 w-8 text-yellow-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Avg Processing</p>
                      <p className="text-3xl font-bold text-gray-900">
                        {Math.round(stats?.avg_processing_time || 0)}s
                      </p>
                      <p className="text-sm text-green-600">-12% vs last week</p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">System Uptime</p>
                      <p className="text-3xl font-bold text-gray-900">{stats?.system_uptime || '0%'}</p>
                      <p className="text-sm text-green-600">Last 30 days</p>
                    </div>
                    <Activity className="h-8 w-8 text-purple-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Claims Overview */}
            <Card>
              <CardHeader>
                <CardTitle>Claims Processing Overview</CardTitle>
                <CardDescription>Real-time claims processing statistics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">{stats?.pending_claims || 0}</p>
                    <p className="text-sm text-blue-800">Pending</p>
                  </div>
                  <div className="text-center p-4 bg-yellow-50 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-600">{stats?.processing_claims || 0}</p>
                    <p className="text-sm text-yellow-800">Processing</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">{stats?.approved_claims || 0}</p>
                    <p className="text-sm text-green-800">Approved</p>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <p className="text-2xl font-bold text-red-600">{stats?.denied_claims || 0}</p>
                    <p className="text-sm text-red-800">Denied</p>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <p className="text-2xl font-bold text-orange-600">{stats?.fraud_flagged || 0}</p>
                    <p className="text-sm text-orange-800">Fraud Flagged</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Claims Queue Tab */}
          <TabsContent value="queue" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Claims Processing Queue</CardTitle>
                    <CardDescription>Manage and monitor claim processing queue</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </Button>
                    <Button size="sm">
                      <Play className="h-4 w-4 mr-2" />
                      Process All
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* Filters */}
                <div className="flex gap-4 mb-6">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Search claims..."
                        value={claimSearch}
                        onChange={(e) => setClaimSearch(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <Select value={claimStatusFilter} onValueChange={setClaimStatusFilter}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="processing">Processing</SelectItem>
                      <SelectItem value="reviewed">Reviewed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Claims Table */}
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Claim ID</TableHead>
                      <TableHead>Patient</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Submitted</TableHead>
                      <TableHead>Est. Completion</TableHead>
                      <TableHead>Assigned To</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredClaims.map((claim) => (
                      <TableRow key={claim.claim_id}>
                        <TableCell className="font-mono text-sm">{claim.claim_id}</TableCell>
                        <TableCell>{claim.patient_name}</TableCell>
                        <TableCell>
                          <Badge className={PRIORITY_COLORS[claim.priority as keyof typeof PRIORITY_COLORS]}>
                            {claim.priority === 1 ? 'Normal' : claim.priority === 2 ? 'High' : 'Urgent'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={STATUS_COLORS[claim.status as keyof typeof STATUS_COLORS]}>
                            {claim.status.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm">{formatDateTime(claim.submitted_at)}</TableCell>
                        <TableCell className="text-sm">{formatDateTime(claim.estimated_completion)}</TableCell>
                        <TableCell className="text-sm">{claim.assigned_processor || 'Unassigned'}</TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* AI Agents Tab */}
          <TabsContent value="agents" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>AI Agent Performance Monitor</CardTitle>
                <CardDescription>Real-time monitoring of AI agent performance and health</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {agentMetrics.map((agent) => (
                    <Card key={agent.agent_name} className="border-l-4 border-l-blue-500">
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <CardTitle className="text-lg">{agent.agent_name}</CardTitle>
                          <div className="flex items-center gap-2">
                            {getAgentStatusIcon(agent.status)}
                            <Badge variant={agent.status === 'active' ? 'default' : 'secondary'}>
                              {agent.status.toUpperCase()}
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm text-gray-600">Processed Today</p>
                            <p className="text-xl font-bold">{agent.processed_today}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Avg Confidence</p>
                            <p className="text-xl font-bold">{agent.avg_confidence}%</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Avg Processing Time</p>
                            <p className="text-xl font-bold">{agent.avg_processing_time}s</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Success Rate</p>
                            <p className="text-xl font-bold">{agent.success_rate}%</p>
                          </div>
                        </div>
                        <div className="mt-4 pt-4 border-t">
                          <p className="text-sm text-gray-600">
                            Last Activity: {formatDateTime(agent.last_activity)}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>User Management</CardTitle>
                    <CardDescription>Manage system users and permissions</CardDescription>
                  </div>
                  <Button size="sm">
                    <UserPlus className="h-4 w-4 mr-2" />
                    Add User
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {/* Filters */}
                <div className="flex gap-4 mb-6">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        placeholder="Search users..."
                        value={userSearch}
                        onChange={(e) => setUserSearch(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  <Select value={userRoleFilter} onValueChange={setUserRoleFilter}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Roles</SelectItem>
                      <SelectItem value="USER">Users</SelectItem>
                      <SelectItem value="PROCESSOR">Processors</SelectItem>
                      <SelectItem value="ADMIN">Admins</SelectItem>
                      <SelectItem value="SUPER_ADMIN">Super Admins</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Users Table */}
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Login</TableHead>
                      <TableHead>Failed Attempts</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{user.first_name} {user.last_name}</div>
                            <div className="text-sm text-gray-500">{user.username}</div>
                          </div>
                        </TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <Badge className={ROLE_COLORS[user.role as keyof typeof ROLE_COLORS]}>
                            {user.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {user.is_active ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-600" />
                            )}
                            <span className={user.is_active ? 'text-green-600' : 'text-red-600'}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">{formatDateTime(user.last_login_at)}</TableCell>
                        <TableCell>
                          <Badge variant={user.failed_login_attempts > 0 ? 'destructive' : 'secondary'}>
                            {user.failed_login_attempts}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Settings Tab */}
          <TabsContent value="system" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>System Configuration</CardTitle>
                  <CardDescription>Core system settings and parameters</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Auto-processing</p>
                      <p className="text-sm text-gray-600">Automatically process incoming claims</p>
                    </div>
                    <Button variant="outline" size="sm">
                      <Play className="h-4 w-4 mr-2" />
                      Enabled
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Fraud Detection</p>
                      <p className="text-sm text-gray-600">AI-powered fraud detection system</p>
                    </div>
                    <Button variant="outline" size="sm">
                      <Shield className="h-4 w-4 mr-2" />
                      Active
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Real-time Processing</p>
                      <p className="text-sm text-gray-600">Process claims in real-time</p>
                    </div>
                    <Button variant="outline" size="sm">
                      <Zap className="h-4 w-4 mr-2" />
                      Enabled
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Security Settings</CardTitle>
                  <CardDescription>Authentication and security configurations</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Two-Factor Authentication</p>
                      <p className="text-sm text-gray-600">Require 2FA for admin accounts</p>
                    </div>
                    <Button variant="outline" size="sm">
                      <Lock className="h-4 w-4 mr-2" />
                      Required
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Session Timeout</p>
                      <p className="text-sm text-gray-600">Automatic session expiration</p>
                    </div>
                    <Button variant="outline" size="sm">
                      <Clock className="h-4 w-4 mr-2" />
                      30 min
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Audit Logging</p>
                      <p className="text-sm text-gray-600">Comprehensive audit trail</p>
                    </div>
                    <Button variant="outline" size="sm">
                      <FileText className="h-4 w-4 mr-2" />
                      Enabled
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Notification System */}
      <NotificationSystem 
        isOpen={showNotifications} 
        onClose={() => setShowNotifications(false)} 
      />
    </div>
  );
}