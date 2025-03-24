import React, { useState } from 'react';
import styled from 'styled-components';
import PokerTable from '../components/poker/PokerTable';
import ActionControls from '../components/poker/ActionControls';

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

// Mock game state for initial development
const initialGameState = {
  players: [
    { id: 'player', name: 'You', chips: 1000, position: 0, cards: [null, null], isActive: true, isCurrent: false, isDealer: true },
    { id: 'ai1', name: 'Bob', chips: 1200, position: 1, cards: [null, null], isActive: true, isCurrent: true, isDealer: false },
    { id: 'ai2', name: 'Alice', chips: 900, position: 2, cards: [null, null], isActive: true, isCurrent: false, isDealer: false },
    { id: 'ai3', name: 'Charlie', chips: 1500, position: 3, cards: [null, null], isActive: true, isCurrent: false, isDealer: false },
    { id: 'ai4', name: 'Dave', chips: 800, position: 4, cards: [null, null], isActive: true, isCurrent: false, isDealer: false },
    { id: 'ai5', name: 'Eve', chips: 1100, position: 5, cards: [null, null], isActive: true, isCurrent: false, isDealer: false },
  ],
  communityCards: [null, null, null, null, null],
  pot: 0,
  currentBet: 0,
  playerTurn: 'ai1',
  round: 'preflop'
};

const GamePage: React.FC = () => {
  const [gameState, setGameState] = useState(initialGameState);
  
  // Mock function to handle player actions
  const handleAction = (action: string, amount?: number) => {
    console.log(`Action taken: ${action}`, amount ? `Amount: ${amount}` : '');
    // In a real implementation, this would send the action to the backend
    // and update the game state based on the response
  };

  return (
    <GameContainer>
      <GameHeader>
        <GameTitle>Texas Hold'em Poker</GameTitle>
        <ChipCount>Your Chips: {gameState.players.find(p => p.id === 'player')?.chips}</ChipCount>
      </GameHeader>
      
      <PokerTable 
        players={gameState.players}
        communityCards={gameState.communityCards}
        pot={gameState.pot}
      />
      
      <ActionControls 
        onAction={handleAction}
        currentBet={gameState.currentBet}
        playerChips={gameState.players.find(p => p.id === 'player')?.chips || 0}
        isPlayerTurn={gameState.playerTurn === 'player'}
      />
    </GameContainer>
  );
};

export default GamePage;