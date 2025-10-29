import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Search, 
  Filter, 
  Download, 
  Eye, 
  MoreHorizontal, 
  Calendar,
  DollarSign,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Loader2,
  RefreshCw,
  Plus
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, Claim } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { DateRange } from 'react-day-picker';

interface ClaimFilters {
  search: string;
  status: string;
  priority: string;
  dateRange: DateRange | undefined;
  amountMin: string;
  amountMax: string;
}

const STATUS_COLORS = {
  submitted: 'bg-blue-100 text-blue-800',
  processing: 'bg-yellow-100 text-yellow-800',
  reviewed: 'bg-purple-100 text-purple-800',
  approved: 'bg-green-100 text-green-800',
  denied: 'bg-red-100 text-red-800',
  pending_info: 'bg-orange-100 text-orange-800',
};

const STATUS_ICONS = {
  submitted: Clock,
  processing: Loader2,
  reviewed: Eye,
  approved: CheckCircle,
  denied: XCircle,
  pending_info: AlertTriangle,
};

const PRIORITY_COLORS = {
  1: 'bg-gray-100 text-gray-800',
  2: 'bg-yellow-100 text-yellow-800',
  3: 'bg-red-100 text-red-800',
};

const PRIORITY_LABELS = {
  1: 'Normal',
  2: 'High',
  3: 'Urgent',
};

