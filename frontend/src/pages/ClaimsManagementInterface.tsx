import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, CheckCircle, Clock, DollarSign, FileText, Eye, Edit, MessageSquare, Download, Upload, Zap, AlertTriangle, TrendingUp, User, Calendar, Shield, Brain, Activity, Target, Award, Flag } from 'lucide-react';
import { apiClient, Claim, ClaimDetails, getStatusColor, formatCurrency, formatDateTime } from '@/lib/api';

// Enhanced interfaces for claims management
interface ClaimReview {
  claim_id: string;
  review_status: 'pending' | 'in_progress' | 'completed';
  reviewer_id?: string;
  reviewer_name?: string;
  review_notes: string;
  decision: 'approve' | 'reject' | 'request_info' | 'escalate';
  decision_reason: string;
  confidence_score: number;
  risk_assessment: {
    overall_risk: 'low' | 'medium' | 'high';
    risk_factors: string[];
    mitigation_actions: string[];
  };
  compliance_check: {
    status: 'pass' | 'fail' | 'review_required';
    violations: string[];
    recommendations: string[];
  };
  financial_impact: {
    approved_amount?: number;
    denied_amount?: number;
    adjustment_reason?: string;
  };
  created_at: string;
  updated_at: string;
}

interface AIAnalysisDetail {
  claim_id: string;
  overall_recommendation: 'approve' | 'reject' | 'review';
  confidence_score: number;
  processing_summary: {
    total_agents: number;
    processing_time: number;
    automation_level: number;
  };
  eligibility_analysis: {
    status: 'eligible' | 'ineligible' | 'conditional';
    details: string[];
    confidence: number;
  };
  medical_analysis: {
    diagnosis_validity: number;
    procedure_appropriateness: number;
    medical_necessity: number;
    details: string[];
  };
  fraud_analysis: {
    risk_score: number;
    suspicious_patterns: string[];
    verification_results: string[];
  };
  financial_analysis: {
    amount_validation: 'valid' | 'invalid' | 'review_required';
    cost_comparison: number;
    savings_opportunity: number;
  };
  regulatory_compliance: {
    hipaa_compliance: boolean;
    state_regulations: boolean;
    federal_requirements: boolean;
    compliance_notes: string[];
  };
  similar_claims: Array<{
    claim_id: string;
    similarity_score: number;
    outcome: string;
    decision_rationale: string;
  }>;
  agent_timeline: Array<{
    agent_name: string;
    start_time: string;
    end_time: string;
    status: string;
    output: string;
    confidence: number;
  }>;
  recommendations: {
    next_steps: string[];
    required_documentation: string[];
    escalation_triggers: string[];
  };
}

interface ClaimCommunication {
  id: string;
  claim_id: string;
  type: 'note' | 'email' | 'phone' | 'document';
  direction: 'inbound' | 'outbound';
  subject?: string;
  content: string;
  sender: string;
  recipient?: string;
  timestamp: string;
  attachments?: Array<{
    filename: string;
    size: number;
    type: string;
  }>;
  status: 'sent' | 'delivered' | 'read' | 'failed';
}

interface ClaimDocument {
  id: string;
  claim_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  uploaded_by: string;
  document_type: 'medical_record' | 'invoice' | 'prescription' | 'insurance_card' | 'id_document' | 'other';
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  ocr_confidence?: number;
  extracted_data?: Record<string, any>;
  review_status: 'not_reviewed' | 'reviewed' | 'flagged';
  review_notes?: string;
}

const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return 'text-green-600';
  if (confidence >= 0.6) return 'text-yellow-600';
  return 'text-red-600';
};

