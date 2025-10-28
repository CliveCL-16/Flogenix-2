import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Activity, Search, Filter, Eye, Loader2, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient, Claim, ClaimStatus, getStatusColor, getStatusLabel, formatCurrency, formatDateTime } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

const ViewClaims = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { userType } = useAuth();
  const [claims, setClaims] = useState<Claim[]>([]);
  const [filteredClaims, setFilteredClaims] = useState<Claim[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<ClaimStatus | "ALL">("ALL");
  const [sortBy, setSortBy] = useState<"date" | "amount" | "status">("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    loadClaims();
  }, []);

  useEffect(() => {
    filterAndSortClaims();
  }, [claims, searchTerm, statusFilter, sortBy, sortOrder]);

  const loadClaims = async () => {
    try {
      setIsLoading(true);
      const claimsData = await apiClient.getClaims();
      setClaims(claimsData);
    } catch (error) {
      toast({
        title: "Error Loading Claims",
        description: error instanceof Error ? error.message : "Failed to load claims",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const filterAndSortClaims = () => {
    let filtered = [...claims];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(claim =>
        claim.claim_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        claim.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        claim.insurance_provider.toLowerCase().includes(searchTerm.toLowerCase()) ||
        claim.provider_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== "ALL") {
      filtered = filtered.filter(claim => claim.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case "date":
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
          break;
        case "amount":
          aValue = a.claim_amount;
          bValue = b.claim_amount;
          break;
        case "status":
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredClaims(filtered);
  };

  const getBackPath = () => {
    return userType === 'admin' ? '/admin' : '/user';
  };

  const getClaimDetailPath = (claimId: string) => {
    return userType === 'admin' ? `/admin/claim/${claimId}` : `/user/claim/${claimId}`;
  };

  const handleRefresh = () => {
    loadClaims();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to={getBackPath()}>
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2" />
                Back to Portal
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
                <Activity className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">Claims Management</h1>
                <p className="text-xs text-muted-foreground">
                  {userType === 'admin' ? 'All system claims' : 'Your submitted claims'}
                </p>
              </div>
            </div>
          </div>
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Filters and Search */}
        <Card className="p-6 mb-6">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                placeholder="Search by claim ID, patient, provider, or insurer..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex gap-2 items-center">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as ClaimStatus | "ALL")}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value={ClaimStatus.PENDING}>Pending</SelectItem>
                  <SelectItem value={ClaimStatus.APPROVED}>Approved</SelectItem>
                  <SelectItem value={ClaimStatus.DENIED}>Denied</SelectItem>
                  <SelectItem value={ClaimStatus.PENDING_REVIEW}>Pending Review</SelectItem>
                  <SelectItem value={ClaimStatus.FRAUD_FLAGGED}>Fraud Flagged</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={(value) => setSortBy(value as "date" | "amount" | "status")}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="amount">Amount</SelectItem>
                  <SelectItem value="status">Status</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
              >
                {sortOrder === "asc" ? "↑" : "↓"}
              </Button>
            </div>
          </div>
        </Card>

        {/* Claims List */}
        {isLoading ? (
          <Card className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Loading claims...</p>
          </Card>
        ) : filteredClaims.length === 0 ? (
          <Card className="p-8 text-center">
            <p className="text-muted-foreground mb-4">
              {claims.length === 0 ? "No claims found" : "No claims match your current filters"}
            </p>
            {userType === 'user' && claims.length === 0 && (
              <Link to="/user/submit-claim">
                <Button>Submit Your First Claim</Button>
              </Link>
            )}
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredClaims.map((claim) => (
              <Card key={claim.claim_id} className="p-6 hover:shadow-lg transition-all duration-200">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-foreground">{claim.claim_id}</h3>
                      <Badge variant={getStatusColor(claim.status) as any}>
                        {getStatusLabel(claim.status)}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Patient</p>
                        <p className="font-medium text-foreground">{claim.patient_name}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Provider</p>
                        <p className="font-medium text-foreground">{claim.provider_name}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Insurance</p>
                        <p className="font-medium text-foreground">{claim.insurance_provider}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Amount</p>
                        <p className="font-semibold text-foreground">{formatCurrency(claim.claim_amount)}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Service Date</p>
                        <p className="font-medium text-foreground">
                          {new Date(claim.service_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Submitted</p>
                        <p className="font-medium text-foreground">{formatDateTime(claim.created_at)}</p>
                      </div>
                    </div>

                    {claim.processed_at && (
                      <div className="mt-2 text-sm">
                        <span className="text-muted-foreground">Processed: </span>
                        <span className="font-medium text-foreground">{formatDateTime(claim.processed_at)}</span>
                      </div>
                    )}
                  </div>

                  <div className="ml-6">
                    <Link to={getClaimDetailPath(claim.claim_id)}>
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4 mr-2" />
                        View Details
                      </Button>
                    </Link>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Summary */}
        {!isLoading && filteredClaims.length > 0 && (
          <Card className="p-4 mt-6">
            <div className="flex justify-between items-center text-sm text-muted-foreground">
              <span>Showing {filteredClaims.length} of {claims.length} claims</span>
              {searchTerm || statusFilter !== "ALL" ? (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearchTerm("");
                    setStatusFilter("ALL");
                  }}
                >
                  Clear Filters
                </Button>
              ) : null}
            </div>
          </Card>
        )}
      </main>
    </div>
  );
};

export default ViewClaims;