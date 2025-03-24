import React from 'react';
import styled from 'styled-components';
import { useSetup, Archetype, PlayerConfig } from '../../../contexts/SetupContext';

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

const PlayersContainer = styled.div`
  width: 100%;
  max-width: 800px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
`;

const PlayerCard = styled.div`
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
`;

const PlayerHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
`;

const PlayerNumber = styled.div`
  font-size: 1rem;
  font-weight: bold;
  color: #f0f0f0;
`;

const PlayerName = styled.input`
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  padding: 0.5rem;
  color: white;
  font-size: 1rem;
  width: 100%;
  margin-bottom: 1rem;
  
  &:focus {
    outline: none;
    border-color: #3498db;
  }
`;

const ArchetypeLabel = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  color: #f0f0f0;
  font-weight: bold;
`;

const SelectContainer = styled.div`
  position: relative;
  width: 100%;
  margin-bottom: 0.5rem;
`;

const SelectArrow = styled.div`
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: rgba(255, 255, 255, 0.7);
`;

const Select = styled.select`
  width: 100%;
  padding: 0.8rem;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  color: #f0f0f0;
  font-size: 1rem;
  appearance: none;
  cursor: pointer;
  
  &:focus {
    outline: none;
    border-color: #3498db;
  }
  
  option {
    background-color: #1e3b2e;
    color: #f0f0f0;
  }
`;

const ArchetypeDescription = styled.p`
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0.5rem 0 0 0;
  font-style: italic;
`;

const InfoText = styled.p`
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 1.5rem;
  text-align: center;
  font-style: italic;
`;

const CashGamePlayerSetup: React.FC = () => {
  const { config, updateCashGamePlayer } = useSetup();
  const { players } = config.cashGame;
  
  // Player archetype information
  const archetypeInfo: Record<Archetype, { name: string, description: string, color: string }> = {
    TAG: {
      name: "Tight Aggressive",
      description: "Plays few hands but plays them aggressively. Strong fundamental player.",
      color: "#3498db" // Blue
    },
    LAG: {
      name: "Loose Aggressive",
      description: "Plays many hands aggressively. Difficult to put on a hand range.",
      color: "#e74c3c" // Red
    },
    TightPassive: {
      name: "Tight Passive",
      description: "Plays few hands and tends to call rather than raise.",
      color: "#f39c12" // Orange
    },
    CallingStation: {
      name: "Calling Station",
      description: "Calls too frequently, rarely folds when they should.",
      color: "#9b59b6" // Purple
    },
    Maniac: {
      name: "Maniac",
      description: "Plays most hands and is extremely aggressive with constant raises.",
      color: "#e67e22" // Dark Orange
    },
    Beginner: {
      name: "Beginner",
      description: "Makes many fundamental errors in strategy and hand selection.",
      color: "#2ecc71" // Green
    },
    Unpredictable: {
      name: "Unpredictable",
      description: "Randomly assigned one archetype for the entire session. Unpredictable until you play against them.",
      color: "#7f8c8d" // Gray
    }
  };
  
  // Available archetypes
  const archetypes: Archetype[] = [
    'TAG', 'LAG', 'TightPassive', 'CallingStation', 'Maniac', 'Beginner', 'Unpredictable'
  ];
  
  const handleNameChange = (player: PlayerConfig, name: string) => {
    updateCashGamePlayer(player.position, { name });
  };
  
  const handleArchetypeChange = (player: PlayerConfig, e: React.ChangeEvent<HTMLSelectElement>) => {
    updateCashGamePlayer(player.position, { archetype: e.target.value as Archetype });
  };
  
  return (
    <Container>
      <Title>Cash Game Player Setup</Title>
      
      <PlayersContainer>
        {players.map(player => (
          <PlayerCard key={player.position}>
            <PlayerHeader>
              <PlayerNumber>Player {player.position}</PlayerNumber>
            </PlayerHeader>
            
            <PlayerName
              placeholder="Player Name"
              value={player.name}
              onChange={(e) => handleNameChange(player, e.target.value)}
            />
            
            <ArchetypeLabel htmlFor={`archetype-${player.position}`}>
              Playing Style
            </ArchetypeLabel>
            
            <SelectContainer>
              <Select
                id={`archetype-${player.position}`}
                value={player.archetype}
                onChange={(e) => handleArchetypeChange(player, e)}
                style={{ borderColor: archetypeInfo[player.archetype]?.color || 'rgba(255, 255, 255, 0.2)' }}
              >
                {archetypes.map(archetype => (
                  <option key={archetype} value={archetype}>
                    {archetypeInfo[archetype].name}
                  </option>
                ))}
              </Select>
              <SelectArrow>▼</SelectArrow>
            </SelectContainer>
            
            <ArchetypeDescription>
              {archetypeInfo[player.archetype]?.description}
            </ArchetypeDescription>
          </PlayerCard>
        ))}
      </PlayersContainer>
      
      <InfoText>
        Configure each opponent's archetype to practice against different playing styles.
        Select "Random" to have the AI randomly assign one archetype to that player for the entire session.
      </InfoText>
    </Container>
  );
};

export default CashGamePlayerSetup;