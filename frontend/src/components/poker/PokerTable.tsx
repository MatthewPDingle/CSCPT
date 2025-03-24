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
  /* Maintain 104:44 ratio (length:width) for a proper poker table */
  width: min(90vw, 900px);
  height: min(90vw * 0.423, 380px); /* 44/104 = 0.423 aspect ratio */
  /* Custom shape for an oval poker table with straight sides and rounded ends */
  background-color: #277714;
  border: 12px solid #6d4c41;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 0 70px rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: visible;
  z-index: 1;
  
  /* Create an oval shape with flat sides and rounded ends */
  border-radius: 22% / 50%;
  position: relative;
`;

const TableFelt = styled.div`
  width: 92%;
  height: 92%; 
  border-radius: 22% / 50%; /* Match container's oval shape */
  background-color: #277714;
  background-image: radial-gradient(ellipse, #2e8b57 0%, #277714 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: inset 0 0 50px rgba(0, 0, 0, 0.4);
`;

const PotDisplay = styled.div`
  position: absolute;
  top: 40px;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.7rem 1.5rem;
  border-radius: 25px;
  font-weight: bold;
  font-size: 1.2rem;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.5);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  z-index: 2;
`;

const CommunityCardsArea = styled.div`
  display: flex;
  justify-content: center;
  gap: 0.7rem;
  margin-bottom: 1rem;
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 15px;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3);
  z-index: 2;
`;

const PlayerPositions = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
`;

// Define fixed positions for proper 10-seat oval poker table
// With dealer at top middle and players in alphabetical order clockwise
const getPlayerPosition = (playerId: string) => {
  // Define the 10 fixed positions around the oval table
  // These positions represent:
  // - 3 seats across the top straight section (top-left, top-middle [dealer], top-right)
  // - 2 seats at right curved section (right-top, right-bottom)
  // - 3 seats across the bottom straight section (bottom-right, bottom-middle, bottom-left)
  // - 2 seats at left curved section (left-bottom, left-top)
  
  const seatPositions = {
    // Dealer position
    "dealer": { x: '50%', y: '5%' },    // Top middle (dealer) - moved even higher
    
    // Player positions in clockwise order from dealer
    "alice":  { x: '72%', y: '12%' },    // Top right (moved more towards middle)
    "bob":    { x: '92%', y: '30%' },    // Right top curved
    "charlie": { x: '92%', y: '70%' },   // Right bottom curved
    "dave":   { x: '72%', y: '88%' },    // Bottom right (moved more towards middle)
    "eve":    { x: '50%', y: '88%' },    // Bottom middle
    "frank":  { x: '28%', y: '88%' },    // Bottom left (moved more towards middle)
    "grace":  { x: '8%',  y: '70%' },    // Left bottom curved
    "hank":   { x: '8%',  y: '30%' },    // Left top curved
    "player": { x: '28%', y: '12%' }     // Top left (moved more towards middle)
  };
  
  // Special cases
  if (playerId === "dealer") {
    return seatPositions.dealer;
  }
  
  // Return position based on player ID
  switch (playerId) {
    case "player": return seatPositions.player;
    case "ai1": return seatPositions.alice;
    case "ai2": return seatPositions.bob;
    case "ai3": return seatPositions.charlie;
    case "ai4": return seatPositions.dave;
    case "ai5": return seatPositions.eve;
    case "ai6": return seatPositions.frank;
    case "ai7": return seatPositions.grace;
    case "ai8": return seatPositions.hank;
    default: return seatPositions.eve; // Fallback
  }
};

const PokerTable: React.FC<PokerTableProps> = ({ players, communityCards, pot }) => {
  const activePlayers = players.filter(player => player.isActive);
  
  return (
    <TableContainer>
      <TableFelt>
        <PotDisplay>Pot: ${pot}</PotDisplay>
        
        <CommunityCardsArea>
          {communityCards.map((card, index) => (
            <Card key={index} card={card} isCommunity={true} />
          ))}
        </CommunityCardsArea>
        
        <PlayerPositions>
          {/* Add dealer position */}
          <PlayerSeat
            key="dealer"
            player={{
              id: 'dealer',
              name: 'Dealer',
              chips: 0,
              position: -1, // Special position for dealer
              cards: [], // Empty cards array for dealer
              isActive: true,
              isCurrent: false,
              isDealer: true
            }}
            position={getPlayerPosition('dealer')}
            isHuman={false}
          />
          
          {/* Player positions */}
          {activePlayers.map(player => {
            const position = getPlayerPosition(player.id);
            
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