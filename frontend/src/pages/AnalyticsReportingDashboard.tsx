import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { DatePickerWithRange } from '@/components/ui/date-range-picker';
import { BarChart3, TrendingUp, DollarSign, Users, Clock, Target, Download, Filter, RefreshCw, Calendar, PieChart, LineChart, Activity, AlertTriangle, CheckCircle, FileText, Settings, Zap, Shield, Award } from 'lucide-react';
import { apiClient, formatCurrency } from '@/lib/api';

// Analytics interfaces
interface AnalyticsOverview {
  claims_metrics: {
    total_claims: number;
    total_processed: number;
    pending_claims: number;
    approved_claims: number;
    denied_claims: number;
    approval_rate: number;
    processing_rate: number;
    avg_processing_time: number;
  };
  financial_metrics: {
    total_claim_value: number;
    approved_amount: number;
    denied_amount: number;
    pending_amount: number;
    cost_savings: number;
    revenue_impact: number;
  };
  ai_metrics: {
    automation_rate: number;
    ai_accuracy: number;
    confidence_avg: number;
    stp_rate: number;
    manual_review_rate: number;
  };
  performance_metrics: {
    user_productivity: number;
    system_uptime: number;
    error_rate: number;
    response_time: number;
  };
  time_period: {
    start_date: string;
    end_date: string;
  };
}

interface TrendData {
  date: string;
  claims_submitted: number;
  claims_processed: number;
  approval_rate: number;
  avg_processing_time: number;
  ai_confidence: number;
  cost_savings: number;
}

interface DetailedReport {
  id: string;
  report_type: string;
  title: string;
  description: string;
  generated_at: string;
  period: string;
  status: 'generating' | 'ready' | 'failed';
  size: string;
  format: 'PDF' | 'CSV' | 'Excel';
  download_url?: string;
}

interface CustomReport {
  name: string;
  description: string;
  metrics: string[];
  filters: {
    date_range: { start: string; end: string };
    claim_status?: string[];
    amount_range?: { min: number; max: number };
    provider_types?: string[];
    departments?: string[];
  };
  grouping: string;
  chart_type: 'bar' | 'line' | 'pie' | 'table';
  schedule?: {
    frequency: 'daily' | 'weekly' | 'monthly';
    email_recipients: string[];
  };
}

interface PerformanceData {
  department: string;
  claims_handled: number;
  avg_processing_time: number;
  accuracy_rate: number;
  cost_per_claim: number;
  user_satisfaction: number;
  efficiency_score: number;
}

interface FraudInsights {
  total_fraud_detected: number;
  fraud_prevention_savings: number;
  fraud_detection_rate: number;
  top_fraud_patterns: Array<{
    pattern: string;
    frequency: number;
    risk_level: 'high' | 'medium' | 'low';
  }>;
  risk_score_distribution: Array<{
    range: string;
    count: number;
    percentage: number;
  }>;
}

const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

const formatDuration = (hours: number): string => {
  if (hours < 1) {
    return `${Math.round(hours * 60)}m`;
  }
  return `${hours.toFixed(1)}h`;
};

