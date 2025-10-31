import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  ArrowLeft, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Brain, 
  Shield, 
  FileText, 
  User, 
  Building, 
  Calendar,
  DollarSign,
  Eye,
  Loader2,
  Bot,
  TrendingUp,
  Activity,
  Target,
  Timer,
  Zap,
  Download,
  RefreshCw,
  Award
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { apiClient, ClaimDetails, formatCurrency, formatDate, formatDateTime } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

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

const AGENT_ICONS = {
  'Intake Agent': FileText,
  'Eligibility Agent': User,
  'Clinical Review Agent': Brain,
  'Fraud Detection Agent': Shield,
  'Final Adjudication Agent': Award,
};

const AGENT_COLORS = {
  'Intake Agent': 'bg-blue-50 border-blue-200',
  'Eligibility Agent': 'bg-green-50 border-green-200',
  'Clinical Review Agent': 'bg-purple-50 border-purple-200',
  'Fraud Detection Agent': 'bg-red-50 border-red-200',
  'Final Adjudication Agent': 'bg-orange-50 border-orange-200',
};

const RISK_LEVEL_COLORS = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-red-100 text-red-800',
};

export default function EnterpriseClaimDetails() {
  const { claimId } = useParams<{ claimId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();

  const [claimDetails, setClaimDetails] = useState<ClaimDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (claimId) {
      fetchClaimDetails();
    }
  }, [claimId]);

  const fetchClaimDetails = async () => {
    if (!claimId) return;

    setLoading(true);
    try {
      const details = await apiClient.getClaimDetails(claimId);
      setClaimDetails(details);
    } catch (error) {
      toast({
        title: 'Error Loading Claim',
        description: 'Failed to fetch claim details. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReprocess = async () => {
    if (!claimId) return;

    setProcessing(true);
    try {
      await apiClient.processClaim(claimId, claimDetails?.claim.priority);
      toast({
        title: 'Claim Reprocessing Started',
        description: 'The claim has been queued for reprocessing.',
      });
      
      // Refresh details after a short delay
      setTimeout(fetchClaimDetails, 2000);
    } catch (error) {
      toast({
        title: 'Reprocessing Failed',
        description: 'Failed to reprocess claim. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="text-lg text-gray-600">Loading claim details...</span>
        </div>
      </div>
    );
  }

  if (!claimDetails) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Claim Not Found</h2>
          <p className="text-gray-600 mb-4">The requested claim could not be found.</p>
          <Button onClick={() => navigate('/user/claims')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Claims
          </Button>
        </div>
      </div>
    );
  }

  const { claim, decision_log, agent_reports, fraud_analysis } = claimDetails;
  const StatusIcon = STATUS_ICONS[claim.status as keyof typeof STATUS_ICONS] || Clock;

  const getProcessingProgress = () => {
    if (!agent_reports.length) return 0;
    const completedAgents = agent_reports.filter(report => report.status === 'completed').length;
    return (completedAgents / agent_reports.length) * 100;
  };

  const getTotalProcessingTime = () => {
    if (!agent_reports.length) return 0;
    return agent_reports.reduce((total, report) => total + report.duration_seconds, 0);
  };

  const getAverageConfidence = () => {
    if (!agent_reports.length) return 0;
    const totalConfidence = agent_reports.reduce((sum, report) => sum + report.confidence_score, 0);
    return totalConfidence / agent_reports.length;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => navigate('/user/claims')}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Claims
              </Button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Claim Details</h1>
                <p className="text-gray-600 mt-1 font-mono text-sm">{claim.claim_id}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge className={`${STATUS_COLORS[claim.status as keyof typeof STATUS_COLORS]} flex items-center gap-1`}>
                <StatusIcon className="h-4 w-4" />
                {claim.status.replace('_', ' ').toUpperCase()}
              </Badge>
              {(user?.role === 'PROCESSOR' || user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN') && (
                <Button 
                  onClick={handleReprocess} 
                  disabled={processing || claim.status === 'processing'}
                  size="sm"
                >
                  {processing ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Reprocess
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                <span className="text-sm font-medium text-gray-600">Claim Amount</span>
              </div>
              <p className="text-2xl font-bold mt-2">{formatCurrency(claim.claim_amount)}</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-2">
                <Timer className="h-5 w-5 text-blue-600" />
                <span className="text-sm font-medium text-gray-600">Processing Time</span>
              </div>
              <p className="text-2xl font-bold mt-2">{Math.round(getTotalProcessingTime())}s</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-purple-600" />
                <span className="text-sm font-medium text-gray-600">Avg Confidence</span>
              </div>
              <p className="text-2xl font-bold mt-2">{Math.round(getAverageConfidence())}%</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-orange-600" />
                <span className="text-sm font-medium text-gray-600">Agents Used</span>
              </div>
              <p className="text-2xl font-bold mt-2">{agent_reports.length}</p>
            </CardContent>
          </Card>
        </div>

        {/* Processing Progress */}
        {claim.status === 'processing' && (
          <Alert className="mb-8">
            <Loader2 className="h-4 w-4 animate-spin" />
            <AlertDescription>
              <div className="flex justify-between items-center">
                <span>Processing in progress...</span>
                <span className="text-sm">{Math.round(getProcessingProgress())}% complete</span>
              </div>
              <Progress value={getProcessingProgress()} className="mt-2" />
            </AlertDescription>
          </Alert>
        )}

        {/* Fraud Alert */}
        {fraud_analysis?.is_flagged && (
          <Alert className="mb-8 border-red-200 bg-red-50">
            <Shield className="h-4 w-4 text-red-600" />
            <AlertDescription>
              <div className="flex justify-between items-center">
                <span className="font-medium text-red-800">
                  Fraud Alert: This claim has been flagged for potential fraud
                </span>
                <Badge className={RISK_LEVEL_COLORS[fraud_analysis.risk_level as keyof typeof RISK_LEVEL_COLORS]}>
                  {fraud_analysis.risk_level.toUpperCase()} RISK
                </Badge>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="timeline">Agent Timeline</TabsTrigger>
            <TabsTrigger value="decision">Decision Log</TabsTrigger>
            <TabsTrigger value="fraud">Fraud Analysis</TabsTrigger>
            <TabsTrigger value="reasoning">AI Reasoning</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Patient Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Patient Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Name</label>
                      <p className="text-sm mt-1">{claim.patient_name}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Patient ID</label>
                      <p className="text-sm mt-1 font-mono">{claim.patient_id}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Insurance Provider</label>
                      <p className="text-sm mt-1">{claim.insurance_provider}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Policy Number</label>
                      <p className="text-sm mt-1 font-mono">{claim.policy_number}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Medical Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    Medical Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Diagnosis Code</label>
                      <p className="text-sm mt-1 font-mono">{claim.diagnosis_code}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Procedure Code</label>
                      <p className="text-sm mt-1 font-mono">{claim.procedure_code}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Service Date</label>
                      <p className="text-sm mt-1">{formatDate(claim.service_date)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600">Claim Amount</label>
                      <p className="text-sm mt-1 font-semibold">{formatCurrency(claim.claim_amount)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Provider Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building className="h-5 w-5" />
                    Provider Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">Provider Name</label>
                      <p className="text-sm mt-1">{claim.provider_name}</p>
                    </div>
                    {claim.provider_npi && (
                      <div>
                        <label className="text-sm font-medium text-gray-600">Provider NPI</label>
                        <p className="text-sm mt-1 font-mono">{claim.provider_npi}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Claim Status */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    Claim Timeline
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-600">Submitted</span>
                      <span className="text-sm">{formatDateTime(claim.created_at)}</span>
                    </div>
                    {claim.processed_at && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-600">Processed</span>
                        <span className="text-sm">{formatDateTime(claim.processed_at)}</span>
                      </div>
                    )}
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-600">Priority</span>
                      <Badge variant={claim.priority > 1 ? 'destructive' : 'secondary'}>
                        {claim.priority === 1 ? 'Normal' : claim.priority === 2 ? 'High' : 'Urgent'}
                      </Badge>
                    </div>
                  </div>
                  
                  {claim.notes && (
                    <>
                      <Separator />
                      <div>
                        <label className="text-sm font-medium text-gray-600">Notes</label>
                        <p className="text-sm mt-1 text-gray-700">{claim.notes}</p>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Agent Timeline Tab */}
          <TabsContent value="timeline" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-5 w-5" />
                  AI Agent Processing Timeline
                </CardTitle>
                <CardDescription>
                  Detailed timeline of AI agent processing steps and decisions
                </CardDescription>
              </CardHeader>
              <CardContent>
                {agent_reports.length === 0 ? (
                  <div className="text-center py-8">
                    <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No agent processing data available</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {agent_reports
                      .sort((a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime())
                      .map((report, index) => {
                        const AgentIcon = AGENT_ICONS[report.agent_name as keyof typeof AGENT_ICONS] || Bot;
                        const isCompleted = report.status === 'completed';
                        
                        return (
                          <div key={index} className="relative">
                            {/* Timeline connector */}
                            {index < agent_reports.length - 1 && (
                              <div className="absolute left-6 top-12 w-0.5 h-16 bg-gray-200" />
                            )}
                            
                            <div className={`flex gap-4 p-4 rounded-lg border-2 ${
                              AGENT_COLORS[report.agent_name as keyof typeof AGENT_COLORS] || 'bg-gray-50 border-gray-200'
                            }`}>
                              <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                                isCompleted ? 'bg-green-100' : 'bg-gray-100'
                              }`}>
                                <AgentIcon className={`h-6 w-6 ${
                                  isCompleted ? 'text-green-600' : 'text-gray-600'
                                }`} />
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-2">
                                  <h3 className="font-semibold text-gray-900">{report.agent_name}</h3>
                                  <div className="flex items-center gap-2">
                                    <Badge variant={isCompleted ? 'default' : 'secondary'}>
                                      {report.status}
                                    </Badge>
                                    <span className="text-sm text-gray-600">
                                      {Math.round(report.duration_seconds)}s
                                    </span>
                                  </div>
                                </div>
                                
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                                  <div>
                                    <span className="text-xs text-gray-600">Confidence</span>
                                    <p className="font-medium">{Math.round(report.confidence_score)}%</p>
                                  </div>
                                  <div>
                                    <span className="text-xs text-gray-600">Reasoning Steps</span>
                                    <p className="font-medium">{report.reasoning_steps.length}</p>
                                  </div>
                                  <div>
                                    <span className="text-xs text-gray-600">Tools Used</span>
                                    <p className="font-medium">{report.tool_usage.length}</p>
                                  </div>
                                  <div>
                                    <span className="text-xs text-gray-600">Result</span>
                                    <p className="font-medium text-sm">{report.result}</p>
                                  </div>
                                </div>
                                
                                <div className="text-sm text-gray-600">
                                  <p><strong>Started:</strong> {formatDateTime(report.started_at)}</p>
                                  {isCompleted && (
                                    <p><strong>Completed:</strong> {formatDateTime(report.completed_at)}</p>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Decision Log Tab */}
          <TabsContent value="decision" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Award className="h-5 w-5" />
                  Final Decision Log
                </CardTitle>
                <CardDescription>
                  Final adjudication decision and reasoning
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!decision_log ? (
                  <div className="text-center py-8">
                    <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">Decision pending - claim still processing</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                            <span className="text-sm font-medium">Decision</span>
                          </div>
                          <p className="text-lg font-bold mt-2 capitalize">{decision_log.decision}</p>
                        </CardContent>
                      </Card>
                      
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-blue-600" />
                            <span className="text-sm font-medium">Confidence</span>
                          </div>
                          <p className="text-lg font-bold mt-2">{Math.round(decision_log.confidence_score)}%</p>
                        </CardContent>
                      </Card>
                      
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <Shield className="h-5 w-5 text-orange-600" />
                            <span className="text-sm font-medium">Fraud Score</span>
                          </div>
                          <p className="text-lg font-bold mt-2">{Math.round(decision_log.fraud_score)}%</p>
                        </CardContent>
                      </Card>
                    </div>
                    
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Decision Reasoning</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-gray-700 leading-relaxed">{decision_log.reasoning_text}</p>
                        
                        <Separator className="my-4" />
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">Processing Time:</span>
                            <span className="ml-2 font-medium">{Math.round(decision_log.processing_time_seconds)}s</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Decision Date:</span>
                            <span className="ml-2 font-medium">{formatDateTime(decision_log.created_at)}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Fraud Analysis Tab */}
          <TabsContent value="fraud" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Fraud Risk Analysis
                </CardTitle>
                <CardDescription>
                  AI-powered fraud detection and risk assessment
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!fraud_analysis ? (
                  <div className="text-center py-8">
                    <Shield className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">Fraud analysis not available</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <Card className={fraud_analysis.is_flagged ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            {fraud_analysis.is_flagged ? (
                              <AlertTriangle className="h-5 w-5 text-red-600" />
                            ) : (
                              <CheckCircle className="h-5 w-5 text-green-600" />
                            )}
                            <span className="text-sm font-medium">Status</span>
                          </div>
                          <p className={`text-lg font-bold mt-2 ${
                            fraud_analysis.is_flagged ? 'text-red-700' : 'text-green-700'
                          }`}>
                            {fraud_analysis.is_flagged ? 'Flagged' : 'Clean'}
                          </p>
                        </CardContent>
                      </Card>
                      
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-orange-600" />
                            <span className="text-sm font-medium">Fraud Score</span>
                          </div>
                          <p className="text-lg font-bold mt-2">{Math.round(fraud_analysis.fraud_score)}%</p>
                        </CardContent>
                      </Card>
                      
                      <Card>
                        <CardContent className="p-4">
                          <div className="flex items-center gap-2">
                            <Activity className="h-5 w-5 text-purple-600" />
                            <span className="text-sm font-medium">Risk Level</span>
                          </div>
                          <Badge className={`mt-2 ${RISK_LEVEL_COLORS[fraud_analysis.risk_level as keyof typeof RISK_LEVEL_COLORS]}`}>
                            {fraud_analysis.risk_level.toUpperCase()}
                          </Badge>
                        </CardContent>
                      </Card>
                    </div>
                    
                    {fraud_analysis.risk_factors.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-lg">Risk Factors Identified</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {fraud_analysis.risk_factors.map((factor, index) => (
                              <div key={index} className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <AlertTriangle className="h-4 w-4 text-yellow-600 flex-shrink-0" />
                                <span className="text-sm text-yellow-800">{factor}</span>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* AI Reasoning Tab */}
          <TabsContent value="reasoning" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  AI Reasoning & Tool Usage
                </CardTitle>
                <CardDescription>
                  Detailed AI reasoning steps and tool interactions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {agent_reports.map((report, agentIndex) => (
                    <Card key={agentIndex} className="border-l-4 border-l-blue-500">
                      <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                          <Bot className="h-5 w-5" />
                          {report.agent_name} - Reasoning Steps
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        {report.reasoning_steps.length === 0 ? (
                          <p className="text-gray-600 italic">No reasoning steps recorded</p>
                        ) : (
                          <div className="space-y-4">
                            {report.reasoning_steps.map((step: any, stepIndex: number) => (
                              <div key={stepIndex} className="border-l-2 border-gray-200 pl-4">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                                    Step {stepIndex + 1}
                                  </span>
                                  <span className="text-sm text-gray-600">Reasoning</span>
                                </div>
                                <p className="text-sm text-gray-700">
                                  {typeof step === 'string' ? step : (step.content || step.thought || step.text || 'No content available')}
                                </p>
                                {typeof step === 'object' && step.action && (
                                  <p className="text-sm text-blue-600 mt-1"><strong>Action:</strong> {step.action}</p>
                                )}
                                {typeof step === 'object' && step.observation && (
                                  <p className="text-sm text-green-600 mt-1"><strong>Observation:</strong> {step.observation}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                        
                        {report.tool_usage.length > 0 && (
                          <>
                            <Separator className="my-4" />
                            <div>
                              <h4 className="font-medium mb-3 flex items-center gap-2">
                                <Zap className="h-4 w-4" />
                                Tools Used
                              </h4>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {report.tool_usage.map((toolItem: any, toolIndex: number) => {
                                  // Handle different tool data structures
                                  let toolName = 'Unknown Tool';
                                  let executionTime = '0';
                                  let description = 'No description available';
                                  let result = 'N/A';
                                  
                                  if (typeof toolItem === 'object') {
                                    if (toolItem.tool_name) {
                                      // Expected structure
                                      toolName = toolItem.tool_name;
                                      executionTime = toolItem.execution_time || '0';
                                      description = toolItem.description || 'No description available';
                                      result = toolItem.result || 'N/A';
                                    } else if (toolItem.tool) {
                                      // Current API structure - extract tool name from tool string
                                      const toolString = toolItem.tool.toString();
                                      const toolNameMatch = toolString.match(/tool_name='([^']+)'/);
                                      toolName = toolNameMatch ? toolNameMatch[1] : 'Unknown Tool';
                                      
                                      // Extract execution time if available
                                      const timeMatch = toolString.match(/execution_time=([0-9.]+)/);
                                      executionTime = timeMatch ? Math.round(parseFloat(timeMatch[1]) * 1000).toString() : '0';
                                      
                                      description = `Tool call with parameters`;
                                      result = toolItem.result || 'success';
                                    }
                                  }
                                  
                                  return (
                                    <div key={toolIndex} className="p-3 bg-gray-50 rounded-lg">
                                      <div className="flex items-center justify-between mb-2">
                                        <span className="font-medium text-sm">{toolName}</span>
                                        <Badge variant="outline" className="text-xs">
                                          {executionTime}ms
                                        </Badge>
                                      </div>
                                      <p className="text-xs text-gray-600">{description}</p>
                                      <p className="text-xs text-green-600 mt-1">
                                        <strong>Result:</strong> {typeof result === 'string' ? result : JSON.stringify(result)}
                                      </p>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}