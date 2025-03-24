import React from 'react';
import styled from 'styled-components';
import { useSetup } from '../../contexts/SetupContext';

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
  const { buyIn, smallBlind, bigBlind, ante, tableSize } = config.cashGame;
  
  const handleBuyInChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setCashGameOption('buyIn', value);
    }
  };
  
  const handleSmallBlindChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setCashGameOption('smallBlind', value);
      
      // Automatically set big blind to double small blind
      setCashGameOption('bigBlind', value * 2);
    }
  };
  
  const handleBigBlindChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setCashGameOption('bigBlind', value);
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
  
  // Calculate effective stack in big blinds
  const effectiveBigBlinds = bigBlind > 0 ? Math.round(buyIn / bigBlind) : 0;
  
  // Recommend buy-in based on big blind
  const recommendedMinBuyIn = bigBlind * 40;
  const recommendedMaxBuyIn = bigBlind * 200;
  
  return (
    <Container>
      <Title>Cash Game Setup</Title>
      
      <FormContainer>
        <FormGroup>
          <Label htmlFor="buyIn">Buy-in Amount</Label>
          <InputRow>
            <CurrencySymbol>$</CurrencySymbol>
            <Input 
              id="buyIn"
              type="number" 
              min="100"
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
          <InfoText>
            Recommended buy-in range: ${recommendedMinBuyIn} - ${recommendedMaxBuyIn}
          </InfoText>
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