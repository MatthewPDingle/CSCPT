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
    }
  }, [gameId, playerId, navigate]);
  
  // Connect to game using WebSocket
  const {
    status,
    gameState,
    actionRequest,
    handResult,
    sendAction,
    isPlayerTurn,
    errors
  } = useGameWebSocket(gameId, playerId);
  
  // Function to determine if we're showing loading screen
  const isLoading = status !== 'open' || !gameState;
  
  // Function to get the human player's data
  const getHumanPlayer = () => {
    if (!gameState) return null;
    return gameState.players.find(p => p.player_id === playerId);
  };
  
  // Function to transform backend player models to frontend format
  const transformPlayersForTable = () => {
    if (!gameState) return [];
    
    return gameState.players.map(player => {
      // Check if this player is at the button position
      const isButton = gameState.button_position === player.position;
      
      // Check if this player is the current player (whose turn it is)
      const isCurrent = gameState.current_player_idx !== undefined && 
        gameState.players[gameState.current_player_idx]?.player_id === player.player_id;
      
      // Transform card objects to strings for the Card component
      const transformedCards = player.cards 
        ? player.cards.map(card => card ? `${card.rank}${card.suit}` : null)
        : [null, null];
        
      return {
        id: player.player_id,
        name: player.name,
        chips: player.chips,
        position: player.position,
        cards: transformedCards,
        isActive: player.status === 'ACTIVE',
        isCurrent,
        isDealer: false, // The dealer seat is added separately in PokerTable
        isButton,
        isSB: player.position === (gameState.button_position + 1) % gameState.players.length,
        isBB: player.position === (gameState.button_position + 2) % gameState.players.length,
        currentBet: player.current_bet || 0
      };
    });
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
  const currentBet = gameState?.current_bet || 0;
  
  return (
    <GameContainer>
      <GameHeader>
        <GameTitle>Texas Hold'em Poker</GameTitle>
        <ChipCount>Your Chips: {chips}</ChipCount>
      </GameHeader>
      
      <PokerTable 
        players={transformPlayersForTable()}
        communityCards={(gameState?.community_cards || []).map(card => 
          card ? `${card.rank}${card.suit}` : null
        )}
        pot={gameState?.total_pot || 0}
      />
      
      <ActionControls 
        onAction={(action, amount) => sendAction(action, amount)}
        currentBet={currentBet}
        playerChips={chips}
        isPlayerTurn={isPlayerTurn()}
        actionRequest={actionRequest}
      />

      {/* Only show cash game controls for cash games */}
      {gameMode === 'cash' && gameState && (
        <CashGameControls
          gameId={gameId}
          playerId={playerId}
          chips={chips}
          maxBuyIn={gameState.max_buy_in ?? 2000}
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