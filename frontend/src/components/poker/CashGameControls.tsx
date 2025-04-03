import React, { useState } from 'react';
import styled from 'styled-components';
import { gameApi } from '../../services/api';

// Props definition
interface CashGameControlsProps {
  gameId: string;
  playerId: string;
  chips: number;
  maxBuyIn: number;
  onPlayerUpdate?: () => void;
}

// Styled components
const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  background-color: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 12px;
  margin-top: 10px;
`;

const Title = styled.h3`
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #f0f0f0;
`;

const ButtonsContainer = styled.div`
  display: flex;
  gap: 8px;
`;

const Button = styled.button`
  background-color: #2c3e50;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #34495e;
  }
  
  &:disabled {
    background-color: #7f8c8d;
    cursor: not-allowed;
  }
`;

const RebuyButton = styled(Button)`
  background-color: #27ae60;
  
  &:hover {
    background-color: #2ecc71;
  }
`;

const CashOutButton = styled(Button)`
  background-color: #e74c3c;
  
  &:hover {
    background-color: #c0392b;
  }
`;

const TopUpButton = styled(Button)`
  background-color: #3498db;
  
  &:hover {
    background-color: #2980b9;
  }
`;

const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background-color: #2c3e50;
  border-radius: 8px;
  padding: 20px;
  width: 100%;
  max-width: 400px;
`;

const ModalTitle = styled.h3`
  margin: 0 0 16px 0;
  color: #f0f0f0;
`;

const InputGroup = styled.div`
  margin-bottom: 16px;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 8px;
  color: #f0f0f0;
`;

const Input = styled.input`
  width: 100%;
  padding: 8px;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  color: white;
  font-size: 14px;
`;

const ModalButtons = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 8px;
`;

const CancelButton = styled(Button)`
  background-color: #7f8c8d;
`;

const ConfirmButton = styled(Button)`
  background-color: #2ecc71;
`;

const CashGameControls: React.FC<CashGameControlsProps> = ({ 
  gameId, 
  playerId, 
  chips, 
  maxBuyIn,
  onPlayerUpdate 
}) => {
  const [showRebuyModal, setShowRebuyModal] = useState(false);
  const [rebuyAmount, setRebuyAmount] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  
  // Can only top up if below max buy-in
  const canTopUp = chips < maxBuyIn;
  
  const handleRebuy = async () => {
    if (rebuyAmount <= 0) return;
    
    setIsLoading(true);
    try {
      await gameApi.cashGame.rebuyPlayer(gameId, playerId, rebuyAmount);
      setShowRebuyModal(false);
      if (onPlayerUpdate) onPlayerUpdate();
    } catch (error) {
      console.error('Error during rebuy:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleTopUp = async () => {
    setIsLoading(true);
    try {
      await gameApi.cashGame.topUpPlayer(gameId, playerId);
      if (onPlayerUpdate) onPlayerUpdate();
    } catch (error) {
      console.error('Error during top-up:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleCashOut = async () => {
    setIsLoading(true);
    try {
      await gameApi.cashGame.cashOutPlayer(gameId, playerId);
      if (onPlayerUpdate) onPlayerUpdate();
    } catch (error) {
      console.error('Error during cash-out:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Container>
      <Title>Cash Game Options</Title>
      
      <ButtonsContainer>
        <RebuyButton 
          onClick={() => setShowRebuyModal(true)}
          disabled={isLoading}
        >
          Rebuy
        </RebuyButton>
        
        <TopUpButton 
          onClick={handleTopUp}
          disabled={isLoading || !canTopUp}
          title={canTopUp ? "Top up to maximum buy-in" : "Already at maximum buy-in"}
        >
          Top Up
        </TopUpButton>
        
        <CashOutButton 
          onClick={handleCashOut}
          disabled={isLoading}
        >
          Cash Out
        </CashOutButton>
      </ButtonsContainer>
      
      {showRebuyModal && (
        <Modal>
          <ModalContent>
            <ModalTitle>Rebuy Chips</ModalTitle>
            
            <InputGroup>
              <Label htmlFor="rebuyAmount">Amount to add</Label>
              <Input
                id="rebuyAmount"
                type="number"
                min="1"
                max={maxBuyIn - chips}
                value={rebuyAmount}
                onChange={(e) => setRebuyAmount(parseInt(e.target.value, 10) || 0)}
              />
            </InputGroup>
            
            <ModalButtons>
              <CancelButton onClick={() => setShowRebuyModal(false)}>
                Cancel
              </CancelButton>
              <ConfirmButton onClick={handleRebuy} disabled={rebuyAmount <= 0}>
                Confirm
              </ConfirmButton>
            </ModalButtons>
          </ModalContent>
        </Modal>
      )}
    </Container>
  );
};

export default CashGameControls;