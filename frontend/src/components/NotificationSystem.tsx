import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Bell, 
  BellRing,
  X, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  Clock,
  Shield,
  Activity,
  Users,
  Settings,
  TrendingUp,
  AlertCircle,
  FileText,
  Zap
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useNotifications, Notification as NotificationItem } from '@/hooks/useNotifications';
import { formatDateTime } from '@/lib/api';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'system';
  category: 'claim' | 'fraud' | 'system' | 'user' | 'performance';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  read: boolean;
  created_at: string;
  action_url?: string;
  action_label?: string;
  related_entity_id?: string;
  related_entity_type?: 'claim' | 'user' | 'agent';
}

interface NotificationSystemProps {
  isOpen: boolean;
  onClose: () => void;
}

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: 'notif-001',
    type: 'warning',
    category: 'fraud',
    title: 'High-Risk Claim Detected',
    message: 'Claim CLM-2024-001 has been flagged for potential fraud with a risk score of 87%. Manual review required.',
    priority: 'high',
    read: false,
    created_at: '2024-01-15T11:45:00Z',
    action_url: '/enterprise/admin/claim/CLM-2024-001',
    action_label: 'Review Claim',
    related_entity_id: 'CLM-2024-001',
    related_entity_type: 'claim'
  },
  {
    id: 'notif-002',
    type: 'info',
    category: 'claim',
    title: 'Claim Processing Complete',
    message: 'Claim CLM-2024-005 has been successfully processed and approved for $2,450.00',
    priority: 'medium',
    read: false,
    created_at: '2024-01-15T11:30:00Z',
    action_url: '/enterprise/admin/claim/CLM-2024-005',
    action_label: 'View Details',
    related_entity_id: 'CLM-2024-005',
    related_entity_type: 'claim'
  },
  {
    id: 'notif-003',
    type: 'error',
    category: 'system',
    title: 'Agent Processing Error',
    message: 'Clinical Review Agent encountered an error processing claim CLM-2024-003. System intervention required.',
    priority: 'critical',
    read: false,
    created_at: '2024-01-15T11:15:00Z',
    action_url: '/enterprise/admin/agents',
    action_label: 'Check Agent Status',
    related_entity_id: 'clinical-review-agent',
    related_entity_type: 'agent'
  },
  {
    id: 'notif-004',
    type: 'success',
    category: 'performance',
    title: 'Processing Milestone Reached',
    message: 'System has successfully processed 1,000 claims today with 98.7% accuracy rate.',
    priority: 'low',
    read: true,
    created_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 'notif-005',
    type: 'warning',
    category: 'system',
    title: 'High Queue Volume',
    message: 'Claims processing queue has reached 25 pending items. Consider scaling processing resources.',
    priority: 'medium',
    read: false,
    created_at: '2024-01-15T09:45:00Z',
    action_url: '/enterprise/admin/queue',
    action_label: 'View Queue'
  },
  {
    id: 'notif-006',
    type: 'info',
    category: 'user',
    title: 'New User Registration',
    message: 'New user account created: jane.smith@healthcare.com with Processor role.',
    priority: 'low',
    read: true,
    created_at: '2024-01-15T09:30:00Z',
    action_url: '/enterprise/admin/users',
    action_label: 'Manage Users'
  }
];

const getNotificationIcon = (type: string, priority: string) => {
  if (priority === 'critical') {
    return <AlertCircle className="h-5 w-5 text-red-600" />;
  }

  switch (type) {
    case 'success':
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    case 'warning':
      return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    case 'error':
      return <AlertCircle className="h-5 w-5 text-red-600" />;
    case 'system':
      return <Settings className="h-5 w-5 text-blue-600" />;
    default:
      return <Info className="h-5 w-5 text-blue-600" />;
  }
};

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'claim':
      return <FileText className="h-4 w-4" />;
    case 'fraud':
      return <Shield className="h-4 w-4" />;
    case 'system':
      return <Settings className="h-4 w-4" />;
    case 'user':
      return <Users className="h-4 w-4" />;
    case 'performance':
      return <TrendingUp className="h-4 w-4" />;
    default:
      return <Bell className="h-4 w-4" />;
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low':
      return 'bg-gray-100 text-gray-800 border-gray-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

export default function NotificationSystem({ isOpen, onClose }: NotificationSystemProps) {
  const { user } = useAuth();
  const {
    notifications,
    unreadCount,
    loading,
    connected,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    loadNotifications
  } = useNotifications();

  const [activeTab, setActiveTab] = useState('all');

  // Refresh notifications when panel opens
  useEffect(() => {
    if (isOpen && loadNotifications) {
      loadNotifications();
    }
  }, [isOpen, loadNotifications]);

  const filteredNotifications = notifications.filter(notification => {
    if (activeTab === 'all') return true;
    if (activeTab === 'unread') return !notification.read;
    return notification.category === activeTab;
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-start justify-end pt-16 pr-4">
      <Card className="w-96 max-h-[80vh] bg-white shadow-2xl">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BellRing className="h-5 w-5 text-blue-600" />
              <CardTitle className="text-lg">Notifications</CardTitle>
              {unreadCount > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {unreadCount}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={markAllAsRead}
                  className="text-xs"
                >
                  Mark all read
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <CardDescription>
            Real-time system notifications and alerts
          </CardDescription>
        </CardHeader>

        <CardContent className="p-0">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <div className="px-6 border-b">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="all" className="text-xs">All</TabsTrigger>
                <TabsTrigger value="unread" className="text-xs">Unread</TabsTrigger>
                <TabsTrigger value="fraud" className="text-xs">Fraud</TabsTrigger>
                <TabsTrigger value="system" className="text-xs">System</TabsTrigger>
              </TabsList>
            </div>

            <ScrollArea className="h-96">
              <TabsContent value={activeTab} className="mt-0">
                <div className="p-3 space-y-3">
                  {filteredNotifications.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No notifications</p>
                    </div>
                  ) : (
                    filteredNotifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`border rounded-lg p-3 transition-all duration-200 hover:shadow-sm ${
                          !notification.read 
                            ? 'bg-blue-50 border-blue-200' 
                            : 'bg-white border-gray-200'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 mt-0.5">
                            {getNotificationIcon(notification.type, notification.priority)}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex items-center gap-2">
                                {getCategoryIcon(notification.category)}
                                <h4 className="text-sm font-medium text-gray-900 truncate">
                                  {notification.title}
                                </h4>
                              </div>
                              <div className="flex items-center gap-1">
                                <Badge
                                  variant="outline"
                                  className={`text-xs ${getPriorityColor(notification.priority)}`}
                                >
                                  {notification.priority.toUpperCase()}
                                </Badge>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => deleteNotification(notification.id)}
                                  className="h-6 w-6 p-0 hover:bg-red-50"
                                >
                                  <X className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                            
                            <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                              {notification.message}
                            </p>
                            
                            <div className="flex items-center justify-between mt-2">
                              <div className="flex items-center gap-2 text-xs text-gray-500">
                                <Clock className="h-3 w-3" />
                                {formatDateTime(notification.created_at)}
                              </div>
                              
                              <div className="flex items-center gap-2">
                                {notification.action_url && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="text-xs h-6"
                                    onClick={() => {
                                      markAsRead(notification.id);
                                      window.location.href = notification.action_url!;
                                    }}
                                  >
                                    {notification.action_label || 'View'}
                                  </Button>
                                )}
                                {!notification.read && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => markAsRead(notification.id)}
                                    className="text-xs h-6"
                                  >
                                    Mark read
                                  </Button>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </TabsContent>
            </ScrollArea>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}