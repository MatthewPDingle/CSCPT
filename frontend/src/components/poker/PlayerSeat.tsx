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
}

interface PlayerSeatProps {
  player: Player;
  position: { x: string; y: string };
  isHuman: boolean;
}

interface PositionProps {
  x: string;
  y: string;
  isActive: boolean;
  isCurrent: boolean;
  isHuman: boolean;
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
  
  ${props => props.isCurrent && `
    box-shadow: 0 0 20px 8px rgba(255, 215, 0, 0.8);
  `}
  
  /* Removed the scaling for human player so all players are the same size */
  ${props => props.isHuman && `
    z-index: 20;
  `}
  
  ${props => !props.isActive && `
    opacity: 0.5;
    filter: grayscale(70%);
  `}
`;

interface PlayerInfoProps {
  isHuman: boolean;
  isDealer?: boolean;
}

const PlayerInfo = styled.div<PlayerInfoProps>`
  background-color: ${props => {
    if (props.isDealer) return 'rgba(155, 89, 182, 0.85)';
    if (props.isHuman) return 'rgba(41, 128, 185, 0.85)';
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
    if (props.isDealer) return '2px solid #8e44ad';
    if (props.isHuman) return '2px solid #3498db';
    return 'none';
  }};
`;

const PlayerName = styled.div<{ isHuman: boolean }>`
  font-weight: bold;
  /* Same font size for all players */
  font-size: 0.85rem;
  margin-bottom: 0.15rem;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ChipCount = styled.div<{ isHuman: boolean }>`
  /* Same font size for all players */
  font-size: 0.75rem;
  font-weight: ${props => props.isHuman ? 'bold' : 'normal'};
  background-color: rgba(0, 0, 0, 0.3);
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  display: inline-block;
  margin-top: 0.15rem;
`;

const PlayerCards = styled.div<{ isHuman: boolean }>`
  display: flex;
  gap: 0.3rem;
  /* Same scale for all players */
  transform: scale(0.75);
  transform-origin: top center;
  filter: drop-shadow(0 5px 5px rgba(0, 0, 0, 0.5));
  min-height: 53px; /* Ensure consistent height even without cards */
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

const PlayerSeat: React.FC<PlayerSeatProps> = ({ player, position, isHuman }) => {
  return (
    <SeatContainer 
      x={position.x} 
      y={position.y} 
      isActive={player.isActive}
      isCurrent={player.isCurrent}
      isHuman={isHuman}
    >
      <PlayerInfo isHuman={isHuman} isDealer={player.id === 'dealer'}>
        <PlayerName isHuman={isHuman}>{player.name}</PlayerName>
        <ChipCount isHuman={isHuman}>${player.chips}</ChipCount>
        
        {/* Container for all markers */}
        {(player.isButton || player.isSB || player.isBB) && (
          <MarkersContainer>
            {player.isButton && <ButtonMarker>B</ButtonMarker>}
            {player.isSB && <SmallBlindMarker>SB</SmallBlindMarker>}
            {player.isBB && <BigBlindMarker>BB</BigBlindMarker>}
          </MarkersContainer>
        )}
      </PlayerInfo>
      
      <PlayerCards isHuman={isHuman}>
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
              faceDown={!isHuman} // Only show the human player's cards
            />
          ))
        )}
      </PlayerCards>
    </SeatContainer>
  );
};

export default PlayerSeat;