import { useEffect, useRef, useState, useCallback } from 'react';

type WebSocketStatus = 'connecting' | 'open' | 'closed' | 'error';

interface UseWebSocketOptions {
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  initialReconnectDelay?: number;   // Initial delay for first reconnect attempt
  maxReconnectDelay?: number;       // Maximum delay cap for backoff
  reconnectBackoffFactor?: number;  // Multiplier for each retry
  reconnectJitter?: number;         // Random jitter factor (e.g., 0.2 = ±20%)
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
    initialReconnectDelay = 1000,   // Start with 1 second
    maxReconnectDelay = 30000,      // Cap at 30 seconds
    reconnectBackoffFactor = 1.5,   // Increase by 50% each attempt
    reconnectJitter = 0.2,          // Add ±20% randomness
    reconnectAttempts = 10,         // More attempts with backoff
    shouldReconnect = true,
  } = options;

  const [status, setStatus] = useState<WebSocketStatus>('connecting');
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Define the interface for connection metrics
  interface ConnectionMetrics {
    connectionStartTime: number;
    connectionCount: number;
    totalConnectionDuration: number;
    disconnectionCount: number;
    successfulReconnects: number;
    failedReconnects: number;
    averageReconnectTime: number;
    lastDisconnectTime: number;
    connectionStability: number;
    // Extended metrics added by getConnectionMetrics
    currentConnectionDuration?: number;
    liveConnectionDuration?: number;
    averageConnectionDuration?: number;
    uptimePercentage?: number;
  }
  
  // Track connection quality metrics
  const connectionMetrics = useRef<ConnectionMetrics>({
    connectionStartTime: 0,        // When the current connection was established
    connectionCount: 0,            // Total successful connections
    totalConnectionDuration: 0,    // Total time connected in ms
    disconnectionCount: 0,         // Total number of disconnections
    successfulReconnects: 0,       // Times we successfully reconnected
    failedReconnects: 0,           // Times reconnection attempts ultimately failed
    averageReconnectTime: 0,       // Average time to reconnect in ms
    lastDisconnectTime: 0,         // When the last disconnect happened
    connectionStability: 1.0       // Score 0-1 of connection stability (1 = stable)
  });

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
      setStatus('open');
      
      // Update connection metrics
      const now = Date.now();
      connectionMetrics.current.connectionCount++;
      connectionMetrics.current.connectionStartTime = now;
      
      // If this was a reconnect, record it as successful
      if (reconnectCountRef.current > 0) {
        connectionMetrics.current.successfulReconnects++;
        
        // Calculate how long it took to reconnect
        if (connectionMetrics.current.lastDisconnectTime > 0) {
          const reconnectTime = now - connectionMetrics.current.lastDisconnectTime;
          
          // Update moving average of reconnect time
          const prevAvg = connectionMetrics.current.averageReconnectTime;
          const successfulReconnects = connectionMetrics.current.successfulReconnects;
          connectionMetrics.current.averageReconnectTime = 
            successfulReconnects === 1 ? 
            reconnectTime : // First reconnect, just use the time
            (prevAvg * (successfulReconnects - 1) + reconnectTime) / successfulReconnects; // Moving average
          
          console.log(`Reconnected after ${reconnectTime}ms (avg: ${Math.round(connectionMetrics.current.averageReconnectTime)}ms)`);
        }
        
        // Reset reconnect counter after successful connection
        reconnectCountRef.current = 0;
      }
      
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
      
      // Update connection metrics
      const now = Date.now();
      connectionMetrics.current.disconnectionCount++;
      connectionMetrics.current.lastDisconnectTime = now;
      
      // Calculate connection duration if we had an active connection
      if (connectionMetrics.current.connectionStartTime > 0) {
        const connectionDuration = now - connectionMetrics.current.connectionStartTime;
        connectionMetrics.current.totalConnectionDuration += connectionDuration;
        
        // Update connection stability metric
        // Short connections (< 5 seconds) indicate stability issues
        const wasShortConnection = connectionDuration < 5000;
        if (wasShortConnection) {
          // Reduce stability score for short connections (min 0.2)
          connectionMetrics.current.connectionStability = 
            Math.max(0.2, connectionMetrics.current.connectionStability * 0.8);
          console.log(`Short connection detected (${connectionDuration}ms). Stability score: ${connectionMetrics.current.connectionStability.toFixed(2)}`);
        } else {
          // Gradually improve stability score for longer connections
          connectionMetrics.current.connectionStability = 
            Math.min(1.0, connectionMetrics.current.connectionStability * 1.05);
        }
        
        connectionMetrics.current.connectionStartTime = 0;
      }
      
      if (onClose) onClose(event);

      // Setup reconnection logic with exponential backoff
      if (shouldReconnect && reconnectCountRef.current < reconnectAttempts) {
        // Calculate exponential backoff delay
        const attempt = reconnectCountRef.current;
        
        // Base delay with exponential increase
        let delay = initialReconnectDelay * 
                    Math.pow(reconnectBackoffFactor, attempt);
        
        // Apply maximum cap
        delay = Math.min(delay, maxReconnectDelay);
        
        // Adjust delay based on connection stability
        // Less stable connections get longer delays to prevent overwhelming the server
        const stabilityAdjustedDelay = delay / connectionMetrics.current.connectionStability;
        
        // Add random jitter (±jitter%) to prevent reconnection storms
        const jitterRange = stabilityAdjustedDelay * reconnectJitter;
        const actualDelay = Math.floor(
          stabilityAdjustedDelay + (Math.random() * jitterRange * 2 - jitterRange)
        );
        
        reconnectCountRef.current += 1;
        console.log(
          `Reconnecting attempt ${reconnectCountRef.current} of ${reconnectAttempts} ` +
          `in ${actualDelay}ms (base: ${Math.floor(delay)}ms, ` +
          `stability: ${connectionMetrics.current.connectionStability.toFixed(2)})`
        );
        
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, actualDelay);
      } else if (reconnectCountRef.current >= reconnectAttempts) {
        connectionMetrics.current.failedReconnects++;
        console.log(`Maximum reconnection attempts (${reconnectAttempts}) reached. Giving up.`);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error occurred:', event);
      setStatus('error');
      if (onError) onError(event);
    };
  }, [url, onOpen, onMessage, onClose, onError, 
      initialReconnectDelay, maxReconnectDelay, reconnectBackoffFactor, reconnectJitter,
      reconnectAttempts, shouldReconnect]);

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

  // Function to get the connection metrics
  const getConnectionMetrics = useCallback((): ConnectionMetrics => {
    const now = Date.now();
    const metrics = { ...connectionMetrics.current };
    
    // If we're currently connected, add the current session to the duration
    if (status === 'open' && metrics.connectionStartTime > 0) {
      metrics.currentConnectionDuration = now - metrics.connectionStartTime;
      metrics.liveConnectionDuration = metrics.totalConnectionDuration + metrics.currentConnectionDuration;
    } else {
      metrics.currentConnectionDuration = 0;
      metrics.liveConnectionDuration = metrics.totalConnectionDuration;
    }
    
    // Calculate average connection duration
    if (metrics.connectionCount > 0) {
      metrics.averageConnectionDuration = metrics.liveConnectionDuration / metrics.connectionCount;
    }
    
    // Calculate uptime percentage
    const totalTime = now - metrics.connectionStartTime + metrics.totalConnectionDuration;
    metrics.uptimePercentage = totalTime > 0 ? (metrics.liveConnectionDuration / totalTime) * 100 : 0;
    
    return metrics;
  }, [status]);

  return {
    sendMessage,
    lastMessage,
    status,
    closeConnection,
    reconnect: connect,
    getConnectionMetrics
  };
};