const getRiskColor = (risk: string): string => {
  switch (risk) {
    case 'low': return 'bg-green-100 text-green-800';
    case 'medium': return 'bg-yellow-100 text-yellow-800';
    case 'high': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

export default function ClaimsManagementInterface() {
  const [selectedClaim, setSelectedClaim] = useState<ClaimDetails | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [claimReview, setClaimReview] = useState<ClaimReview | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysisDetail | null>(null);
  const [communications, setCommunications] = useState<ClaimCommunication[]>([]);
  const [documents, setDocuments] = useState<ClaimDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingAction, setProcessingAction] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [reviewForm, setReviewForm] = useState({
    decision: '',
    reason: '',
    notes: '',
    adjustedAmount: ''
  });

  useEffect(() => {
    loadClaims();
  }, []);

  useEffect(() => {
    if (selectedClaim) {
      loadClaimDetails(selectedClaim.claim.claim_id);
    }
  }, [selectedClaim]);

  const loadClaims = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getClaims({ limit: 50 });
      setClaims(response.claims || []);
      
      // Auto-select first claim if none selected
      if (response.claims && response.claims.length > 0 && !selectedClaim) {
        const firstClaimDetails = await apiClient.getClaimDetails(response.claims[0].claim_id);
        setSelectedClaim(firstClaimDetails);
      }
    } catch (error) {
      console.error('Error loading claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadClaimDetails = async (claimId: string) => {
    try {
      const [details, aiData, commData, docData, reviewData] = await Promise.all([
        apiClient.getClaimDetails(claimId),
        loadAIAnalysis(claimId),
        loadCommunications(claimId),
        loadDocuments(claimId),
        loadClaimReview(claimId)
      ]);

      setSelectedClaim(details);
      setAiAnalysis(aiData);
      setCommunications(commData);
      setDocuments(docData);
      setClaimReview(reviewData);
    } catch (error) {
      console.error('Error loading claim details:', error);
    }
  };

  const loadAIAnalysis = async (claimId: string): Promise<AIAnalysisDetail> => {
    // Mock AI analysis data - would normally come from backend
    return {
      claim_id: claimId,
      overall_recommendation: 'approve',
      confidence_score: 0.89,
      processing_summary: {
        total_agents: 5,
        processing_time: 3.2,
        automation_level: 0.95
      },
      eligibility_analysis: {
        status: 'eligible',
        details: [
          'Patient policy is active and in good standing',
          'Deductible requirements met',
          'No exclusions apply to this procedure'
        ],
        confidence: 0.92
      },
      medical_analysis: {
        diagnosis_validity: 0.94,
        procedure_appropriateness: 0.87,
        medical_necessity: 0.91,
        details: [
          'Diagnosis code ICD-10: M54.2 - Cervicalgia validated',
          'Procedure CPT: 97110 - Therapeutic exercises appropriate',
          'Medical necessity supported by documentation'
        ]
      },
      fraud_analysis: {
        risk_score: 0.15,
        suspicious_patterns: [],
        verification_results: [
          'Provider credentials verified',
          'Patient identity confirmed',
          'Service dates consistent with records'
        ]
      },
      financial_analysis: {
        amount_validation: 'valid',
        cost_comparison: 0.98,
        savings_opportunity: 50
      },
      regulatory_compliance: {
        hipaa_compliance: true,
        state_regulations: true,
        federal_requirements: true,
        compliance_notes: ['All compliance requirements satisfied']
      },
      similar_claims: [
        {
          claim_id: 'CLM-2024-001',
          similarity_score: 0.94,
          outcome: 'approved',
          decision_rationale: 'Similar procedure and diagnosis'
        },
        {
          claim_id: 'CLM-2024-045',
          similarity_score: 0.87,
          outcome: 'approved',
          decision_rationale: 'Same provider, similar treatment'
        }
      ],
      agent_timeline: [
        {
          agent_name: 'EligibilityAgent',
          start_time: '2024-01-15T10:00:00Z',
          end_time: '2024-01-15T10:01:30Z',
          status: 'completed',
          output: 'Patient eligible for coverage',
          confidence: 0.92
        },
        {
          agent_name: 'MedicalReviewAgent',
          start_time: '2024-01-15T10:01:30Z',
          end_time: '2024-01-15T10:03:45Z',
          status: 'completed',
          output: 'Medical necessity established',
          confidence: 0.89
        }
      ],
      recommendations: {
        next_steps: ['Approve claim for payment'],
        required_documentation: [],
        escalation_triggers: []
      }
    };
  };

  const loadCommunications = async (claimId: string): Promise<ClaimCommunication[]> => {
    // Mock communication data
    return [
      {
        id: 'comm-001',
        claim_id: claimId,
        type: 'email',
        direction: 'inbound',
        subject: 'Additional documentation requested',
        content: 'Please provide updated medical records for this claim.',
        sender: 'provider@healthcenter.com',
        timestamp: '2024-01-15T09:30:00Z',
        status: 'read'
      },
      {
        id: 'comm-002',
        claim_id: claimId,
        type: 'note',
        direction: 'outbound',
        content: 'Claim reviewed and approved for processing.',
        sender: 'system',
        timestamp: '2024-01-15T10:45:00Z',
        status: 'sent'
      }
    ];
  };

  const loadDocuments = async (claimId: string): Promise<ClaimDocument[]> => {
    // Mock document data
    return [
      {
        id: 'doc-001',
        claim_id: claimId,
        filename: 'medical_report.pdf',
        file_type: 'application/pdf',
        file_size: 2048000,
        upload_date: '2024-01-15T08:00:00Z',
        uploaded_by: 'provider',
        document_type: 'medical_record',
        processing_status: 'completed',
        ocr_confidence: 0.94,
        extracted_data: {
          patient_name: 'John Doe',
          diagnosis: 'Cervicalgia',
          procedure: 'Physical Therapy'
        },
        review_status: 'reviewed'
      },
      {
        id: 'doc-002',
        claim_id: claimId,
        filename: 'invoice.pdf',
        file_type: 'application/pdf',
        file_size: 512000,
        upload_date: '2024-01-15T08:15:00Z',
        uploaded_by: 'provider',
        document_type: 'invoice',
        processing_status: 'completed',
        ocr_confidence: 0.98,
        review_status: 'reviewed'
      }
    ];
  };

  const loadClaimReview = async (claimId: string): Promise<ClaimReview> => {
    // Mock review data
    return {
      claim_id: claimId,
      review_status: 'pending',
      review_notes: '',
      decision: 'approve',
      decision_reason: '',
      confidence_score: 0.89,
      risk_assessment: {
        overall_risk: 'low',
        risk_factors: [],
        mitigation_actions: []
      },
      compliance_check: {
        status: 'pass',
        violations: [],
        recommendations: []
      },
      financial_impact: {},
      created_at: '2024-01-15T08:00:00Z',
      updated_at: '2024-01-15T10:45:00Z'
    };
  };

  const handleClaimSelection = async (claim: Claim) => {
    try {
      const details = await apiClient.getClaimDetails(claim.claim_id);
      setSelectedClaim(details);
    } catch (error) {
      console.error('Error loading claim details:', error);
    }
  };

  const handleDecisionSubmit = async () => {
    if (!selectedClaim || !reviewForm.decision) return;

    try {
      setProcessingAction(true);
      
      // Mock API call for claim decision
      console.log('Submitting decision:', {
        claimId: selectedClaim.claim.claim_id,
        decision: reviewForm.decision,
        reason: reviewForm.reason,
        notes: reviewForm.notes,
        adjustedAmount: reviewForm.adjustedAmount
      });

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Reset form and refresh data
      setReviewForm({ decision: '', reason: '', notes: '', adjustedAmount: '' });
      await loadClaims();
      
      // Show success message (would normally use a toast notification)
      alert('Decision submitted successfully!');
    } catch (error) {
      console.error('Error submitting decision:', error);
      alert('Error submitting decision. Please try again.');
    } finally {
      setProcessingAction(false);
    }
  };

  const handleDocumentUpload = async (file: File) => {
    if (!selectedClaim) return;

    try {
      // Mock document upload
      console.log('Uploading document:', file.name);
      
      const newDocument: ClaimDocument = {
        id: `doc-${Date.now()}`,
        claim_id: selectedClaim.claim.claim_id,
        filename: file.name,
        file_type: file.type,
        file_size: file.size,
        upload_date: new Date().toISOString(),
        uploaded_by: 'current_user',
        document_type: 'other',
        processing_status: 'processing',
        review_status: 'not_reviewed'
      };

      setDocuments(prev => [...prev, newDocument]);
    } catch (error) {
      console.error('Error uploading document:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading claims management interface...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex gap-6 h-[calc(100vh-8rem)]">
          {/* Claims List Panel */}
          <div className="w-1/3">
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <FileText className="h-5 w-5" />
                  <span>Claims Queue</span>
                </CardTitle>
                <CardDescription>
                  Select a claim to review and manage
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[calc(100vh-12rem)]">
                  <div className="space-y-2 p-4">
                    {claims.map((claim) => (
                      <Card 
                        key={claim.claim_id}
                        className={`cursor-pointer transition-colors hover:bg-gray-50 ${
                          selectedClaim?.claim.claim_id === claim.claim_id ? 'border-blue-500 bg-blue-50' : ''
                        }`}
                        onClick={() => handleClaimSelection(claim)}
                      >
                        <CardContent className="p-4">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-sm">{claim.claim_id}</span>
                              <Badge className={getStatusColor(claim.status)}>
                                {claim.status}
                              </Badge>
                            </div>
                            <div className="text-sm text-gray-600">
                              <div>{claim.patient_name}</div>
                              <div>{formatCurrency(claim.claim_amount)}</div>
                            </div>
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <span>{formatDateTime(claim.created_at)}</span>
                              {claim.confidence_score && (
                                <div className="flex items-center space-x-1">
                                  <Target className="h-3 w-3" />
                                  <span className={getConfidenceColor(claim.confidence_score)}>
                                    {(claim.confidence_score * 100).toFixed(0)}%
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Claim Details Panel */}
          <div className="w-2/3">
            {selectedClaim ? (
              <Card className="h-full">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center space-x-2">
                        <Eye className="h-5 w-5" />
                        <span>Claim Details - {selectedClaim.claim.claim_id}</span>
                      </CardTitle>
                      <CardDescription>
                        {selectedClaim.claim.patient_name} • {formatCurrency(selectedClaim.claim.claim_amount)}
                      </CardDescription>
                    </div>
                    <Badge className={getStatusColor(selectedClaim.claim.status)}>
                      {selectedClaim.claim.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
                    <TabsList className="grid w-full grid-cols-6 px-4">
                      <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="ai-analysis">AI Analysis</TabsTrigger>
                      <TabsTrigger value="documents">Documents</TabsTrigger>
                      <TabsTrigger value="communications">Communications</TabsTrigger>
                      <TabsTrigger value="review">Review</TabsTrigger>
                      <TabsTrigger value="timeline">Timeline</TabsTrigger>
                    </TabsList>

                    <ScrollArea className="h-[calc(100vh-16rem)] px-4">
                      {/* Overview Tab */}
                      <TabsContent value="overview" className="space-y-6 mt-4">
                        {/* Claim Summary */}
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-lg">Claim Summary</CardTitle>
                          </CardHeader>
                          <CardContent className="grid grid-cols-2 gap-4">
                            <div>
                              <Label className="text-sm font-medium">Patient</Label>
                              <div className="text-sm">{selectedClaim.claim.patient_name}</div>
                            </div>
                            <div>
                              <Label className="text-sm font-medium">Patient ID</Label>
                              <div className="text-sm">{selectedClaim.claim.patient_id}</div>
                            </div>
                            <div>
                              <Label className="text-sm font-medium">Insurance Provider</Label>
                              <div className="text-sm">{selectedClaim.claim.insurance_provider}</div>
                            </div>
                            <div>
                              <Label className="text-sm font-medium">Policy Number</Label>
                              <div className="text-sm">{selectedClaim.claim.policy_number}</div>
                            </div>
                            <div>
                              <Label className="text-sm font-medium">Diagnosis Code</Label>
                              <div className="text-sm">{selectedClaim.claim.diagnosis_code}</div>
                            </div>
                            <div>
                              <Label className="text-sm font-medium">Procedure Code</Label>
                              <div className="text-sm">{selectedClaim.claim.procedure_code}</div>
                            </div>
                            <div>
                              <Label className="text-sm font-medium">Service Date</Label>
                              <div className="text-sm">{formatDateTime(selectedClaim.claim.service_date)}</div>
                            </div>
                            <div>
                              <Label className="text-sm font-medium">Claim Amount</Label>
                              <div className="text-sm font-semibold">{formatCurrency(selectedClaim.claim.claim_amount)}</div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Provider Information */}
                        <Card>
                          <CardHeader>
                            <CardTitle className="text-lg">Provider Information</CardTitle>
                          </CardHeader>
                          <CardContent className="grid grid-cols-2 gap-4">
                            <div>
                              <Label className="text-sm font-medium">Provider Name</Label>
                              <div className="text-sm">{selectedClaim.claim.provider_name}</div>
                            </div>
                            <div>
                              <Label className="text-sm font-medium">Provider NPI</Label>
                              <div className="text-sm">{selectedClaim.claim.provider_npi || 'N/A'}</div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Decision Summary */}
                        {selectedClaim.decision_log && (
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-lg">AI Decision Summary</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                  <span>Decision:</span>
                                  <Badge className={getStatusColor(selectedClaim.decision_log.decision)}>
                                    {selectedClaim.decision_log.decision}
                                  </Badge>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span>Confidence Score:</span>
                                  <div className="flex items-center space-x-2">
                                    <Progress value={(selectedClaim.decision_log.confidence_score || 0) * 100} className="w-20 h-2" />
                                    <span className={getConfidenceColor(selectedClaim.decision_log.confidence_score || 0)}>
                                      {selectedClaim.decision_log.confidence_score 
                                        ? `${(selectedClaim.decision_log.confidence_score * 100).toFixed(1)}%`
                                        : 'N/A'
                                      }
                                    </span>
                                  </div>
                                </div>
                                <div>
                                  <Label className="text-sm font-medium">Reasoning</Label>
                                  <div className="text-sm mt-1 p-3 bg-gray-50 rounded">
                                    {selectedClaim.decision_log.reasoning_text}
                                  </div>
                                </div>
                                <div className="flex items-center justify-between text-sm text-gray-500">
                                  <span>Processing Time:</span>
                                  <span>
                                    {selectedClaim.decision_log.processing_time_seconds 
                                      ? `${selectedClaim.decision_log.processing_time_seconds.toFixed(2)}s`
                                      : 'N/A'
                                    }
                                  </span>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </TabsContent>

                      {/* AI Analysis Tab */}
                      <TabsContent value="ai-analysis" className="space-y-6 mt-4">
                        {aiAnalysis && (
                          <>
                            {/* Overall Recommendation */}
                            <Card>
                              <CardHeader>
                                <CardTitle className="flex items-center space-x-2">
                                  <Brain className="h-5 w-5" />
                                  <span>AI Analysis Overview</span>
                                </CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="grid grid-cols-3 gap-4">
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-blue-600 capitalize">
                                      {aiAnalysis.overall_recommendation}
                                    </div>
                                    <div className="text-sm text-gray-600">Recommendation</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-green-600">
                                      {aiAnalysis.confidence_score 
                                        ? `${(aiAnalysis.confidence_score * 100).toFixed(1)}%`
                                        : 'N/A'
                                      }
                                    </div>
                                    <div className="text-sm text-gray-600">Confidence</div>
                                  </div>
                                  <div className="text-center">
                                    <div className="text-2xl font-bold text-purple-600">
                                      {aiAnalysis.processing_summary.total_agents}
                                    </div>
                                    <div className="text-sm text-gray-600">Agents Used</div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>

                            {/* Detailed Analysis */}
                            <div className="grid grid-cols-2 gap-4">
                              {/* Eligibility Analysis */}
                              <Card>
                                <CardHeader>
                                  <CardTitle className="text-sm">Eligibility Analysis</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Status:</span>
                                      <Badge className={aiAnalysis.eligibility_analysis.status === 'eligible' ? 'bg-green-500' : 'bg-red-500'}>
                                        {aiAnalysis.eligibility_analysis.status}
                                      </Badge>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Confidence:</span>
                                      <span className={getConfidenceColor(aiAnalysis.eligibility_analysis.confidence || 0)}>
                                        {aiAnalysis.eligibility_analysis.confidence 
                                          ? `${(aiAnalysis.eligibility_analysis.confidence * 100).toFixed(1)}%`
                                          : 'N/A'
                                        }
                                      </span>
                                    </div>
                                    <div className="text-xs space-y-1">
                                      {aiAnalysis.eligibility_analysis.details.map((detail, index) => (
                                        <div key={index} className="flex items-start space-x-1">
                                          <CheckCircle className="h-3 w-3 text-green-500 mt-0.5 flex-shrink-0" />
                                          <span>{detail}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                </CardContent>
                              </Card>

                              {/* Medical Analysis */}
                              <Card>
                                <CardHeader>
                                  <CardTitle className="text-sm">Medical Analysis</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                      <span className="text-xs">Diagnosis Validity:</span>
                                      <Progress value={aiAnalysis.medical_analysis.diagnosis_validity * 100} className="w-16 h-2" />
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-xs">Procedure Appropriateness:</span>
                                      <Progress value={aiAnalysis.medical_analysis.procedure_appropriateness * 100} className="w-16 h-2" />
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-xs">Medical Necessity:</span>
                                      <Progress value={aiAnalysis.medical_analysis.medical_necessity * 100} className="w-16 h-2" />
                                    </div>
                                  </div>
                                </CardContent>
                              </Card>

                              {/* Fraud Analysis */}
                              <Card>
                                <CardHeader>
                                  <CardTitle className="text-sm">Fraud Analysis</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Risk Score:</span>
                                      <Badge className={(aiAnalysis.fraud_analysis.risk_score || 0) < 0.3 ? 'bg-green-500' : 'bg-yellow-500'}>
                                        {aiAnalysis.fraud_analysis.risk_score 
                                          ? `${(aiAnalysis.fraud_analysis.risk_score * 100).toFixed(1)}%`
                                          : 'N/A'
                                        }
                                      </Badge>
                                    </div>
                                    {aiAnalysis.fraud_analysis.suspicious_patterns.length === 0 ? (
                                      <div className="text-xs text-green-600">No suspicious patterns detected</div>
                                    ) : (
                                      <div className="text-xs space-y-1">
                                        {aiAnalysis.fraud_analysis.suspicious_patterns.map((pattern, index) => (
                                          <div key={index} className="flex items-start space-x-1">
                                            <AlertTriangle className="h-3 w-3 text-red-500 mt-0.5" />
                                            <span>{pattern}</span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </CardContent>
                              </Card>

                              {/* Financial Analysis */}
                              <Card>
                                <CardHeader>
                                  <CardTitle className="text-sm">Financial Analysis</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Amount Validation:</span>
                                      <Badge className={aiAnalysis.financial_analysis.amount_validation === 'valid' ? 'bg-green-500' : 'bg-red-500'}>
                                        {aiAnalysis.financial_analysis.amount_validation}
                                      </Badge>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Cost Comparison:</span>
                                      <span className="text-sm">
                                        {aiAnalysis.financial_analysis.cost_comparison 
                                          ? `${(aiAnalysis.financial_analysis.cost_comparison * 100).toFixed(1)}%`
                                          : 'N/A'
                                        }
                                      </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm">Savings Opportunity:</span>
                                      <span className="text-sm text-green-600">
                                        {formatCurrency(aiAnalysis.financial_analysis.savings_opportunity)}
                                      </span>
                                    </div>
                                  </div>
                                </CardContent>
                              </Card>
                            </div>

                            {/* Similar Claims */}
                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Similar Claims Comparison</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="space-y-2">
                                  {aiAnalysis.similar_claims.map((similar, index) => (
                                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                                      <div className="flex items-center space-x-2">
                                        <span className="text-sm font-medium">{similar.claim_id}</span>
                                        <Badge variant="outline">{similar.outcome}</Badge>
                                      </div>
                                      <div className="flex items-center space-x-2">
                                        <Progress value={(similar.similarity_score || 0) * 100} className="w-16 h-2" />
                                        <span className="text-xs">
                                          {similar.similarity_score 
                                            ? `${(similar.similarity_score * 100).toFixed(0)}%`
                                            : 'N/A'
                                          }
                                        </span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>

                            {/* Compliance Check */}
                            <Card>
                              <CardHeader>
                                <CardTitle className="text-sm">Regulatory Compliance</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="grid grid-cols-3 gap-4">
                                  <div className="text-center">
                                    <Shield className={`h-6 w-6 mx-auto ${aiAnalysis.regulatory_compliance.hipaa_compliance ? 'text-green-500' : 'text-red-500'}`} />
                                    <div className="text-xs mt-1">HIPAA</div>
                                  </div>
                                  <div className="text-center">
                                    <Shield className={`h-6 w-6 mx-auto ${aiAnalysis.regulatory_compliance.state_regulations ? 'text-green-500' : 'text-red-500'}`} />
                                    <div className="text-xs mt-1">State</div>
                                  </div>
                                  <div className="text-center">
                                    <Shield className={`h-6 w-6 mx-auto ${aiAnalysis.regulatory_compliance.federal_requirements ? 'text-green-500' : 'text-red-500'}`} />
                                    <div className="text-xs mt-1">Federal</div>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          </>
                        )}
                      </TabsContent>

                      {/* Documents Tab */}
                      <TabsContent value="documents" className="space-y-6 mt-4">
                        <Card>
                          <CardHeader>
                            <div className="flex items-center justify-between">
                              <CardTitle className="flex items-center space-x-2">
                                <FileText className="h-5 w-5" />
                                <span>Documents</span>
                              </CardTitle>
                              <Button size="sm" onClick={() => document.getElementById('file-upload')?.click()}>
                                <Upload className="h-4 w-4 mr-2" />
                                Upload
                              </Button>
                              <input
                                id="file-upload"
                                type="file"
                                className="hidden"
                                onChange={(e) => {
                                  const file = e.target.files?.[0];
                                  if (file) handleDocumentUpload(file);
                                }}
                              />
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-3">
                              {documents.map((doc) => (
                                <div key={doc.id} className="flex items-center justify-between p-3 border rounded">
                                  <div className="flex items-center space-x-3">
                                    <FileText className="h-5 w-5 text-gray-500" />
                                    <div>
                                      <div className="font-medium text-sm">{doc.filename}</div>
                                      <div className="text-xs text-gray-500">
                                        {doc.document_type} • {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : 'Unknown size'} • {formatDateTime(doc.upload_date)}
                                      </div>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <Badge variant="outline">{doc.processing_status}</Badge>
                                    {doc.ocr_confidence && (
                                      <Badge variant="outline">
                                        OCR: {(doc.ocr_confidence * 100).toFixed(0)}%
                                      </Badge>
                                    )}
                                    <Button size="sm" variant="ghost">
                                      <Download className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      </TabsContent>

                      {/* Communications Tab */}
                      <TabsContent value="communications" className="space-y-6 mt-4">
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center space-x-2">
                              <MessageSquare className="h-5 w-5" />
                              <span>Communications</span>
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-4">
                              {communications.map((comm) => (
                                <div key={comm.id} className="border-l-4 border-blue-500 pl-4">
                                  <div className="flex items-center justify-between">
                                    <div className="font-medium text-sm">{comm.subject || comm.type}</div>
                                    <div className="text-xs text-gray-500">
                                      {formatDateTime(comm.timestamp)}
                                    </div>
                                  </div>
                                  <div className="text-sm text-gray-600 mt-1">{comm.content}</div>
                                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                    <span>From: {comm.sender}</span>
                                    <Badge variant="outline">{comm.status}</Badge>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </CardContent>
                        </Card>
                      </TabsContent>

                      {/* Review Tab */}
                      <TabsContent value="review" className="space-y-6 mt-4">
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center space-x-2">
                              <Edit className="h-5 w-5" />
                              <span>Claim Review & Decision</span>
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            <div>
                              <Label htmlFor="decision">Decision</Label>
                              <Select value={reviewForm.decision} onValueChange={(value) => setReviewForm(prev => ({ ...prev, decision: value }))}>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select decision" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="approve">Approve</SelectItem>
                                  <SelectItem value="reject">Reject</SelectItem>
                                  <SelectItem value="request_info">Request More Information</SelectItem>
                                  <SelectItem value="escalate">Escalate</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>

                            <div>
                              <Label htmlFor="reason">Decision Reason</Label>
                              <Textarea
                                id="reason"
                                value={reviewForm.reason}
                                onChange={(e) => setReviewForm(prev => ({ ...prev, reason: e.target.value }))}
                                placeholder="Provide reasoning for your decision..."
                                rows={3}
                              />
                            </div>

                            <div>
                              <Label htmlFor="notes">Additional Notes</Label>
                              <Textarea
                                id="notes"
                                value={reviewForm.notes}
                                onChange={(e) => setReviewForm(prev => ({ ...prev, notes: e.target.value }))}
                                placeholder="Any additional notes or comments..."
                                rows={3}
                              />
                            </div>

                            {reviewForm.decision === 'approve' && (
                              <div>
                                <Label htmlFor="adjustedAmount">Adjusted Amount (if different)</Label>
                                <Input
                                  id="adjustedAmount"
                                  type="number"
                                  value={reviewForm.adjustedAmount}
                                  onChange={(e) => setReviewForm(prev => ({ ...prev, adjustedAmount: e.target.value }))}
                                  placeholder="Leave empty if no adjustment"
                                />
                              </div>
                            )}

                            <div className="flex space-x-4 pt-4">
                              <Button 
                                onClick={handleDecisionSubmit}
                                disabled={!reviewForm.decision || processingAction}
                                className="flex-1"
                              >
                                {processingAction ? (
                                  <>
                                    <Activity className="h-4 w-4 mr-2 animate-spin" />
                                    Processing...
                                  </>
                                ) : (
                                  <>
                                    <CheckCircle className="h-4 w-4 mr-2" />
                                    Submit Decision
                                  </>
                                )}
                              </Button>
                              <Button variant="outline" className="flex-1">
                                <Clock className="h-4 w-4 mr-2" />
                                Save Draft
                              </Button>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Risk Assessment */}
                        {claimReview && (
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-sm">Risk Assessment</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                  <span className="text-sm">Overall Risk:</span>
                                  <Badge className={getRiskColor(claimReview.risk_assessment.overall_risk)}>
                                    {claimReview.risk_assessment.overall_risk}
                                  </Badge>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-sm">Compliance Status:</span>
                                  <Badge className={claimReview.compliance_check.status === 'pass' ? 'bg-green-500' : 'bg-red-500'}>
                                    {claimReview.compliance_check.status}
                                  </Badge>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </TabsContent>

                      {/* Timeline Tab */}
                      <TabsContent value="timeline" className="space-y-6 mt-4">
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center space-x-2">
                              <Calendar className="h-5 w-5" />
                              <span>Processing Timeline</span>
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            {aiAnalysis && (
                              <div className="space-y-4">
                                {aiAnalysis.agent_timeline.map((agent, index) => (
                                  <div key={index} className="flex items-start space-x-4">
                                    <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                                    <div className="flex-1">
                                      <div className="flex items-center justify-between">
                                        <span className="font-medium text-sm">{agent.agent_name}</span>
                                        <span className="text-xs text-gray-500">
                                          {formatDateTime(agent.start_time)}
                                        </span>
                                      </div>
                                      <div className="text-sm text-gray-600 mt-1">{agent.output}</div>
                                      <div className="flex items-center space-x-4 mt-2">
                                        <Badge variant="outline">{agent.status}</Badge>
                                        <div className="flex items-center space-x-1">
                                          <span className="text-xs">Confidence:</span>
                                          <span className={`text-xs ${getConfidenceColor(agent.confidence || 0)}`}>
                                            {agent.confidence 
                                              ? `${(agent.confidence * 100).toFixed(0)}%`
                                              : 'N/A'
                                            }
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      </TabsContent>
                    </ScrollArea>
                  </Tabs>
                </CardContent>
              </Card>
            ) : (
              <Card className="h-full flex items-center justify-center">
                <CardContent>
                  <div className="text-center text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <div>Select a claim from the list to view details</div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}