export default function EnterpriseViewClaims() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClaims, setSelectedClaims] = useState<string[]>([]);
  const [currentTab, setCurrentTab] = useState('all');

  const [filters, setFilters] = useState<ClaimFilters>({
    search: '',
    status: 'all',
    priority: 'all',
    dateRange: undefined,
    amountMin: '',
    amountMax: '',
  });

  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
  });

  useEffect(() => {
    fetchClaims();
  }, [currentTab, filters, pagination.page]);

  const fetchClaims = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getClaims({
        limit: pagination.limit,
        offset: (pagination.page - 1) * pagination.limit,
        status: filters.status === 'all' ? undefined : filters.status,
        priority: filters.priority === 'all' ? undefined : parseInt(filters.priority),
        search: filters.search || undefined,
        date_from: filters.dateRange?.from?.toISOString(),
        date_to: filters.dateRange?.to?.toISOString(),
        amount_min: filters.amountMin ? parseFloat(filters.amountMin) : undefined,
        amount_max: filters.amountMax ? parseFloat(filters.amountMax) : undefined,
      });

      setClaims(response.claims || []);
      setPagination(prev => ({ ...prev, total: response.total || 0 }));
    } catch (error) {
      toast({
        title: 'Error Loading Claims',
        description: 'Failed to fetch claims. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: keyof ClaimFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleSelectClaim = (claimId: string, checked: boolean) => {
    if (checked) {
      setSelectedClaims(prev => [...prev, claimId]);
    } else {
      setSelectedClaims(prev => prev.filter(id => id !== claimId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedClaims(claims.map(claim => claim.claim_id));
    } else {
      setSelectedClaims([]);
    }
  };

  const handleExport = async () => {
    try {
      const claimIds = selectedClaims.length > 0 ? selectedClaims : undefined;
      const response = await apiClient.exportClaims({ claim_ids: claimIds });
      
      // Create download link
      const blob = new Blob([response], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `claims-export-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);

      toast({
        title: 'Export Successful',
        description: `${selectedClaims.length || claims.length} claims exported successfully.`,
      });
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export claims. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const getStatusIcon = (status: string) => {
    const Icon = STATUS_ICONS[status as keyof typeof STATUS_ICONS] || Clock;
    return <Icon className="h-4 w-4" />;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getTabCounts = () => {
    const statusCounts = claims.reduce((acc, claim) => {
      acc[claim.status] = (acc[claim.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      all: claims.length,
      pending: (statusCounts.submitted || 0) + (statusCounts.processing || 0),
      approved: statusCounts.approved || 0,
      denied: statusCounts.denied || 0,
    };
  };

  const tabCounts = getTabCounts();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">My Claims</h1>
              <p className="text-gray-600 mt-1">
                Track and manage your healthcare claims
              </p>
            </div>
            <Button onClick={() => navigate('/user/submit-claim')}>
              <Plus className="h-4 w-4 mr-2" />
              New Claim
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="mb-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all" className="relative">
              All Claims
              {tabCounts.all > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {tabCounts.all}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="pending" className="relative">
              Pending
              {tabCounts.pending > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {tabCounts.pending}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="approved" className="relative">
              Approved
              {tabCounts.approved > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {tabCounts.approved}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="denied" className="relative">
              Denied
              {tabCounts.denied > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {tabCounts.denied}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search claims..."
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Status</label>
                <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="submitted">Submitted</SelectItem>
                    <SelectItem value="processing">Processing</SelectItem>
                    <SelectItem value="reviewed">Reviewed</SelectItem>
                    <SelectItem value="approved">Approved</SelectItem>
                    <SelectItem value="denied">Denied</SelectItem>
                    <SelectItem value="pending_info">Pending Info</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Priority</label>
                <Select value={filters.priority} onValueChange={(value) => handleFilterChange('priority', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Priorities</SelectItem>
                    <SelectItem value="1">Normal</SelectItem>
                    <SelectItem value="2">High</SelectItem>
                    <SelectItem value="3">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Date Range</label>
                <div className="flex gap-2">
                  <Input
                    type="date"
                    placeholder="From date"
                    onChange={(e) => handleFilterChange('dateRange', { from: new Date(e.target.value), to: filters.dateRange?.to })}
                  />
                  <Input
                    type="date"
                    placeholder="To date"
                    onChange={(e) => handleFilterChange('dateRange', { from: filters.dateRange?.from, to: new Date(e.target.value) })}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Min Amount</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    type="number"
                    placeholder="0.00"
                    value={filters.amountMin}
                    onChange={(e) => handleFilterChange('amountMin', e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Max Amount</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    type="number"
                    placeholder="10000.00"
                    value={filters.amountMax}
                    onChange={(e) => handleFilterChange('amountMax', e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center mt-4">
              <Button variant="outline" onClick={() => setFilters({
                search: '',
                status: 'all',
                priority: 'all',
                dateRange: undefined,
                amountMin: '',
                amountMax: '',
              })}>
                Clear Filters
              </Button>

              <div className="flex gap-2">
                <Button variant="outline" onClick={fetchClaims}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </Button>
                <Button variant="outline" onClick={handleExport} disabled={loading}>
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Claims Table */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Claims List</CardTitle>
              {selectedClaims.length > 0 && (
                <Badge variant="secondary">
                  {selectedClaims.length} selected
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-600">Loading claims...</span>
              </div>
            ) : claims.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No claims found</h3>
                <p className="text-gray-600 mb-4">
                  {Object.values(filters).some(f => f !== 'all' && f !== '' && f !== undefined)
                    ? 'Try adjusting your filters or search criteria.'
                    : 'Get started by submitting your first claim.'}
                </p>
                <Button onClick={() => navigate('/user/submit-claim')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Submit New Claim
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">
                        <Checkbox
                          checked={selectedClaims.length === claims.length}
                          onCheckedChange={handleSelectAll}
                        />
                      </TableHead>
                      <TableHead>Claim ID</TableHead>
                      <TableHead>Patient</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Submitted</TableHead>
                      <TableHead>Updated</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {claims.map((claim) => (
                      <TableRow key={claim.claim_id} className="hover:bg-gray-50">
                        <TableCell>
                          <Checkbox
                            checked={selectedClaims.includes(claim.claim_id)}
                            onCheckedChange={(checked) => 
                              handleSelectClaim(claim.claim_id, checked as boolean)
                            }
                          />
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {claim.claim_id}
                        </TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{claim.patient_name}</div>
                            <div className="text-sm text-gray-500">{claim.patient_id}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={`${STATUS_COLORS[claim.status as keyof typeof STATUS_COLORS]} flex items-center gap-1 w-fit`}>
                            {getStatusIcon(claim.status)}
                            {claim.status.replace('_', ' ').toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={PRIORITY_COLORS[claim.priority as keyof typeof PRIORITY_COLORS]}>
                            {PRIORITY_LABELS[claim.priority as keyof typeof PRIORITY_LABELS]}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-medium">
                          {formatCurrency(claim.claim_amount)}
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {formatDate(claim.created_at)}
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {formatDate(claim.updated_at)}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem 
                                onClick={() => navigate(`/user/claim/${claim.claim_id}`)}
                              >
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleExport()}>
                                <Download className="h-4 w-4 mr-2" />
                                Download
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {/* Pagination */}
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Showing {((pagination.page - 1) * pagination.limit) + 1} to{' '}
                    {Math.min(pagination.page * pagination.limit, pagination.total)} of{' '}
                    {pagination.total} claims
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                      disabled={pagination.page === 1}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                      disabled={pagination.page * pagination.limit >= pagination.total}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}