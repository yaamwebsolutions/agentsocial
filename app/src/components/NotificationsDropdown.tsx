import { useState } from "react";
import { Bell, Sparkles, Bot, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTheme } from "@/contexts/ThemeContext";
import { useNavigate } from "react-router-dom";

interface Notification {
  id: string;
  type: 'agent_response' | 'mention' | 'system';
  title: string;
  message: string;
  agentHandle?: string;
  agentIcon?: string;
  agentColor?: string;
  threadId?: string;
  timestamp: Date;
  read: boolean;
}

// Mock notifications - in production, these would come from the API
const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'agent_response',
    title: 'Grok responded',
    message: 'Here\'s what I found about that topic...',
    agentHandle: '@grok',
    agentIcon: '🚀',
    agentColor: '#10B981',
    threadId: 'thread-1',
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 min ago
    read: false,
  },
  {
    id: '2',
    type: 'mention',
    title: 'You were mentioned',
    message: '@dev mentioned you in a thread',
    agentHandle: '@dev',
    agentIcon: '⚡',
    agentColor: '#F59E0B',
    threadId: 'thread-2',
    timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 min ago
    read: false,
  },
  {
    id: '3',
    type: 'system',
    title: 'Welcome to AgentTwitter!',
    message: 'Start by mentioning agents in your posts',
    timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
    read: true,
  },
];

export function NotificationsDropdown() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [open, setOpen] = useState(false);

  const unreadCount = notifications.filter(n => !n.read).length;

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(n => ({ ...n, read: true }))
    );
  };

  const clearNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const handleNotificationClick = (notification: Notification) => {
    markAsRead(notification.id);
    setOpen(false);
    if (notification.threadId) {
      navigate(`/thread/${notification.threadId}`);
    }
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="relative rounded-full hover:bg-accent transition-all"
        >
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className={`absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full text-[10px] font-bold flex items-center justify-center ${
              isDark
                ? 'bg-amber-500 text-white'
                : 'bg-blue-500 text-white'
            }`}>
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-80 max-h-[400px] overflow-hidden flex flex-col"
      >
        <DropdownMenuLabel className="flex items-center justify-between py-3">
          <span className="font-semibold">Notifications</span>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={markAllAsRead}
              className="h-auto p-1 text-xs text-primary hover:underline"
            >
              Mark all read
            </Button>
          )}
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <div className="flex-1 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No notifications</p>
            </div>
          ) : (
            <DropdownMenuGroup>
              {notifications.map((notification) => (
                <DropdownMenuItem
                  key={notification.id}
                  className={`flex items-start gap-3 p-3 cursor-pointer transition-colors ${
                    !notification.read ? 'bg-muted/30' : ''
                  }`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  {/* Icon */}
                  <div className="flex-shrink-0 mt-0.5">
                    {notification.type === 'agent_response' || notification.type === 'mention' ? (
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-sm"
                        style={{ backgroundColor: notification.agentColor || '#3B82F6' }}
                      >
                        {notification.agentIcon || <Bot className="w-4 h-4 text-white" />}
                      </div>
                    ) : (
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        isDark ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400'
                      }`}>
                        <Sparkles className="w-4 h-4" />
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium text-sm truncate">{notification.title}</p>
                      {!notification.read && (
                        <div className={`w-2 h-2 rounded-full ${
                          isDark ? 'bg-amber-400' : 'bg-blue-400'
                        }`} />
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {notification.message}
                    </p>
                    <p className="text-[10px] text-muted-foreground/60 mt-0.5">
                      {formatTime(notification.timestamp)}
                    </p>
                  </div>

                  {/* Actions */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 flex-shrink-0 opacity-0 group-hover:opacity-100 hover:bg-destructive/20"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearNotification(notification.id);
                    }}
                  >
                    <Trash2 className="w-3 h-3 text-muted-foreground" />
                  </Button>
                </DropdownMenuItem>
              ))}
            </DropdownMenuGroup>
          )}
        </div>

        {notifications.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <div className="p-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAll}
                className="w-full justify-center text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Clear all notifications
              </Button>
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
