import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import PokerTable from '../components/poker/PokerTable';
import ActionControls from '../components/poker/ActionControls';
import CashGameControls from '../components/poker/CashGameControls';
import { useLocation, useNavigate } from 'react-router-dom';
import { useGameWebSocket } from '../hooks/useGameWebSocket';

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
`;

const GameTitle = styled.h1`
  margin: 0;
  font-size: 1.5rem;
`;

const ChipCount = styled.div`
  font-size: 1.2rem;
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

interface LocationState {
  gameId: string;
  playerId: string;
  gameMode: 'cash' | 'tournament';
}

const GamePage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { gameId, playerId, gameMode } = (location.state as LocationState) || {};
  
  // Redirect back to lobby if no game info is provided
  useEffect(() => {
    if (!gameId || !playerId) {
      navigate('/lobby');
    } else {
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
    }
  }, [gameId, playerId, navigate]);
  
  // Create websocket URL only once to avoid recreating the connection
  const wsUrl = React.useMemo(() => {
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsBaseUrl = API_URL.replace(/^https?:\/\//, `${wsProtocol}://`);
    return `${wsBaseUrl}/ws/game/${gameId}${playerId ? `?player_id=${playerId}` : ''}`;
  }, [gameId, playerId]);
  console.log('Using WebSocket URL:', wsUrl);
  
  // Connect to game using WebSocket with a stable reference
  const {
    status,
    gameState,
    actionRequest,
    handResult,
    sendAction,
    isPlayerTurn,
    errors,
    reconnect
  } = useGameWebSocket(wsUrl);
  
  // Store game state in local state when received
  const [localGameState, setLocalGameState] = React.useState<typeof gameState | null>(null);
  const [connectionStatus, setConnectionStatus] = React.useState("connecting");
  
  // Update local game state when WebSocket state changes
  React.useEffect(() => {
    if (gameState) {
      console.log('Saving new game state to local state');
      setLocalGameState(gameState);
      // Also save to localStorage as backup
      try {
        localStorage.setItem(`gameState_${gameId}`, JSON.stringify(gameState));
      } catch (e) {
        console.error('Failed to save game state to localStorage:', e);
      }
    }
  }, [gameState, gameId]);
  
  // Handle connection status and errors
  React.useEffect(() => {
    setConnectionStatus(status);
    
    // If we see "403 Forbidden" errors, the game might not exist anymore
    const hasGameNotFoundError = errors.some(err => 
      err.code === 'game_not_found' || 
      err.message?.includes('Game not found') ||
      err.message?.includes('not found')
    );
    
    if (hasGameNotFoundError) {
      console.error('Game not found on server. Redirecting to lobby...');
      // Clear any saved state for this game to prevent reconnection loops
      try {
        localStorage.removeItem(`gameState_${gameId}`);
      } catch (e) {
        console.error('Failed to clear localStorage:', e);
      }
      // Redirect back to lobby after a short delay
      setTimeout(() => navigate('/lobby'), 1000);
      return;
    }
    
    // If disconnected, try reconnecting after a delay
    if (status === 'closed' || status === 'error') {
      const timeoutId = setTimeout(() => {
        console.log('Attempting to reconnect...');
        reconnect();
      }, 2000);
      return () => clearTimeout(timeoutId);
    }
  }, [status, reconnect, errors, gameId, navigate]);
  
  // Debug logs to help identify the issue
  console.log('WebSocket status:', status);
  console.log('GameState exists:', !!gameState);
  console.log('LocalGameState exists:', !!localGameState);
  
  // Use either WebSocket game state or local game state
  const effectiveGameState = gameState || localGameState;
  
  // Only show loading if we have no game state at all
  const isLoading = !effectiveGameState;
  
  // Function to get the human player's data
  const getHumanPlayer = () => {
    if (!effectiveGameState) return null;
    
    try {
      // Add validation for players array
      if (!Array.isArray(effectiveGameState.players)) {
        console.error('Players is not an array in game state');
        return null;
      }
      
      const player = effectiveGameState.players.find(p => p && p.player_id === playerId);
      
      // If we can't find the player, log an error and return default values
      if (!player) {
        console.warn(`Could not find human player with ID ${playerId}`);
        console.log('Available players:', effectiveGameState.players.map(p => p?.player_id || 'undefined'));
        
        // Return a default player object as fallback
        return {
          player_id: playerId,
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
  const handlePlayerUpdate = () => {
    // In a real implementation, WebSocket updates would handle this
    console.log('Player data will be updated via WebSocket');
  };
  
  // Render loading screen if needed
  if (isLoading) {
    return (
      <GameContainer>
        <StatusOverlay>
          <LoadingSpinner />
          <StatusText>
            {status === 'connecting' ? 'Connecting to game...' : 'Loading game state...'}
          </StatusText>
          <BackButton onClick={handleBackToLobby}>Back to Lobby</BackButton>
        </StatusOverlay>
      </GameContainer>
    );
  }
  
  // Get human player
  const humanPlayer = getHumanPlayer();
  const chips = humanPlayer?.chips || 0;
  const currentBet = effectiveGameState?.current_bet || 0;
  
  // Add a connection status indicator to the UI
  const connectionIndicator = (
    <div style={{ 
      position: 'absolute', 
      top: '10px', 
      right: '10px', 
      padding: '5px 10px',
      borderRadius: '4px',
      backgroundColor: connectionStatus === 'open' ? 'rgba(0, 255, 0, 0.3)' : 'rgba(255, 0, 0, 0.3)',
      color: 'white',
      fontSize: '12px'
    }}>
      {connectionStatus === 'open' ? 'Connected' : 'Reconnecting...'}
    </div>
  );
  
  return (
    <GameContainer>
      <GameHeader>
        <GameTitle>Texas Hold'em Poker</GameTitle>
        <ChipCount>Your Chips: {chips}</ChipCount>
      </GameHeader>
      
      {/* Add connection status indicator */}
      {connectionIndicator}
      
      <PokerTable 
        players={transformPlayersForTable()}
        communityCards={(effectiveGameState?.community_cards || []).map(card => 
          card ? `${card.rank}${card.suit}` : null
        )}
        pot={effectiveGameState?.total_pot || 0}
      />
      
      <ActionControls 
        onAction={(action, amount) => sendAction(action, amount)}
        currentBet={currentBet}
        playerChips={chips}
        isPlayerTurn={isPlayerTurn()}
        actionRequest={actionRequest}
      />

      {/* Only show cash game controls for cash games */}
      {gameMode === 'cash' && effectiveGameState && (
        <CashGameControls
          gameId={gameId}
          playerId={playerId}
          chips={chips}
          maxBuyIn={effectiveGameState.max_buy_in ?? 2000}
          onPlayerUpdate={handlePlayerUpdate}
        />
      )}
      
      {/* Show hand result overlay if available */}
      {handResult && (
        <StatusOverlay>
          <StatusText>Hand Complete</StatusText>
          <div>
            {handResult.winners.map((winner, index) => (
              <div key={index}>
                {winner.name} wins ${winner.amount} with {winner.hand_rank}
              </div>
            ))}
          </div>
          <BackButton onClick={() => navigate(0)}>Play Next Hand</BackButton>
        </StatusOverlay>
      )}
      
      {/* Show error overlay if any errors */}
      {errors.length > 0 && (
        <StatusOverlay>
          <StatusText>Error</StatusText>
          <div style={{ color: 'red', marginBottom: '1rem' }}>
            {errors[errors.length - 1].message}
          </div>
          <BackButton onClick={() => navigate(0)}>Refresh Game</BackButton>
        </StatusOverlay>
      )}
    </GameContainer>
  );
};

export default GamePage;