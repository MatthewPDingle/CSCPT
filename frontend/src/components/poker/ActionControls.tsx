import React, { useState, useEffect } from 'react';
import styled from 'styled-components';

interface ActionRequest {
  handId: string;
  player_id: string;
  options: string[];
  callAmount: number;
  minRaise: number;
  maxRaise: number;
  timeLimit: number;
  timestamp: string;
}

interface ActionControlsProps {
  onAction: (action: string, amount?: number) => void;
  currentBet: number;
  playerChips: number;
  isPlayerTurn: boolean;
  actionRequest: ActionRequest | null;
}

const ControlsContainer = styled.div<{ $isActive: boolean }>`
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
  opacity: ${props => props.$isActive ? 1 : 0.5};
  pointer-events: ${props => props.$isActive ? 'auto' : 'none'};
  transition: opacity 0.3s ease;
`;

const ActionButton = styled.button<{ $action: string }>`
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
  
  ${props => {
    switch (props.$action) {
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
  isPlayerTurn,
  actionRequest
}) => {
  // Debug logging on props change using useEffect
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") {
      console.log("ActionControls props updated:", {
        currentBet,
        playerChips,
        isPlayerTurn,
        "actionRequest exists": !!actionRequest,
        "actionRequest?.player_id": actionRequest?.player_id,
        "actionRequest?.options": actionRequest?.options
      });
    }
  }, [currentBet, playerChips, isPlayerTurn, actionRequest]);
  
  // Use action request data if available, otherwise use defaults
  const callAmount = actionRequest?.callAmount ?? Math.min(currentBet, playerChips);
  const minRaiseAmount = actionRequest?.minRaise ?? currentBet * 2;
  const maxRaiseAmount = actionRequest?.maxRaise ?? playerChips;
  
  // Initialize bet amount based on action request data or defaults
  const [betAmount, setBetAmount] = useState(minRaiseAmount || playerChips * 0.1);
  
  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setBetAmount(parseInt(e.target.value));
  };
  
  // Determine available actions based on action request or game state
  const availableOptions = actionRequest?.options ?? [];
  
  const canCheck = availableOptions.includes('CHECK') || currentBet === 0;
  const canCall = availableOptions.includes('CALL') || (currentBet > 0 && playerChips > 0);
  const canRaise = availableOptions.includes('RAISE') || (playerChips > minRaiseAmount && currentBet > 0);
  const canBet = availableOptions.includes('BET') || (playerChips > 0 && currentBet === 0);
  const canFold = availableOptions.includes('FOLD') || !canCheck;
  
  return (
    <ControlsContainer $isActive={isPlayerTurn}>
      <ActionButton 
        $action="fold"
        onClick={() => onAction('FOLD')}
        disabled={!canFold || !isPlayerTurn}
      >
        Fold
      </ActionButton>
      
      {canCheck ? (
        <ActionButton 
          $action="check" 
          onClick={() => onAction('CHECK')}
          disabled={!isPlayerTurn}
        >
          Check
        </ActionButton>
      ) : (
        <ActionButton 
          $action="call" 
          onClick={() => onAction('CALL')}
          disabled={!canCall || !isPlayerTurn}
        >
          Call ${callAmount}
        </ActionButton>
      )}
      
      {canBet ? (
        <BetControls>
          <BetSlider 
            type="range" 
            min={Number((playerChips * 0.05).toFixed(0))}
            max={playerChips}
            value={betAmount}
            onChange={handleSliderChange}
          />
          <BetAmount>${betAmount}</BetAmount>
          <ActionButton 
            $action="bet" 
            onClick={() => onAction('BET', betAmount)}
            disabled={!isPlayerTurn}
          >
            Bet
          </ActionButton>
        </BetControls>
      ) : canRaise ? (
        <BetControls>
          <BetSlider 
            type="range" 
            min={minRaiseAmount}
            max={maxRaiseAmount}
            value={betAmount}
            onChange={handleSliderChange}
          />
          <BetAmount>${betAmount}</BetAmount>
          <ActionButton 
            $action="raise" 
            onClick={() => onAction('RAISE', betAmount)}
            disabled={!isPlayerTurn}
          >
            Raise
          </ActionButton>
        </BetControls>
      ) : null}
      
      {availableOptions.includes('ALL_IN') && (
        <ActionButton 
          $action="allIn"
          onClick={() => onAction('ALL_IN', playerChips)}
          disabled={playerChips === 0 || !isPlayerTurn}
        >
          All In (${playerChips})
        </ActionButton>
      )}
    </ControlsContainer>
  );
};

export default ActionControls;