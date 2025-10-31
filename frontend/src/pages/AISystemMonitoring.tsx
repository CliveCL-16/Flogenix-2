import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertCircle, CheckCircle, Clock, Activity, Zap, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, Cpu, Database, Cloud, Shield, Brain, Target, Users, FileText, Settings, BarChart3, PieChart, LineChart } from 'lucide-react';
import { apiClient } from '@/lib/api';

// AI System Monitoring interfaces
interface SystemHealth {
  overall_status: 'healthy' | 'degraded' | 'critical';
  uptime_percentage: number;
  last_incident: string | null;
  services: Array<{
    name: string;
    status: 'online' | 'offline' | 'maintenance';
    response_time: number;
    error_rate: number;
    last_check: string;
  }>;
  infrastructure: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    network_latency: number;
  };
}

interface ModelPerformance {
  models: Array<{
    model_id: string;
    model_name: string;
    model_type: 'eligibility' | 'medical_review' | 'fraud_detection' | 'triage' | 'customer_support';
    version: string;
    status: 'active' | 'training' | 'deploying' | 'deprecated';
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    confidence_avg: number;
    predictions_count: number;
    last_updated: string;
    drift_score: number;
    performance_trend: 'improving' | 'stable' | 'declining';
  }>;
  ensemble_performance: {
    overall_accuracy: number;
    decision_consistency: number;
    processing_speed: number;
  };
}

interface AgentMetrics {
  agents: Array<{
    agent_name: string;
    agent_type: 'eligibility' | 'medical' | 'fraud' | 'triage' | 'customer_support' | 'exception_handling';
    status: 'active' | 'idle' | 'busy' | 'error';
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    avg_processing_time: number;
    success_rate: number;
    last_activity: string;
    current_load: number;
    queue_size: number;
  }>;
  workflow_efficiency: {
    end_to_end_time: number;
    handoff_delays: number;
    bottlenecks: string[];
    optimization_suggestions: string[];
  };
}

interface RealTimeMetrics {
  current_timestamp: string;
  active_sessions: number;
  claims_in_progress: number;
  api_requests_per_minute: number;
  average_response_time: number;
  error_rate: number;
  throughput: {
    claims_per_hour: number;
    decisions_per_hour: number;
    documents_processed_per_hour: number;
  };
  resource_utilization: {
    ai_compute_usage: number;
    database_connections: number;
    queue_lengths: Record<string, number>;
  };
}

interface AlertsAndNotifications {
  active_alerts: Array<{
    id: string;
    severity: 'critical' | 'warning' | 'info';
    category: 'performance' | 'security' | 'business' | 'technical';
    title: string;
    description: string;
    created_at: string;
    acknowledged: boolean;
    assigned_to?: string;
  }>;
  performance_warnings: Array<{
    metric: string;
    current_value: number;
    threshold: number;
    trend: 'increasing' | 'decreasing' | 'stable';
  }>;
  system_events: Array<{
    timestamp: string;
    event_type: 'deployment' | 'configuration_change' | 'maintenance' | 'incident';
    description: string;
    impact: 'none' | 'low' | 'medium' | 'high';
  }>;
}

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'healthy':
    case 'online':
    case 'active':
      return 'bg-green-500';
    case 'degraded':
    case 'warning':
    case 'idle':
      return 'bg-yellow-500';
    case 'critical':
    case 'offline':
    case 'error':
      return 'bg-red-500';
    case 'maintenance':
    case 'training':
    case 'deploying':
      return 'bg-blue-500';
    default:
      return 'bg-gray-500';
  }
};

const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
};

const formatUptime = (percentage: number): string => {
  return `${(percentage * 100).toFixed(3)}%`;
};

