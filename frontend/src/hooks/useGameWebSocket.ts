import { useCallback, useState, useEffect } from 'react';
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
export const useGameWebSocket = (gameId: string, playerId?: string) => {
  // Construct WebSocket URL
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsBaseUrl = API_URL.replace(/^https?:\/\//, `${wsProtocol}://`);
  const wsUrl = `${wsBaseUrl}/ws/game/${gameId}${playerId ? `?player_id=${playerId}` : ''}`;
  
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
      const message: WebSocketMessage = JSON.parse(event.data);
      console.log('Received WebSocket message type:', message.type);
      
      switch (message.type) {
        case 'game_state':
          console.log('Game state received:', message.data);
          setGameState(message.data);
          break;
        case 'player_action':
          console.log('Player action received:', message.data);
          setLastAction(message.data);
          break;
        case 'action_request':
          console.log('Action request received:', message.data);
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
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }, []);
  
  // Setup WebSocket connection
  const { sendMessage, status, reconnect } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    reconnectAttempts: 10,
    shouldReconnect: true,
    reconnectInterval: 1000, // Reconnect faster - every 1 second
    onOpen: () => {
      // Send an immediate ping when connection opens to establish stable connection
      console.log('WebSocket connection opened, sending immediate ping');
      setTimeout(() => {
        try {
          sendMessage({
            type: 'ping',
            timestamp: Date.now()
          });
        } catch (err) {
          console.error('Error sending immediate ping:', err);
        }
      }, 100); // Small delay to ensure connection is really ready
    }
  });
  
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
  
  // Send heartbeat
  useEffect(() => {
    if (status !== 'open') {
      return; // Don't start ping interval unless connection is open
    }
    
    console.log('Starting heartbeat interval');
    const pingInterval = setInterval(() => {
      try {
        console.log('Sending ping');
        sendMessage({
          type: 'ping',
          timestamp: Date.now()
        });
      } catch (err) {
        console.error('Error sending ping:', err);
      }
    }, 30000); // Send ping every 30 seconds
    
    return () => {
      console.log('Clearing heartbeat interval');
      clearInterval(pingInterval);
    };
  }, [sendMessage, status]);
  
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
    isPlayerTurn
  };
};