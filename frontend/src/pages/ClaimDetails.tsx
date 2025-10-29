import { useState, useEffect } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowLeft, 
  Activity, 
  FileText, 
  Shield, 
  Brain, 
  Settings, 
  Clock, 
  User, 
  Building, 
  CreditCard, 
  Calendar,
  Loader2,
  Play,
  CheckCircle,
  AlertTriangle
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { 
  apiClient, 
  type Claim,
  ClaimDetails, 
  getStatusColor, 
  getStatusLabel, 
  formatCurrency, 
  formatDateTime 
} from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

const ClaimDetailsPage = () => {
  const { claimId } = useParams<{ claimId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { userType } = useAuth();
  const [claim, setClaim] = useState<ClaimDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [fraudAnalysis, setFraudAnalysis] = useState<any>(null);
  const [agentTimeline, setAgentTimeline] = useState<any>(null);

  useEffect(() => {
    if (claimId) {
      loadClaimDetails();
    }
  }, [claimId]);

  const loadClaimDetails = async () => {
    if (!claimId) return;
    
    try {
      setIsLoading(true);
      const claimData = await apiClient.getClaimDetails(claimId);
      setClaim(claimData);

      // Load additional data for admin users
      if (userType === 'admin') {
        // TODO: Implement fraud analysis API endpoint
        // try {
        //   const fraudData = await apiClient.getFraudAnalysis(claimId);
        //   setFraudAnalysis(fraudData);
        // } catch (error) {
        //   // Fraud analysis might not exist yet
        // }

        try {
          const timelineData = await apiClient.getAgentTimeline(claimId);
          setAgentTimeline(timelineData);
        } catch (error) {
          // Agent timeline might not exist yet
        }
      }
    } catch (error) {
      toast({
        title: "Error Loading Claim",
        description: error instanceof Error ? error.message : "Failed to load claim details",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcessClaim = async () => {
    if (!claimId) return;
    
    try {
      setIsProcessing(true);
      const result = await apiClient.processClaim(claimId);
      
      toast({
        title: "Claim Processed",
        description: `Claim has been ${result.decision.toLowerCase()} with ${result.confidence_score}% confidence`,
      });

      // Reload claim details
      await loadClaimDetails();
    } catch (error) {
      toast({
        title: "Processing Failed",
        description: error instanceof Error ? error.message : "Failed to process claim",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const getBackPath = () => {
    return userType === 'admin' ? '/admin/claims' : '/user/claims';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading claim details...</p>
        </div>
      </div>
    );
  }

  if (!claim) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Claim not found</p>
          <Link to={getBackPath()}>
            <Button>Back to Claims</Button>
          </Link>
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
            <Link to={getBackPath()}>
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2" />
                Back to Claims
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
                <Activity className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">{claim.claim.claim_id}</h1>
                <p className="text-xs text-muted-foreground">Claim Details</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge variant={getStatusColor(claim.claim.status) as any} className="text-sm">
              {getStatusLabel(claim.claim.status)}
            </Badge>
            {userType === 'admin' && claim.claim.status === 'PENDING' && (
              <Button 
                onClick={handleProcessClaim} 
                disabled={isProcessing}
                size="sm"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Process Claim
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="details">Details</TabsTrigger>
            {userType === 'admin' && <TabsTrigger value="analysis">Analysis</TabsTrigger>}
            {userType === 'admin' && <TabsTrigger value="processing">Processing</TabsTrigger>}
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Claim Summary */}
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <FileText className="w-6 h-6 text-primary" />
                  <h3 className="text-lg font-semibold">Claim Summary</h3>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Amount:</span>
                    <span className="font-semibold text-lg">{formatCurrency(claim.claim.claim_amount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Service Date:</span>
                    <span>{new Date(claim.claim.service_date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Submitted:</span>
                    <span>{formatDateTime(claim.claim.created_at)}</span>
                  </div>
                  {claim.claim.processed_at && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Processed:</span>
                      <span>{formatDateTime(claim.claim.processed_at)}</span>
                    </div>
                  )}
                </div>
              </Card>

              {/* Patient Information */}
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <User className="w-6 h-6 text-info" />
                  <h3 className="text-lg font-semibold">Patient Information</h3>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <p className="text-muted-foreground text-sm">Name</p>
                    <p className="font-medium">{claim.claim.patient_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Patient ID</p>
                    <p className="font-medium">{claim.claim.patient_id}</p>
                  </div>
                </div>
              </Card>

              {/* Insurance Information */}
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Shield className="w-6 h-6 text-success" />
                  <h3 className="text-lg font-semibold">Insurance Information</h3>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <p className="text-muted-foreground text-sm">Provider</p>
                    <p className="font-medium">{claim.claim.insurance_provider}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Policy Number</p>
                    <p className="font-medium">{claim.claim.policy_number}</p>
                  </div>
                </div>
              </Card>

              {/* Provider Information */}
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Building className="w-6 h-6 text-warning" />
                  <h3 className="text-lg font-semibold">Provider Information</h3>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <p className="text-muted-foreground text-sm">Provider Name</p>
                    <p className="font-medium">{claim.claim.provider_name}</p>
                  </div>
                  {claim.claim.provider_npi && (
                    <div>
                      <p className="text-sm text-muted-foreground">Provider NPI</p>
                      <p className="font-medium">{claim.claim.provider_npi}</p>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            {/* Decision Information */}
            {claim.decision_log && (
              <Card className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Brain className="w-6 h-6 text-primary" />
                  <h3 className="text-lg font-semibold">Decision Information</h3>
                </div>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <p className="text-muted-foreground text-sm mb-1">Decision</p>
                    <Badge variant={claim.decision_log.decision === 'APPROVE' ? 'success' : 
                                  claim.decision_log.decision === 'DENY' ? 'destructive' : 'warning'}>
                      {claim.decision_log.decision}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-sm mb-1">Confidence Score</p>
                    <div className="flex items-center gap-2">
                      <Progress value={claim.decision_log.confidence_score} className="flex-1" />
                      <span className="text-sm font-medium">{claim.decision_log.confidence_score}%</span>
                    </div>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-muted-foreground text-sm mb-2">Reasoning</p>
                    <p className="text-sm bg-accent/30 p-3 rounded-md">{claim.decision_log.reasoning_text}</p>
                  </div>
                </div>
              </Card>
            )}
          </TabsContent>

          {/* Details Tab */}
          <TabsContent value="details" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Medical Codes</h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <p className="text-muted-foreground text-sm">Diagnosis Code (ICD-10)</p>
                  <p className="font-medium text-lg">{claim.claim.diagnosis_code}</p>
                </div>
                <div>
                  <p className="text-muted-foreground text-sm">Procedure Code (CPT)</p>
                  <p className="font-medium text-lg">{claim.claim.procedure_code}</p>
                </div>
              </div>
            </Card>

            {claim.claim.notes && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Additional Notes</h3>
                <p className="text-sm bg-accent/30 p-4 rounded-md">{claim.claim.notes}</p>
              </Card>
            )}

            {/* TODO: Add exception_logs field to ClaimDetails interface once backend supports it */}
            {/* {claim.exception_logs && claim.exception_logs.length > 0 && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">Exception Logs</h3>
                <div className="space-y-3">
                  {claim.exception_logs.map((exception, index) => (
                    <div key={index} className="border-l-4 border-warning pl-4 py-2">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className="w-4 h-4 text-warning" />
                        <span className="font-medium">{exception.exception_type}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDateTime(exception.created_at)}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">{exception.resolution_action}</p>
                    </div>
                  ))}
                </div>
              </Card>
            )} */}
          </TabsContent>

          {/* Analysis Tab (Admin Only) */}
          {userType === 'admin' && (
            <TabsContent value="analysis" className="space-y-6">
              {fraudAnalysis ? (
                <Card className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Shield className="w-6 h-6 text-destructive" />
                    <h3 className="text-lg font-semibold">Fraud Analysis</h3>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-muted-foreground text-sm mb-1">Fraud Score</p>
                      <div className="flex items-center gap-2">
                        <Progress 
                          value={fraudAnalysis.fraud_score} 
                          className="flex-1"
                          // @ts-ignore
                          indicatorClassName={fraudAnalysis.fraud_score > 70 ? "bg-destructive" : 
                                            fraudAnalysis.fraud_score > 40 ? "bg-warning" : "bg-success"}
                        />
                        <span className="text-sm font-medium">{fraudAnalysis.fraud_score}%</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-sm mb-1">Status</p>
                      <Badge variant={fraudAnalysis.is_flagged ? 'destructive' : 'success'}>
                        {fraudAnalysis.is_flagged ? 'Flagged' : 'Clear'}
                      </Badge>
                    </div>
                    {fraudAnalysis.risk_factors.length > 0 && (
                      <div className="md:col-span-2">
                        <p className="text-muted-foreground text-sm mb-2">Risk Factors</p>
                        <div className="flex flex-wrap gap-2">
                          {fraudAnalysis.risk_factors.map((factor: string, index: number) => (
                            <Badge key={index} variant="outline">{factor}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>
              ) : (
                <Card className="p-6 text-center">
                  <p className="text-muted-foreground">No fraud analysis available</p>
                </Card>
              )}
            </TabsContent>
          )}

          {/* Processing Tab (Admin Only) */}
          {userType === 'admin' && (
            <TabsContent value="processing" className="space-y-6">
              {agentTimeline ? (
                <Card className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Brain className="w-6 h-6 text-info" />
                    <h3 className="text-lg font-semibold">Agent Processing Timeline</h3>
                  </div>
                  
                  <div className="space-y-4">
                    {agentTimeline.agents?.map((agent: any, index: number) => (
                      <div key={index} className="flex items-center gap-4 p-4 border rounded-lg">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <CheckCircle className="w-5 h-5 text-primary" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium">{agent.name}</h4>
                          <p className="text-sm text-muted-foreground">{agent.description}</p>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {agent.duration && `${agent.duration}s`}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              ) : (
                <Card className="p-6 text-center">
                  <p className="text-muted-foreground">No processing timeline available</p>
                </Card>
              )}
            </TabsContent>
          )}
        </Tabs>
      </main>
    </div>
  );
};

export default ClaimDetailsPage;