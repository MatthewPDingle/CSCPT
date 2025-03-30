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
  font-size: 1.6rem;
  margin-bottom: 1.5rem;
  color: #f0f0f0;
  text-align: center;
`;

const DistributionContainer = styled.div`
  width: 100%;
  max-width: 800px;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  padding: 1.5rem;
`;

const DistributionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const DistributionTitle = styled.h3`
  font-size: 1.3rem;
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
  gap: 0.5rem; /* Reduced from 0.8rem */
  padding-right: 0.25rem;
  margin-bottom: 0.25rem;
`;

const ArchetypeSlider = styled.div`
  display: flex;
  flex-direction: column;
  padding: 0.3rem 0.4rem; /* Reduced vertical padding */
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.1);
  margin-bottom: 0.1rem; /* Minimal margin */
`;

const SliderHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.2rem; /* Reduced from 0.5rem */
`;

const ArchetypeName = styled.span`
  font-weight: bold;
  color: #f0f0f0;
  font-size: 0.9rem; /* Reduced size */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 65%; /* Limit width to prevent wrapping */
`;

const PercentageDisplay = styled.span`
  color: #3498db;
  font-weight: bold;
  font-size: 0.9rem; /* Reduced size */
`;

const SliderContainer = styled.div`
  position: relative;
  width: 100%;
  height: 18px; /* Further reduced from 20px */
  margin: 0.1rem 0; /* Reduced from 0.2rem */
`;

const SliderTrack = styled.div`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100%;
  height: 6px; /* Reduced from 8px */
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  z-index: 1;
`;

const ProgressBar = styled.div`
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  left: 0;
  height: 6px; /* Reduced from 8px */
  background-color: #2ecc71;
  border-radius: 3px;
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
    width: 16px; /* Reduced from 18px */
    height: 16px; /* Reduced from 18px */
    background: #3498db;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
  }
  
  &::-moz-range-thumb {
    width: 16px; /* Reduced from 18px */
    height: 16px; /* Reduced from 18px */
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
  margin-top: 1rem; /* Reduced from 1.5rem */
  padding: 0.7rem; /* Reduced from 1rem */
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  text-align: center;
  font-size: 1rem; /* Reduced from 1.1rem */
  font-weight: bold;
  color: ${props => props.color || '#f0f0f0'};
`;

const InfoText = styled.p`
  font-size: 0.8rem; /* Reduced from 0.9rem */
  color: rgba(255, 255, 255, 0.7);
  margin-top: 0.7rem; /* Reduced from 1rem */
  text-align: center;
  font-style: italic;
`;

const ArchetypeDescription = styled.p`
  font-size: 0.75rem; /* Reduced from 0.85rem */
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  line-height: 1.2; /* Added to reduce vertical space */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  max-height: 2.4em;
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
    description: "Tight-Passive players play very few, premium hands but rarely raise with them, preferring to call and minimize risk.",
    color: "#f39c12" // Orange
  },
  CallingStation: {
    description: "Calling Stations call excessively with weak holdings and chase draws regardless of odds. They rarely fold once invested in a pot.",
    color: "#9b59b6" // Purple
  },
  LoosePassive: {
    description: "Loose-Passive players play many starting hands but play them cautiously. Unlike Calling Stations, they can fold to pressure and rarely chase bad draws.",
    color: "#16a085" // Greenish Blue
  },
  Maniac: {
    description: "Maniacs play a very wide range of hands and are extremely aggressive with constant raises and re-raises.",
    color: "#e67e22" // Dark Orange
  },
  Beginner: {
    description: "Beginners have basic knowledge of the game but make many fundamental errors in strategy and hand selection.",
    color: "#2ecc71" // Green
  },
  Adaptable: {
    description: "Adaptable players change their strategy based on table dynamics and opponent tendencies.",
    color: "#8e44ad" // Purple
  },
  GTO: {
    description: "GTO players utilize balanced, mathematically sound strategies that are theoretically unexploitable.",
    color: "#1abc9c" // Turquoise
  },
  ShortStack: {
    description: "Short Stack specialists excel with small stacks, using push/fold strategies and maximizing fold equity.",
    color: "#d35400" // Burnt Orange
  },
  Trappy: {
    description: "Trappy players (slow-players) frequently underrepresent their hand strength to induce bluffs and build larger pots.",
    color: "#c0392b" // Dark Red
  }
};

const TournamentPlayerSetup: React.FC = () => {
  const { config, updateArchetypeDistribution, resetTournamentDistribution } = useSetup();
  const { archetypeDistribution } = config.tournament;

  // Local state for immediate slider feedback
  const [localValues, setLocalValues] = useState(archetypeDistribution);

  // Sync local values with context when it changes
  useEffect(() => {
    // Ensure all archetypes have values
    const allArchetypes: Archetype[] = [
      'TAG', 'LAG', 'TightPassive', 'CallingStation', 'LoosePassive', 
      'Maniac', 'Beginner', 'Adaptable', 'GTO', 'ShortStack', 'Trappy'
    ];
    
    // Create a complete distribution with all archetypes
    const completeDistribution = { ...archetypeDistribution };
    
    // Check if any archetypes are missing and add them with 0
    allArchetypes.forEach(arch => {
      if (completeDistribution[arch] === undefined) {
        completeDistribution[arch] = 0;
      }
    });
    
    setLocalValues(completeDistribution);
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
            
            // Format display name to make some long names more compact
            const displayName = archetypeKey === 'ShortStack' ? 'Short Stack' : 
                               archetypeKey === 'CallingStation' ? 'Call Station' : 
                               archetypeKey === 'TightPassive' ? 'Tight Passive' : 
                               archetypeKey === 'LoosePassive' ? 'Loose Passive' : archetype;
            
            return (
              <ArchetypeSlider key={archetype}>
                <SliderHeader>
                  <ArchetypeName style={{ color: archetypeColor }} title={archetypeDesc}>
                    {displayName}
                  </ArchetypeName>
                  <PercentageDisplay>
                    {localValues[archetypeKey]}%
                  </PercentageDisplay>
                </SliderHeader>
                
                <ArchetypeDescription title={archetypeDesc}>
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