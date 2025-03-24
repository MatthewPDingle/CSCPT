import React from 'react';
import styled from 'styled-components';
import Card from './Card';

interface Player {
  id: string;
  name: string;
  chips: number;
  cards: (string | null)[];
  isActive: boolean;
  isCurrent: boolean;
  isDealer: boolean;
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
  transition: all 0.2s ease-in-out;
  
  ${props => props.isCurrent && `
    box-shadow: 0 0 15px 5px rgba(255, 215, 0, 0.7);
    border-radius: 10px;
  `}
  
  ${props => !props.isActive && `
    opacity: 0.5;
  `}
`;

const PlayerInfo = styled.div`
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.5rem;
  border-radius: 5px;
  text-align: center;
  margin-bottom: 0.5rem;
  min-width: 100px;
`;

const PlayerName = styled.div`
  font-weight: bold;
  font-size: 0.9rem;
  margin-bottom: 0.2rem;
`;

const ChipCount = styled.div`
  font-size: 0.8rem;
`;

const PlayerCards = styled.div`
  display: flex;
  gap: 0.3rem;
  transform: scale(0.8);
`;

const DealerButton = styled.div`
  position: absolute;
  top: -15px;
  right: -15px;
  width: 25px;
  height: 25px;
  border-radius: 50%;
  background-color: white;
  color: black;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.8rem;
  font-weight: bold;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
`;

const PlayerSeat: React.FC<PlayerSeatProps> = ({ player, position, isHuman }) => {
  return (
    <SeatContainer 
      x={position.x} 
      y={position.y} 
      isActive={player.isActive}
      isCurrent={player.isCurrent}
    >
      <PlayerInfo>
        <PlayerName>{player.name}</PlayerName>
        <ChipCount>${player.chips}</ChipCount>
        {player.isDealer && <DealerButton>D</DealerButton>}
      </PlayerInfo>
      
      <PlayerCards>
        {player.cards.map((card, index) => (
          <Card 
            key={index} 
            card={card}
            faceDown={!isHuman} // Only show the human player's cards
          />
        ))}
      </PlayerCards>
    </SeatContainer>
  );
};

export default PlayerSeat;