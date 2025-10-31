import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { 
  ArrowLeft, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  FileText, 
  Brain, 
  Shield, 
  Eye, 
  Download,
  MessageCircle,
  User,
  Building,
  Calendar,
  DollarSign,
  RefreshCw,
  Loader2,
  Send,
  Bot,
  TrendingUp,
  AlertTriangle
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { 
  apiClient, 
  ClaimDetails,
  AgentTimeline,
  formatCurrency, 
  formatDateTime 
} from "@/lib/api";

interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  status: 'completed' | 'current' | 'pending' | 'failed';
  timestamp?: string;
  duration?: number;
  confidence?: number;
  details?: string;
  icon: any;
}

interface AIDecisionSummary {
  decision: string;
  confidence_score: number;
  risk_level: string;
  reasoning: string[];
  next_steps: string[];
  fraud_indicators?: string[];
  estimated_processing_time?: number;
}

interface DocumentStatus {
  id: string;
  name: string;
  type: string;
  upload_time: string;
  ocr_status: 'pending' | 'processing' | 'completed' | 'failed';
  extraction_confidence: number;
  extracted_fields: Record<string, any>;
  validation_status: 'pending' | 'validated' | 'needs_review';
}

interface CommunicationMessage {
  id: string;
  sender: 'user' | 'system' | 'agent';
  message: string;
  timestamp: string;
  type: 'info' | 'request' | 'response' | 'alert';
}

