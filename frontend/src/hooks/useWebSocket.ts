import { useEffect, useRef, useState, useCallback } from 'react';

type WebSocketStatus = 'connecting' | 'open' | 'closed' | 'error';

interface UseWebSocketOptions {
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  reconnectInterval?: number;
  reconnectAttempts?: number;
  shouldReconnect?: boolean;
}

/**
 * React hook for managing WebSocket connections
 */
export const useWebSocket = (
  url: string, 
  options: UseWebSocketOptions = {}
) => {
  const {
    onOpen,
    onMessage,
    onClose,
    onError,
    reconnectInterval = 3000,
    reconnectAttempts = 5,
    shouldReconnect = true,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>('connecting');
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Function to handle sending messages
  const sendMessage = useCallback((data: any) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  // Function to close the connection
  const closeConnection = useCallback(() => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }
  }, []);

  // Function to connect or reconnect
  const connect = useCallback(() => {
    // Clear any existing reconnect timer
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    // Close any existing connection
    if (websocketRef.current) {
      websocketRef.current.close();
    }

    // Create new connection
    const ws = new WebSocket(url);
    websocketRef.current = ws;
    setStatus('connecting');

    // Setup event handlers
    ws.onopen = (event) => {
      reconnectCountRef.current = 0;
      setStatus('open');
      if (onOpen) onOpen(event);
    };

    ws.onmessage = (event) => {
      setLastMessage(event);
      if (onMessage) onMessage(event);
    };

    ws.onclose = (event) => {
      setStatus('closed');
      if (onClose) onClose(event);

      // Setup reconnection logic
      if (shouldReconnect && reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current += 1;
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      }
    };

    ws.onerror = (event) => {
      setStatus('error');
      if (onError) onError(event);
    };
  }, [url, onOpen, onMessage, onClose, onError, reconnectInterval, reconnectAttempts, shouldReconnect]);

  // Connect when component mounts or URL changes
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [connect]);

  return {
    sendMessage,
    lastMessage,
    status,
    closeConnection,
    reconnect: connect,
  };
};