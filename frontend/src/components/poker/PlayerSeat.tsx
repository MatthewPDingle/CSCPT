import React, { useRef, useEffect } from 'react';
import styled from 'styled-components';
import Card from './Card';

interface Player {
  id: string;
  name: string;
  chips: number;
  position: number;
  cards: (string | null)[];
  isActive: boolean;
  isCurrent: boolean;
  isDealer: boolean;
  isButton?: boolean;
  isSB?: boolean;
  isBB?: boolean;
  status?: string;
  currentBet: number;
}

interface PlayerSeatProps {
  player: Player;
  position: { x: string; y: string };
  isHuman: boolean;
  showdownActive?: boolean;
  isCurrentTurn?: boolean;
  showTurnHighlight?: boolean;
  isFolding?: boolean;
  /** Whether this player won the last hand */
  isWinner?: boolean;
  /** Callback to register the bet-stack position for animations */
  updatePlayerSeatPosition: (playerId: string, pos: { x: string; y: string }) => void;
  /** Ref to the table container for coordinate calculations */
  tableContainerRef: React.RefObject<HTMLDivElement | null>;
  /** Suppress static bet stack display (when animating to pot) */
  suppressBetStack?: boolean;
}

interface PositionProps {
  x: string;
  y: string;
  $isActive: boolean;
  $isCurrent: boolean;
  $isCurrentTurn: boolean;
  $showTurnHighlight: boolean;
  $isHuman: boolean;
}

const SeatContainer = styled.div<PositionProps>`
  position: absolute;
  left: ${props => props.x};
  top: ${props => props.y};
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 10;
  transition: all 0.3s ease-in-out;
  
  /* Apply golden highlight when it's the player's turn and highlighting is enabled */
  ${props => props.$isCurrentTurn && props.$showTurnHighlight && `
    box-shadow: 0 0 20px 8px rgba(255, 215, 0, 0.8);
  `}
  
  /* Keep backward compatibility with the old isCurrent property for now */
  ${props => props.$isCurrent && !props.$isCurrentTurn && `
    box-shadow: 0 0 20px 8px rgba(255, 215, 0, 0.8);
  `}
  
  /* Removed the scaling for human player so all players are the same size */
  ${props => props.$isHuman && `
    z-index: 20;
  `}
  /* Note: fold/inactive styling is handled per-component (PlayerInfo, PlayerCards) to avoid graying out bet stacks */
`;

interface PlayerInfoProps {
  $isHuman: boolean;
  $isDealer?: boolean;
  $isFolded?: boolean;
}

const PlayerInfo = styled.div<PlayerInfoProps>`
  background-color: ${props => {
    if (props.$isFolded) return 'rgba(100, 100, 100, 0.75)';
    if (props.$isDealer) return 'rgba(155, 89, 182, 0.85)';
    if (props.$isHuman) return 'rgba(41, 128, 185, 0.85)';
    return 'rgba(0, 0, 0, 0.75)';
  }};
  color: white;
  padding: 0.5rem;
  border-radius: 6px;
  text-align: center;
  margin-bottom: 0.3rem;
  min-width: 100px;
  max-width: 110px;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
  border: ${props => {
    if (props.$isFolded) return 'none';
    if (props.$isDealer) return '2px solid #8e44ad';
    if (props.$isHuman) return '2px solid #3498db';
    return 'none';
  }};
  filter: ${props => props.$isFolded ? 'grayscale(80%)' : 'none'};
`;

const PlayerName = styled.div<{ $isHuman: boolean }>`
  font-weight: bold;
  /* Same font size for all players */
  font-size: 0.85rem;
  margin-bottom: 0.15rem;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ChipCount = styled.div<{ $isHuman: boolean }>`
  /* Same font size for all players */
  font-size: 0.75rem;
  font-weight: ${props => props.$isHuman ? 'bold' : 'normal'};
  background-color: rgba(0, 0, 0, 0.3);
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  display: inline-block;
  margin-top: 0.15rem;
`;

const PlayerCards = styled.div<{ $isHuman: boolean; $isFolded?: boolean }>`
  display: flex;
  gap: 0.3rem;
  /* Same scale for all players */
  transform: scale(0.75);
  transform-origin: top center;
  filter: drop-shadow(0 5px 5px rgba(0, 0, 0, 0.5));
  min-height: 53px; /* Ensure consistent height even without cards */
  opacity: ${props => props.$isFolded ? 0.6 : 1};
`;

// Create a container for the markers
const MarkersContainer = styled.div`
  position: absolute;
  top: -8px;
  right: -8px;
  display: flex;
  flex-direction: row-reverse; // Ensures Button is rightmost
  gap: 4px;
  z-index: 5;
`;

// Base style for all position markers
const PositionMarker = styled.div`
  width: 22px;
  height: 22px;
  border-radius: 50%;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.7rem;
  font-weight: bold;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  border: 1.5px solid white;
`;

// Button marker (Dealer position)
const ButtonMarker = styled(PositionMarker)`
  background-color: #f39c12; // Orange
`;

// Small blind marker 
const SmallBlindMarker = styled(PositionMarker)`
  background-color: #3498db; // Blue
`;

// Big blind marker
const BigBlindMarker = styled(PositionMarker)`
  background-color: #e74c3c; // Red
