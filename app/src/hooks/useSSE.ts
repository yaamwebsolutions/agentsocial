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
  // Use refs for callbacks to avoid re-creating EventSource when callbacks change
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // Ref to track if we've already connected (prevents double connections in Strict Mode)
  const hasConnectedRef = useRef(false);

  useEffect(() => {
    if (!threadId) return;

    // Prevent double connection in React Strict Mode
    if (hasConnectedRef.current) {
      return;
    }
    hasConnectedRef.current = true;

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
        optionsRef.current.onAgentRun?.(data.data);
      } catch (err) {
        console.error("Failed to parse agent_run event:", err);
      }
    });

    // Handle agent status change events
    eventSource.addEventListener("agent_status_change", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        optionsRef.current.onAgentStatusChange?.(data.data);
      } catch (err) {
        console.error("Failed to parse agent_status_change event:", err);
      }
    });

    // Handle new post events
    eventSource.addEventListener("new_post", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        optionsRef.current.onNewPost?.(data.data);
      } catch (err) {
        console.error("Failed to parse new_post event:", err);
      }
    });

    // Handle error events
    eventSource.addEventListener("error", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        optionsRef.current.onError?.(data.data.message);
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
      hasConnectedRef.current = false;
    };
  }, [threadId]);

  const reconnect = useCallback(() => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    hasConnectedRef.current = false;
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
