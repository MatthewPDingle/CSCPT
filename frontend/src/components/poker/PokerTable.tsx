import React from 'react';
import styled from 'styled-components';
import PlayerSeat from './PlayerSeat';
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
}

interface PokerTableProps {
  players: Player[];
  communityCards: (string | null)[];
  pot: number;
}

const TableContainer = styled.div`
  position: relative;
  width: 800px;
  height: 400px;
  border-radius: 200px;
  background-color: #277714;
  border: 15px solid #6d4c41;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3), inset 0 0 50px rgba(0, 0, 0, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
`;

const TableFelt = styled.div`
  width: 90%;
  height: 90%;
  border-radius: 180px;
  background-color: #277714;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
`;

const PotDisplay = styled.div`
  position: absolute;
  top: 20px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 15px;
  font-weight: bold;
`;

const CommunityCardsArea = styled.div`
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
`;

const PlayerPositions = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
`;

// Calculate position for each player around the table
const getPlayerPosition = (position: number, totalPlayers: number) => {
  const angle = (position / totalPlayers) * 2 * Math.PI;
  // Elliptical positions look better on a rectangular monitor
  const x = 50 + 45 * Math.cos(angle - Math.PI/2);
  const y = 50 + 35 * Math.sin(angle - Math.PI/2);
  
  return { x: `${x}%`, y: `${y}%` };
};

const PokerTable: React.FC<PokerTableProps> = ({ players, communityCards, pot }) => {
  const activePlayers = players.filter(player => player.isActive);
  
  return (
    <TableContainer>
      <TableFelt>
        <PotDisplay>Pot: ${pot}</PotDisplay>
        
        <CommunityCardsArea>
          {communityCards.map((card, index) => (
            <Card key={index} card={card} />
          ))}
        </CommunityCardsArea>
        
        <PlayerPositions>
          {activePlayers.map(player => {
            const position = getPlayerPosition(player.position, activePlayers.length);
            
            return (
              <PlayerSeat
                key={player.id}
                player={player}
                position={position}
                isHuman={player.id === 'player'}
              />
            );
          })}
        </PlayerPositions>
      </TableFelt>
    </TableContainer>
  );
};

export default PokerTable;