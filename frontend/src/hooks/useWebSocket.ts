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
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      console.log('Sending WebSocket message:', message.substring(0, 100));
      websocketRef.current.send(message);
      return true;
    } else {
      console.warn('Cannot send message, WebSocket not open. Current state:', 
        websocketRef.current ? 
        ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][websocketRef.current.readyState] : 
        'No connection'
      );
      return false;
    }
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

    // Prevent connecting if no URL provided
    if (!url) {
      console.warn('Cannot connect WebSocket - no URL provided');
      return;
    }

    // Close any existing connection
    if (websocketRef.current) {
      // Remove event handlers before closing to prevent unexpected callbacks
      if (websocketRef.current) {
        websocketRef.current.onclose = null;
        websocketRef.current.onopen = null;
        websocketRef.current.onmessage = null;
        websocketRef.current.onerror = null;
      }
      websocketRef.current.close();
      websocketRef.current = null;
    }

    // Create new connection
    console.log(`Creating new WebSocket connection to ${url}`);
    const ws = new WebSocket(url);
    websocketRef.current = ws;
    setStatus('connecting');

    // Setup event handlers
    ws.onopen = (event) => {
      console.log('WebSocket connection opened');
      reconnectCountRef.current = 0;
      setStatus('open');
      if (onOpen) onOpen(event);
    };

    ws.onmessage = (event) => {
      try {
        console.log('WebSocket message received:', 
          typeof event.data === 'string' ? 
          event.data.substring(0, 100) + (event.data.length > 100 ? '...' : '') : 
          'Binary data'
        );
        
        // Process the message first
        setLastMessage(event);
        
        // Then call the user-provided handler in a try-catch block
        if (onMessage) {
          try {
            // Add delay to prevent event handling race conditions
            setTimeout(() => {
              try {
                onMessage(event);
              } catch (delayedError) {
                console.error('Error in delayed onMessage handler:', delayedError);
              }
            }, 0);
          } catch (innerError) {
            // Don't let errors in the message handler break the connection
            console.error('Error in onMessage handler:', innerError);
          }
        }
      } catch (error) {
        // Don't let ANY error in message processing cause a disconnect
        console.error('Critical error processing WebSocket message:', error);
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket connection closed with code ${event.code}: ${event.reason}`);
      setStatus('closed');
      if (onClose) onClose(event);

      // Setup reconnection logic
      if (shouldReconnect && reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current += 1;
        console.log(`Reconnecting attempt ${reconnectCountRef.current} of ${reconnectAttempts} in ${reconnectInterval}ms`);
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error occurred:', event);
      setStatus('error');
      if (onError) onError(event);
    };
  }, [url, onOpen, onMessage, onClose, onError, reconnectInterval, reconnectAttempts, shouldReconnect]);

  // Connect when component mounts or URL changes
  useEffect(() => {
    console.log('useWebSocket mounting or URL changed, connecting to:', url);
    
    // Connect explicitly
    connect();

    // Cleanup on unmount
    return () => {
      console.log('useWebSocket unmounting, closing connection to:', url);
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      
      // Only close if we still have a reference (might be null if already closed)
      if (websocketRef.current) {
        console.log('Explicitly closing WebSocket on cleanup');
        try {
          // Set a flag to prevent auto-reconnect on this deliberate close
          websocketRef.current.onclose = null; // Remove onclose handler to prevent reconnect
          websocketRef.current.close(1000, "Component unmounting");
        } catch (e) {
          console.error('Error closing WebSocket:', e);
        }
        websocketRef.current = null;
      }
    };
  }, [url]); // Removed 'connect' from the dependency array to prevent reconnection cycles

  return {
    sendMessage,
    lastMessage,
    status,
    closeConnection,
    reconnect: connect,
  };
};