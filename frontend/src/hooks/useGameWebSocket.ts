import { useCallback, useState, useEffect, useRef } from 'react';
import { useWebSocket } from './useWebSocket';

// Define message types based on API spec
interface CardModel {
  rank: string;
  suit: string;
}

interface PlayerModel {
  player_id: string;
  name: string;
  chips: number;
  position: number;
  status: string;
  current_bet: number;
  total_bet: number;
  cards?: CardModel[] | null;
}

interface PotModel {
  name: string;
  amount: number;
  eligible_player_ids: string[];
}

interface GameState {
  game_id: string;
  players: PlayerModel[];
  community_cards: CardModel[];
  pots: PotModel[];
  total_pot: number;
  current_round: string;
  button_position: number;
  current_player_idx: number;
  current_bet: number;
  small_blind: number;
  big_blind: number;
  max_buy_in?: number;
  min_buy_in?: number;
}

interface PlayerAction {
  player_id: string;
  action: string;
  amount?: number;
  timestamp: string;
}

interface HandResultWinner {
  player_id: string;
  name: string;
  amount: number;
  cards?: string[];
  hand_rank?: string;
}

interface HandResultPlayer {
  player_id: string;
  name: string;
  folded: boolean;
  cards?: string[];
}

interface HandResult {
  handId: string;
  winners: HandResultWinner[];
  players: HandResultPlayer[];
  board: string[];
  timestamp: string;
}

interface ActionRequest {
  handId: string;
  player_id: string;
  options: string[];
  callAmount: number;
  minRaise: number;
  maxRaise: number;
  timeLimit: number;
  timestamp: string;
}

interface ChatMessage {
  from: string;
  text: string;
  timestamp: string;
}

interface ErrorMessage {
  code: string;
  message: string;
  detail?: any;
}

interface WebSocketMessage {
  type: string;
  data: any;
}

/**
 * React hook for managing game WebSocket communication
 */
