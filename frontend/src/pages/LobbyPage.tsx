import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { SetupProvider, useSetup, GameMode } from '../contexts/SetupContext';
import GameModePanel from '../components/lobby/GameModePanel';
import CashGameSetup from '../components/lobby/CashGameSetup';
import TournamentSetup from '../components/lobby/TournamentSetup';
import PlayerSetup from '../components/lobby/PlayerSetup';

// Styled components
const LobbyContainer = styled.div`
  width: 100%;
  min-height: 100vh;
  background-color: #1e3b2e; /* Dark green background */
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: white;
`;

const LobbyHeader = styled.div`
  width: 100%;
  max-width: 1200px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
`;

const LobbyTitle = styled.h1`
  font-size: 2.5rem;
  margin: 0;
  color: #f0f0f0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
`;

const TabContainer = styled.div`
  display: flex;
  width: 100%;
  max-width: 1200px;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const Tab = styled.div<{ active: boolean }>`
  padding: 0.8rem 1.5rem;
  margin-right: 0.5rem;
  cursor: pointer;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  background-color: ${props => props.active ? '#2a5e45' : 'transparent'};
  color: ${props => props.active ? 'white' : 'rgba(255, 255, 255, 0.6)'};
  border: 1px solid ${props => props.active ? '#2a5e45' : 'transparent'};
  border-bottom: none;
  font-weight: ${props => props.active ? 'bold' : 'normal'};
  transition: all 0.2s ease;
  
  &:hover {
    background-color: ${props => props.active ? '#2a5e45' : 'rgba(255, 255, 255, 0.1)'};
  }
`;

const ContentContainer = styled.div`
  width: 100%;
  max-width: 1200px;
  background-color: #234535;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
`;

const StartGameButton = styled.button`
  padding: 1rem 2.5rem;
  font-size: 1.2rem;
  font-weight: bold;
  background-color: #f39c12; /* Orange button */
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 2rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #e67e22;
    transform: translateY(-2px);
  }
  
  &:active {
    transform: translateY(1px);
  }
`;

const ButtonContainer = styled.div`
  width: 100%;
  max-width: 1200px;
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
`;

// Enum for tab indexes
enum TabIndex {
  GAME_MODE = 0,
  GAME_SETUP = 1,
  PLAYER_SETUP = 2
}

// Inner component to use context
const LobbyContent: React.FC = () => {
  const navigate = useNavigate();
  const { config } = useSetup();
  const [activeTab, setActiveTab] = useState<TabIndex>(TabIndex.GAME_MODE);
  
  const handleStartGame = () => {
    // Save the final configuration before starting the game
    localStorage.setItem('currentGameSetup', JSON.stringify(config));
    
    // Navigate to the game page
    navigate('/game');
  };
  
  const renderTabContent = () => {
    switch (activeTab) {
      case TabIndex.GAME_MODE:
        return <GameModePanel onNext={() => setActiveTab(TabIndex.GAME_SETUP)} />;
      case TabIndex.GAME_SETUP:
        return config.gameMode === 'cash' 
          ? <CashGameSetup onNext={() => setActiveTab(TabIndex.PLAYER_SETUP)} /> 
          : <TournamentSetup onNext={() => setActiveTab(TabIndex.PLAYER_SETUP)} />;
      case TabIndex.PLAYER_SETUP:
        return <PlayerSetup />;
      default:
        return <div>Game Mode Selection</div>;
    }
  };
  
  const getTabName = (index: TabIndex): string => {
    switch (index) {
      case TabIndex.GAME_MODE:
        return "Game Mode";
      case TabIndex.GAME_SETUP:
        return config.gameMode === 'cash' ? "Cash Game Setup" : "Tournament Setup";
      case TabIndex.PLAYER_SETUP:
        return config.gameMode === 'cash' ? "Player Selection" : "Player Distribution";
      default:
        return "";
    }
  };
  
  return (
    <LobbyContainer>
      <LobbyHeader>
        <LobbyTitle>Chip Swinger Championship Poker Trainer</LobbyTitle>
      </LobbyHeader>
      
      <TabContainer>
        {[TabIndex.GAME_MODE, TabIndex.GAME_SETUP, TabIndex.PLAYER_SETUP].map((tab) => (
          <Tab 
            key={tab} 
            active={activeTab === tab}
            onClick={() => setActiveTab(tab)}
          >
            {getTabName(tab)}
          </Tab>
        ))}
      </TabContainer>
      
      <ContentContainer>
        {renderTabContent()}
      </ContentContainer>
      
      <ButtonContainer>
        <StartGameButton onClick={handleStartGame}>
          Start Game
        </StartGameButton>
      </ButtonContainer>
    </LobbyContainer>
  );
};

// Wrapper component with provider
const LobbyPage: React.FC = () => {
  return (
    <SetupProvider>
      <LobbyContent />
    </SetupProvider>
  );
};

export default LobbyPage;