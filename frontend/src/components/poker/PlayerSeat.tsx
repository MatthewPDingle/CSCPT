import React from 'react';
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
}

interface PlayerSeatProps {
  player: Player;
  position: { x: string; y: string };
  isHuman: boolean;
  showdownActive?: boolean;
  isCurrentTurn?: boolean;
  showTurnHighlight?: boolean;
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
  
  ${props => !props.$isActive && `
    opacity: 0.5;
    filter: grayscale(70%);
  `}
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

const PlayerSeat: React.FC<PlayerSeatProps> = ({ 
  player, 
  position, 
  isHuman, 
  showdownActive = false,
  isCurrentTurn = false,
  showTurnHighlight = false
}) => {
  // Check if player is folded based on status
  const isFolded = player.status === 'FOLDED';
  
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
        $isFolded={isFolded}
      >
        <PlayerName $isHuman={isHuman}>{player.name}</PlayerName>
        <ChipCount $isHuman={isHuman}>${player.chips}</ChipCount>
        
        {/* Container for all markers */}
        {(player.isButton || player.isSB || player.isBB) && (
          <MarkersContainer>
            {player.isButton && <ButtonMarker>B</ButtonMarker>}
            {player.isSB && <SmallBlindMarker>SB</SmallBlindMarker>}
            {player.isBB && <BigBlindMarker>BB</BigBlindMarker>}
          </MarkersContainer>
        )}
      </PlayerInfo>
      
      <PlayerCards $isHuman={isHuman} $isFolded={isFolded}>
        {player.id === 'dealer' ? (
          // Empty div placeholders for dealer (invisible)
          <>
            <div style={{ width: '36px', height: '0px' }}></div>
            <div style={{ width: '36px', height: '0px' }}></div>
          </>
        ) : (
          // Regular cards for players
          player.cards.map((card, index) => (
            <Card 
              key={index} 
              card={card}
              faceDown={!(isHuman || (showdownActive && !isFolded))} // Show cards if human player OR during showdown for non-folded players
            />
          ))
        )}
      </PlayerCards>
    </SeatContainer>
  );
};

export default PlayerSeat;