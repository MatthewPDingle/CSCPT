import React, { useState } from 'react';
import styled from 'styled-components';

interface ActionControlsProps {
  onAction: (action: string, amount?: number) => void;
  currentBet: number;
  playerChips: number;
  isPlayerTurn: boolean;
}

const ControlsContainer = styled.div<{ isActive: boolean }>`
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  padding: 1rem;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  opacity: ${props => props.isActive ? 1 : 0.5};
  pointer-events: ${props => props.isActive ? 'auto' : 'none'};
  transition: opacity 0.3s ease;
`;

const ActionButton = styled.button<{ action: string }>`
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
  
  ${props => {
    switch (props.action) {
      case 'fold':
        return `
          background-color: #e74c3c;
          color: white;
          &:hover { background-color: #c0392b; }
        `;
      case 'check':
      case 'call':
        return `
          background-color: #3498db;
          color: white;
          &:hover { background-color: #2980b9; }
        `;
      case 'bet':
      case 'raise':
        return `
          background-color: #2ecc71;
          color: white;
          &:hover { background-color: #27ae60; }
        `;
      default:
        return `
          background-color: #95a5a6;
          color: white;
          &:hover { background-color: #7f8c8d; }
        `;
    }
  }}
  
  &:disabled {
    background-color: #95a5a6;
    cursor: not-allowed;
    opacity: 0.7;
  }
`;

const BetControls = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const BetSlider = styled.input`
  width: 200px;
`;

const BetAmount = styled.div`
  background-color: #34495e;
  color: white;
  padding: 0.5rem;
  border-radius: 4px;
  min-width: 80px;
  text-align: center;
`;

const ActionControls: React.FC<ActionControlsProps> = ({
  onAction,
  currentBet,
  playerChips,
  isPlayerTurn
}) => {
  const [betAmount, setBetAmount] = useState(currentBet * 2 || playerChips * 0.1);
  const minBet = currentBet * 2;
  
  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setBetAmount(parseInt(e.target.value));
  };
  
  // Determine available actions based on game state
  const canCheck = currentBet === 0;
  const callAmount = Math.min(currentBet, playerChips);
  const canCall = currentBet > 0 && playerChips > 0;
  
  const minRaise = currentBet * 2;
  const canRaise = playerChips > minRaise && currentBet > 0;
  
  const canBet = playerChips > 0 && currentBet === 0;
  
  return (
    <ControlsContainer isActive={isPlayerTurn}>
      <ActionButton 
        action="fold"
        onClick={() => onAction('fold')}
        disabled={canCheck} // Can't fold if you can check
      >
        Fold
      </ActionButton>
      
      {canCheck ? (
        <ActionButton 
          action="check" 
          onClick={() => onAction('check')}
        >
          Check
        </ActionButton>
      ) : (
        <ActionButton 
          action="call" 
          onClick={() => onAction('call')}
          disabled={!canCall}
        >
          Call ${callAmount}
        </ActionButton>
      )}
      
      {canBet ? (
        <BetControls>
          <BetSlider 
            type="range" 
            min={playerChips * 0.05}
            max={playerChips}
            value={betAmount}
            onChange={handleSliderChange}
          />
          <BetAmount>${betAmount}</BetAmount>
          <ActionButton 
            action="bet" 
            onClick={() => onAction('bet', betAmount)}
          >
            Bet
          </ActionButton>
        </BetControls>
      ) : canRaise ? (
        <BetControls>
          <BetSlider 
            type="range" 
            min={minRaise}
            max={playerChips}
            value={betAmount}
            onChange={handleSliderChange}
          />
          <BetAmount>${betAmount}</BetAmount>
          <ActionButton 
            action="raise" 
            onClick={() => onAction('raise', betAmount)}
          >
            Raise
          </ActionButton>
        </BetControls>
      ) : null}
      
      <ActionButton 
        action="allIn"
        onClick={() => onAction('allIn', playerChips)}
        disabled={playerChips === 0}
      >
        All In (${playerChips})
      </ActionButton>
    </ControlsContainer>
  );
};

export default ActionControls;