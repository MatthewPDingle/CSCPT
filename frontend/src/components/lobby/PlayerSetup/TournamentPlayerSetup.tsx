import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useSetup, Archetype } from '../../../contexts/SetupContext';

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

const DistributionContainer = styled.div`
  width: 100%;
  max-width: 800px;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  padding: 2rem;
`;

const DistributionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const DistributionTitle = styled.h3`
  font-size: 1.4rem;
  margin: 0;
  color: #f0f0f0;
`;

const ResetButton = styled.button`
  padding: 0.5rem 1rem;
  background-color: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: rgba(231, 76, 60, 0.3);
  }
`;

const ArchetypeSliders = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const ArchetypeSlider = styled.div`
  display: flex;
  flex-direction: column;
`;

const SliderHeader = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
`;

const ArchetypeName = styled.span`
  font-weight: bold;
  color: #f0f0f0;
`;

const PercentageDisplay = styled.span`
  color: #3498db;
  font-weight: bold;
`;

const SliderContainer = styled.div`
  position: relative;
  width: 100%;
  height: 24px;
  margin: 0.5rem 0;
`;

const SliderTrack = styled.div`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  z-index: 1;
`;

const ProgressBar = styled.div`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  left: 0;
  height: 8px;
  background-color: #2ecc71;
  border-radius: 4px;
  z-index: 2;
  transition: width 0.2s;
`;

const Slider = styled.input.attrs({ type: 'range' })`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  outline: none;
  z-index: 3;
  margin: 0;
  padding: 0;
  
  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    background: #3498db;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
  }
  
  &::-moz-range-thumb {
    width: 18px;
    height: 18px;
    background: #3498db;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
    border: none;
  }
  
  &::-webkit-slider-runnable-track {
    -webkit-appearance: none;
    appearance: none;
    background: transparent;
    cursor: pointer;
  }
  
  &::-moz-range-track {
    background: transparent;
    cursor: pointer;
  }
`;

const TotalDisplay = styled.div<{ color?: string }>`
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  text-align: center;
  font-size: 1.1rem;
  font-weight: bold;
  color: ${props => props.color || '#f0f0f0'};
`;

const InfoText = styled.p`
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 1rem;
  text-align: center;
  font-style: italic;
`;

const ArchetypeDescription = styled.p`
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
`;

// Archetype info
const archetypeInfo: Record<Archetype, { description: string, color: string }> = {
  TAG: {
    description: "Tight-Aggressive players are disciplined and play fewer hands but play them aggressively.",
    color: "#3498db" // Blue
  },
  LAG: {
    description: "Loose-Aggressive players play more hands than average and play them aggressively.",
    color: "#e74c3c" // Red
  },
  TightPassive: {
    description: "Tight-Passive players play few hands and tend to call rather than raise, avoiding confrontation.",
    color: "#f39c12" // Orange
  },
  CallingStation: {
    description: "Calling Stations call too frequently and rarely fold when they should, chasing draws regardless of odds.",
    color: "#9b59b6" // Purple
  },
  Maniac: {
    description: "Maniacs play a very wide range of hands and are extremely aggressive with constant raises and re-raises.",
    color: "#e67e22" // Dark Orange
  },
  Beginner: {
    description: "Beginners have basic knowledge of the game but make many fundamental errors in strategy and hand selection.",
    color: "#2ecc71" // Green
  },
  Unpredictable: {
    description: "A player who switches between the other non-Beginner archetypes, making them difficult to read and counter.",
    color: "#7f8c8d" // Gray
  }
};

const TournamentPlayerSetup: React.FC = () => {
  const { config, updateArchetypeDistribution, resetTournamentDistribution } = useSetup();
  const { archetypeDistribution } = config.tournament;

  // Local state for immediate slider feedback
  const [localValues, setLocalValues] = useState(archetypeDistribution);

  // Sync local values with context when it changes
  useEffect(() => {
    setLocalValues(archetypeDistribution);
  }, [archetypeDistribution]);

  // Calculate total percentage based on local values
  const totalPercentage = Object.values(localValues).reduce((sum, val) => sum + val, 0);

  // Handle slider change (immediate local update)
  const handleSliderChange = (archetype: Archetype, value: number) => {
    setLocalValues(prev => ({ ...prev, [archetype]: value }));
  };

  // Handle slider release (update context with final value)
  const handleSliderRelease = (archetype: Archetype) => {
    updateArchetypeDistribution(archetype, localValues[archetype]);
  };

  return (
    <Container>
      <Title>Tournament Player Distribution</Title>
      
      <DistributionContainer>
        <DistributionHeader>
          <DistributionTitle>Archetype Distribution</DistributionTitle>
          <ResetButton onClick={resetTournamentDistribution}>
            Reset to Default
          </ResetButton>
        </DistributionHeader>
        
        <ArchetypeSliders>
          {Object.entries(archetypeDistribution).map(([archetype, percentage]) => {
            const archetypeKey = archetype as Archetype;
            const archetypeColor = archetypeInfo[archetypeKey]?.color || "#7f8c8d";
            const archetypeDesc = archetypeInfo[archetypeKey]?.description || "Player archetype";
            
            return (
              <ArchetypeSlider key={archetype}>
                <SliderHeader>
                  <ArchetypeName style={{ color: archetypeColor }}>
                    {archetype}
                  </ArchetypeName>
                  <PercentageDisplay>
                    {localValues[archetypeKey]}%
                  </PercentageDisplay>
                </SliderHeader>
                
                <ArchetypeDescription>
                  {archetypeDesc}
                </ArchetypeDescription>
                
                <SliderContainer>
                  <SliderTrack />
                  <ProgressBar 
                    style={{ 
                      width: `${localValues[archetypeKey]}%`,
                      backgroundColor: archetypeColor
                    }} 
                  />
                  <Slider
                    min="0"
                    max="100"
                    value={localValues[archetypeKey]}
                    onChange={(e) => handleSliderChange(archetypeKey, parseInt(e.target.value, 10))}
                    onMouseUp={() => handleSliderRelease(archetypeKey)}
                    onTouchEnd={() => handleSliderRelease(archetypeKey)}
                  />
                </SliderContainer>
              </ArchetypeSlider>
            );
          })}
        </ArchetypeSliders>
        
        <TotalDisplay color={totalPercentage === 100 ? '#2ecc71' : '#e74c3c'}>
          Total: {totalPercentage}% {totalPercentage === 100 ? '✓' : `(${100 - totalPercentage}% off)`}
        </TotalDisplay>
        
        <InfoText>
          The distribution above determines the likelihood of facing each player archetype in your tournament.
          Adjusting one archetype will automatically rebalance others to maintain a 100% total.
        </InfoText>
      </DistributionContainer>
    </Container>
  );
};

export default TournamentPlayerSetup;