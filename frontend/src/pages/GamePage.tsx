import React, { useState, useEffect, useRef, useCallback } from 'react';
import styled from 'styled-components';
import PokerTable from '../components/poker/PokerTable';
import ActionControls from '../components/poker/ActionControls';
import CashGameControls from '../components/poker/CashGameControls';
import { useLocation, useNavigate } from 'react-router-dom';
import { useGameWebSocket } from '../hooks/useGameWebSocket';

// Audio initialization handled automatically in useGameWebSocket

const GameContainer = styled.div`
  width: 100%;
  height: 100vh;
  background-color: #2c3e50;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

const GameHeader = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 1rem;
  color: white;
  display: flex;
  justify-content: space-between;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 5;
`;

const GameTitle = styled.h1`
  margin: 0;
  font-size: 1.5rem;
`;

const ChipCount = styled.div`
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 1.2rem;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  z-index: 10;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
`;

const StatusOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  z-index: 100;
`;

const StatusText = styled.h2`
  margin: 1rem;
  font-size: 2rem;
`;

const LoadingSpinner = styled.div`
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #3498db;
  border-radius: 50%;
  animation: spin 2s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const BackButton = styled.button`
  padding: 0.8rem 1.5rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  margin-top: 2rem;
  
  &:hover {
    background-color: #2980b9;
  }
`;

const DebugButton = styled.button`
  padding: 0.5rem 1rem;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  z-index: 10;
  
  &:hover {
    background-color: #c0392b;
  }
  
  &:disabled {
    background-color: #7f8c8d;
    cursor: not-allowed;
  }
`;

// Connection status styled components
const ConnectionHealthDisplay = styled.div`
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 8px 12px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  z-index: 15;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  cursor: pointer;
  max-width: 250px;
`;

// Define the status type to avoid PropType warnings
type ConnectionStatus = 'open' | 'connecting' | 'closed';

const CopyButton = styled.button`
  position: absolute;
  top: 5px;
  right: 5px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-size: 0.8rem;
  padding: 3px 6px;
  border-radius: 3px;
  cursor: pointer;
  opacity: 0.7;
  transition: all 0.2s ease;
  z-index: 25;
  backdrop-filter: blur(2px);

  &:hover {
    opacity: 1;
    background: rgba(0, 0, 0, 0.8);
    border-color: rgba(255, 255, 255, 0.5);
  }
`;

// Use transient prop to avoid DOM warnings
// The $ prefix makes styled-components not pass the prop to the DOM
const ConnectionStatusDot = styled.div<{ $status: ConnectionStatus }>`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
  background-color: ${props => {
    if (props.$status === 'open') return '#2ecc71';
    if (props.$status === 'connecting') return '#f39c12';
    return '#e74c3c';
  }};
  display: inline-block;
`;

const ConnectionStats = styled.div`
  margin-top: 5px;
  font-size: 11px;
  color: #bdc3c7;
  line-height: 1.4;
`;

const ActionLogContainer = styled.div`
  position: absolute;
  bottom: 80px;
  left: 20px;
  width: 450px;
  height: 150px;
  background-color: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  z-index: 20;
  overflow: hidden;
`;

const ActionLogDisplay = styled.div`
  width: 100%;
  height: 100%;
  padding: 10px;
  overflow-y: auto;
  color: white;
  font-size: 0.8rem;

  /* Styling for scrollbar */
  &::-webkit-scrollbar {
    width: 5px;
  }
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 3px;
  }
  &::-webkit-scrollbar-thumb:hover {
    background: #555;
  }
`;

const ActionLogItem = styled.p`
   margin: 0 0 5px 0;
   line-height: 1.3;
`;

interface LocationState {
  gameId: string;
  playerId: string;
  gameMode: 'cash' | 'tournament';
}