export default function AISystemMonitoring() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [modelPerformance, setModelPerformance] = useState<ModelPerformance | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics | null>(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState<RealTimeMetrics | null>(null);
  const [alerts, setAlerts] = useState<AlertsAndNotifications | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadSystemData();
    
    // Set up auto-refresh
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadSystemData(true);
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadSystemData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      if (silent) setRefreshing(true);

      const [healthData, performanceData, agentsData, metricsData, alertsData] = await Promise.all([
        apiClient.getAISystemHealth(),
        apiClient.getModelPerformance(),
        apiClient.getAgentMetrics(),
        loadRealTimeMetrics(),
        loadAlertsAndNotifications()
      ]);

      setSystemHealth(healthData);
      setModelPerformance(performanceData);
      setAgentMetrics(agentsData);
      setRealTimeMetrics(metricsData);
      setAlerts(alertsData);
    } catch (error) {
      console.error('Error loading system data:', error);
    } finally {
      if (!silent) setLoading(false);
      if (silent) setRefreshing(false);
    }
  };

  const loadSystemHealth = async (): Promise<SystemHealth> => {
    // Get system stats and health check data
    const systemStats = await apiClient.getSystemStats();
    const healthCheck = await apiClient.healthCheck();

    return {
      overall_status: healthCheck.status === 'healthy' ? 'healthy' : 'degraded',
      uptime_percentage: 0.9987, // Mock uptime
      last_incident: null,
      services: [
        {
          name: 'Claims Processing API',
          status: 'online',
          response_time: 245,
          error_rate: 0.002,
          last_check: new Date().toISOString()
        },
        {
          name: 'AI Decision Engine',
          status: 'online',
          response_time: 180,
          error_rate: 0.001,
          last_check: new Date().toISOString()
        },
        {
          name: 'Document Processing',
          status: 'online',
          response_time: 320,
          error_rate: 0.005,
          last_check: new Date().toISOString()
        },
        {
          name: 'Notification Service',
          status: 'online',
          response_time: 95,
          error_rate: 0.001,
          last_check: new Date().toISOString()
        },
        {
          name: 'Database',
          status: 'online',
          response_time: 12,
          error_rate: 0.0001,
          last_check: new Date().toISOString()
        }
      ],
      infrastructure: {
        cpu_usage: 0.65, // Mock value - would come from infrastructure monitoring
        memory_usage: 0.72, // Mock value
        disk_usage: 0.45, // Mock value
        network_latency: 8.5
      }
    };
  };

  const loadModelPerformance = async (): Promise<ModelPerformance> => {
    // Mock model performance data
    return {
      models: [
        {
          model_id: 'eligibility-v2.1',
          model_name: 'Eligibility Verification Model',
          model_type: 'eligibility',
          version: '2.1.0',
          status: 'active',
          accuracy: 0.947,
          precision: 0.952,
          recall: 0.941,
          f1_score: 0.946,
          confidence_avg: 0.892,
          predictions_count: 15420,
          last_updated: '2024-01-10T00:00:00Z',
          drift_score: 0.02,
          performance_trend: 'stable'
        },
        {
          model_id: 'medical-review-v3.0',
          model_name: 'Medical Review Assistant',
          model_type: 'medical_review',
          version: '3.0.1',
          status: 'active',
          accuracy: 0.923,
          precision: 0.934,
          recall: 0.911,
          f1_score: 0.922,
          confidence_avg: 0.867,
          predictions_count: 8743,
          last_updated: '2024-01-12T00:00:00Z',
          drift_score: 0.05,
          performance_trend: 'improving'
        },
        {
          model_id: 'fraud-detection-v4.2',
          model_name: 'Fraud Detection Engine',
          model_type: 'fraud_detection',
          version: '4.2.3',
          status: 'active',
          accuracy: 0.978,
          precision: 0.965,
          recall: 0.982,
          f1_score: 0.973,
          confidence_avg: 0.934,
          predictions_count: 12567,
          last_updated: '2024-01-08T00:00:00Z',
          drift_score: 0.01,
          performance_trend: 'stable'
        },
        {
          model_id: 'triage-v1.8',
          model_name: 'Claim Triage Classifier',
          model_type: 'triage',
          version: '1.8.2',
          status: 'active',
          accuracy: 0.889,
          precision: 0.901,
          recall: 0.876,
          f1_score: 0.888,
          confidence_avg: 0.812,
          predictions_count: 22341,
          last_updated: '2024-01-14T00:00:00Z',
          drift_score: 0.08,
          performance_trend: 'declining'
        }
      ],
      ensemble_performance: {
        overall_accuracy: 0.934,
        decision_consistency: 0.912,
        processing_speed: 2.3
      }
    };
  };

  const loadAgentMetrics = async (): Promise<AgentMetrics> => {
    // Get agent metrics from backend
    const agentData = await apiClient.getAgentMetrics();

    // Transform to expected format
    const transformedAgents = agentData.map((agent: any) => ({
      agent_name: agent.agent_name || agent.name,
      agent_type: agent.agent_type || 'eligibility',
      status: agent.status || 'active',
      total_tasks: agent.total_tasks || 0,
      completed_tasks: agent.completed_tasks || 0,
      failed_tasks: agent.failed_tasks || 0,
      avg_processing_time: agent.avg_processing_time || 0,
      success_rate: agent.success_rate || 0,
      last_activity: agent.last_activity || new Date().toISOString(),
      current_load: agent.current_load || 0,
      queue_size: agent.queue_size || 0
    }));

    return {
      agents: transformedAgents.length > 0 ? transformedAgents : [
        {
          agent_name: 'EligibilityAgent',
          agent_type: 'eligibility',
          status: 'active',
          total_tasks: 1542,
          completed_tasks: 1498,
          failed_tasks: 12,
          avg_processing_time: 1.8,
          success_rate: 0.972,
          last_activity: new Date().toISOString(),
          current_load: 0.65,
          queue_size: 23
        },
        {
          agent_name: 'MedicalReviewAgent',
          agent_type: 'medical',
          status: 'active',
          total_tasks: 874,
          completed_tasks: 856,
          failed_tasks: 8,
          avg_processing_time: 4.2,
          success_rate: 0.979,
          last_activity: new Date().toISOString(),
          current_load: 0.43,
          queue_size: 15
        },
        {
          agent_name: 'FraudDetectionAgent',
          agent_type: 'fraud',
          status: 'active',
          total_tasks: 1256,
          completed_tasks: 1243,
          failed_tasks: 3,
          avg_processing_time: 2.1,
          success_rate: 0.990,
          last_activity: new Date().toISOString(),
          current_load: 0.78,
          queue_size: 8
        },
        {
          agent_name: 'TriageAgent',
          agent_type: 'triage',
          status: 'active',
          total_tasks: 2234,
          completed_tasks: 2198,
          failed_tasks: 18,
          avg_processing_time: 0.8,
          success_rate: 0.984,
          last_activity: new Date().toISOString(),
          current_load: 0.52,
          queue_size: 34
        },
        {
          agent_name: 'CustomerSupportAgent',
          agent_type: 'customer_support',
          status: 'active',
          total_tasks: 456,
          completed_tasks: 445,
          failed_tasks: 5,
          avg_processing_time: 3.7,
          success_rate: 0.976,
          last_activity: new Date().toISOString(),
          current_load: 0.38,
          queue_size: 12
        }
      ],
      workflow_efficiency: {
        end_to_end_time: 6.8,
        handoff_delays: 0.3,
        bottlenecks: ['Medical Review Queue', 'Document Processing'],
        optimization_suggestions: [
          'Increase Medical Review Agent capacity during peak hours',
          'Implement parallel document processing for large files',
          'Add caching for frequently accessed eligibility data'
        ]
      }
    };
  };

  const loadRealTimeMetrics = async (): Promise<RealTimeMetrics> => {
    // Mock real-time metrics
    return {
      current_timestamp: new Date().toISOString(),
      active_sessions: 247,
      claims_in_progress: 156,
      api_requests_per_minute: 892,
      average_response_time: 234,
      error_rate: 0.0018,
      throughput: {
        claims_per_hour: 185,
        decisions_per_hour: 172,
        documents_processed_per_hour: 423
      },
      resource_utilization: {
        ai_compute_usage: 0.67,
        database_connections: 45,
        queue_lengths: {
          'eligibility_queue': 23,
          'medical_review_queue': 15,
          'fraud_detection_queue': 8,
          'triage_queue': 34,
          'document_processing_queue': 12
        }
      }
    };
  };

  const loadAlertsAndNotifications = async (): Promise<AlertsAndNotifications> => {
    // Mock alerts and notifications
    return {
      active_alerts: [
        {
          id: 'alert-001',
          severity: 'warning',
          category: 'performance',
          title: 'Medical Review Queue Length High',
          description: 'Medical review queue has exceeded normal capacity threshold',
          created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          acknowledged: false
        },
        {
          id: 'alert-002',
          severity: 'info',
          category: 'business',
          title: 'Model Performance Update Available',
          description: 'New version of fraud detection model ready for deployment',
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          acknowledged: true
        }
      ],
      performance_warnings: [
        {
          metric: 'Medical Review Processing Time',
          current_value: 4.2,
          threshold: 4.0,
          trend: 'increasing'
        },
        {
          metric: 'Document Processing Queue',
          current_value: 12,
          threshold: 10,
          trend: 'stable'
        }
      ],
      system_events: [
        {
          timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          event_type: 'deployment',
          description: 'Deployed fraud detection model v4.2.3',
          impact: 'none'
        },
        {
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          event_type: 'configuration_change',
          description: 'Updated eligibility agent timeout settings',
          impact: 'low'
        }
      ]
    };
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      console.log('Acknowledging alert:', alertId);
      
      // Update local state
      setAlerts(prev => prev ? {
        ...prev,
        active_alerts: prev.active_alerts.map(alert => 
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      } : null);
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const refreshData = async () => {
    await loadSystemData(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading AI system monitoring...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">AI System Monitoring</h1>
            <p className="text-gray-600">Real-time monitoring of AI models and system performance</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 text-sm">
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${systemHealth?.overall_status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                <span>System {systemHealth?.overall_status}</span>
              </div>
              <span className="text-gray-400">•</span>
              <span>Last updated: {realTimeMetrics?.current_timestamp ? new Date(realTimeMetrics.current_timestamp).toLocaleTimeString() : 'N/A'}</span>
            </div>
            <Button
              onClick={refreshData}
              disabled={refreshing}
              variant="outline"
              size="sm"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              onClick={() => setAutoRefresh(!autoRefresh)}
              variant={autoRefresh ? 'default' : 'outline'}
              size="sm"
            >
              {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            </Button>
          </div>
        </div>

        {/* System Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Uptime</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {formatUptime(systemHealth?.uptime_percentage || 0)}
              </div>
              <div className="text-xs text-muted-foreground">
                {systemHealth?.services.filter(s => s.status === 'online').length || 0} / {systemHealth?.services.length || 0} services online
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Claims</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{realTimeMetrics?.claims_in_progress || 0}</div>
              <div className="text-xs text-muted-foreground">
                {realTimeMetrics?.throughput.claims_per_hour || 0}/hour processing rate
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Performance</CardTitle>
              <Brain className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {formatPercentage(modelPerformance?.ensemble_performance.overall_accuracy || 0)}
              </div>
              <div className="text-xs text-muted-foreground">
                Overall model accuracy
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Response Time</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{realTimeMetrics?.average_response_time || 0}ms</div>
              <div className="text-xs text-muted-foreground">
                API average response
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Active Alerts */}
        {alerts && alerts.active_alerts.length > 0 && (
          <Card className="border-l-4 border-l-orange-500">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
                <span>Active Alerts ({alerts.active_alerts.filter(a => !a.acknowledged).length})</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alerts.active_alerts.filter(a => !a.acknowledged).slice(0, 3).map(alert => (
                  <div key={alert.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div className="flex items-center space-x-3">
                      <Badge variant={alert.severity === 'critical' ? 'destructive' : alert.severity === 'warning' ? 'secondary' : 'default'}>
                        {alert.severity}
                      </Badge>
                      <div>
                        <div className="font-medium text-sm">{alert.title}</div>
                        <div className="text-xs text-gray-600">{alert.description}</div>
                      </div>
                    </div>
                    <Button
                      onClick={() => acknowledgeAlert(alert.id)}
                      size="sm"
                      variant="outline"
                    >
                      Acknowledge
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="models">Model Performance</TabsTrigger>
            <TabsTrigger value="agents">Agent Metrics</TabsTrigger>
            <TabsTrigger value="infrastructure">Infrastructure</TabsTrigger>
            <TabsTrigger value="real-time">Real-time</TabsTrigger>
            <TabsTrigger value="alerts">Alerts</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Service Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Cloud className="h-5 w-5" />
                  <span>Service Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {systemHealth?.services.map((service, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(service.status)}`}></div>
                        <div>
                          <div className="font-medium text-sm">{service.name}</div>
                          <div className="text-xs text-gray-600">
                            {service.response_time}ms • {formatPercentage(service.error_rate)} errors
                          </div>
                        </div>
                      </div>
                      <Badge variant="outline" className={service.status === 'online' ? 'text-green-600' : 'text-red-600'}>
                        {service.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Throughput Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5" />
                    <span>Processing Throughput</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Claims per Hour</span>
                    <span className="font-medium">{realTimeMetrics?.throughput.claims_per_hour}/h</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Decisions per Hour</span>
                    <span className="font-medium">{realTimeMetrics?.throughput.decisions_per_hour}/h</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Documents per Hour</span>
                    <span className="font-medium">{realTimeMetrics?.throughput.documents_processed_per_hour}/h</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="h-5 w-5" />
                    <span>System Load</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Active Sessions</span>
                    <span className="font-medium">{realTimeMetrics?.active_sessions}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">API Requests/Min</span>
                    <span className="font-medium">{realTimeMetrics?.api_requests_per_minute}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Error Rate</span>
                    <span className={`font-medium ${(realTimeMetrics?.error_rate || 0) < 0.01 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercentage(realTimeMetrics?.error_rate || 0)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Model Performance Tab */}
          <TabsContent value="models" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Brain className="h-5 w-5" />
                  <span>AI Model Performance</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Model</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Accuracy</TableHead>
                      <TableHead>Predictions</TableHead>
                      <TableHead>Drift Score</TableHead>
                      <TableHead>Trend</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {modelPerformance?.models.map((model) => (
                      <TableRow key={model.model_id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{model.model_name}</div>
                            <div className="text-sm text-gray-500">{model.model_type}</div>
                          </div>
                        </TableCell>
                        <TableCell>{model.version}</TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(model.status)}>
                            {model.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Progress value={model.accuracy * 100} className="w-16 h-2" />
                            <span className="text-sm">{formatPercentage(model.accuracy)}</span>
                          </div>
                        </TableCell>
                        <TableCell>{model.predictions_count.toLocaleString()}</TableCell>
                        <TableCell>
                          <Badge variant={model.drift_score < 0.05 ? 'default' : model.drift_score < 0.1 ? 'secondary' : 'destructive'}>
                            {model.drift_score.toFixed(3)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            {model.performance_trend === 'improving' ? (
                              <TrendingUp className="h-4 w-4 text-green-500" />
                            ) : model.performance_trend === 'declining' ? (
                              <TrendingDown className="h-4 w-4 text-red-500" />
                            ) : (
                              <Activity className="h-4 w-4 text-gray-500" />
                            )}
                            <span className="text-sm capitalize">{model.performance_trend}</span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Ensemble Performance */}
            <Card>
              <CardHeader>
                <CardTitle>Ensemble Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {formatPercentage(modelPerformance?.ensemble_performance.overall_accuracy || 0)}
                    </div>
                    <div className="text-sm text-gray-600">Overall Accuracy</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {formatPercentage(modelPerformance?.ensemble_performance.decision_consistency || 0)}
                    </div>
                    <div className="text-sm text-gray-600">Decision Consistency</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {formatDuration(modelPerformance?.ensemble_performance.processing_speed || 0)}
                    </div>
                    <div className="text-sm text-gray-600">Avg Processing Speed</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Agent Metrics Tab */}
          <TabsContent value="agents" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="h-5 w-5" />
                  <span>AI Agent Performance</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Agent</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Success Rate</TableHead>
                      <TableHead>Avg Time</TableHead>
                      <TableHead>Current Load</TableHead>
                      <TableHead>Queue Size</TableHead>
                      <TableHead>Total Tasks</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {agentMetrics?.agents.map((agent) => (
                      <TableRow key={agent.agent_name}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{agent.agent_name}</div>
                            <div className="text-sm text-gray-500 capitalize">{agent.agent_type}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(agent.status)}>
                            {agent.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Progress value={agent.success_rate * 100} className="w-16 h-2" />
                            <span className="text-sm">{formatPercentage(agent.success_rate)}</span>
                          </div>
                        </TableCell>
                        <TableCell>{formatDuration(agent.avg_processing_time)}</TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Progress value={agent.current_load * 100} className="w-16 h-2" />
                            <span className="text-sm">{formatPercentage(agent.current_load)}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={agent.queue_size > 20 ? 'destructive' : agent.queue_size > 10 ? 'secondary' : 'default'}>
                            {agent.queue_size}
                          </Badge>
                        </TableCell>
                        <TableCell>{agent.total_tasks.toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Workflow Efficiency */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5" />
                  <span>Workflow Efficiency</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <div className="text-2xl font-bold text-blue-600">
                        {formatDuration(agentMetrics?.workflow_efficiency.end_to_end_time || 0)}
                      </div>
                      <div className="text-sm text-gray-600">End-to-end Processing Time</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-orange-600">
                        {formatDuration(agentMetrics?.workflow_efficiency.handoff_delays || 0)}
                      </div>
                      <div className="text-sm text-gray-600">Average Handoff Delays</div>
                    </div>
                  </div>

                  {agentMetrics?.workflow_efficiency.bottlenecks && agentMetrics.workflow_efficiency.bottlenecks.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Current Bottlenecks:</h4>
                      <div className="space-y-1">
                        {agentMetrics.workflow_efficiency.bottlenecks.map((bottleneck, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <AlertTriangle className="h-4 w-4 text-orange-500" />
                            <span className="text-sm">{bottleneck}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {agentMetrics?.workflow_efficiency.optimization_suggestions && agentMetrics.workflow_efficiency.optimization_suggestions.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Optimization Suggestions:</h4>
                      <div className="space-y-1">
                        {agentMetrics.workflow_efficiency.optimization_suggestions.map((suggestion, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <span className="text-sm">{suggestion}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Infrastructure Tab */}
          <TabsContent value="infrastructure" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Cpu className="h-5 w-5" />
                  <span>Infrastructure Metrics</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">CPU Usage</span>
                      <span className="text-sm font-medium">{formatPercentage(systemHealth?.infrastructure.cpu_usage || 0)}</span>
                    </div>
                    <Progress value={(systemHealth?.infrastructure.cpu_usage || 0) * 100} className="h-3" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Memory Usage</span>
                      <span className="text-sm font-medium">{formatPercentage(systemHealth?.infrastructure.memory_usage || 0)}</span>
                    </div>
                    <Progress value={(systemHealth?.infrastructure.memory_usage || 0) * 100} className="h-3" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Disk Usage</span>
                      <span className="text-sm font-medium">{formatPercentage(systemHealth?.infrastructure.disk_usage || 0)}</span>
                    </div>
                    <Progress value={(systemHealth?.infrastructure.disk_usage || 0) * 100} className="h-3" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Network Latency</span>
                      <span className="text-sm font-medium">{systemHealth?.infrastructure.network_latency}ms</span>
                    </div>
                    <Progress value={Math.min((systemHealth?.infrastructure.network_latency || 0) / 100 * 100, 100)} className="h-3" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Resource Utilization */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="h-5 w-5" />
                  <span>Resource Utilization</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">AI Compute Usage</span>
                      <span className="text-sm font-medium">{formatPercentage(realTimeMetrics?.resource_utilization.ai_compute_usage || 0)}</span>
                    </div>
                    <Progress value={(realTimeMetrics?.resource_utilization.ai_compute_usage || 0) * 100} className="h-2" />
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Database Connections</span>
                      <span className="text-sm font-medium">{realTimeMetrics?.resource_utilization.database_connections}/100</span>
                    </div>
                    <Progress value={(realTimeMetrics?.resource_utilization.database_connections || 0) / 100 * 100} className="h-2" />
                  </div>
                  
                  <div className="space-y-3">
                    <h4 className="font-medium">Queue Lengths</h4>
                    {realTimeMetrics?.resource_utilization.queue_lengths && Object.entries(realTimeMetrics.resource_utilization.queue_lengths).map(([queue, length]) => (
                      <div key={queue} className="flex items-center justify-between">
                        <span className="text-sm capitalize">{queue.replace('_', ' ')}</span>
                        <Badge variant={length > 20 ? 'destructive' : length > 10 ? 'secondary' : 'default'}>
                          {length}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Real-time Tab */}
          <TabsContent value="real-time" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Current Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Active Sessions</span>
                      <span className="text-lg font-bold">{realTimeMetrics?.active_sessions}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Claims in Progress</span>
                      <span className="text-lg font-bold">{realTimeMetrics?.claims_in_progress}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">API Requests/Min</span>
                      <span className="text-lg font-bold">{realTimeMetrics?.api_requests_per_minute}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Processing Rates</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Claims/Hour</span>
                      <span className="text-lg font-bold text-blue-600">{realTimeMetrics?.throughput.claims_per_hour}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Decisions/Hour</span>
                      <span className="text-lg font-bold text-green-600">{realTimeMetrics?.throughput.decisions_per_hour}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Documents/Hour</span>
                      <span className="text-lg font-bold text-purple-600">{realTimeMetrics?.throughput.documents_processed_per_hour}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Performance Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Avg Response Time</span>
                      <span className="text-lg font-bold">{realTimeMetrics?.average_response_time}ms</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Error Rate</span>
                      <span className={`text-lg font-bold ${(realTimeMetrics?.error_rate || 0) < 0.01 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercentage(realTimeMetrics?.error_rate || 0)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">AI Compute Usage</span>
                      <span className="text-lg font-bold text-orange-600">
                        {formatPercentage(realTimeMetrics?.resource_utilization.ai_compute_usage || 0)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Active Alerts */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <AlertTriangle className="h-5 w-5" />
                    <span>Active Alerts</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-64">
                    <div className="space-y-3">
                      {alerts?.active_alerts.map((alert) => (
                        <div key={alert.id} className={`p-3 border rounded ${alert.acknowledged ? 'bg-gray-50' : 'bg-white'}`}>
                          <div className="flex items-center justify-between mb-2">
                            <Badge variant={alert.severity === 'critical' ? 'destructive' : alert.severity === 'warning' ? 'secondary' : 'default'}>
                              {alert.severity}
                            </Badge>
                            <span className="text-xs text-gray-500">{new Date(alert.created_at).toLocaleString()}</span>
                          </div>
                          <div className="font-medium text-sm">{alert.title}</div>
                          <div className="text-xs text-gray-600 mt-1">{alert.description}</div>
                          {!alert.acknowledged && (
                            <Button
                              onClick={() => acknowledgeAlert(alert.id)}
                              size="sm"
                              variant="outline"
                              className="mt-2"
                            >
                              Acknowledge
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* Performance Warnings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5" />
                    <span>Performance Warnings</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {alerts?.performance_warnings.map((warning, index) => (
                      <div key={index} className="p-3 border rounded">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">{warning.metric}</span>
                          <Badge variant="secondary">{warning.trend}</Badge>
                        </div>
                        <div className="text-xs text-gray-600 mt-1">
                          Current: {warning.current_value} | Threshold: {warning.threshold}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* System Events */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5" />
                  <span>Recent System Events</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {alerts?.system_events.map((event, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center space-x-3">
                        <Badge variant="outline" className="capitalize">
                          {event.event_type.replace('_', ' ')}
                        </Badge>
                        <span className="text-sm">{event.description}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant={event.impact === 'high' ? 'destructive' : event.impact === 'medium' ? 'secondary' : 'default'}>
                          {event.impact}
                        </Badge>
                        <span className="text-xs text-gray-500">{new Date(event.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
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