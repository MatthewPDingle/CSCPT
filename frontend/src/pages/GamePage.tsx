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

const TableControls = styled.div`
  position: absolute;
  top: 70px;
  right: 20px;
  background-color: rgba(0, 0, 0, 0.7);
  padding: 1rem;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  color: white;
`;

const ControlLabel = styled.div`
  font-size: 0.9rem;
  margin-bottom: 0.3rem;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 0.3rem;
`;

const SizeButton = styled.button<{ active: boolean }>`
  background-color: ${props => props.active ? '#2ecc71' : '#34495e'};
  color: white;
  border: none;
  border-radius: 3px;
  padding: 0.3rem 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
  
  &:hover {
    background-color: ${props => props.active ? '#27ae60' : '#2c3e50'};
  }
`;

// Mock game state for initial development
const initialGameState = {
  players: [
    // Human player (position following alphabetical order)
    { id: 'player', name: 'You', chips: 1000, position: 9, cards: [null, null], isActive: true, isCurrent: false, isDealer: false, isButton: false, isSB: false, isBB: false },
    
    // AI players in alphabetical order (used for clockwise seating from dealer)
    { id: 'ai1', name: 'Alice', chips: 900, position: 1, cards: [null, null], isActive: true, isCurrent: false, isDealer: false, isButton: true, isSB: false, isBB: false },
    { id: 'ai2', name: 'Bob', chips: 1200, position: 2, cards: [null, null], isActive: true, isCurrent: true, isDealer: false, isButton: false, isSB: true, isBB: false },
    { id: 'ai3', name: 'Charlie', chips: 1500, position: 3, cards: [null, null], isActive: true, isCurrent: false, isDealer: false, isButton: false, isSB: false, isBB: true },
    { id: 'ai4', name: 'Dave', chips: 800, position: 4, cards: [null, null], isActive: true, isCurrent: false, isDealer: false, isButton: false, isSB: false, isBB: false },
    { id: 'ai5', name: 'Eve', chips: 1100, position: 5, cards: [null, null], isActive: true, isCurrent: false, isDealer: false, isButton: false, isSB: false, isBB: false },
    { id: 'ai6', name: 'Frank', chips: 950, position: 6, cards: [null, null], isActive: true, isCurrent: false, isDealer: false, isButton: false, isSB: false, isBB: false },
    { id: 'ai7', name: 'Grace', chips: 1050, position: 7, cards: [null, null], isActive: true, isCurrent: false, isDealer: false, isButton: false, isSB: false, isBB: false },
    { id: 'ai8', name: 'Hank', chips: 1300, position: 8, cards: [null, null], isActive: true, isCurrent: false, isDealer: false, isButton: false, isSB: false, isBB: false }
  ],
  communityCards: [null, null, null, null, null],
  pot: 0,
  currentBet: 0,
  playerTurn: 'ai2', // Bob is current player
  round: 'preflop'
};

const GamePage: React.FC = () => {
  const [gameState, setGameState] = useState(initialGameState);
  const [tableSize, setTableSize] = useState(9);
  
  // Mock function to handle player actions
  const handleAction = (action: string, amount?: number) => {
    console.log(`Action taken: ${action}`, amount ? `Amount: ${amount}` : '');
    // In a real implementation, this would send the action to the backend
    // and update the game state based on the response
  };
  
  // Function to change table size (2-9 players)
  const setTablePlayerCount = (count: number) => {
    if (count < 2 || count > 9) return;
    
    // Always keep the human player and include players alphabetically
    
    // Get the human player (always stays in the same position)
    const humanPlayer = initialGameState.players[0];
    
    // Get AI players in alphabetical order
    const aiPlayers = initialGameState.players.slice(1, 9);
    
    // Select the first (count-1) AI players
    const selectedAiPlayers = aiPlayers.slice(0, count - 1);
    
    // Keep original positions (since we use player IDs for positioning now)
    const selectedPlayers = [
      humanPlayer,
      ...selectedAiPlayers
    ];
    
    setGameState(prevState => ({
      ...prevState,
      players: selectedPlayers
    }));
    setTableSize(count);
  };

  return (
    <GameContainer>
      <GameHeader>
        <GameTitle>Texas Hold'em Poker</GameTitle>
        <ChipCount>Your Chips: {gameState.players.find(p => p.id === 'player')?.chips}</ChipCount>
      </GameHeader>
      
      <TableControls>
        <ControlLabel>Players at Table</ControlLabel>
        <ButtonGroup>
          {[2, 3, 4, 5, 6, 7, 8, 9].map(count => (
            <SizeButton 
              key={count} 
              active={tableSize === count}
              onClick={() => setTablePlayerCount(count)}
            >
              {count}
            </SizeButton>
          ))}
        </ButtonGroup>
      </TableControls>
      
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