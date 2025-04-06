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
  isButton?: boolean;
  isSB?: boolean;
  isBB?: boolean;
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
// With dealer at top middle and players in position order clockwise
const getPlayerPosition = (player: Player) => {
  // Define the 10 fixed positions around the oval table in clockwise order
  const seatPositions = [
    { x: '28%', y: '12%' },    // Position 0: Top left
    { x: '72%', y: '12%' },    // Position 1: Top right
    { x: '92%', y: '30%' },    // Position 2: Right top
    { x: '92%', y: '70%' },    // Position 3: Right bottom
    { x: '72%', y: '88%' },    // Position 4: Bottom right
    { x: '50%', y: '88%' },    // Position 5: Bottom middle
    { x: '28%', y: '88%' },    // Position 6: Bottom left
    { x: '8%',  y: '70%' },    // Position 7: Left bottom
    { x: '8%',  y: '30%' }     // Position 8: Left top
  ];
  
  // Dealer position is special
  const dealerPosition = { x: '50%', y: '5%' };  // Top middle
  
  // Special cases
  if (player.id === "dealer") {
    return dealerPosition;
  }
  
  // Use player.position if it exists and is valid
  if (typeof player.position === 'number' && 
      player.position >= 0 && 
      player.position < seatPositions.length) {
    return seatPositions[player.position];
  }
  
  // Fallback to ID-based positioning if position property isn't valid
  const playerId = player.id;
  
  // Extract position number if present in the ID
  // This handles cases like "player_0", "player_1", etc.
  const posMatch = playerId.match(/.*?_?(\d+)$/);
  if (posMatch && posMatch[1]) {
    const position = parseInt(posMatch[1], 10);
    if (!isNaN(position) && position >= 0 && position < seatPositions.length) {
      return seatPositions[position];
    }
  }
  
  // Handle common IDs
  if (playerId === "player" || playerId.toLowerCase().includes("you")) {
    return seatPositions[0]; // Human player usually in position 0
  }
  
  // Handle specific player names if present in our system
  const playerNameMap: {[key: string]: number} = {
    "michael": 1,
    "dwight": 2,
    "jim": 3,
    "mose": 4,
    "andy": 5,
    "pam": 6,
    "angela": 7,
    "kevin": 8
  };
  
  // Check if player name is in our mapping
  const lowerPlayerId = playerId.toLowerCase();
  for (const [name, position] of Object.entries(playerNameMap)) {
    if (lowerPlayerId.includes(name)) {
      return seatPositions[position];
    }
  }
  
  // Default fallback - use middle bottom position
  return seatPositions[5];
};

const PokerTable: React.FC<PokerTableProps> = ({ players, communityCards, pot }) => {
  // Ensure players array is valid and handle potential undefined/null values
  const validPlayers = Array.isArray(players) ? players.filter(p => p && typeof p === 'object') : [];
  console.log(`Valid players: ${validPlayers.length}/${players?.length || 0}`);
  
  // Define active players (non-folded)
  const activePlayers = validPlayers.filter(player => player.isActive);
  console.log(`Active players: ${activePlayers.length}`);
  
  // Ensure communityCards is an array
  const validCommunityCards = Array.isArray(communityCards) ? communityCards : [];
  // Pad community cards to exactly 5 with nulls if necessary
  const paddedCommunityCards = [...validCommunityCards];
  while (paddedCommunityCards.length < 5) {
    paddedCommunityCards.push(null);
  }
  
  // Ensure pot is a valid number
  const validPot = typeof pot === 'number' && !isNaN(pot) ? pot : 0;
  
  return (
    <TableContainer>
      <TableFelt>
        <PotDisplay>Pot: ${validPot}</PotDisplay>
        
        <CommunityCardsArea>
          {paddedCommunityCards.slice(0, 5).map((card, index) => (
            <Card key={index} card={card} isCommunity />
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
              isDealer: true,
              isButton: false,
              isSB: false,
              isBB: false
            }}
            position={getPlayerPosition({
              id: 'dealer',
              name: 'Dealer',
              chips: 0,
              position: -1,
              cards: [],
              isActive: true,
              isCurrent: false,
              isDealer: true
            })}
            isHuman={false}
          />
          
          {/* Player positions */}
          {activePlayers.map((player, index) => {
            try {
              // Ensure player has an ID
              const playerId = player.id || `player_${index}`;
              
              // Create sanitized player object with fallback values
              const sanitizedPlayer = {
                ...player,
                id: playerId,
                name: player.name || `Player ${index}`,
                chips: typeof player.chips === 'number' ? player.chips : 1000,
                position: typeof player.position === 'number' ? player.position : index,
                cards: Array.isArray(player.cards) ? player.cards : [null, null],
                isActive: !!player.isActive,
                isCurrent: !!player.isCurrent,
                isDealer: !!player.isDealer,
                isButton: !!player.isButton,
                isSB: !!player.isSB,
                isBB: !!player.isBB
              };
              
              // Get position - use player's actual position from the game state
              const position = getPlayerPosition(sanitizedPlayer);
              
              return (
                <PlayerSeat
                  key={playerId}
                  player={sanitizedPlayer}
                  position={position}
                  isHuman={playerId.toLowerCase().includes('you')}
                />
              );
            } catch (error) {
              console.error(`Error rendering player at index ${index}:`, error);
              // Return a placeholder in case of error
              return null;
            }
          })}
        </PlayerPositions>
      </TableFelt>
    </TableContainer>
  );
};

export default PokerTable;