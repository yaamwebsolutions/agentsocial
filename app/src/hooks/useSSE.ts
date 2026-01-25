import { useEffect, useRef, useState, useCallback } from "react";
import type { AgentRun, Post } from "@/types/api";

interface UseSSEOptions {
  onAgentRun?: (run: AgentRun) => void;
  onAgentStatusChange?: (run: AgentRun) => void;
  onNewPost?: (post: Post) => void;
  onError?: (error: string) => void;
}

export function useSSE(threadId: string, options: UseSSEOptions = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!threadId) return;

    const API_BASE =
      import.meta.env.VITE_API_BASE_URL ||
      import.meta.env.VITE_API_URL ||
      window.location.origin;

    const eventSource = new EventSource(
      `${API_BASE}/threads/${threadId}/stream`
    );

    eventSourceRef.current = eventSource;

    // Connection opened
    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    // Handle agent run events
    eventSource.addEventListener("agent_run", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        options.onAgentRun?.(data.data);
      } catch (err) {
        console.error("Failed to parse agent_run event:", err);
      }
    });

    // Handle agent status change events
    eventSource.addEventListener("agent_status_change", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        options.onAgentStatusChange?.(data.data);
      } catch (err) {
        console.error("Failed to parse agent_status_change event:", err);
      }
    });

    // Handle new post events
    eventSource.addEventListener("new_post", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        options.onNewPost?.(data.data);
      } catch (err) {
        console.error("Failed to parse new_post event:", err);
      }
    });

    // Handle error events
    eventSource.addEventListener("error", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        options.onError?.(data.data.message);
        setError(data.data.message);
      } catch (err) {
        console.error("Failed to parse error event:", err);
      }
    });

    // Handle connection errors
    eventSource.onerror = (err) => {
      setIsConnected(false);
      setError("Connection lost");
      console.error("SSE connection error:", err);
    };

    // Cleanup on unmount
    return () => {
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, [threadId]);

  const reconnect = useCallback(() => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setIsConnected(false);
    setError(null);
    // The useEffect will re-establish the connection
  }, []);

  return {
    isConnected,
    error,
    reconnect,
  };
}
