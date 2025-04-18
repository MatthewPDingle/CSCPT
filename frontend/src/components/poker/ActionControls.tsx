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
  /** Amount of big blind to step bet slider */
  bigBlind: number;
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

// Editable input for bet amount
const BetAmountInput = styled.input.attrs({ type: 'number' })`
  background-color: #34495e;
  color: white;
  padding: 0.5rem;
  border-radius: 4px;
  min-width: 80px;
  text-align: center;
  font-size: 1rem;
  border: none;
  /* hide number spinners */
  &::-webkit-outer-spin-button,
  &::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
  &[type='number'] { -moz-appearance: textfield; }
`;

const ActionControls: React.FC<ActionControlsProps> = ({
  onAction,
  currentBet,
  playerChips,
  isPlayerTurn,
  actionRequest,
  bigBlind
}) => {
  // Use action request data if available, otherwise use defaults
  const callAmount = actionRequest?.callAmount ?? Math.min(currentBet, playerChips);
  const minRaiseAmount = actionRequest?.minRaise ?? currentBet * 2;
  const maxRaiseAmount = actionRequest?.maxRaise ?? playerChips;

  // Determine available actions based on action request
  const availableOptions = actionRequest?.options ?? [];
  const canCheck = availableOptions.includes('CHECK') || currentBet === 0;
  const canCall = availableOptions.includes('CALL') || (currentBet > 0 && playerChips > 0);
  const canRaise = availableOptions.includes('RAISE') || (playerChips > minRaiseAmount && currentBet > 0);
  const canBet = availableOptions.includes('BET') || (playerChips > 0 && currentBet === 0);
  const canFold = availableOptions.includes('FOLD') || !canCheck;

  // Initialize bet amount: start at big blind or minimum raise
  const [betAmount, setBetAmount] = useState(() =>
    canBet ? bigBlind : minRaiseAmount
  );
  
  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = parseInt(e.target.value, 10);
    if (!isNaN(v)) setBetAmount(v);
  };
  // Manual input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let v = parseInt(e.target.value, 10);
    if (isNaN(v) || v < (canBet ? bigBlind : minRaiseAmount)) {
      v = canBet ? bigBlind : minRaiseAmount;
    }
    if (v > (canBet ? playerChips : maxRaiseAmount)) {
      v = canBet ? playerChips : maxRaiseAmount;
    }
    setBetAmount(v);
  };
  
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
      
      // Log more detailed information about action request and available options
      if (actionRequest) {
        console.log("ACTION CONTROLS - Action request details:", {
          player_id: actionRequest.player_id,
          options: actionRequest.options,
          callAmount: actionRequest.callAmount,
          minRaise: actionRequest.minRaise,
          maxRaise: actionRequest.maxRaise,
          handId: actionRequest.handId,
          timestamp: actionRequest.timestamp
        });
        
        // Log calculated available actions
        console.log("ACTION CONTROLS - Calculated available actions:", {
          canCheck,
          canCall,
          canBet,
          canRaise,
          canFold
        });
      }
      
      // Log if the control container should be active
      console.log("ACTION CONTROLS - Container active:", isPlayerTurn);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentBet, playerChips, isPlayerTurn, actionRequest]);
  
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
          Call {callAmount}
        </ActionButton>
      )}
      
      {canBet ? (
        <BetControls>
          <BetSlider
            type="range"
            min={bigBlind}
            max={playerChips}
            step={bigBlind}
            value={betAmount}
            onChange={handleSliderChange}
          />
          <BetAmountInput
            value={betAmount}
            min={bigBlind}
            max={playerChips}
            onChange={handleInputChange}
          />
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
            step={bigBlind}
            value={betAmount}
            onChange={handleSliderChange}
          />
          <BetAmountInput
            value={betAmount}
            min={minRaiseAmount}
            max={maxRaiseAmount}
            onChange={handleInputChange}
          />
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
          All In ({playerChips})
        </ActionButton>
      )}
    </ControlsContainer>
  );
};

export default ActionControls;