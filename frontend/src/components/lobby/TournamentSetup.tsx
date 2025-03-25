import React from 'react';
import styled from 'styled-components';
import { useSetup, TournamentTier, TournamentStage, AnteValueType } from '../../contexts/SetupContext';

// Props definition
interface TournamentSetupProps {
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

const FormContainer = styled.div`
  width: 100%;
  max-width: 600px;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  padding: 2rem;
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #f0f0f0;
`;

const SelectContainer = styled.div`
  position: relative;
  width: 100%;
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

const SelectArrow = styled.div`
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: rgba(255, 255, 255, 0.7);
`;

const TierOptionsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  width: 100%;
`;

const TierCard = styled.div<{ selected: boolean }>`
  padding: 1rem;
  background-color: ${props => props.selected ? 'rgba(52, 152, 219, 0.2)' : 'rgba(255, 255, 255, 0.1)'};
  border: 2px solid ${props => props.selected ? '#3498db' : 'transparent'};
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: ${props => props.selected ? '#3498db' : 'rgba(52, 152, 219, 0.5)'};
    background-color: ${props => props.selected ? 'rgba(52, 152, 219, 0.2)' : 'rgba(255, 255, 255, 0.15)'};
  }
`;

const TierName = styled.h4`
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
`;

const TierDescription = styled.p`
  margin: 0;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
`;

const StageOptionsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  width: 100%;
`;

const StageOption = styled.div<{ selected: boolean }>`
  padding: 0.8rem 1rem;
  background-color: ${props => props.selected ? 'rgba(46, 204, 113, 0.2)' : 'rgba(255, 255, 255, 0.1)'};
  border: 2px solid ${props => props.selected ? '#2ecc71' : 'transparent'};
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: ${props => props.selected ? '#2ecc71' : 'rgba(46, 204, 113, 0.5)'};
    background-color: ${props => props.selected ? 'rgba(46, 204, 113, 0.2)' : 'rgba(255, 255, 255, 0.15)'};
  }
`;

const StageName = styled.h4`
  margin: 0;
  font-size: 1.1rem;
`;

const InfoText = styled.p`
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 0.5rem;
  font-style: italic;
`;

const NumberInput = styled.input.attrs({ type: 'number' })`
  width: 100%;
  padding: 0.8rem;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  color: #f0f0f0;
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: #3498db;
  }
`;

const Checkbox = styled.input.attrs({ type: 'checkbox' })`
  margin-right: 10px;
  width: 18px;
  height: 18px;
  cursor: pointer;
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  font-size: 1rem;
  color: #f0f0f0;
  margin-top: 0.5rem;
  cursor: pointer;
`;

const InputRow = styled.div`
  display: flex;
  gap: 1rem;
  align-items: center;
`;

const InputGroup = styled.div`
  flex: 1;
`;

const NextButton = styled.button`
  padding: 0.8rem 2rem;
  margin-top: 2rem;
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