export default function AnalyticsReportingDashboard() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [reports, setReports] = useState<DetailedReport[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [fraudInsights, setFraudInsights] = useState<FraudInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('last_30_days');
  const [customReportDialog, setCustomReportDialog] = useState(false);
  const [customReport, setCustomReport] = useState<CustomReport>({
    name: '',
    description: '',
    metrics: [],
    filters: {
      date_range: { start: '', end: '' }
    },
    grouping: 'date',
    chart_type: 'bar'
  });

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Load analytics data from multiple sources
      const [metricsData, trendsData, reportsData, perfData, fraudData] = await Promise.all([
        loadOverviewMetrics(),
        loadTrendData(),
        loadReports(),
        loadPerformanceData(),
        loadFraudInsights()
      ]);

      setOverview(metricsData);
      setTrends(trendsData);
      setReports(reportsData);
      setPerformanceData(perfData);
      setFraudInsights(fraudData);
    } catch (error) {
      console.error('Error loading analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOverviewMetrics = async (): Promise<AnalyticsOverview> => {
    // Get real analytics overview from backend
    const analyticsOverview = await apiClient.getAnalyticsOverview();
    return analyticsOverview;
  };

  const loadTrendData = async (): Promise<TrendData[]> => {
    // Get performance analytics trend data
    const performanceAnalytics = await apiClient.getPerformanceAnalytics();
    return performanceAnalytics.trends || [];
  };

  const loadReports = async (): Promise<DetailedReport[]> => {
    // Mock reports data - would integrate with real reporting system
    return [
      {
        id: '1',
        report_type: 'monthly_summary',
        title: 'Monthly Claims Summary',
        description: 'Comprehensive overview of claims processing for the month',
        generated_at: new Date().toISOString(),
        period: 'Last 30 days',
        status: 'ready',
        size: '2.3 MB',
        format: 'PDF'
      },
      {
        id: '2',
        report_type: 'fraud_analysis',
        title: 'Fraud Detection Report',
        description: 'Analysis of fraud patterns and prevention metrics',
        generated_at: new Date(Date.now() - 86400000).toISOString(),
        period: 'Last 7 days',
        status: 'ready',
        size: '1.8 MB',
        format: 'Excel'
      }
    ];
  };

  const loadPerformanceData = async (): Promise<PerformanceData[]> => {
    // Get performance analytics
    const performanceAnalytics = await apiClient.getPerformanceAnalytics();
    return performanceAnalytics.department_performance || [];
  };

  const loadFraudInsights = async (): Promise<FraudInsights> => {
    // Get fraud analytics
    const fraudAnalytics = await apiClient.getFraudAnalytics();
    return {
      total_fraud_detected: fraudAnalytics.total_fraud_detected,
      fraud_prevention_savings: fraudAnalytics.fraud_prevention_savings,
      fraud_detection_rate: fraudAnalytics.fraud_detection_rate,
      top_fraud_patterns: fraudAnalytics.top_fraud_patterns,
      risk_score_distribution: fraudAnalytics.risk_score_distribution
    };
  };
        denied_amount: 0, // Placeholder
        pending_amount: dashboardMetrics.revenue_approved_today * 0.2 || 0, // Approximation
        cost_savings: dashboardMetrics.revenue_approved_today * 0.15 || 0, // Approximation
        revenue_impact: dashboardMetrics.revenue_approved_today || 0,
      },
      ai_metrics: {
        automation_rate: 0.78, // Placeholder
        ai_accuracy: dashboardMetrics.approval_rate || 0,
        confidence_avg: 0.87, // Placeholder
        stp_rate: 0.65, // Placeholder
        manual_review_rate: 0.22, // Placeholder
      },
      performance_metrics: {
        user_productivity: 0.89, // Placeholder
        system_uptime: 0.998, // Placeholder
        error_rate: 0.02, // Placeholder
        response_time: 245, // Placeholder (ms)
      },
      time_period: {
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        end_date: new Date().toISOString()
      }
    };
  };

  const loadTrendData = async (): Promise<TrendData[]> => {
    // Mock trend data - would normally come from backend analytics
    const mockTrends: TrendData[] = [];
    const now = new Date();
    
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      mockTrends.push({
        date: date.toISOString().split('T')[0],
        claims_submitted: Math.floor(Math.random() * 50) + 100,
        claims_processed: Math.floor(Math.random() * 45) + 95,
        approval_rate: 0.7 + Math.random() * 0.25,
        avg_processing_time: 2 + Math.random() * 3,
        ai_confidence: 0.8 + Math.random() * 0.15,
        cost_savings: Math.floor(Math.random() * 5000) + 2000
      });
    }
    
    return mockTrends;
  };

  const loadReports = async (): Promise<DetailedReport[]> => {
    // Mock reports data
    return [
      {
        id: 'rpt-001',
        report_type: 'claims_summary',
        title: 'Monthly Claims Summary',
        description: 'Comprehensive overview of claims processing for the month',
        generated_at: '2024-01-15T10:00:00Z',
        period: 'January 2024',
        status: 'ready',
        size: '2.5 MB',
        format: 'PDF'
      },
      {
        id: 'rpt-002',
        report_type: 'ai_performance',
        title: 'AI Performance Analysis',
        description: 'Detailed analysis of AI decision accuracy and processing metrics',
        generated_at: '2024-01-15T08:30:00Z',
        period: 'Last 30 Days',
        status: 'ready',
        size: '1.8 MB',
        format: 'Excel'
      },
      {
        id: 'rpt-003',
        report_type: 'fraud_detection',
        title: 'Fraud Detection Report',
        description: 'Analysis of fraud patterns and prevention effectiveness',
        generated_at: '2024-01-15T09:15:00Z',
        period: 'Q4 2023',
        status: 'ready',
        size: '3.2 MB',
        format: 'PDF'
      },
      {
        id: 'rpt-004',
        report_type: 'financial_impact',
        title: 'Financial Impact Analysis',
        description: 'Cost savings and revenue impact analysis',
        generated_at: '2024-01-15T11:00:00Z',
        period: 'This Month',
        status: 'generating',
        size: 'N/A',
        format: 'Excel'
      }
    ];
  };

  const loadPerformanceData = async (): Promise<PerformanceData[]> => {
    // Mock performance data
    return [
      {
        department: 'Claims Processing',
        claims_handled: 1250,
        avg_processing_time: 2.3,
        accuracy_rate: 0.94,
        cost_per_claim: 12.50,
        user_satisfaction: 0.87,
        efficiency_score: 0.91
      },
      {
        department: 'Medical Review',
        claims_handled: 890,
        avg_processing_time: 4.1,
        accuracy_rate: 0.97,
        cost_per_claim: 18.75,
        user_satisfaction: 0.92,
        efficiency_score: 0.88
      },
      {
        department: 'Fraud Investigation',
        claims_handled: 156,
        avg_processing_time: 8.5,
        accuracy_rate: 0.99,
        cost_per_claim: 45.00,
        user_satisfaction: 0.95,
        efficiency_score: 0.86
      }
    ];
  };

  const loadFraudInsights = async (): Promise<FraudInsights> => {
    // Mock fraud insights
    return {
      total_fraud_detected: 23,
      fraud_prevention_savings: 156000,
      fraud_detection_rate: 0.94,
      top_fraud_patterns: [
        { pattern: 'Duplicate billing', frequency: 8, risk_level: 'high' },
        { pattern: 'Unusual service patterns', frequency: 6, risk_level: 'medium' },
        { pattern: 'Provider anomalies', frequency: 4, risk_level: 'high' },
        { pattern: 'Patient identity issues', frequency: 3, risk_level: 'medium' },
        { pattern: 'Billing code inconsistencies', frequency: 2, risk_level: 'low' }
      ],
      risk_score_distribution: [
        { range: '0.0-0.2', count: 1245, percentage: 0.78 },
        { range: '0.2-0.4', count: 234, percentage: 0.15 },
        { range: '0.4-0.6', count: 78, percentage: 0.05 },
        { range: '0.6-0.8', count: 23, percentage: 0.015 },
        { range: '0.8-1.0', count: 8, percentage: 0.005 }
      ]
    };
  };

  const generateCustomReport = async () => {
    try {
      console.log('Generating custom report:', customReport);
      
      // Mock report generation
      const newReport: DetailedReport = {
        id: `rpt-custom-${Date.now()}`,
        report_type: 'custom',
        title: customReport.name,
        description: customReport.description,
        generated_at: new Date().toISOString(),
        period: 'Custom Period',
        status: 'generating',
        size: 'N/A',
        format: 'PDF'
      };

      setReports(prev => [newReport, ...prev]);
      setCustomReportDialog(false);
      setCustomReport({
        name: '',
        description: '',
        metrics: [],
        filters: { date_range: { start: '', end: '' } },
        grouping: 'date',
        chart_type: 'bar'
      });

      // Simulate report generation completion
      setTimeout(() => {
        setReports(prev => prev.map(r => 
          r.id === newReport.id 
            ? { ...r, status: 'ready', size: '1.2 MB' }
            : r
        ));
      }, 3000);
    } catch (error) {
      console.error('Error generating custom report:', error);
    }
  };

  const downloadReport = async (reportId: string) => {
    try {
      console.log('Downloading report:', reportId);
      
      // Mock report download
      const csvContent = `Report ID,${reportId}\nGenerated,${new Date().toISOString()}\nStatus,Ready\n`;
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${reportId}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  const exportData = async (dataType: string) => {
    try {
      console.log('Exporting data:', dataType);
      
      let csvContent = '';
      let filename = '';

      switch (dataType) {
        case 'overview':
          csvContent = `Metric,Value\nTotal Claims,${overview?.claims_metrics.total_claims}\nApproval Rate,${formatPercentage(overview?.claims_metrics.approval_rate || 0)}\n`;
          filename = 'overview_metrics.csv';
          break;
        case 'trends':
          csvContent = 'Date,Claims Submitted,Claims Processed,Approval Rate\n';
          trends.forEach(trend => {
            csvContent += `${trend.date},${trend.claims_submitted},${trend.claims_processed},${formatPercentage(trend.approval_rate)}\n`;
          });
          filename = 'trend_data.csv';
          break;
        case 'performance':
          csvContent = 'Department,Claims Handled,Avg Processing Time,Accuracy Rate\n';
          performanceData.forEach(dept => {
            csvContent += `${dept.department},${dept.claims_handled},${dept.avg_processing_time},${formatPercentage(dept.accuracy_rate)}\n`;
          });
          filename = 'performance_data.csv';
          break;
        default:
          csvContent = 'Export Type,Not Supported\n';
          filename = 'export.csv';
      }

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading analytics dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analytics & Reporting</h1>
            <p className="text-gray-600">Comprehensive insights and performance metrics</p>
          </div>
          <div className="flex space-x-2">
            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="last_7_days">Last 7 Days</SelectItem>
                <SelectItem value="last_30_days">Last 30 Days</SelectItem>
                <SelectItem value="last_90_days">Last 90 Days</SelectItem>
                <SelectItem value="this_year">This Year</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={loadAnalyticsData} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Dialog open={customReportDialog} onOpenChange={setCustomReportDialog}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  Create Report
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create Custom Report</DialogTitle>
                  <DialogDescription>
                    Build a custom report with your selected metrics and filters
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="reportName">Report Name</Label>
                    <Input
                      id="reportName"
                      value={customReport.name}
                      onChange={(e) => setCustomReport(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter report name"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="reportDescription">Description</Label>
                    <Input
                      id="reportDescription"
                      value={customReport.description}
                      onChange={(e) => setCustomReport(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="Enter report description"
                    />
                  </div>
                  
                  <div>
                    <Label>Chart Type</Label>
                    <Select value={customReport.chart_type} onValueChange={(value: any) => setCustomReport(prev => ({ ...prev, chart_type: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="bar">Bar Chart</SelectItem>
                        <SelectItem value="line">Line Chart</SelectItem>
                        <SelectItem value="pie">Pie Chart</SelectItem>
                        <SelectItem value="table">Table</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="flex space-x-4">
                    <Button onClick={generateCustomReport} className="flex-1">
                      Generate Report
                    </Button>
                    <Button variant="outline" onClick={() => setCustomReportDialog(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="fraud">Fraud Analysis</TabsTrigger>
            <TabsTrigger value="reports">Reports</TabsTrigger>
            <TabsTrigger value="custom">Custom</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Claims</CardTitle>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{overview?.claims_metrics.total_claims.toLocaleString()}</div>
                  <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                    <TrendingUp className="h-3 w-3" />
                    <span>+12% from last period</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Approval Rate</CardTitle>
                  <Target className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatPercentage(overview?.claims_metrics.approval_rate || 0)}</div>
                  <Progress value={(overview?.claims_metrics.approval_rate || 0) * 100} className="h-2 mt-2" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Value</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatCurrency(overview?.financial_metrics.total_claim_value || 0)}</div>
                  <div className="text-xs text-green-600">
                    {formatCurrency(overview?.financial_metrics.cost_savings || 0)} saved
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Processing Time</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{formatDuration(overview?.claims_metrics.avg_processing_time || 0)}</div>
                  <div className="text-xs text-blue-600">
                    {formatPercentage(overview?.ai_metrics.automation_rate || 0)} automated
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Financial Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <DollarSign className="h-5 w-5" />
                    <span>Financial Breakdown</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Approved Amount</span>
                    <span className="font-medium text-green-600">
                      {formatCurrency(overview?.financial_metrics.approved_amount || 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Denied Amount</span>
                    <span className="font-medium text-red-600">
                      {formatCurrency(overview?.financial_metrics.denied_amount || 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Pending Amount</span>
                    <span className="font-medium text-yellow-600">
                      {formatCurrency(overview?.financial_metrics.pending_amount || 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-t pt-2">
                    <span className="text-sm font-medium">Cost Savings</span>
                    <span className="font-bold text-blue-600">
                      {formatCurrency(overview?.financial_metrics.cost_savings || 0)}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Zap className="h-5 w-5" />
                    <span>AI Performance</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Automation Rate</span>
                      <span className="text-sm font-medium">{formatPercentage(overview?.ai_metrics.automation_rate || 0)}</span>
                    </div>
                    <Progress value={(overview?.ai_metrics.automation_rate || 0) * 100} className="h-2" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">AI Accuracy</span>
                      <span className="text-sm font-medium">{formatPercentage(overview?.ai_metrics.ai_accuracy || 0)}</span>
                    </div>
                    <Progress value={(overview?.ai_metrics.ai_accuracy || 0) * 100} className="h-2" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">STP Rate</span>
                      <span className="text-sm font-medium">{formatPercentage(overview?.ai_metrics.stp_rate || 0)}</span>
                    </div>
                    <Progress value={(overview?.ai_metrics.stp_rate || 0) * 100} className="h-2" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* System Performance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5" />
                  <span>System Performance</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {formatPercentage(overview?.performance_metrics.system_uptime || 0)}
                    </div>
                    <div className="text-sm text-gray-600">System Uptime</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {overview?.performance_metrics.response_time}ms
                    </div>
                    <div className="text-sm text-gray-600">Response Time</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {formatPercentage(overview?.performance_metrics.error_rate || 0)}
                    </div>
                    <div className="text-sm text-gray-600">Error Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {formatPercentage(overview?.performance_metrics.user_productivity || 0)}
                    </div>
                    <div className="text-sm text-gray-600">User Productivity</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Export Options */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Download className="h-5 w-5" />
                  <span>Quick Exports</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex space-x-4">
                  <Button onClick={() => exportData('overview')} variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export Overview
                  </Button>
                  <Button onClick={() => exportData('trends')} variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export Trends
                  </Button>
                  <Button onClick={() => exportData('performance')} variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export Performance
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Trends Tab */}
          <TabsContent value="trends" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <LineChart className="h-5 w-5" />
                  <span>Claims Processing Trends</span>
                </CardTitle>
                <CardDescription>
                  30-day trend analysis of claims processing metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Simplified trend visualization */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {trends.reduce((sum, t) => sum + t.claims_submitted, 0).toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">Total Claims Submitted</div>
                      <div className="text-xs text-green-600 mt-1">
                        Avg: {Math.round(trends.reduce((sum, t) => sum + t.claims_submitted, 0) / trends.length)}/day
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {formatPercentage(trends.reduce((sum, t) => sum + t.approval_rate, 0) / trends.length)}
                      </div>
                      <div className="text-sm text-gray-600">Average Approval Rate</div>
                      <div className="text-xs text-blue-600 mt-1">
                        Range: {formatPercentage(Math.min(...trends.map(t => t.approval_rate)))} - {formatPercentage(Math.max(...trends.map(t => t.approval_rate)))}
                      </div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {formatDuration(trends.reduce((sum, t) => sum + t.avg_processing_time, 0) / trends.length)}
                      </div>
                      <div className="text-sm text-gray-600">Average Processing Time</div>
                      <div className="text-xs text-orange-600 mt-1">
                        Improved by 15% this month
                      </div>
                    </div>
                  </div>

                  {/* Recent trend highlights */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="h-4 w-4 text-green-500" />
                          <span className="text-sm font-medium">Best Performance Day</span>
                        </div>
                        <div className="text-lg font-bold mt-1">
                          {trends.reduce((best, current) => 
                            current.approval_rate > best.approval_rate ? current : best, trends[0]
                          )?.date || 'N/A'}
                        </div>
                        <div className="text-xs text-gray-600">
                          {formatPercentage(Math.max(...trends.map(t => t.approval_rate)))} approval rate
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <Clock className="h-4 w-4 text-blue-500" />
                          <span className="text-sm font-medium">Fastest Processing</span>
                        </div>
                        <div className="text-lg font-bold mt-1">
                          {formatDuration(Math.min(...trends.map(t => t.avg_processing_time)))}
                        </div>
                        <div className="text-xs text-gray-600">
                          Minimum processing time achieved
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5" />
                  <span>Department Performance</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Department</TableHead>
                      <TableHead>Claims Handled</TableHead>
                      <TableHead>Avg Processing Time</TableHead>
                      <TableHead>Accuracy Rate</TableHead>
                      <TableHead>Cost per Claim</TableHead>
                      <TableHead>Efficiency Score</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {performanceData.map((dept) => (
                      <TableRow key={dept.department}>
                        <TableCell className="font-medium">{dept.department}</TableCell>
                        <TableCell>{dept.claims_handled.toLocaleString()}</TableCell>
                        <TableCell>{formatDuration(dept.avg_processing_time)}</TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Progress value={dept.accuracy_rate * 100} className="w-16 h-2" />
                            <span className="text-sm">{formatPercentage(dept.accuracy_rate)}</span>
                          </div>
                        </TableCell>
                        <TableCell>{formatCurrency(dept.cost_per_claim)}</TableCell>
                        <TableCell>
                          <Badge variant={dept.efficiency_score >= 0.9 ? 'default' : dept.efficiency_score >= 0.8 ? 'secondary' : 'destructive'}>
                            {formatPercentage(dept.efficiency_score)}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Fraud Analysis Tab */}
          <TabsContent value="fraud" className="space-y-6">
            {fraudInsights && (
              <>
                {/* Fraud Overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Fraud Cases Detected</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-red-600">{fraudInsights.total_fraud_detected}</div>
                      <div className="text-xs text-gray-600">This period</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Prevention Savings</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">
                        {formatCurrency(fraudInsights.fraud_prevention_savings)}
                      </div>
                      <div className="text-xs text-gray-600">Total saved</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">Detection Rate</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-blue-600">
                        {formatPercentage(fraudInsights.fraud_detection_rate)}
                      </div>
                      <div className="text-xs text-gray-600">Accuracy rate</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Fraud Patterns */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <AlertTriangle className="h-5 w-5" />
                      <span>Top Fraud Patterns</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {fraudInsights.top_fraud_patterns.map((pattern, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                          <div className="flex items-center space-x-3">
                            <Badge 
                              variant={pattern.risk_level === 'high' ? 'destructive' : pattern.risk_level === 'medium' ? 'secondary' : 'default'}
                            >
                              {pattern.risk_level}
                            </Badge>
                            <span className="font-medium">{pattern.pattern}</span>
                          </div>
                          <div className="text-sm text-gray-600">
                            {pattern.frequency} cases
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Risk Score Distribution */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <PieChart className="h-5 w-5" />
                      <span>Risk Score Distribution</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {fraudInsights.risk_score_distribution.map((range, index) => (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Risk {range.range}</span>
                            <span className="text-sm font-medium">{range.count} claims ({formatPercentage(range.percentage)})</span>
                          </div>
                          <Progress value={range.percentage * 100} className="h-2" />
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Reports Tab */}
          <TabsContent value="reports" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <FileText className="h-5 w-5" />
                  <span>Generated Reports</span>
                </CardTitle>
                <CardDescription>
                  Download and manage your generated reports
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Report</TableHead>
                      <TableHead>Period</TableHead>
                      <TableHead>Generated</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reports.map((report) => (
                      <TableRow key={report.id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{report.title}</div>
                            <div className="text-sm text-gray-500">{report.description}</div>
                          </div>
                        </TableCell>
                        <TableCell>{report.period}</TableCell>
                        <TableCell>{new Date(report.generated_at).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Badge 
                            variant={
                              report.status === 'ready' ? 'default' : 
                              report.status === 'generating' ? 'secondary' : 'destructive'
                            }
                          >
                            {report.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{report.size}</TableCell>
                        <TableCell>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => downloadReport(report.id)}
                            disabled={report.status !== 'ready'}
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Download
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Custom Tab */}
          <TabsContent value="custom" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="h-5 w-5" />
                  <span>Custom Analytics</span>
                </CardTitle>
                <CardDescription>
                  Create custom reports and analytics views
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">Custom Report Builder</h3>
                  <p className="text-gray-600 mb-4">
                    Build custom reports with your specific metrics and filters
                  </p>
                  <Button onClick={() => setCustomReportDialog(true)}>
                    <FileText className="h-4 w-4 mr-2" />
                    Create Custom Report
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}