const GamePage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Use state to ensure stable initialization before creating websocket
  const [initData, setInitData] = useState<{ gameId: string; playerId: string; gameMode: 'cash' | 'tournament' } | null>(null);
  const [copyStatus, setCopyStatus] = useState('');
  const [isShowdown, setIsShowdown] = useState<boolean>(false);
  const showdownTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // We'll add a debug logging useEffect later after useGameWebSocket is called
  
  // Extract required data from location state, only after mounting
  useEffect(() => {
    if (location.state) {
      const { gameId, playerId, gameMode } = location.state as LocationState;
      if (gameId && playerId) {
        console.log(`GamePage initializing with gameId=${gameId}, playerId=${playerId}, gameMode=${gameMode}`);
        setInitData({ gameId, playerId, gameMode });
        
        // Clear any old game state in localStorage if it's not for the current game
        try {
          // Get all keys in localStorage
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('gameState_') && !key.includes(gameId)) {
              console.log(`Clearing old game state: ${key}`);
              localStorage.removeItem(key);
            }
          }
        } catch (e) {
          console.error('Error clearing localStorage:', e);
        }
      } else {
        console.error("Game ID or Player ID missing in location state.");
        navigate('/lobby');
      }
    } else {
      console.error("No location state found for GamePage.");
      navigate('/lobby');
    }
  }, [location.state, navigate]);
  
  // Create websocket URL using useMemo, but only when initData is ready
  const wsUrl = React.useMemo(() => {
    if (!initData) {
      console.log("GamePage: initData not ready for WebSocket URL.");
      return ''; 
    }
    
    const { gameId, playerId } = initData;
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsBaseUrl = API_URL.replace(/^https?:\/\//, `${wsProtocol}://`);
    const url = `${wsBaseUrl}/ws/game/${gameId}${playerId ? `?player_id=${playerId}` : ''}`;
    
    console.log(`GamePage: Generated WebSocket URL: ${url}`);
    return url;
  }, [initData]);
  
  // Always use the hook (to follow React Hooks rules)
  // The hook will only actually connect when wsUrl is non-empty
  const {
    status,
    gameState,
    actionRequest,
    handResult,
    sendAction,
    isPlayerTurn,
    errors,
    reconnect,
    getConnectionHealth,
    actionLog,
    // Betting pot and animations
    accumulatedPot,
    currentStreetPot,
    betsToAnimate,
    flashMainPot,
    flashCurrentStreetPot,
    updatePlayerSeatPosition,
    // Community card reveal events
    pendingStreetReveal,
    // Showdown hole cards
    showdownHands,
    // Pot winners and chip distribution
    potWinners,
    chipsDistributed,
    // Final winner pulse event
    handVisuallyConcluded,
    // Turn highlighting states
    currentTurnPlayerId,
    showTurnHighlight,
    processingAITurn,
    foldedPlayerId
  } = useGameWebSocket(wsUrl);
  
  // Store game state in local state when received
  const [localGameState, setLocalGameState] = React.useState<typeof gameState | null>(null);
  const [connectionStatus, setConnectionStatus] = React.useState("connecting");
  const [showConnectionDetails, setShowConnectionDetails] = useState(false);
  const [connectionHealth, setConnectionHealth] = useState<any>(null);
  
  // Audio initialization now handled automatically in useGameWebSocket
  
  // Debug logging for turn state and action requests
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") {
      console.log("GamePage debug - isPlayerTurn result:", isPlayerTurn());
      console.log("GamePage debug - actionRequest state:", actionRequest);
      
      // More detailed debugging for action request state
      if (actionRequest) {
        console.log("GamePage debug - Action request details:", {
          player_id: actionRequest.player_id,
          options: actionRequest.options,
          timestamp: actionRequest.timestamp
        });
        
        // Check if this action request should be for the current player
        if (initData && actionRequest.player_id === initData.playerId) {
          console.log("🔔 GamePage debug - This action request is for the current player!");
        } else if (initData) {
          console.log("⚠️ GamePage debug - Action request is NOT for current player:", 
            actionRequest.player_id, "vs", initData.playerId);
        }
      }
      
      // Check game state for current player
      if (gameState && initData) {
        const currentPlayerIdx = gameState.current_player_idx;
        if (currentPlayerIdx >= 0 && currentPlayerIdx < gameState.players.length) {
          const currentPlayer = gameState.players[currentPlayerIdx];
          console.log("GamePage debug - Current player according to game state:", {
            name: currentPlayer?.name,
            id: currentPlayer?.player_id,
            isThisPlayer: currentPlayer?.player_id === initData.playerId
          });
        }
      }
    }
  }, [isPlayerTurn, actionRequest, gameState, initData]);
  
  // Update local game state when WebSocket state changes
  React.useEffect(() => {
    if (gameState && initData) {
      console.log('Saving new game state to local state');
      setLocalGameState(gameState);
      // Also save to localStorage as backup
      try {
        localStorage.setItem(`gameState_${initData.gameId}`, JSON.stringify(gameState));
      } catch (e) {
        console.error('Failed to save game state to localStorage:', e);
      }
    }
  }, [gameState, initData]);
  
  // Handle connection status and errors
  React.useEffect(() => {
    setConnectionStatus(status);
    
    // If we see "403 Forbidden" errors, the game might not exist anymore
    const hasGameNotFoundError = errors.some(err => 
      err.code === 'game_not_found' || 
      err.message?.includes('Game not found') ||
      err.message?.includes('not found')
    );
    
    if (hasGameNotFoundError && initData) {
      console.error('Game not found on server. Redirecting to lobby...');
      // Clear any saved state for this game to prevent reconnection loops
      try {
        // Remove ALL game-related localStorage items 
        Object.keys(localStorage).forEach(key => {
          if (key.startsWith('gameState_')) {
            console.log(`Clearing game state from localStorage: ${key}`);
            localStorage.removeItem(key);
          }
        });
      } catch (e) {
        console.error('Failed to clear localStorage:', e);
      }
      // Redirect back to lobby after a short delay
      setTimeout(() => navigate('/lobby'), 1000);
      return;
    }
    
    // The useWebSocket hook now handles reconnection with exponential backoff
    // We don't need manual reconnection logic here as it's handled by the hook
    if (status === 'closed' || status === 'error') {
      console.log('Connection closed or errored. The WebSocket hook will handle reconnection with exponential backoff.');
      // We can still update the UI to show reconnection status
      setConnectionHealth(getConnectionHealth());
      
      // If we get multiple connection errors, clear all saved game states to prevent connection loops
      if (errors.length > 3) {
        console.log('Multiple connection errors detected. Clearing all saved game states.');
        try {
          Object.keys(localStorage).forEach(key => {
            if (key.startsWith('gameState_')) {
              localStorage.removeItem(key);
            }
          });
        } catch (e) {
          console.error('Failed to clear localStorage:', e);
        }
      }
    }
  }, [status, errors, initData, navigate, getConnectionHealth]);
  
  // Use refs to track state changes and only log when they actually change
  const prevStatusRef = React.useRef(status);
  const prevGameStateRef = React.useRef(!!gameState);
  const prevLocalGameStateRef = React.useRef(!!localGameState);
  
  // Update connection health metrics periodically
  React.useEffect(() => {
    if (connectionStatus === 'open') {
      // Fetch connection health immediately when connected
      setConnectionHealth(getConnectionHealth());
      
      // Update every 5 seconds while connected
      const intervalId = setInterval(() => {
        setConnectionHealth(getConnectionHealth());
      }, 5000);
      
      return () => clearInterval(intervalId);
    }
  }, [connectionStatus, getConnectionHealth]);
  
  React.useEffect(() => {
    // Only log when values actually change
    if (prevStatusRef.current !== status) {
      console.log('WebSocket status changed to:', status);
      prevStatusRef.current = status;
    }
    
    if (prevGameStateRef.current !== !!gameState) {
      console.log('GameState exists:', !!gameState);
      prevGameStateRef.current = !!gameState;
    }
    
    if (prevLocalGameStateRef.current !== !!localGameState) {
      console.log('LocalGameState exists:', !!localGameState);
      prevLocalGameStateRef.current = !!localGameState;
    }
  }, [status, gameState, localGameState]);
  
  // Use either WebSocket game state or local game state
  const effectiveGameState = gameState || localGameState;

  // Handle showdown state to display cards
  useEffect(() => {
    if (handResult) {
      console.log('Showdown active - showing cards for all players');
      setIsShowdown(true);
      
      // Clear previous timer if any
      if (showdownTimerRef.current) {
        clearTimeout(showdownTimerRef.current);
      }
      
      // Set timer to hide cards after delay (2.5 seconds)
      showdownTimerRef.current = setTimeout(() => {
        console.log('Showdown timer expired - hiding cards');
        setIsShowdown(false);
      }, 1000); // Display cards for 1 second
    }
    
    // Cleanup timer on unmount
    return () => {
      if (showdownTimerRef.current) {
        clearTimeout(showdownTimerRef.current);
      }
    };
  }, [handResult]);
  
  // Only show loading if we have no game state at all
  const isLoading = !effectiveGameState;
  
  // Function to get the human player's data
  const getHumanPlayer = () => {
    if (!effectiveGameState || !initData) return null;
    
    try {
      // Add validation for players array
      if (!Array.isArray(effectiveGameState.players)) {
        console.error('Players is not an array in game state');
        return null;
      }
      
      const player = effectiveGameState.players.find(p => p && p.player_id === initData.playerId);
      
      // If we can't find the player, log an error and return default values
      if (!player) {
        console.warn(`Could not find human player with ID ${initData.playerId}`);
        console.log('Available players:', effectiveGameState.players.map(p => p?.player_id || 'undefined'));
        
        // Return a default player object as fallback
        return {
          player_id: initData.playerId,
          name: "You",
          chips: 1000,
          position: 0,
          status: "ACTIVE",
          current_bet: 0,
          total_bet: 0,
          cards: null
        };
      }
      
      return player;
    } catch (error) {
      console.error('Error finding human player:', error);
      return null;
    }
  };
  
  // Function to transform backend player models to frontend format
  const transformPlayersForTable = () => {
    if (!effectiveGameState) return [];
    
    try {
      console.log('Transforming players, count:', effectiveGameState.players?.length || 0);
      
      // Validate players array
      if (!Array.isArray(effectiveGameState.players)) {
        console.error('Players is not an array in game state');
        return []; // Return empty array instead of failing
      }
      
      return effectiveGameState.players.map((player, index) => {
        try {
          // Ensure player has required fields or use defaults
          if (!player) {
            console.warn(`Player at index ${index} is undefined, using default player`);
            // Return default player object to prevent rendering failures
            return {
              id: `missing_${index}`,
              name: `Player ${index}`,
              chips: 1000,
              position: index,
              cards: [null, null],
              isActive: false,
              isCurrent: false,
              isDealer: false,
              isButton: false,
              isSB: false,
              isBB: false,
              status: "ACTIVE",
              currentBet: 0
            };
          }
          
          // Check if this player is at the button position
          const isButton = effectiveGameState.button_position === player.position;
          
          // Check if this player is the current player (whose turn it is)
          const isCurrent = effectiveGameState.current_player_idx !== undefined && 
            effectiveGameState.players[effectiveGameState.current_player_idx]?.player_id === player.player_id;
          
          // Transform card objects to strings for the Card component
          // Handle potential null/undefined values safely
          const transformedCards = player.cards 
            ? player.cards.map(card => card ? `${card.rank}${card.suit}` : null)
            : [null, null];
            
          // Ensure we have exactly 2 cards for the UI
          if (!transformedCards || transformedCards.length !== 2) {
            if (transformedCards?.length === 0) {
              transformedCards.push(null, null);
            } else if (transformedCards?.length === 1) {
              transformedCards.push(null);
            }
          }
          
          // Get player position safely
          const position = typeof player.position === 'number' ? player.position : index;
          
          // Calculate button and blinds positions safely
          const playerCount = effectiveGameState.players.length;
          const buttonPos = effectiveGameState.button_position || 0;
          const sbPos = (buttonPos + 1) % playerCount;
          const bbPos = (buttonPos + 2) % playerCount;
            
          return {
            id: player.player_id || `player_${index}`,
            name: player.name || `Player ${index}`,
            chips: typeof player.chips === 'number' ? player.chips : 1000,
            position,
            cards: transformedCards || [null, null],
            isActive: player.status === 'ACTIVE',
            isCurrent,
            isDealer: false, // The dealer seat is added separately in PokerTable
            isButton,
            isSB: position === sbPos,
            isBB: position === bbPos,
            status: player.status, // Pass the player status to handle folded state
            currentBet: typeof player.current_bet === 'number' ? player.current_bet : 0
          };
        } catch (playerError) {
          console.error(`Error transforming player at index ${index}:`, playerError);
          // Return default player to avoid breaking UI
          return {
            id: `error_${index}`,
            name: `Player ${index}`,
            chips: 1000,
            position: index,
            cards: [null, null],
            isActive: false,
            isCurrent: false,
            isDealer: false,
            isButton: false,
            isSB: false,
            isBB: false,
            status: "ACTIVE",
            currentBet: 0
          };
        }
      });
    } catch (e) {
      // Catch any errors in the entire transformation process
      console.error('Failed to transform players:', e);
      console.error('Game state that caused error:', effectiveGameState);
      
      // Return empty array as fallback
      return [];
    }
  };
  
  // Function to handle going back to lobby
  const handleBackToLobby = () => {
    navigate('/lobby');
  };
  
  // Function to update player data after cash game operations
  const handlePlayerUpdate = useCallback(() => {
    // In a real implementation, WebSocket updates would handle this
    console.log('Player data will be updated via WebSocket');
  }, []);
  
  // Function to copy action log to clipboard
  const handleCopyLog = useCallback(() => {
    const logText = actionLog.join('\n');
    navigator.clipboard.writeText(logText)
      .then(() => {
        console.log('Action log copied to clipboard!');
        setCopyStatus('Copied!');
        setTimeout(() => setCopyStatus(''), 1500); // Clear message after 1.5s
      })
      .catch(err => {
        console.error('Failed to copy action log:', err);
        setCopyStatus('Failed');
        setTimeout(() => setCopyStatus(''), 1500);
      });
  }, [actionLog]);
  
  // Render loading screen if needed
  if (isLoading || !initData || !wsUrl || status === 'connecting' || status === 'error') {
    // Get connection health metrics even during loading/connecting
    const metrics = connectionHealth || (getConnectionHealth && getConnectionHealth());
    
    console.log(`GamePage Loading State - isLoading: ${isLoading}, initData: ${!!initData}, wsUrl: ${!!wsUrl}, status: ${status}`);
    
    return (
      <GameContainer>
        <StatusOverlay>
          <LoadingSpinner />
          <StatusText>
            {!initData
              ? 'Initializing game...'
              : !wsUrl 
                ? 'Initializing game connection...' 
                : status === 'error' 
                  ? 'Connection error. Reconnecting...'
                  : status === 'connecting' 
                    ? 'Connecting to game...' 
                    : 'Loading game state...'}
          </StatusText>
          
          {/* Show connection metrics if available */}
          {metrics && status !== 'open' && metrics.successfulReconnects > 0 && (
            <div style={{ 
              color: '#bdc3c7', 
              marginBottom: '1rem', 
              fontSize: '0.9rem',
              padding: '10px',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              borderRadius: '4px',
              maxWidth: '80%'
            }}>
              <div>Connection attempts: {metrics.connectionCount}</div>
              <div>Successful reconnects: {metrics.successfulReconnects}</div>
              <div>Connection stability: {(metrics.connectionStability * 100).toFixed(0)}%</div>
            </div>
          )}
          
          <div style={{ color: '#f39c12', marginBottom: '1rem', fontSize: '0.9rem' }}>
            {!initData && 'Game information not found. Please try again.'}
            {initData && !wsUrl && 'Game connection initialization failed. Please try again.'}
          </div>
          
          <div style={{ display: 'flex', gap: '10px' }}>
            <BackButton onClick={handleBackToLobby}>Back to Lobby</BackButton>
            
            {status === 'error' && (
              <BackButton 
                onClick={() => reconnect()} 
                style={{ backgroundColor: '#3498db' }}
              >
                Force Reconnect
              </BackButton>
            )}
          </div>
        </StatusOverlay>
      </GameContainer>
    );
  }
  
  // Get human player
  const humanPlayer = getHumanPlayer();
  const chips = humanPlayer?.chips || 0;
  const currentBet = effectiveGameState?.current_bet || 0;
  
  // Add a connection status indicator to the UI
  // Toggle connection details function must be defined inside the component
  const toggleConnectionDetails = () => {
    setShowConnectionDetails(prev => !prev);
    // Update metrics when expanding
    if (!showConnectionDetails) {
      setConnectionHealth(getConnectionHealth());
    }
  };

