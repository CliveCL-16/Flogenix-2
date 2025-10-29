import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient } from '@/lib/api';
import { useAuth } from './useAuth';
import { useToast } from './use-toast';

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
  related_entity_type?: string;
}

export interface NotificationStats {
  total_notifications: number;
  unread_notifications: number;
  category_breakdown: Record<string, { total: number; unread: number }>;
  priority_breakdown: Record<string, { total: number; unread: number }>;
}

export function useNotifications() {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  
  // Load notifications from API
  const loadNotifications = useCallback(async (unreadOnly = false) => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await apiClient.getNotifications({
        unread_only: unreadOnly,
        limit: 50
      });
      setNotifications(response.notifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      toast({
        title: 'Error',
        description: 'Failed to load notifications',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  }, [user, toast]);
  
  // Load notification statistics
  const loadStats = useCallback(async () => {
    if (!user) return;
    
    try {
      const statsData = await apiClient.getNotificationStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load notification stats:', error);
    }
  }, [user]);
  
  // Mark notification as read
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await apiClient.markNotificationRead(notificationId);
      
      // Update local state
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      
      // Reload stats
      loadStats();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      toast({
        title: 'Error',
        description: 'Failed to mark notification as read',
        variant: 'destructive'
      });
    }
  }, [loadStats, toast]);
  
  // Mark all notifications as read
  const markAllAsRead = useCallback(async () => {
    try {
      const result = await apiClient.markAllNotificationsRead();
      
      // Update local state
      setNotifications(prev => 
        prev.map(n => ({ ...n, read: true }))
      );
      
      // Reload stats
      loadStats();
      
      toast({
        title: 'Success',
        description: `Marked ${result.updated_count} notifications as read`
      });
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      toast({
        title: 'Error',
        description: 'Failed to mark notifications as read',
        variant: 'destructive'
      });
    }
  }, [loadStats, toast]);
  
  // Delete notification
  const deleteNotification = useCallback(async (notificationId: string) => {
    try {
      await apiClient.deleteNotification(notificationId);
      
      // Update local state
      setNotifications(prev => 
        prev.filter(n => n.id !== notificationId)
      );
      
      // Reload stats
      loadStats();
    } catch (error) {
      console.error('Failed to delete notification:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete notification',
        variant: 'destructive'
      });
    }
  }, [loadStats, toast]);
  
  // Handle incoming WebSocket notification
  const handleNewNotification = useCallback((notification: Notification) => {
    // Add to notifications list
    setNotifications(prev => [notification, ...prev.slice(0, 49)]); // Keep only 50 latest
    
    // Show toast for high priority notifications
    if (notification.priority === 'high' || notification.priority === 'critical') {
      const variant = notification.type === 'error' ? 'destructive' : 'default';
      
      toast({
        title: notification.title,
        description: notification.message,
        variant
      });
    }
    
    // Update stats
    loadStats();
  }, [toast, loadStats]);
  
  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!user || wsRef.current?.readyState === WebSocket.OPEN) return;
    
    console.log('🔗 Connecting to notification WebSocket...');
    
    const ws = apiClient.connectNotifications(handleNewNotification);
    
    if (!ws) {
      console.error('Failed to create WebSocket connection');
      return;
    }
    
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('✅ Notification WebSocket connected');
      setConnected(true);
      reconnectAttempts.current = 0;
      
      // Clear any pending reconnection
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
    
    ws.onclose = (event) => {
      console.log('❌ Notification WebSocket disconnected:', event.code, event.reason);
      setConnected(false);
      wsRef.current = null;
      
      // Attempt to reconnect with exponential backoff
      if (user && reconnectAttempts.current < 10) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        console.log(`🔄 Reconnecting in ${delay}ms...`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++;
          connectWebSocket();
        }, delay);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };
  }, [user, handleNewNotification]);
  
  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setConnected(false);
  }, []);
  
  // Initialize notifications when user logs in
  useEffect(() => {
    if (user) {
      loadNotifications();
      loadStats();
      connectWebSocket();
    } else {
      setNotifications([]);
      setStats(null);
      disconnectWebSocket();
    }
    
    return () => {
      disconnectWebSocket();
    };
  }, [user, loadNotifications, loadStats, connectWebSocket, disconnectWebSocket]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);
  
  // Computed values
  const unreadCount = notifications.filter(n => !n.read).length;
  const hasUnread = unreadCount > 0;
  const criticalCount = notifications.filter(n => !n.read && n.priority === 'critical').length;
  const highPriorityCount = notifications.filter(n => !n.read && n.priority === 'high').length;
  
  return {
    // Data
    notifications,
    stats,
    unreadCount,
    hasUnread,
    criticalCount,
    highPriorityCount,
    
    // State
    loading,
    connected,
    
    // Actions
    loadNotifications,
    loadStats,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    connectWebSocket,
    disconnectWebSocket
  };
}