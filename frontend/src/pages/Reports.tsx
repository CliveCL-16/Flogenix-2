import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { 
  Brain, 
  Clock, 
  TrendingUp, 
  BarChart3, 
  Activity, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Eye,
  ArrowRight
} from 'lucide-react';
import { apiClient } from '@/lib/api';

interface ClaimAnalytics {
  claim_id: string;
  patient_name: string;
  status: string;
  processing_time?: number;
  confidence_score?: number;
  decision?: string;
  risk_level?: string;
  ai_analysis_available: boolean;
  timeline_available: boolean;
}

interface ProcessingMetrics {
  total_claims: number;
  avg_processing_time: number;
  avg_confidence_score: number;
  approval_rate: number;
  fraud_detection_rate: number;
}

export default function Reports() {
  const navigate = useNavigate();
  const [claimAnalytics, setClaimAnalytics] = useState<ClaimAnalytics[]>([]);
  const [metrics, setMetrics] = useState<ProcessingMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedClaim, setSelectedClaim] = useState<string>('');

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      // Get user's claims first
      const claimsResponse = await apiClient.getClaims({ limit: 50 });
      const userClaims = claimsResponse.claims || [];
      
      // For each claim, check if analytics data is available
      const analyticsData: ClaimAnalytics[] = [];
      let totalProcessingTime = 0;
      let totalConfidence = 0;
      let validConfidenceCount = 0;
      let approvedCount = 0;
      let fraudCount = 0;
      
      for (const claim of userClaims) {
        try {
          // Try to get AI analysis for this claim
          let aiAnalysis = null;
          let timeline = null;
          
          try {
            aiAnalysis = await apiClient.getClaimAIAnalysis(claim.claim_id);
          } catch (error) {
            // AI analysis not available for this claim
          }
          
          try {
            timeline = await apiClient.getClaimTimeline(claim.claim_id);
          } catch (error) {
            // Timeline not available for this claim
          }
          
          // Calculate processing time from timeline if available
          let processingTime = undefined;
          if (timeline && timeline.agents && timeline.agents.length > 0) {
            processingTime = timeline.agents.reduce((total: number, agent: any) => 
              total + (agent.duration_seconds || 0), 0);
            totalProcessingTime += processingTime;
          }
          
          // Extract confidence score if available
          let confidenceScore = undefined;
          if (aiAnalysis && aiAnalysis.confidence_score !== undefined) {
            confidenceScore = aiAnalysis.confidence_score;
            totalConfidence += confidenceScore;
            validConfidenceCount++;
          }
          
          // Count approvals and fraud detections
          if (claim.status === 'APPROVED') approvedCount++;
          if (claim.status === 'FRAUD_DETECTED') fraudCount++;
          
          analyticsData.push({
            claim_id: claim.claim_id,
            patient_name: claim.patient_name || '',
            status: claim.status || '',
            processing_time: processingTime,
            confidence_score: confidenceScore,
            decision: aiAnalysis?.decision || '',
            risk_level: aiAnalysis?.risk_level || '',
            ai_analysis_available: !!aiAnalysis,
            timeline_available: !!timeline
          });
          
        } catch (error) {
          // If we can't get analytics for a claim, still include basic info
          analyticsData.push({
            claim_id: claim.claim_id,
            patient_name: claim.patient_name || '',
            status: claim.status || '',
            ai_analysis_available: false,
            timeline_available: false
          });
        }
      }
      
      // Calculate overall metrics from real data
      const totalClaims = userClaims.length;
      const avgProcessingTime = totalClaims > 0 ? totalProcessingTime / totalClaims : 0;
      const avgConfidence = validConfidenceCount > 0 ? totalConfidence / validConfidenceCount : 0;
      const approvalRate = totalClaims > 0 ? (approvedCount / totalClaims) * 100 : 0;
      const fraudRate = totalClaims > 0 ? (fraudCount / totalClaims) * 100 : 0;
      
      setClaimAnalytics(analyticsData);
      setMetrics({
        total_claims: totalClaims,
        avg_processing_time: avgProcessingTime,
        avg_confidence_score: avgConfidence,
        approval_rate: approvalRate,
        fraud_detection_rate: fraudRate
      });
      
    } catch (error) {
      console.error('Error loading analytics data:', error);
      setClaimAnalytics([]);
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  };

  const viewClaimAnalysis = (claimId: string) => {
    navigate(`/user/claim/${claimId}`);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'APPROVED': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'DENIED': return <XCircle className="h-4 w-4 text-red-600" />;
      case 'FRAUD_DETECTED': return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default: return <Clock className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="text-gray-600">Loading processing analytics...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Processing Analytics</h1>
            <p className="text-gray-600">AI analysis, processing insights, and performance metrics for your claims</p>
          </div>
        </div>

        {/* Metrics Overview */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Claims</p>
                    <p className="text-2xl font-bold">{metrics.total_claims}</p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-blue-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg Processing Time</p>
                    <p className="text-2xl font-bold">
                      {metrics.avg_processing_time > 0 
                        ? `${Math.round(metrics.avg_processing_time)}s` 
                        : '—'}
                    </p>
                  </div>
                  <Clock className="h-8 w-8 text-green-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Avg AI Confidence</p>
                    <p className="text-2xl font-bold">
                      {metrics.avg_confidence_score > 0 
                        ? `${Math.round(metrics.avg_confidence_score)}%` 
                        : '—'}
                    </p>
                  </div>
                  <Brain className="h-8 w-8 text-purple-600" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Approval Rate</p>
                    <p className="text-2xl font-bold">
                      {metrics.approval_rate > 0 
                        ? `${Math.round(metrics.approval_rate)}%` 
                        : '—'}
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-orange-600" />
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Claims Analytics Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Claim Processing Analytics
            </CardTitle>
            <CardDescription>
              Detailed AI analysis and processing metrics for your submitted claims
            </CardDescription>
          </CardHeader>
          <CardContent>
            {claimAnalytics.length === 0 ? (
              <div className="text-center py-8">
                <Brain className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-medium mb-2">No Analytics Data Available</h3>
                <p className="text-gray-600">
                  Submit some claims to see detailed processing analytics and AI insights.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-medium">Claim ID</th>
                      <th className="text-left py-3 px-4 font-medium">Patient</th>
                      <th className="text-left py-3 px-4 font-medium">Status</th>
                      <th className="text-left py-3 px-4 font-medium">AI Decision</th>
                      <th className="text-left py-3 px-4 font-medium">Confidence</th>
                      <th className="text-left py-3 px-4 font-medium">Risk Level</th>
                      <th className="text-left py-3 px-4 font-medium">Processing Time</th>
                      <th className="text-left py-3 px-4 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {claimAnalytics.map((claim) => (
                      <tr key={claim.claim_id} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4 font-mono text-sm">{claim.claim_id}</td>
                        <td className="py-3 px-4">{claim.patient_name || '—'}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(claim.status)}
                            <Badge variant="outline">{claim.status || '—'}</Badge>
                          </div>
                        </td>
                        <td className="py-3 px-4">{claim.decision || '—'}</td>
                        <td className="py-3 px-4">
                          {claim.confidence_score !== undefined ? (
                            <div className="flex items-center gap-2">
                              <Progress value={claim.confidence_score} className="w-16 h-2" />
                              <span className="text-sm">{Math.round(claim.confidence_score)}%</span>
                            </div>
                          ) : '—'}
                        </td>
                        <td className="py-3 px-4">
                          {claim.risk_level ? (
                            <Badge className={getRiskLevelColor(claim.risk_level)}>
                              {claim.risk_level}
                            </Badge>
                          ) : '—'}
                        </td>
                        <td className="py-3 px-4">
                          {claim.processing_time !== undefined 
                            ? `${Math.round(claim.processing_time)}s` 
                            : '—'}
                        </td>
                        <td className="py-3 px-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => viewClaimAnalysis(claim.claim_id)}
                            disabled={!claim.ai_analysis_available && !claim.timeline_available}
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            View Analysis
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};