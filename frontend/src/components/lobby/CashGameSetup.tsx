import React, { useState } from 'react';
import styled from 'styled-components';
import { useSetup, BettingStructure } from '../../contexts/SetupContext';

// Props definition
interface CashGameSetupProps {
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

const InputRow = styled.div`
  display: flex;
  align-items: center;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.8rem;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  color: white;
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: #3498db;
  }
`;

const CurrencySymbol = styled.span`
  margin-right: 0.5rem;
  font-size: 1.2rem;
  color: #f0f0f0;
`;

const Slider = styled.input.attrs({ type: 'range' })`
  width: 100%;
  margin: 1rem 0;
  -webkit-appearance: none;
  appearance: none;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  outline: none;
  
  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 22px;
    height: 22px;
    background: #3498db;
    border-radius: 50%;
    cursor: pointer;
  }
  
  &::-moz-range-thumb {
    width: 22px;
    height: 22px;
    background: #3498db;
    border-radius: 50%;
    cursor: pointer;
  }
`;

const SliderValue = styled.div`
  text-align: center;
  font-size: 1.1rem;
  font-weight: bold;
  color: #f0f0f0;
  margin-top: 0.5rem;
`;

const BlindStructureContainer = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 1rem;
`;

const BlindInput = styled.div`
  flex: 1;
`;

const InfoText = styled.p`
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 0.5rem;
  font-style: italic;
`;

const StructureContainer = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
`;

const StructureOption = styled.div<{ selected?: boolean }>`
  flex: 1;
  padding: 1rem;
  background-color: ${props => props.selected ? 'rgba(52, 152, 219, 0.3)' : 'rgba(0, 0, 0, 0.3)'};
  border: 1px solid ${props => props.selected ? '#3498db' : 'rgba(255, 255, 255, 0.2)'};
  border-radius: 5px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: rgba(52, 152, 219, 0.2);
  }
`;

const StructureTitle = styled.div`
  font-weight: bold;
  margin-bottom: 0.5rem;
  color: #f0f0f0;
`;

const StructureDescription = styled.div`
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
`;

const BuyInContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const BuyInRange = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
`;

const RakeContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
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

const CashGameSetup: React.FC<CashGameSetupProps> = ({ onNext }) => {
  const { config, setCashGameOption } = useSetup();
  const { 
    buyIn, smallBlind, bigBlind, ante, tableSize, 
    bettingStructure, minBuyIn, maxBuyIn, rakePercentage, rakeCap 
  } = config.cashGame;
  
  // Structure options descriptions
  const bettingStructureInfo = {
    'no_limit': {
      title: 'No Limit',
      description: 'Players can bet any amount up to their stack at any time.'
    },
    'pot_limit': {
      title: 'Pot Limit',
      description: 'Maximum bet is limited to the current pot size.'
    },
    'fixed_limit': {
      title: 'Fixed Limit',
      description: 'Bet sizes and raises are fixed based on blind levels.'
    }
  };
  
  const handleBuyInChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setCashGameOption('buyIn', value);
    }
  };
  
  const handleMinBuyInChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setCashGameOption('minBuyIn', value);
      
      // If current buy-in is less than new minimum, update it
      if (buyIn < value) {
        setCashGameOption('buyIn', value);
      }
    }
  };
  
  const handleMaxBuyInChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setCashGameOption('maxBuyIn', value);
      
      // If current buy-in is more than new maximum, update it
      if (buyIn > value) {
        setCashGameOption('buyIn', value);
      }
    }
  };
  
  const handleSmallBlindChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setCashGameOption('smallBlind', value);
      
      // Automatically set big blind to double small blind
      setCashGameOption('bigBlind', value * 2);
      
      // Update recommended buy-ins
      const newBigBlind = value * 2;
      setCashGameOption('minBuyIn', newBigBlind * 40);
      setCashGameOption('maxBuyIn', newBigBlind * 200);
    }
  };
  
  const handleBigBlindChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setCashGameOption('bigBlind', value);
      
      // Update recommended buy-ins
      setCashGameOption('minBuyIn', value * 40);
      setCashGameOption('maxBuyIn', value * 200);
    }
  };
  
  const handleAnteChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 0) {
      setCashGameOption('ante', value);
    }
  };
  
  const handleTableSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    setCashGameOption('tableSize', value);
  };
  
  const handleBettingStructureChange = (structure: BettingStructure) => {
    setCashGameOption('bettingStructure', structure);
  };
  
  const handleRakePercentageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    if (!isNaN(value) && value >= 0 && value <= 0.1) {
      setCashGameOption('rakePercentage', value);
    }
  };
  
  const handleRakeCapChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value >= 0) {
      setCashGameOption('rakeCap', value);
    }
  };
  
  // Calculate effective stack in big blinds
  const effectiveBigBlinds = bigBlind > 0 ? Math.round(buyIn / bigBlind) : 0;
  
  // Format rake percentage for display (0.05 -> 5%)
  const formattedRakePercentage = Math.round(rakePercentage * 100);
  
  return (
    <Container>
      <Title>Cash Game Setup</Title>
      
      <FormContainer>
        <FormGroup>
          <Label>Betting Structure</Label>
          <StructureContainer>
            {Object.entries(bettingStructureInfo).map(([key, info]) => (
              <StructureOption 
                key={key}
                selected={bettingStructure === key}
                onClick={() => handleBettingStructureChange(key as BettingStructure)}
              >
                <StructureTitle>{info.title}</StructureTitle>
                <StructureDescription>{info.description}</StructureDescription>
              </StructureOption>
            ))}
          </StructureContainer>
        </FormGroup>
        
        <FormGroup>
          <Label>Blind Structure</Label>
          <BlindStructureContainer>
            <BlindInput>
              <Label htmlFor="smallBlind">Small Blind</Label>
              <InputRow>
                <CurrencySymbol>$</CurrencySymbol>
                <Input 
                  id="smallBlind"
                  type="number" 
                  min="1"
                  value={smallBlind} 
                  onChange={handleSmallBlindChange}
                />
              </InputRow>
            </BlindInput>
            
            <BlindInput>
              <Label htmlFor="bigBlind">Big Blind</Label>
              <InputRow>
                <CurrencySymbol>$</CurrencySymbol>
                <Input 
                  id="bigBlind"
                  type="number" 
                  min="2"
                  value={bigBlind} 
                  onChange={handleBigBlindChange}
                />
              </InputRow>
            </BlindInput>
          </BlindStructureContainer>
          
          <Label htmlFor="ante" style={{ marginTop: '1rem' }}>Ante</Label>
          <InputRow>
            <CurrencySymbol>$</CurrencySymbol>
            <Input 
              id="ante"
              type="number" 
              min="0"
              value={ante} 
              onChange={handleAnteChange}
            />
          </InputRow>
          <InfoText>
            Optional ante paid by all players before each hand. Set to 0 for no ante.
          </InfoText>
        </FormGroup>
        
        <FormGroup>
          <Label>Buy-in Settings</Label>
          <BuyInContainer>
            <Label htmlFor="buyIn">Default Buy-in Amount</Label>
            <InputRow>
              <CurrencySymbol>$</CurrencySymbol>
              <Input 
                id="buyIn"
                type="number" 
                min={minBuyIn}
                max={maxBuyIn}
                step="100"
                value={buyIn} 
                onChange={handleBuyInChange}
              />
            </InputRow>
            <InfoText>
              Effective stack: {effectiveBigBlinds} big blinds
              {effectiveBigBlinds < 40 && " (Very shallow stack)"}
              {effectiveBigBlinds >= 40 && effectiveBigBlinds < 100 && " (Standard stack)"}
              {effectiveBigBlinds >= 100 && " (Deep stack)"}
            </InfoText>
            
            <BuyInRange>
              <BlindInput>
                <Label htmlFor="minBuyIn">Minimum Buy-in</Label>
                <InputRow>
                  <CurrencySymbol>$</CurrencySymbol>
                  <Input 
                    id="minBuyIn"
                    type="number" 
                    min={bigBlind * 20}
                    step="100"
                    value={minBuyIn} 
                    onChange={handleMinBuyInChange}
                  />
                </InputRow>
                <InfoText>
                  {bigBlind > 0 ? Math.round(minBuyIn / bigBlind) : 0} big blinds
                </InfoText>
              </BlindInput>
              
              <BlindInput>
                <Label htmlFor="maxBuyIn">Maximum Buy-in</Label>
                <InputRow>
                  <CurrencySymbol>$</CurrencySymbol>
                  <Input 
                    id="maxBuyIn"
                    type="number" 
                    min={minBuyIn}
                    step="100"
                    value={maxBuyIn} 
                    onChange={handleMaxBuyInChange}
                  />
                </InputRow>
                <InfoText>
                  {bigBlind > 0 ? Math.round(maxBuyIn / bigBlind) : 0} big blinds
                </InfoText>
              </BlindInput>
            </BuyInRange>
          </BuyInContainer>
        </FormGroup>
        
        <FormGroup>
          <Label>Rake Settings</Label>
          <RakeContainer>
            <Label htmlFor="rakePercentage">Rake Percentage: {formattedRakePercentage}%</Label>
            <Slider
              id="rakePercentage"
              type="range"
              min="0"
              max="0.1"
              step="0.01"
              value={rakePercentage}
              onChange={handleRakePercentageChange}
            />
            
            <Label htmlFor="rakeCap">Rake Cap (in big blinds)</Label>
            <InputRow>
              <Input 
                id="rakeCap"
                type="number" 
                min="0"
                value={rakeCap} 
                onChange={handleRakeCapChange}
              />
            </InputRow>
            <InfoText>
              Maximum rake amount: ${rakeCap * bigBlind}
            </InfoText>
          </RakeContainer>
        </FormGroup>
        
        <FormGroup>
          <Label htmlFor="tableSize">Table Size: {tableSize} players</Label>
          <Slider
            id="tableSize"
            min="2"
            max="9"
            value={tableSize}
            onChange={handleTableSizeChange}
          />
          <SliderValue>{tableSize} players</SliderValue>
          <InfoText>
            You'll always be seated in position 0 as the hero player.
          </InfoText>
        </FormGroup>
      </FormContainer>
      
      <NextButton onClick={onNext}>
        Continue to Player Selection
      </NextButton>
    </Container>
  );
};

export default CashGameSetup;