const connectionIndicator = (
  <ConnectionHealthDisplay onClick={toggleConnectionDetails}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <ConnectionStatusDot $status={connectionStatus as ConnectionStatus} />
        <span>{connectionStatus === 'open' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : 'Reconnecting...'}</span>
      </div>
      <span style={{ marginLeft: '5px', fontSize: '10px' }}>{showConnectionDetails ? '▲' : '▼'}</span>
    </div>
    
    {showConnectionDetails && connectionHealth && (
      <ConnectionStats>
        <div>Stability: {(connectionHealth.connectionStability * 100).toFixed(0)}%</div>
        {connectionHealth.currentConnectionDuration !== undefined && (
          <div>Uptime: {Math.floor(connectionHealth.currentConnectionDuration / 1000)}s</div>
        )}
        <div>Reconnects: {connectionHealth.successfulReconnects}</div>
        {connectionHealth.successfulReconnects > 0 && (
          <div>Connection count: {connectionHealth.connectionCount}</div>
        )}
        <div style={{ marginTop: '4px' }}>
          <DebugButton
            onClick={(e) => {
              e.stopPropagation();
              reconnect();
            }}
            style={{ 
              padding: '3px 6px', 
              fontSize: '10px', 
              backgroundColor: '#3498db'
            }}
          >
            Force Reconnect
          </DebugButton>
        </div>
      </ConnectionStats>
    )}
  </ConnectionHealthDisplay>
);
  
  // Function to manually trigger AI move - FOR DEBUGGING ONLY
  const triggerAIMove = async () => {
    if (!initData) {
      console.error("Cannot trigger AI move - game data not initialized");
      return;
    }

    try {
      const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      // Display warning that this is a debug-only function
      console.warn(
        "⚠️ DEBUG FUNCTION USED: Manually triggering AI move. " +
        "In normal gameplay, AI players should act automatically without manual triggers. " +
        "This may disrupt the natural flow of the game."
      );
      
      console.log(`Triggering AI move for game ${initData.gameId}`);
      
      // CRITICAL: Delay first to allow any in-flight WebSocket operations to complete
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const response = await fetch(`${API_URL}/game/ai-move/${initData.gameId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Don't include credentials to avoid CORS issues
        credentials: 'omit',
        // Use cors mode for cross-origin requests
        mode: 'cors'
      });
      
      if (!response.ok) {
        console.error('Failed to trigger AI move:', await response.text());
      } else {
        console.log('AI move triggered successfully');
      }
      
      // IMPORTANT: After AI move, we don't need to send manual pings
      // The WebSocket connection will automatically send keepalive pings
      // Just let the system handle reconnection if needed
      console.log('AI move completed, letting WebSocket manage its own connection');
      
      // Check connection health later
      setTimeout(() => {
        // Get connection health status
        const metrics = getConnectionHealth();
        console.log('Connection health after AI move:', 
          metrics?.connectionStability ? 
          `${(metrics.connectionStability * 100).toFixed(0)}%` : 'unknown');
      }, 1000);
      
    } catch (error) {
      console.error('Error triggering AI move:', error);
      
      // If there was an actual error with the fetch, then reconnect
      if (status !== 'open') {
        setTimeout(() => {
          console.log('Reconnecting WebSocket due to closed status');
          reconnect();
        }, 500);
      }
    }
  };
  
  return (
    <GameContainer>
      <GameHeader>
        <GameTitle>Texas Hold'em Poker</GameTitle>
      </GameHeader>
      
      {/* Add connection status indicator */}
      {connectionIndicator}
      
      {/* Audio initialization now handled automatically in useGameWebSocket */}
      
      <PokerTable
        // Pass the human player's ID for correct hole-card display
        humanPlayerId={initData?.playerId}
        players={transformPlayersForTable()}
        communityCards={(effectiveGameState?.community_cards || []).map(card =>
          card ? `${card.rank}${card.suit}` : null
        )}
        pot={accumulatedPot}
        flashMainPot={flashMainPot}
        currentRound={effectiveGameState?.current_round || ''}
        currentStreetTotal={currentStreetPot}
        betsToAnimate={betsToAnimate}
        updatePlayerSeatPosition={updatePlayerSeatPosition}
        flashCurrentStreetPot={flashCurrentStreetPot}
        pendingStreetReveal={pendingStreetReveal}
        showdownHands={showdownHands}
        potWinners={potWinners}
        chipsDistributed={chipsDistributed}
        handVisuallyConcluded={handVisuallyConcluded}
        handResultPlayers={handResult?.players}
        // IDs of winning players for pulsing their cards
        handWinners={handResult?.winners.map(w => w.player_id) ?? []}
        showdownActive={isShowdown}
        currentTurnPlayerId={currentTurnPlayerId}
        showTurnHighlight={showTurnHighlight}
        foldedPlayerId={foldedPlayerId}
      />
      
      {/* Debug logging handled before the return statement */}
      <ActionControls
        onAction={(action, amount) => sendAction(action, amount)}
        currentBet={currentBet}
        playerChips={chips}
        isPlayerTurn={isPlayerTurn()}
        actionRequest={actionRequest}
        bigBlind={effectiveGameState?.big_blind || 1}
      />

      {/* Chips count now appears at the bottom center */}
      <ChipCount>Your Chips: {chips}</ChipCount>

      {/* Only show cash game controls for cash games - now positioned at bottom */}
      {initData?.gameMode === 'cash' && effectiveGameState && (
        <div style={{
          position: 'absolute',
          bottom: '80px',
          right: '20px',
          zIndex: 10
        }}>
          <CashGameControls
            gameId={initData.gameId}
            playerId={initData.playerId}
            chips={chips}
            maxBuyIn={effectiveGameState.max_buy_in ?? 2000}
            onPlayerUpdate={handlePlayerUpdate}
          />
        </div>
      )}
      
      {/* Action Log Display */}
      {actionLog && actionLog.length > 0 && (
        <ActionLogContainer>
          <CopyButton onClick={handleCopyLog} title="Copy Action Log">
            {copyStatus || '📋'}
          </CopyButton>
          <ActionLogDisplay ref={(el) => {
            // Auto-scroll to bottom whenever action log changes
            if (el) {
              el.scrollTop = el.scrollHeight;
            }
          }}>
            {actionLog.map((log, index) => (
              <ActionLogItem key={index}>{log}</ActionLogItem>
            ))}
          </ActionLogDisplay>
        </ActionLogContainer>
      )}
      
      {/* Debug button to trigger AI moves */}
      <div style={{
        position: 'absolute',
        top: '80px',
        right: '20px',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        <div style={{
          backgroundColor: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '5px',
          borderRadius: '4px',
          marginBottom: '5px',
          fontSize: '10px',
          maxWidth: '120px',
          textAlign: 'center'
        }}>
          DEBUG ONLY: AI actions should happen automatically
        </div>
        <DebugButton 
          onClick={triggerAIMove}
          disabled={status !== 'open'}
        >
          Force AI Move
        </DebugButton>
      </div>
      
      
      {/* Show error overlay if any errors */}
      {errors.length > 0 && (
        <StatusOverlay>
          <StatusText>Error</StatusText>
          <div style={{ color: 'red', marginBottom: '1rem' }}>
            {errors[errors.length - 1].message}
          </div>
          <BackButton onClick={() => {
            // Reset UI state without page refresh
            setConnectionStatus("connecting");
            reconnect();
          }}>Refresh Game</BackButton>
        </StatusOverlay>
      )}
    </GameContainer>
  );
};

export default GamePage;