`;
// Container for bet stack display
// Direction where to place bet stack relative to seat
type StackDirection = 'top' | 'bottom' | 'left' | 'right';
interface BetStackContainerProps {
  amount: number;
  direction: StackDirection;
}
const BetStackContainer = styled.div<BetStackContainerProps>`
  position: absolute;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: rgba(0, 0, 0, 0.6);
  color: #ffd700;
  font-size: 0.75rem;
  font-weight: bold;
  border-radius: 10px;
  z-index: 15;
  opacity: ${props => (props.amount > 0 ? 1 : 0)};
  ${props => {
    switch (props.direction) {
      case 'top':
        // Bottom seats: place badge above, closer to player (moved down)
        return `
          top: -30px;
          left: 50%;
          transform: translateX(-50%);
        `;
      case 'bottom':
        // Top seats: place badge below the player card
        return `
          bottom: -8px;
          left: 50%;
          transform: translateX(-50%);
        `;
      case 'left':
        // Left side seats: badge outside on left, moved further left
        return `
          top: calc(50% - 10px);
          right: calc(0% - 40px);
          transform: translateY(-50%);
        `;
      case 'right':
        // Right side seats: badge outside on right, moved further right
        return `
          top: calc(50% - 10px);
          left: calc(0% - 50px);
          transform: translateY(-50%);
        `;
      default:
        return '';
    }
  }}
`;

const PlayerSeat: React.FC<PlayerSeatProps> = ({
  player,
  position,
  isHuman,
  showdownActive = false,
  isCurrentTurn = false,
  showTurnHighlight = false,
  isFolding = false,
  isWinner = false,
  updatePlayerSeatPosition,
  tableContainerRef,
  suppressBetStack = false
}) => {
  // Ref for player's bet-stack container to register position for chip animations
  const betStackRef = useRef<HTMLDivElement>(null);
  // Report bet-stack position relative to the table container
  useEffect(() => {
    if (betStackRef.current && tableContainerRef.current) {
      const betRect = betStackRef.current.getBoundingClientRect();
      const tableRect = tableContainerRef.current.getBoundingClientRect();
      const relX = ((betRect.left + betRect.width / 2 - tableRect.left) / tableRect.width) * 100;
      const relY = ((betRect.top + betRect.height / 2 - tableRect.top) / tableRect.height) * 100;
      updatePlayerSeatPosition(player.id, { x: `${relX}%`, y: `${relY}%` });
    }
  }, [player.currentBet, updatePlayerSeatPosition, tableContainerRef]);
  // Determine seat direction based on seat index (player.position)
  const seatIndex = player.position;
  let direction: StackDirection;
  if (seatIndex === 0 || seatIndex === 1) {
    // Top seats: badge below
    direction = 'bottom';
  } else if ([4, 5, 6].includes(seatIndex)) {
    // Bottom seats: badge above
    direction = 'top';
  } else if ([7, 8].includes(seatIndex)) {
    // Left side seats: badge to outside left
    direction = 'left';
  } else if ([2, 3].includes(seatIndex)) {
    // Right side seats: badge to outside right
    direction = 'right';
  } else {
    // Fallback: above
    direction = 'top';
  }
  // Check if player is folded based on status (permanent) or is currently folding (transitional)
  // The status-based fold styling persists after a hand, while isFolding is only for transitions
  const isFolded = player.status === 'FOLDED';
  
  // Apply fold style if either condition is true:
  // 1. Status is FOLDED (permanent state from game)
  // 2. isFolding flag is true (temporary transition state during fold animation)
  const shouldShowFoldStyle = isFolded || isFolding;
  
  // Debug logging for fold state and highlighting only in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`PlayerSeat ${player.name}: isFolded=${isFolded}, isFolding=${isFolding}, status=${player.status}, showTurnHighlight=${showTurnHighlight}, isCurrentTurn=${isCurrentTurn}`);
  }
  
  return (
    <SeatContainer 
      x={position.x} 
      y={position.y} 
      $isActive={player.isActive}
      $isCurrent={player.isCurrent}
      $isCurrentTurn={isCurrentTurn}
      $showTurnHighlight={showTurnHighlight}
      $isHuman={isHuman}
    >
      <PlayerInfo
        $isHuman={isHuman}
        $isDealer={player.id === 'dealer'}
        $isFolded={shouldShowFoldStyle}
      >
        <PlayerName $isHuman={isHuman}>{player.name}</PlayerName>
        { !player.isDealer && (
          <ChipCount $isHuman={isHuman}>{player.chips}</ChipCount>
        )}
        
        {/* Container for all markers */}
        {(player.isButton || player.isSB || player.isBB) && (
          <MarkersContainer>
            {player.isButton && <ButtonMarker>B</ButtonMarker>}
            {player.isSB && <SmallBlindMarker>SB</SmallBlindMarker>}
            {player.isBB && <BigBlindMarker>BB</BigBlindMarker>}
          </MarkersContainer>
        )}
      </PlayerInfo>
      {/* Bet stack display (suppress during animation) */}
      {player.currentBet > 0 && !suppressBetStack && (
        <BetStackContainer ref={betStackRef} amount={player.currentBet} direction={direction}>
          <span role="img" aria-label="chips">🪙</span>
          <span>{player.currentBet}</span>
        </BetStackContainer>
      )}
      
      <PlayerCards $isHuman={isHuman} $isFolded={shouldShowFoldStyle}>
        {player.id === 'dealer' ? (
          // Empty div placeholders for dealer (invisible)
          <>
            <div style={{ width: '36px', height: '0px' }}></div>
            <div style={{ width: '36px', height: '0px' }}></div>
          </>
        ) : (
          // Regular cards for players
          player.cards.map((card, index) => {
            const cardFaceDown = !(isHuman || (showdownActive && !shouldShowFoldStyle));
            return (
              <Card
                key={index}
                card={card}
                faceDown={cardFaceDown}
                isCommunity={false}
                // Flash hole cards when player wins
                flash={!cardFaceDown && isWinner}
              />
            );
          })
        )}
      </PlayerCards>
    </SeatContainer>
  );
};

export default PlayerSeat;