export const useGameWebSocket = (wsUrl: string) => {
  // Store player ID for checking turns
  const [playerId, setPlayerId] = useState<string | undefined>();
  
  // Extract playerId from URL if present
  useEffect(() => {
    // Skip if URL isn't provided
    if (!wsUrl) {
      console.log('No WebSocket URL provided, skipping URL parsing');
      return;
    }

    try {
      const url = new URL(wsUrl);
      const playerIdParam = url.searchParams.get('player_id');
      if (playerIdParam) {
        setPlayerId(playerIdParam);
        console.log('Extracted player ID from WebSocket URL:', playerIdParam);
      }
    } catch (e) {
      console.error('Error parsing WebSocket URL:', e);
    }
  }, [wsUrl]);
  
  // State for different message types
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [lastAction, setLastAction] = useState<PlayerAction | null>(null);
  const [actionRequest, setActionRequest] = useState<ActionRequest | null>(null);
  const [handResult, setHandResult] = useState<HandResult | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [errors, setErrors] = useState<ErrorMessage[]>([]);
  
  // Handle WebSocket messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      // Check if data is empty or invalid
      if (!event.data) {
        console.error('Empty WebSocket message received');
        return;
      }

      // Log raw data for debugging
      console.log('Raw message data:', typeof event.data === 'string' ? 
        event.data.substring(0, 200) + (event.data.length > 200 ? '...' : '') : 
        'Binary data');
      
      let message: WebSocketMessage;
      try {  
        message = JSON.parse(event.data);
      } catch (parseError) {
        console.error('Failed to parse WebSocket message:', parseError);
        return;
      }
      
      console.log('Received WebSocket message type:', message.type);
      
      // Add defensive checks
      if (!message || typeof message !== 'object') {
        console.error('Invalid message format, not an object');
        return;
      }
      
      if (!message.type) {
        console.error('Message has no type:', message);
        return;
      }
      
      // Validate data exists
      if (!message.data && message.type !== 'pong') {
        console.warn(`Message of type ${message.type} has no data`);
        // Continue processing anyway
      }
      
      // Process by type with extra error handling
      try {
        switch (message.type) {
          case 'game_state':
            console.log('Game state received with player count:', 
              message.data?.players?.length || 'unknown');
              
            // Add validation for game state
            if (!message.data?.players || !Array.isArray(message.data.players)) {
              console.error('Invalid game state: players array missing or not an array');
              return;
            }
            
            // Check each player has required data
            for (const player of message.data.players) {
              if (!player.player_id || typeof player.chips !== 'number') {
                console.warn('Player has invalid data:', player);
                // We continue anyway, don't return
              }
            }
            
            // Proceed with setting state after validation
            setGameState(message.data);
            break;
            
          case 'player_action':
            console.log('Player action received:', message.data);
            if (!message.data?.player_id || !message.data?.action) {
              console.error('Invalid player action data');
              return;
            }
            setLastAction(message.data);
            break;
            
          case 'action_request':
            console.log('Action request received:', message.data);
            if (!message.data?.player_id || !message.data?.options) {
              console.error('Invalid action request data');
              return;
            }
            setActionRequest(message.data);
            break;
            
          case 'hand_result':
            console.log('Hand result received:', message.data);
            setHandResult(message.data);
            break;
            
          case 'chat':
            console.log('Chat message received');
            setChatMessages(prev => [...prev, message.data]);
            break;
            
          case 'error':
            console.error('Game WebSocket error:', message.data);
            setErrors(prev => [...prev, message.data]);
            break;
            
          case 'pong':
            console.log('Pong received');
            break;
            
          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (processingError) {
        console.error(`Error processing message of type ${message.type}:`, processingError);
        // Don't throw, keep the connection alive
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      console.error('Raw message that caused error:', event.data);
      // Keep connection alive despite parsing errors
    }
  }, []);
  
  // Prevent unnecessary re-creation of WebSocket
  const wsUrlRef = useRef(wsUrl);
  
  // Create a ref to hold the sendMessage function
  const sendMessageRef = useRef<any>(null);
  
  // Setup WebSocket connection
  const { sendMessage, status, reconnect, lastMessage } = useWebSocket(wsUrlRef.current, {
    onMessage: handleMessage,
    reconnectAttempts: 20, // Increased for more persistent reconnection
    shouldReconnect: true,
    reconnectInterval: 3000, // Increased to 3 seconds for more stability
    onOpen: () => {
      // Send just a single ping with a delay to establish a connection
      console.log('WebSocket connection opened, will send ping after delay');
      
      // Use a longer delay to give things time to fully settle
      setTimeout(() => {
        try {
          console.log('Sending single initialization ping');
          sendMessage({
            type: 'ping',
            timestamp: Date.now(),
            stabilize: true
          });
        } catch (err) {
          console.error('Error sending initialization ping:', err);
        }
      }, 2000); // Single ping with 2 second delay
    },
    onClose: (event) => {
      console.log(`WebSocket closed with code ${event.code}, reason: "${event.reason}"`);
      // Log extra info for debugging
      if (event.code === 1001) {
        console.warn('Connection closed with "Going Away" code - this may indicate a server-side issue');
      }
    },
    onError: (event) => {
      console.error('WebSocket connection error:', event);
    }
  });
  
  // Store sendMessage in ref to maintain a stable reference
  useEffect(() => {
    sendMessageRef.current = sendMessage;
  }, [sendMessage]);
  
  // Send player action
  const sendAction = useCallback((action: string, amount?: number) => {
    const message = {
      type: 'action',
      data: {
        handId: gameState?.game_id,
        action,
        amount
      }
    };
    
    return sendMessage(message);
  }, [sendMessage, gameState?.game_id]);
  
  // Send chat message
  const sendChat = useCallback((text: string, target: 'table' | 'coach' = 'table') => {
    const message = {
      type: 'chat',
      data: {
        text,
        target
      }
    };
    
    return sendMessage(message);
  }, [sendMessage]);
  
  // Store connection status in a ref to avoid closure issues
  const statusRef = useRef(status);
  useEffect(() => {
    statusRef.current = status;
  }, [status]);
  
  // Track last successful response time to detect one-way connections
  const lastResponseRef = useRef(Date.now());
  
  // Keep track of ping/pong success rate
  const pingCountRef = useRef(0);
  const pongCountRef = useRef(0);
  
  // Store received pongs when they come in
  useEffect(() => {
    if (lastMessage?.data && typeof lastMessage.data === 'string') {
      try {
        const message = JSON.parse(lastMessage.data);
        if (message.type === 'pong') {
          console.log('Received pong response from server');
          lastResponseRef.current = Date.now();
          pongCountRef.current++;
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }
  }, [lastMessage]);
  
  // Heartbeat manager with adaptive ping interval based on connection quality
  useEffect(() => {
    if (status !== 'open') {
      return; // Don't start ping interval unless connection is open
    }
    
    // Ensure we have a valid sendMessage function
    if (!sendMessageRef.current) {
      sendMessageRef.current = sendMessage;
    }
    
    // Reset counters when connection (re)opens
    pingCountRef.current = 0;
    pongCountRef.current = 0;
    lastResponseRef.current = Date.now();
    
    // Increased ping interval to reduce traffic
    const basePingInterval = 60000; // 60 seconds instead of 30
    console.log('Starting heartbeat interval - approximately every 60 seconds');
    
    // Send ping every ~60 seconds, with refresh every ~4 minutes
    let pingCount = 0;
    const pingInterval = setInterval(() => {
      try {
        // Check if we've received any responses recently (within 2 intervals)
        const timeSinceLastResponse = Date.now() - lastResponseRef.current;
        const responseTimeout = basePingInterval * 2;
        
        // If server seems unresponsive but WebSocket is still "open",
        // we might be in the "backend tracking lost" state
        if (pingCountRef.current > 3 && 
            timeSinceLastResponse > responseTimeout && 
            statusRef.current === 'open') {
          console.log('Server not responding to pings. Reducing ping frequency to avoid log spam.');
          // Still send occasional pings in case the server reconnects
          if (pingCount % 5 !== 0) {
            return; // Skip 4 out of 5 pings when in this state
          }
        }
        
        pingCount++;
        pingCountRef.current++;
        const needsRefresh = pingCount % 4 === 0; // Request refresh every 4th ping
        console.log(`Sending heartbeat ping${needsRefresh ? ' with refresh' : ''}`);
        
        sendMessageRef.current({
          type: 'ping',
          timestamp: Date.now(),
          needsRefresh: needsRefresh
        });
      } catch (err) {
        console.error('Error sending ping:', err);
      }
    }, basePingInterval);
    
    // We don't need an immediate ping after connection as we already have 
    // one from the onOpen handler. This was causing double pings.
    
    return () => {
      console.log('Clearing heartbeat interval');
      clearInterval(pingInterval);
    };
  }, [status]); // Only depend on status changes, not lastMessage or sendMessage
  
  // Check if it's the player's turn
  const isPlayerTurn = useCallback(() => {
    if (!gameState || !playerId || !actionRequest) {
      return false;
    }
    
    return actionRequest.player_id === playerId;
  }, [gameState, playerId, actionRequest]);
  
  // Clear action request when it's no longer the player's turn
  useEffect(() => {
    if (actionRequest && lastAction && actionRequest.player_id === lastAction.player_id) {
      setActionRequest(null);
    }
  }, [lastAction, actionRequest]);
  
  return {
    status,
    gameState,
    lastAction,
    actionRequest,
    handResult,
    chatMessages,
    errors,
    sendAction,
    sendChat,
    reconnect,
    isPlayerTurn,
    lastMessage
  };
};