const TournamentSetup: React.FC<TournamentSetupProps> = ({ onNext }) => {
  const { config, setTournamentOption } = useSetup();
  const { 
    tier, 
    stage, 
    payoutStructure, 
    buyInAmount,
    levelDuration,
    startingChips,
    totalPlayers,
    startingBigBlind,
    startingSmallBlind,
    anteEnabled,
    anteStartLevel,
    anteValueType,
    rebuyOption, 
    rebuyLevelCutoff 
  } = config.tournament;
  
  const handleTierChange = (selectedTier: TournamentTier) => {
    // Set the tier
    setTournamentOption('tier', selectedTier);
    
    // Update default values based on tier
    const tierDefaults = {
      Local: { totalPlayers: 50, buyInAmount: 100 },
      Regional: { totalPlayers: 200, buyInAmount: 400 },
      National: { totalPlayers: 500, buyInAmount: 2000 },
      International: { totalPlayers: 5000, buyInAmount: 10000 }
    };
    
    // Set default values for this tier
    setTournamentOption('totalPlayers', tierDefaults[selectedTier].totalPlayers);
    setTournamentOption('buyInAmount', tierDefaults[selectedTier].buyInAmount);
  };
  
  const handleStageChange = (selectedStage: TournamentStage) => {
    setTournamentOption('stage', selectedStage);
  };
  
  const handlePayoutStructureChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTournamentOption('payoutStructure', e.target.value);
  };
  
  const handleBuyInAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setTournamentOption('buyInAmount', value);
    }
  };
  
  const handleLevelDurationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setTournamentOption('levelDuration', value);
    }
  };
  
  const handleStartingChipsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setTournamentOption('startingChips', value);
    }
  };
  
  const handleTotalPlayersChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setTournamentOption('totalPlayers', value);
    }
  };
  
  const handleStartingBigBlindChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setTournamentOption('startingBigBlind', value);
      // Small blind is half of big blind
      setTournamentOption('startingSmallBlind', Math.floor(value / 2));
    }
  };
  
  const handleAnteEnabledChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTournamentOption('anteEnabled', e.target.checked);
  };
  
  const handleAnteStartLevelChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setTournamentOption('anteStartLevel', value);
    }
  };
  
  const handleAnteValueTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTournamentOption('anteValueType', e.target.value as AnteValueType);
  };
  
  const handleRebuyOptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTournamentOption('rebuyOption', e.target.checked);
  };
  
  const handleRebuyLevelCutoffChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setTournamentOption('rebuyLevelCutoff', value);
    }
  };
  
  // Round to 1 significant figure
  const roundToOneSignificantFigure = (num: number): number => {
    if (num === 0) return 0;
    
    const magnitude = Math.pow(10, Math.floor(Math.log10(num)));
    return Math.round(num / magnitude) * magnitude;
  };

  // Calculate the blind structure at a specific level
  const calculateBlindsAtLevel = (level: number): {bb: number, sb: number, ante: number} => {
    // Starting values
    let bb = startingBigBlind;
    let sb = startingSmallBlind;
    
    // Calculate blinds for this level
    for (let i = 1; i < level; i++) {
      bb = bb * 1.5; // Multiply by 1.5x
      bb = roundToOneSignificantFigure(bb); // Round to 1 significant figure
      sb = Math.floor(bb / 2);
    }
    
    // Calculate ante if enabled and if this level is at or after ante start level
    let ante = 0;
    if (anteEnabled && level >= anteStartLevel) {
      switch(anteValueType) {
        case 'SB':
          ante = sb;
          break;
        case 'BB':
          ante = bb;
          break;
        case '2xBB':
          ante = bb * 2;
          break;
        default:
          ante = bb;
      }
    }
    
    return { bb, sb, ante };
  };
  
  // Tournament tier descriptions
  const tierDescriptions: Record<TournamentTier, string> = {
    Local: "Home games and small local tournaments. Players are more casual with a wide range of skill levels.",
    Regional: "Mid-sized tournaments at casinos or poker clubs. More serious players but still with diverse skill levels.",
    National: "Large tournaments with substantial prizepools. Many strong regular players and some professionals.",
    International: "Elite level tournaments with the highest stakes. Mostly professional players and top amateurs."
  };
  
  // Tournament stage descriptions
  const stageDescriptions: Record<TournamentStage, string> = {
    Beginning: "Initial stages with deep stacks relative to blinds. Most players are still in the tournament.",
    Mid: "Medium stacks, rising blinds, players starting to adapt their strategies.",
    "Money Bubble": "Approaching the money bubble where play tightens as players try to survive.",
    "Post Bubble": "After reaching the money, play loosens up as players aim for final table.",
    "Final Table": "Final table play with ICM considerations and high pressure situations."
  };
  
  return (
    <Container>
      <Title>Tournament Setup</Title>
      
      <FormContainer>
        <FormGroup>
          <Label>Tournament Tier</Label>
          <TierOptionsContainer>
            {Object.entries(tierDescriptions).map(([tierName, description]) => (
              <TierCard 
                key={tierName}
                selected={tier === tierName}
                onClick={() => handleTierChange(tierName as TournamentTier)}
              >
                <TierName>{tierName}</TierName>
                <TierDescription>{description}</TierDescription>
              </TierCard>
            ))}
          </TierOptionsContainer>
          <InfoText>
            Tournament tier determines the distribution of player archetypes you'll face
          </InfoText>
        </FormGroup>
        
        <FormGroup>
          <Label>Tournament Stage</Label>
          <StageOptionsContainer>
            {Object.entries(stageDescriptions).map(([stageName, description]) => (
              <StageOption 
                key={stageName}
                selected={stage === stageName}
                onClick={() => handleStageChange(stageName as TournamentStage)}
              >
                <StageName>{stageName}</StageName>
              </StageOption>
            ))}
          </StageOptionsContainer>
          <InfoText>
            Choose which stage of a tournament to begin your practice. "Beginning" starts at the first level, 
            while other options fast-forward to different stages with appropriate blind levels and stack depths.
          </InfoText>
        </FormGroup>
        
        <FormGroup>
          <Label>Tournament Setup</Label>
          <InputRow>
            <InputGroup>
              <Label htmlFor="totalPlayers">Total Players</Label>
              <NumberInput 
                id="totalPlayers"
                min="9"
                max="10000"
                value={totalPlayers} 
                onChange={handleTotalPlayersChange}
              />
            </InputGroup>
            
            <InputGroup>
              <Label htmlFor="buyInAmount">Buy-in Amount ($)</Label>
              <NumberInput 
                id="buyInAmount"
                min="1"
                max="100000"
                value={buyInAmount} 
                onChange={handleBuyInAmountChange}
              />
            </InputGroup>
          </InputRow>
        </FormGroup>

        <FormGroup>
          <Label>Tournament Structure</Label>
          <InputRow>
            <InputGroup>
              <Label htmlFor="startingChips">Starting Chips</Label>
              <NumberInput 
                id="startingChips"
                min="1000"
                max="100000"
                step="1000"
                value={startingChips} 
                onChange={handleStartingChipsChange}
              />
            </InputGroup>
            
            <InputGroup>
              <Label htmlFor="levelDuration">Level Duration (minutes)</Label>
              <NumberInput 
                id="levelDuration"
                min="5"
                max="60"
                value={levelDuration} 
                onChange={handleLevelDurationChange}
              />
            </InputGroup>
          </InputRow>
          <InfoText>
            Level duration determines how quickly blinds increase during the tournament
          </InfoText>
        </FormGroup>
        
        <FormGroup>
          <Label>Blind Structure</Label>
          <InputRow>
            <InputGroup>
              <Label htmlFor="startingBigBlind">Level 1 Big Blind</Label>
              <NumberInput 
                id="startingBigBlind"
                min="10"
                max="1000"
                step="10"
                value={startingBigBlind} 
                onChange={handleStartingBigBlindChange}
              />
            </InputGroup>
            
            <InputGroup>
              <Label htmlFor="startingSmallBlind">Level 1 Small Blind</Label>
              <NumberInput 
                id="startingSmallBlind"
                value={startingSmallBlind}
                disabled
              />
            </InputGroup>
          </InputRow>
          <InfoText>
            Big blinds increase by approximately 1.5x each level. Small blind is always half of big blind.
          </InfoText>
          
          {/* Display blind progression vertically */}
          <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: '5px' }}>
            <p style={{ margin: 0, fontWeight: 'bold', marginBottom: '0.5rem' }}>Blind Progression:</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '300px', overflowY: 'auto' }}>
              {(() => {
                const levels = [];
                let level = 1;
                let currentBB = startingBigBlind;
                const maxLevel = 30; // Safety cap to prevent infinite loop
                
                // Calculate total chips in the tournament
                const totalTournamentChips = totalPlayers * startingChips;
                // 5% threshold of total tournament chips
                const threshold = totalTournamentChips * 0.05;
                
                // Continue generating levels until BB reaches 5% of total tournament chips or we hit max levels
                while (currentBB < threshold && level <= maxLevel) {
                  const blinds = calculateBlindsAtLevel(level);
                  const hasAnte = anteEnabled && level >= anteStartLevel;
                  
                  levels.push(
                    <div key={level} style={{ 
                      padding: '0.3rem 0.5rem', 
                      backgroundColor: 'rgba(255,255,255,0.1)', 
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center'
                    }}>
                      <span style={{ width: '65px', fontWeight: 'bold' }}>Level {level}:</span>
                      <span>{blinds.sb}/{blinds.bb}</span>
                      {hasAnte && (
                        <span style={{ marginLeft: '0.5rem', color: '#f39c12' }}>
                          + {blinds.ante} ante
                        </span>
                      )}
                    </div>
                  );
                  
                  // Calculate BB for next level to check against the 5% threshold
                  currentBB = blinds.bb * 1.5;
                  currentBB = roundToOneSignificantFigure(currentBB);
                  level++;
                }
                
                return levels;
              })()}
            </div>
          </div>
        </FormGroup>
        
        <FormGroup>
          <Label>Ante Options</Label>
          <CheckboxLabel>
            <Checkbox 
              checked={anteEnabled} 
              onChange={handleAnteEnabledChange}
              id="anteEnabled"
            />
            Enable Antes
          </CheckboxLabel>
          
          {anteEnabled && (
            <div style={{ marginTop: '0.8rem' }}>
              <InputRow>
                <InputGroup>
                  <Label htmlFor="anteStartLevel">Ante Starts at Level</Label>
                  <NumberInput 
                    id="anteStartLevel"
                    min="1"
                    max="20"
                    value={anteStartLevel} 
                    onChange={handleAnteStartLevelChange}
                  />
                </InputGroup>
                
                <InputGroup>
                  <Label htmlFor="anteValueType">Ante Value</Label>
                  <SelectContainer>
                    <Select 
                      id="anteValueType" 
                      value={anteValueType}
                      onChange={handleAnteValueTypeChange}
                    >
                      <option value="SB">Small Blind (SB)</option>
                      <option value="BB">Big Blind (BB)</option>
                      <option value="2xBB">2x Big Blind (2xBB)</option>
                    </Select>
                    <SelectArrow>▼</SelectArrow>
                  </SelectContainer>
                </InputGroup>
              </InputRow>
              <InfoText>
                Antes increase pot size and force more action. They'll begin at the specified level.
              </InfoText>
            </div>
          )}
        </FormGroup>
        
        <FormGroup>
          <Label>Rebuy Options</Label>
          <CheckboxLabel>
            <Checkbox 
              checked={rebuyOption} 
              onChange={handleRebuyOptionChange}
              id="rebuyOption"
            />
            Allow rebuys
          </CheckboxLabel>
          
          {rebuyOption && (
            <div style={{ marginTop: '0.5rem', marginLeft: '1.8rem' }}>
              <Label htmlFor="rebuyLevelCutoff">Rebuy available until level</Label>
              <NumberInput 
                id="rebuyLevelCutoff"
                min="1"
                max="20"
                value={rebuyLevelCutoff} 
                onChange={handleRebuyLevelCutoffChange}
                style={{ width: '120px' }}
              />
            </div>
          )}
        </FormGroup>
        
        <FormGroup>
          <Label htmlFor="payoutStructure">Payout Structure</Label>
          <SelectContainer>
            <Select 
              id="payoutStructure" 
              value={payoutStructure}
              onChange={handlePayoutStructureChange}
            >
              <option value="Standard">Standard (15% of field)</option>
              <option value="Top Heavy">Top Heavy (10% of field)</option>
              <option value="Flat">Flat (20% of field)</option>
            </Select>
            <SelectArrow>▼</SelectArrow>
          </SelectContainer>
          <InfoText>
            Payout structure affects ICM considerations in final stages
          </InfoText>
        </FormGroup>
      </FormContainer>
      
      <NextButton onClick={onNext}>
        Continue to Player Distribution
      </NextButton>
    </Container>
  );
};

export default TournamentSetup;