const EnhancedClaimTracking = () => {
  const { claimId } = useParams<{ claimId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { userType } = useAuth();
  
  // State management
  const [claimDetails, setClaimDetails] = useState<ClaimDetails | null>(null);
  const [agentTimeline, setAgentTimeline] = useState<AgentTimeline | null>(null);
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([]);
  const [aiDecision, setAiDecision] = useState<AIDecisionSummary | null>(null);
  const [documentStatuses, setDocumentStatuses] = useState<DocumentStatus[]>([]);
  const [communications, setCommunications] = useState<CommunicationMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);

  useEffect(() => {
    if (claimId) {
      loadClaimData();
      // Set up periodic refresh for real-time updates
      const interval = setInterval(loadClaimData, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [claimId]);

  const loadClaimData = async () => {
    try {
      if (!claimId) return;
      
      setIsLoading(true);
      await Promise.all([
        loadClaimDetails(),
        loadAgentTimeline(),
        loadDocumentStatuses(),
        loadCommunications()
      ]);
    } catch (error) {
      toast({
        title: "Error Loading Claim",
        description: "Failed to load claim information",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadClaimDetails = async () => {
    try {
      if (!claimId) return;
      const details = await apiClient.getClaimDetails(claimId);
      setClaimDetails(details);
      
      // Load AI analysis for this claim
      const aiAnalysis = await apiClient.getClaimAIAnalysis(claimId);
      setAiDecision({
        decision: aiAnalysis.decision,
        confidence_score: aiAnalysis.confidence_score,
        risk_level: aiAnalysis.risk_level,
        reasoning: aiAnalysis.reasoning,
        next_steps: aiAnalysis.next_steps,
        fraud_indicators: aiAnalysis.fraud_indicators || [],
        estimated_processing_time: aiAnalysis.estimated_processing_time
      });
    } catch (error) {
      console.error('Failed to load claim details:', error);
    }
  };

  const loadAgentTimeline = async () => {
    try {
      if (!claimId) return;
      const timeline = await apiClient.getClaimTimeline(claimId);
      setAgentTimeline(timeline);
      
      // Convert agent timeline to workflow steps
      const steps = generateWorkflowSteps(timeline);
      setWorkflowSteps(steps);
    } catch (error) {
      console.error('Failed to load agent timeline:', error);
    }
  };

  const loadDocumentStatuses = async () => {
    try {
      if (!claimId) return;
      
      // Get claim documents and their OCR/validation status
      const claimDetails = await apiClient.getClaimDetailedReview(claimId);
      const documents: DocumentStatus[] = [];
      
      // If claim has documents, get their processing status
      if (claimDetails.documents && claimDetails.documents.length > 0) {
        for (const doc of claimDetails.documents) {
          try {
            const ocrResults = await apiClient.getDocumentOCRResults(doc.id);
            const validation = await apiClient.getDocumentValidation(doc.id);
            
            documents.push({
              id: doc.id,
              name: doc.filename,
              type: doc.document_type,
              upload_time: doc.uploaded_at,
              ocr_status: ocrResults.status,
              extraction_confidence: ocrResults.confidence,
              extracted_fields: ocrResults.extracted_data,
              validation_status: validation.status
            });
          } catch (error) {
            // Document might not have OCR/validation yet
            documents.push({
              id: doc.id,
              name: doc.filename,
              type: doc.document_type,
              upload_time: doc.uploaded_at,
              ocr_status: 'pending',
              extraction_confidence: 0,
              extracted_fields: {},
              validation_status: 'pending'
            });
          }
        }
      }
      
      setDocumentStatuses(documents);
    } catch (error) {
      console.error('Failed to load document statuses:', error);
    }
  };

  const loadCommunications = async () => {
    try {
      if (!claimId) return;
      
      // Get real communication history from backend
      const commHistory = await apiClient.getClaimCommunicationHistory(claimId);
      
      const communications: CommunicationMessage[] = commHistory.map(comm => ({
        id: comm.id,
        sender: comm.sender_type as 'user' | 'system' | 'agent',
        message: comm.message,
        timestamp: comm.timestamp,
        type: comm.message_type as 'info' | 'request' | 'response' | 'alert'
      }));
      
      setCommunications(communications);
    } catch (error) {
      console.error('Failed to load communications:', error);
    }
  };

  const generateWorkflowSteps = (timeline: AgentTimeline): WorkflowStep[] => {
    const baseSteps: Omit<WorkflowStep, 'status' | 'timestamp' | 'duration' | 'confidence'>[] = [
      {
        id: 'submitted',
        title: 'Claim Submitted',
        description: 'Initial submission received',
        icon: FileText
      },
      {
        id: 'extraction',
        title: 'Data Extraction',
        description: 'AI extracting information from documents',
        icon: Brain
      },
      {
        id: 'validation',
        title: 'Validation',
        description: 'Verifying claim data and eligibility',
        icon: CheckCircle
      },
      {
        id: 'triage',
        title: 'Triage',
        description: 'AI determining priority and routing',
        icon: TrendingUp
      },
      {
        id: 'review',
        title: 'Review',
        description: 'Medical and policy review',
        icon: Eye
      },
      {
        id: 'decision',
        title: 'Decision',
        description: 'Final approval or denial decision',
        icon: CheckCircle
      }
    ];

    return baseSteps.map((step, index) => {
      const agentData = timeline.agents.find(a => 
        a.agent.toLowerCase().includes(step.id) || 
        step.id === 'submitted' && index === 0 ||
        step.id === 'decision' && a.agent.toLowerCase().includes('adjudication')
      );

      let status: WorkflowStep['status'] = 'pending';
      if (agentData) {
        if (agentData.status === 'completed') {
          status = 'completed';
        } else if (agentData.status === 'running') {
          status = 'current';
        } else if (agentData.status === 'failed') {
          status = 'failed';
        }
      } else if (step.id === 'submitted') {
        status = 'completed';
      }

      return {
        ...step,
        status,
        timestamp: agentData?.completed_at || agentData?.started_at,
        duration: agentData?.duration,
        confidence: agentData?.confidence,
        details: agentData?.result
      };
    });
  };

  const getNextSteps = (status: string): string[] => {
    switch (status.toLowerCase()) {
      case 'pending':
        return ['Your claim will be reviewed within 24-48 hours', 'Ensure all required documents are uploaded'];
      case 'processing':
        return ['Review is in progress', 'You will be notified of any additional requirements'];
      case 'approved':
        return ['Payment will be processed within 5-7 business days', 'Check your account for payment details'];
      case 'denied':
        return ['Review the denial reason', 'You may appeal this decision within 30 days'];
      default:
        return ['Monitor your claim status for updates'];
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadClaimData();
    setIsRefreshing(false);
    toast({
      title: "Claim Updated",
      description: "Latest information has been loaded",
    });
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;
    
    setIsSendingMessage(true);
    try {
      // Mock sending message - would integrate with real messaging system
      const message: CommunicationMessage = {
        id: Date.now().toString(),
        sender: 'user',
        message: newMessage,
        timestamp: new Date().toISOString(),
        type: 'request'
      };
      
      setCommunications(prev => [...prev, message]);
      setNewMessage('');
      
      // Mock auto-response
      setTimeout(() => {
        const response: CommunicationMessage = {
          id: (Date.now() + 1).toString(),
          sender: 'system',
          message: 'Thank you for your message. A customer service representative will respond within 24 hours.',
          timestamp: new Date().toISOString(),
          type: 'response'
        };
        setCommunications(prev => [...prev, response]);
      }, 1000);
      
      toast({
        title: "Message Sent",
        description: "Your message has been submitted",
      });
    } catch (error) {
      toast({
        title: "Failed to Send",
        description: "Message could not be sent",
        variant: "destructive",
      });
    } finally {
      setIsSendingMessage(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading claim details...</span>
        </div>
      </div>
    );
  }

  if (!claimDetails) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Claim Not Found</h2>
          <p className="text-gray-600 mb-4">The requested claim could not be found.</p>
          <Button onClick={() => navigate('/user/claims')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Claims
          </Button>
        </div>
      </div>
    );
  }

  const currentStep = workflowSteps.findIndex(step => step.status === 'current');
  const completedSteps = workflowSteps.filter(step => step.status === 'completed').length;
  const progressPercentage = (completedSteps / workflowSteps.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => navigate(userType === 'admin' ? '/admin/claims' : '/user/claims')}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Claims
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Claim #{claimDetails.claim.claim_id}
                </h1>
                <p className="text-gray-600">{claimDetails.claim.patient_name}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Badge 
                variant={
                  claimDetails.claim.status === 'approved' ? 'default' :
                  claimDetails.claim.status === 'denied' ? 'destructive' :
                  'secondary'
                }
                className="text-sm"
              >
                {claimDetails.claim.status.replace('_', ' ').toUpperCase()}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Overview */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Claim Progress</span>
              <span className="text-sm font-normal text-gray-500">
                {completedSteps} of {workflowSteps.length} steps completed
              </span>
            </CardTitle>
            <Progress value={progressPercentage} className="h-2" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {workflowSteps.map((step, index) => (
                <div key={step.id} className="text-center">
                  <div className={`
                    w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2 border-2
                    ${step.status === 'completed' ? 'bg-green-100 border-green-500 text-green-600' :
                      step.status === 'current' ? 'bg-blue-100 border-blue-500 text-blue-600' :
                      step.status === 'failed' ? 'bg-red-100 border-red-500 text-red-600' :
                      'bg-gray-100 border-gray-300 text-gray-400'}
                  `}>
                    {step.status === 'completed' ? (
                      <CheckCircle className="h-6 w-6" />
                    ) : step.status === 'failed' ? (
                      <XCircle className="h-6 w-6" />
                    ) : step.status === 'current' ? (
                      <step.icon className="h-6 w-6 animate-pulse" />
                    ) : (
                      <step.icon className="h-6 w-6" />
                    )}
                  </div>
                  <h4 className="font-medium text-sm">{step.title}</h4>
                  <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                  {step.confidence && (
                    <p className="text-xs text-blue-600 mt-1">
                      {(step.confidence * 100).toFixed(0)}% confidence
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="details" className="space-y-6">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="details">Details</TabsTrigger>
                <TabsTrigger value="timeline">Timeline</TabsTrigger>
                <TabsTrigger value="documents">Documents</TabsTrigger>
                <TabsTrigger value="communication">Messages</TabsTrigger>
              </TabsList>

              {/* Claim Details Tab */}
              <TabsContent value="details" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Claim Information</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div className="flex items-center space-x-3">
                          <User className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="font-medium">Patient</p>
                            <p className="text-gray-600">{claimDetails.claim.patient_name}</p>
                            <p className="text-sm text-gray-500">ID: {claimDetails.claim.patient_id}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <Building className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="font-medium">Provider</p>
                            <p className="text-gray-600">{claimDetails.claim.provider_name}</p>
                            {claimDetails.claim.provider_npi && (
                              <p className="text-sm text-gray-500">NPI: {claimDetails.claim.provider_npi}</p>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="flex items-center space-x-3">
                          <Calendar className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="font-medium">Service Date</p>
                            <p className="text-gray-600">{claimDetails.claim.service_date}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <DollarSign className="h-5 w-5 text-gray-400" />
                          <div>
                            <p className="font-medium">Claim Amount</p>
                            <p className="text-gray-600">{formatCurrency(claimDetails.claim.claim_amount)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <Separator className="my-6" />
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <p className="font-medium mb-2">Diagnosis Code</p>
                        <p className="text-gray-600">{claimDetails.claim.diagnosis_code}</p>
                      </div>
                      
                      <div>
                        <p className="font-medium mb-2">Procedure Code</p>
                        <p className="text-gray-600">{claimDetails.claim.procedure_code}</p>
                      </div>
                    </div>
                    
                    {claimDetails.claim.notes && (
                      <div className="mt-6">
                        <p className="font-medium mb-2">Notes</p>
                        <p className="text-gray-600">{claimDetails.claim.notes}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* AI Decision Summary */}
                {aiDecision && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <Brain className="h-5 w-5" />
                        <span>AI Decision Summary</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">Decision:</span>
                          <Badge variant={aiDecision.decision === 'approved' ? 'default' : 'destructive'}>
                            {aiDecision.decision.toUpperCase()}
                          </Badge>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="font-medium">Confidence Score:</span>
                          <div className="flex items-center space-x-2">
                            <Progress value={aiDecision.confidence_score * 100} className="w-24 h-2" />
                            <span className="text-sm font-medium">
                              {(aiDecision.confidence_score * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="font-medium">Risk Level:</span>
                          <Badge variant={
                            aiDecision.risk_level === 'low' ? 'default' :
                            aiDecision.risk_level === 'medium' ? 'secondary' :
                            'destructive'
                          }>
                            {aiDecision.risk_level.toUpperCase()}
                          </Badge>
                        </div>
                        
                        <div>
                          <p className="font-medium mb-2">AI Reasoning:</p>
                          <ul className="list-disc list-inside space-y-1 text-gray-600">
                            {aiDecision.reasoning.map((reason, index) => (
                              <li key={index}>{reason}</li>
                            ))}
                          </ul>
                        </div>
                        
                        <div>
                          <p className="font-medium mb-2">Next Steps:</p>
                          <ul className="list-disc list-inside space-y-1 text-gray-600">
                            {aiDecision.next_steps.map((step, index) => (
                              <li key={index}>{step}</li>
                            ))}
                          </ul>
                        </div>
                        
                        {aiDecision.fraud_indicators && aiDecision.fraud_indicators.length > 0 && (
                          <Alert className="border-yellow-200 bg-yellow-50">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                              <p className="font-medium">Fraud Indicators Detected:</p>
                              <ul className="list-disc list-inside mt-1">
                                {aiDecision.fraud_indicators.map((indicator, index) => (
                                  <li key={index}>{indicator}</li>
                                ))}
                              </ul>
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Agent Timeline Tab */}
              <TabsContent value="timeline" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Processing Timeline</CardTitle>
                    <CardDescription>Detailed view of AI agent processing steps</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {agentTimeline && agentTimeline.agents.length > 0 ? (
                      <div className="space-y-6">
                        {agentTimeline.agents.map((agent, index) => (
                          <div key={index} className="relative">
                            {index < agentTimeline.agents.length - 1 && (
                              <div className="absolute left-6 top-12 w-0.5 h-16 bg-gray-200"></div>
                            )}
                            <div className="flex items-start space-x-4">
                              <div className={`
                                w-12 h-12 rounded-full flex items-center justify-center border-2
                                ${agent.status === 'completed' ? 'bg-green-100 border-green-500' :
                                  agent.status === 'failed' ? 'bg-red-100 border-red-500' :
                                  'bg-blue-100 border-blue-500'}
                              `}>
                                <Bot className="h-6 w-6" />
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center justify-between">
                                  <h4 className="font-medium">{agent.agent}</h4>
                                  <Badge variant="outline" className="text-xs">
                                    {agent.agent_type}
                                  </Badge>
                                </div>
                                <p className="text-sm text-gray-600 mt-1">{agent.result}</p>
                                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                  <span>Duration: {agent.duration}s</span>
                                  <span>Confidence: {(agent.confidence * 100).toFixed(0)}%</span>
                                  <span>{formatDateTime(agent.completed_at)}</span>
                                </div>
                                {agent.reasoning_steps > 0 && (
                                  <p className="text-xs text-blue-600 mt-1">
                                    {agent.reasoning_steps} reasoning steps completed
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-center text-gray-500 py-8">
                        Processing timeline will appear here as your claim progresses
                      </p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Documents Tab */}
              <TabsContent value="documents" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Uploaded Documents</CardTitle>
                    <CardDescription>Document processing status and extracted information</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {documentStatuses.map((doc) => (
                        <div key={doc.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <FileText className="h-5 w-5 text-gray-400" />
                              <div>
                                <p className="font-medium">{doc.name}</p>
                                <p className="text-sm text-gray-500">{doc.type.replace('_', ' ')}</p>
                              </div>
                            </div>
                            <Badge variant={
                              doc.ocr_status === 'completed' ? 'default' :
                              doc.ocr_status === 'failed' ? 'destructive' :
                              'secondary'
                            }>
                              {doc.ocr_status}
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                            <div>
                              <p className="text-sm font-medium">OCR Confidence</p>
                              <div className="flex items-center space-x-2 mt-1">
                                <Progress value={doc.extraction_confidence * 100} className="flex-1 h-2" />
                                <span className="text-sm">{(doc.extraction_confidence * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                            <div>
                              <p className="text-sm font-medium">Validation Status</p>
                              <Badge variant={doc.validation_status === 'validated' ? 'default' : 'secondary'} className="mt-1">
                                {doc.validation_status.replace('_', ' ')}
                              </Badge>
                            </div>
                          </div>
                          
                          {Object.keys(doc.extracted_fields).length > 0 && (
                            <div>
                              <p className="text-sm font-medium mb-2">Extracted Information</p>
                              <div className="bg-gray-50 rounded p-3 text-sm">
                                {Object.entries(doc.extracted_fields).map(([key, value]) => (
                                  <div key={key} className="flex justify-between py-1">
                                    <span className="font-medium">{key.replace('_', ' ')}:</span>
                                    <span>{typeof value === 'number' && key.includes('amount') ? formatCurrency(value) : String(value)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Communication Tab */}
              <TabsContent value="communication" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Communication History</CardTitle>
                    <CardDescription>Messages and updates about your claim</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4 max-h-96 overflow-y-auto mb-4">
                      {communications.map((message) => (
                        <div key={message.id} className={`
                          flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}
                        `}>
                          <div className={`
                            max-w-xs lg:max-w-md px-4 py-2 rounded-lg
                            ${message.sender === 'user' ? 'bg-blue-500 text-white' :
                              message.sender === 'system' ? 'bg-gray-100 text-gray-800' :
                              'bg-green-100 text-green-800'}
                          `}>
                            <div className="flex items-center space-x-2 mb-1">
                              {message.sender === 'user' ? <User className="h-4 w-4" /> :
                               message.sender === 'system' ? <Bot className="h-4 w-4" /> :
                               <MessageCircle className="h-4 w-4" />}
                              <span className="text-xs font-medium">
                                {message.sender === 'user' ? 'You' :
                                 message.sender === 'system' ? 'System' :
                                 'Agent'}
                              </span>
                            </div>
                            <p className="text-sm">{message.message}</p>
                            <p className="text-xs opacity-75 mt-1">
                              {formatDateTime(message.timestamp)}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <div className="flex space-x-2">
                      <Textarea
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Type your message here..."
                        className="flex-1"
                        rows={2}
                      />
                      <Button
                        onClick={handleSendMessage}
                        disabled={isSendingMessage || !newMessage.trim()}
                        size="sm"
                      >
                        {isSendingMessage ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Quick Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm">Submitted:</span>
                    <span className="text-sm font-medium">
                      {formatDateTime(claimDetails.claim.created_at)}
                    </span>
                  </div>
                  
                  {claimDetails.claim.processed_at && (
                    <div className="flex justify-between">
                      <span className="text-sm">Processed:</span>
                      <span className="text-sm font-medium">
                        {formatDateTime(claimDetails.claim.processed_at)}
                      </span>
                    </div>
                  )}
                  
                  <div className="flex justify-between">
                    <span className="text-sm">Priority:</span>
                    <Badge variant={claimDetails.claim.priority > 2 ? 'destructive' : 'default'}>
                      {claimDetails.claim.priority > 2 ? 'High' : 'Normal'}
                    </Badge>
                  </div>
                  
                  {aiDecision && (
                    <div className="flex justify-between">
                      <span className="text-sm">AI Confidence:</span>
                      <span className="text-sm font-medium">
                        {(aiDecision.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <Download className="h-4 w-4 mr-2" />
                    Download Report
                  </Button>
                  
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <FileText className="h-4 w-4 mr-2" />
                    Request Documents
                  </Button>
                  
                  {claimDetails.claim.status === 'denied' && (
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <AlertCircle className="h-4 w-4 mr-2" />
                      File Appeal
                    </Button>
                  )}
                  
                  <Button variant="outline" size="sm" className="w-full justify-start">
                    <MessageCircle className="h-4 w-4 mr-2" />
                    Contact Support
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Related Claims */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Related Claims</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-500 text-center py-4">
                  No related claims found
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedClaimTracking;