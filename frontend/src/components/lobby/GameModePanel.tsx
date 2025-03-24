import React from 'react';
import styled from 'styled-components';
import { useSetup, GameMode } from '../../contexts/SetupContext';

// Props definition
interface GameModePanelProps {
  onNext: () => void;
}

// Styled components
const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
`;

const Title = styled.h2`
  font-size: 1.8rem;
  margin-bottom: 2rem;
  color: #f0f0f0;
  text-align: center;
`;

const GameModeSelectionContainer = styled.div`
  display: flex;
  justify-content: center;
  gap: 2rem;
  width: 100%;
  max-width: 800px;
`;

const GameModeCard = styled.div<{ selected: boolean }>`
  width: 300px;
  padding: 2rem;
  background-color: ${props => props.selected ? 'rgba(46, 204, 113, 0.15)' : 'rgba(0, 0, 0, 0.2)'};
  border: 2px solid ${props => props.selected ? '#2ecc71' : 'transparent'};
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  position: relative;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
    border-color: ${props => props.selected ? '#2ecc71' : 'rgba(255, 255, 255, 0.3)'};
  }
`;

const GameModeIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 1.5rem;
`;

const GameModeTitle = styled.h3`
  font-size: 1.5rem;
  margin-bottom: 1rem;
`;

const GameModeDescription = styled.p`
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  line-height: 1.5;
`;

const NextButton = styled.button`
  padding: 0.8rem 2rem;
  margin-top: 2.5rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #2980b9;
  }
`;

const SelectedBadge = styled.div`
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: #2ecc71;
  color: white;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
`;

const GameModePanel: React.FC<GameModePanelProps> = ({ onNext }) => {
  const { config, setGameMode } = useSetup();
  
  const handleModeSelection = (mode: GameMode) => {
    setGameMode(mode);
  };
  
  return (
    <Container>
      <Title>Select Game Mode</Title>
      
      <GameModeSelectionContainer>
        <GameModeCard 
          selected={config.gameMode === 'cash'} 
          onClick={() => handleModeSelection('cash')}
        >
          {config.gameMode === 'cash' && <SelectedBadge>Selected</SelectedBadge>}
          <GameModeIcon>💰</GameModeIcon>
          <GameModeTitle>Cash Game</GameModeTitle>
          <GameModeDescription>
            Play a single table poker game with customizable buy-in and blind structure.
            Perfect for practicing specific scenarios and strategies against various
            opponent archetypes.
          </GameModeDescription>
        </GameModeCard>
        
        <GameModeCard 
          selected={config.gameMode === 'tournament'} 
          onClick={() => handleModeSelection('tournament')}
        >
          {config.gameMode === 'tournament' && <SelectedBadge>Selected</SelectedBadge>}
          <GameModeIcon>🏆</GameModeIcon>
          <GameModeTitle>Tournament</GameModeTitle>
          <GameModeDescription>
            Jump into a tournament at any stage, from early levels to the final table.
            Practice tournament-specific strategies against a customizable distribution
            of player archetypes based on tournament tier.
          </GameModeDescription>
        </GameModeCard>
      </GameModeSelectionContainer>
      
      <NextButton onClick={onNext}>
        Continue to {config.gameMode === 'cash' ? 'Cash Game' : 'Tournament'} Setup
      </NextButton>
    </Container>
  );
};

export default GameModePanel;