import React, { useState, useRef, useEffect } from 'react';
import styled, { css } from 'styled-components';
import PlayerSeat from './PlayerSeat';
import Card from './Card';
import AnimatingBetChip from './AnimatingBetChip';
import { CARD_STAGGER_DELAY_MS, POST_STREET_PAUSE_MS, POT_FLASH_DURATION_MS, CHIP_ANIMATION_DURATION_MS } from '../../constants/animation';

interface Player {
  id: string;
  name: string;
  chips: number;
  currentBet: number;
  position: number;
  cards: (string | null)[];
  isActive: boolean;
  isCurrent: boolean;
  isDealer: boolean;
  isButton?: boolean;
  isSB?: boolean;
  isBB?: boolean;
  status?: string;
  /** Raw current street bet from server */
  current_bet?: number;
}

interface PokerTableProps {
  players: Player[];
  communityCards: (string | null)[];
  /** Total pot (sum of all street pots) */
  /** Total pot from all completed betting rounds */
  pot: number;
  /** Name of the current betting round (PREFLOP, FLOP, TURN, RIVER, SHOWDOWN) */
  currentRound: string;
  /** Sum of bets in the current active betting round */
  currentStreetTotal?: number;
  /** Chip animations for bet collection at end of round */
  betsToAnimate?: Array<{ playerId: string; amount: number; fromPosition?: { x: string; y: string } }>;
  /** Target position for animating chips (center of currentStreetPot display) */
  animationTargetPosition?: { x: string; y: string };
  /** Callback for PlayerSeat to register its bet-stack position */
  updatePlayerSeatPosition?: (playerId: string, pos: { x: string; y: string }) => void;
  /** Register exact chip-stack position for end-of-hand animations */
  registerChipPosition?: (playerId: string, pos: { x: string; y: string }) => void;
  /** Flash main pot pulse */
  flashMainPot?: boolean;
  /** Flash current street pot pulse */
  flashCurrentStreetPot?: boolean;
  showdownActive?: boolean;
  handResultPlayers?: { player_id: string; cards?: string[] }[];
  /** IDs of players who won the last hand */
  handWinners?: string[];
  currentTurnPlayerId?: string | null;
  showTurnHighlight?: boolean;
  foldedPlayerId?: string | null;
  /** ID of the human player, so we can show their hole cards face-up */
  humanPlayerId?: string;
  /** Animation trigger for upcoming community street reveal */
  pendingStreetReveal?: { street: string; cards: string[] } | null;
  showdownHands?: { player_id: string; cards: string[] }[] | null;
  potWinners?: { pot_id: string; amount: number; winners: { player_id: string; hand_rank: string; share: number }[] }[] | null;
  chipsDistributed?: boolean;
  handVisuallyConcluded?: boolean;
  /** Current animation step from orchestrator */
  currentStep?: { type: string; data: any } | null;
  /** Callback when a visual animation step is fully complete */
  onAnimationDone?: (stepType: string) => void;
}

// Note: animation timing constants are centralized in constants/animation.ts

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

interface PotDisplayProps {
  flash?: boolean;
  $moveDelta?: { dx: number; dy: number };
  $moving?: boolean;
}
const PotDisplay = styled.div<PotDisplayProps>`
  position: absolute;
  top: 24px;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.7rem 1.0rem;
  border-radius: 25px;
  font-weight: bold;
  font-size: 1.2rem;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.5);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  z-index: 2;
  height: 49px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* Pulse animation when pot increases */
  ${props => props.flash && css`
    animation: potFlash 0.6s ease-out;
  `}
  /* Removed pot-to-winner translation; handled via chip animations */

  @keyframes potFlash {
    0% {
      transform: scale(1);
      color: white;
    }
    50% {
      transform: scale(1.2);
      color: #ffd700;
    }
    100% {
      transform: scale(1);
      color: white;
    }
  }
`;
// Display for current street bets
const CurrentRoundPotDisplay = styled(PotDisplay)`
  top: auto;
  bottom: 82px;  // moved up 12px
  height: 26px;
  font-size: 1rem;
  padding: 0.4rem 0.8rem;
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
    { x: '28%', y: 'calc(1% - 40px)' },     // Position 0: Top left (moved up ~80px)
    { x: '72%', y: 'calc(1% - 40px)' },     // Position 1: Top right (moved up ~80px)
    { x: '92%', y: '24%' },    // Position 2: Right top (moved up by 6%)
    { x: '92%', y: '78%' },    // Position 3: Right bottom (moved down by 8%)
    { x: '72%', y: '112%' },   // Position 4: Bottom right (moved down more)
    { x: '50%', y: '112%' },   // Position 5: Bottom middle (moved down more)
    { x: '28%', y: '112%' },   // Position 6: Bottom left (moved down more)
    { x: '8%',  y: '78%' },    // Position 7: Left bottom (moved down by 8%)
    { x: '8%',  y: '24%' }     // Position 8: Left top (moved up by 6%)
  ];
  
  // Dealer position is special
  const dealerPosition = { x: '50%', y: '2%' };  // Top middle (same)
  
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

const PokerTable: React.FC<PokerTableProps> = ({
  players,
  communityCards,
  pot,
  currentRound,
  currentStreetTotal = 0,
  betsToAnimate = [],
  updatePlayerSeatPosition = () => {},
  registerChipPosition = () => {},
  flashMainPot = false,
  flashCurrentStreetPot = false,
  showdownActive = false,
  handResultPlayers,
  handWinners = [],
  currentTurnPlayerId = null,
  showTurnHighlight = false,
  foldedPlayerId = null,
  humanPlayerId,
  pendingStreetReveal = null,
  showdownHands = null,
  potWinners = null,
  chipsDistributed = false,
  handVisuallyConcluded = false,
  currentStep = null,
  onAnimationDone
}) => {
  // Refs for table container and pot display (for animation coordinate calculations)
  const tableContainerRef = useRef<HTMLDivElement>(null);
  const potDisplayRef = useRef<HTMLDivElement>(null);
  const [animationTargetPosition, setAnimationTargetPosition] = useState<{ x: string; y: string }>({ x: '50%', y: '50%' });
  // Compute animation target (center of pot display) relative to table
  /**
   * Handle pendingStreetReveal: stage reveal of new community street cards
   */
  useEffect(() => {
    if (!pendingStreetReveal) return;
    setPendingRevealCount(prev => prev + pendingStreetReveal.cards.length);
  }, [pendingStreetReveal]);
  
  /**
   * Handle showdown_hands_revealed: reveal player hole cards and pause
   */
  useEffect(() => {
    if (!showdownHands) return;
    // Pause to allow players to see revealed hole cards
    const timer = setTimeout(() => onAnimationDone?.('showdown_hands_revealed'), POST_STREET_PAUSE_MS);
    return () => clearTimeout(timer);
  }, [showdownHands, onAnimationDone]);
  
  /**
   * Handle pot_winners_determined: animate pots to winners
   */
  // Pot-to-player animations are handled by potToPlayerAnimations state
  
  /**
   * Handle chips_distributed: pot amounts added to player chip stacks
   */
  // Chips distribution updates are reflected via gameState players' chip counts
  
  /**
   * Handle hand_visually_concluded: final winner pulse complete
   */
  // Winner seat pulse handled via isWinner prop and CSS animation
  useEffect(() => {
    if (potDisplayRef.current && tableContainerRef.current) {
      const potRect = potDisplayRef.current.getBoundingClientRect();
      const tableRect = tableContainerRef.current.getBoundingClientRect();
      const relX = ((potRect.left + potRect.width / 2 - tableRect.left) / tableRect.width) * 100;
      const relY = ((potRect.top + potRect.height / 2 - tableRect.top) / tableRect.height) * 100;
      setAnimationTargetPosition({ x: `${relX}%`, y: `${relY}%` });
    }
  }, [currentStreetTotal, flashCurrentStreetPot]);
  // Displayed pot and flash controlled by hook props and updates directly on pot changes
  const [flashPot, setFlashPot] = useState<boolean>(false);
  const [displayedPot, setDisplayedPot] = useState<number>(pot);
  useEffect(() => {
    if (pot !== displayedPot) {
      setDisplayedPot(pot);
      setFlashPot(true);
      setTimeout(() => setFlashPot(false), POT_FLASH_DURATION_MS);
    }
  }, [pot]);
  // Ensure players array is valid and handle potential undefined/null values
  const validPlayers = Array.isArray(players) ? players.filter(p => p && typeof p === 'object') : [];
  console.log(`Valid players: ${validPlayers.length}/${players?.length || 0}`);
  
  // Use all valid players, including folded ones
  const filteredPlayers = validPlayers;
  console.log(`Total players: ${filteredPlayers.length}`);
  
  // Ensure communityCards is an array
  const validCommunityCards = Array.isArray(communityCards) ? communityCards : [];
  // Pad community cards to exactly 5 with nulls if necessary
  const paddedCommunityCards = [...validCommunityCards];
  while (paddedCommunityCards.length < 5) {
    paddedCommunityCards.push(null);
  }
  
  // State for staged community card reveal
  const [displayCount, setDisplayCount] = useState<number>(validCommunityCards.length);
  const [pendingRevealCount, setPendingRevealCount] = useState<number>(0);
  const prevCommCountRef = useRef<number>(validCommunityCards.length);
  
  // Audio refs for card deal sounds
  const flopAudioRef = useRef<HTMLAudioElement | null>(null);
  const cardAudioRef = useRef<HTMLAudioElement | null>(null);
  
  // Initialize audio elements once
  useEffect(() => {
    try {
      const baseUrl = window.location.origin;
      flopAudioRef.current = new Audio(`${baseUrl}/audio/3cards.wav`);
      flopAudioRef.current.volume = 1.0;
      cardAudioRef.current = new Audio(`${baseUrl}/audio/card.wav`);
      cardAudioRef.current.volume = 1.0;
    } catch (e) {
      console.error('Error initializing deal audio in PokerTable:', e);
    }
  }, []);
  
  // Detect changes in communityCards prop to stage reveal
  useEffect(() => {
    const newCount = validCommunityCards.length;
    const prevCount = prevCommCountRef.current;
    if (newCount > prevCount) {
      setPendingRevealCount(newCount - prevCount);
      setDisplayCount(prevCount);
    } else if (newCount === 0) {
      // New hand reset
      setDisplayCount(0);
      setPendingRevealCount(0);
    }
    prevCommCountRef.current = newCount;
  }, [validCommunityCards]);
  
  // Reveal staged cards after chip animations complete
  useEffect(() => {
    if (betsToAnimate && betsToAnimate.length === 0 && pendingRevealCount > 0) {
      const count = pendingRevealCount;
      setPendingRevealCount(0);
      // Handle staged reveal of community cards
      if (count >= 3) {
        setDisplayCount(d => d + 3);
        flopAudioRef.current?.play().catch(() => {});
        if (count > 3) {
          setTimeout(() => { setDisplayCount(d => d + 1); cardAudioRef.current?.play().catch(() => {}); }, CARD_STAGGER_DELAY_MS);
          setTimeout(() => { setDisplayCount(d => d + 1); cardAudioRef.current?.play().catch(() => {}); }, CARD_STAGGER_DELAY_MS * 2);
        }
      } else if (count === 2) {
        setDisplayCount(d => d + 1);
        cardAudioRef.current?.play().catch(() => {});
        setTimeout(() => { setDisplayCount(d => d + 1); cardAudioRef.current?.play().catch(() => {}); }, CARD_STAGGER_DELAY_MS);
      } else if (count === 1) {
        setDisplayCount(d => d + 1);
        cardAudioRef.current?.play().catch(() => {});
      }
      // Notify orchestrator when street reveal animation completes
      const totalRevealTime = count * CARD_STAGGER_DELAY_MS + POST_STREET_PAUSE_MS;
      const doneTimer = setTimeout(() => onAnimationDone?.('street_dealt'), totalRevealTime);
      return () => clearTimeout(doneTimer);
    }
  }, [betsToAnimate, pendingRevealCount, onAnimationDone]);

  // Pot-to-winner animations
  const [potMoveDelta, setPotMoveDelta] = useState<{ dx: number; dy: number } | null>(null);
  const [potMoveActive, setPotMoveActive] = useState<boolean>(false);
  // Track per-winner chip animations
  const [potToPlayerAnimations, setPotToPlayerAnimations] = useState<
    Array<{ playerId: string; amount: number }>
  >([]);
  // Highlight flag for winner seat pulse
  const [highlightWinnerActive, setHighlightWinnerActive] = useState<boolean>(false);

  useEffect(() => {
    if (!potWinners) return;
    console.log('PokerTable: Pot winners determined, triggering chip transfer animations', potWinners);
    const anims: Array<{ playerId: string; amount: number }> = [];
    potWinners.forEach(pot => {
      const share = pot.winners.length > 0 ? pot.amount / pot.winners.length : 0;
      pot.winners.forEach(w => {
        anims.push({ playerId: w.player_id, amount: share });
      });
    });
    if (anims.length > 0) {
      setPotToPlayerAnimations(anims);
      setPotMoveActive(true);
      // After chip-transfer animation (0.5s), highlight winners and notify orchestrator
      const transferTime = CHIP_ANIMATION_DURATION_MS;
      const transferTimer = setTimeout(() => {
        setPotMoveActive(false);
        setPotToPlayerAnimations([]);
        setHighlightWinnerActive(true);
        // Pulse duration
        setTimeout(() => setHighlightWinnerActive(false), POT_FLASH_DURATION_MS);
        // Notify orchestrator
        onAnimationDone?.('pot_winners_determined');
      }, transferTime);
      return () => clearTimeout(transferTimer);
    }
  }, [potWinners]);
  
  /**
   * Handle chips_distributed: update chip stacks visually then continue
   */
  useEffect(() => {
    if (chipsDistributed) {
      onAnimationDone?.('chips_distributed');
    }
  }, [chipsDistributed, onAnimationDone]);
  
  /**
   * Handle hand_visually_concluded: show final winner pulse and pause
   */
  useEffect(() => {
    if (handVisuallyConcluded) {
      setHighlightWinnerActive(true);
      const timer = setTimeout(() => {
        setHighlightWinnerActive(false);
        onAnimationDone?.('hand_visually_concluded');
      }, POT_FLASH_DURATION_MS + POST_STREET_PAUSE_MS);
      return () => clearTimeout(timer);
    }
  }, [handVisuallyConcluded, onAnimationDone]);
  
  // Ensure pot is a valid number
  const validPot = typeof pot === 'number' && !isNaN(pot) ? pot : 0;
  
  return (
    <TableContainer ref={tableContainerRef}>
      <TableFelt>
        <PotDisplay
          ref={potDisplayRef}
          flash={flashPot}
        >
          Pot: {displayedPot}
        </PotDisplay>
        {/*
          Override the "Bets" textbox while chip animations are running so it
          immediately resets to 0 and does **not** flash yellow.  This prevents
          the stale amount from being shown during the 0.5 s animation where
          each player's bet stack flies to the main pot.

          The logic is:
            • if there are bet-chip animations in progress (`betsToAnimate` is
              non-empty) – force the value to 0 and disable the flash effect
            • otherwise – use the real street-pot value and the flash flag that
              comes from props
        */}
        <CurrentRoundPotDisplay
          flash={betsToAnimate.length > 0 ? false : flashCurrentStreetPot}
        >
          Bets: {betsToAnimate.length > 0 ? 0 : currentStreetTotal}
        </CurrentRoundPotDisplay>
        
        <CommunityCardsArea>
          {/* Always show existing cards; staged reveal of new cards */}
          {Array.from({ length: 5 }).map((_, i) => {
            const card = i < displayCount ? paddedCommunityCards[i] : null;
            return <Card key={i} card={card} isCommunity />;
          })}
          {/* Chip animation elements for completed bets */}
          {betsToAnimate.map(bet => (
            bet.fromPosition && (
              <AnimatingBetChip
                key={`anim-${bet.playerId}`}
                amount={bet.amount}
                fromPosition={bet.fromPosition}
                targetPosition={animationTargetPosition}
                onEnd={() => {}}
              />
            )
          ))}
        </CommunityCardsArea>
        {/* Pot-to-player animations for end-of-hand */}
        {potMoveActive && potToPlayerAnimations.map((anim, i) => {
          // Find player object and compute seat pixel position
          const playerObj = players.find(p => p.id === anim.playerId);
          if (!playerObj || !potDisplayRef.current || !tableContainerRef.current) return null;
          const tableRect = tableContainerRef.current.getBoundingClientRect();
          const potRect = potDisplayRef.current.getBoundingClientRect();
          // Compute from position (center of pot) relative to table container
          const potCx = (potRect.left - tableRect.left) + potRect.width / 2;
          const potCy = (potRect.top  - tableRect.top ) + potRect.height / 2;
          // Compute target position (seat center) relative to table container
          const seatPercent = getPlayerPosition(playerObj);
          const targetCx = (parseFloat(seatPercent.x) / 100) * tableRect.width;
          const targetCy = (parseFloat(seatPercent.y) / 100) * tableRect.height;
          const fromPos = { x: `${potCx}px`, y: `${potCy}px` };
          const toPos   = { x: `${targetCx}px`, y: `${targetCy}px` };
          return (
            <AnimatingBetChip
              key={`win-anim-${i}-${anim.playerId}`}
              amount={anim.amount}
              fromPosition={fromPos}
              targetPosition={toPos}
              onEnd={() => {}}
            />
          );
        })}
        
        <PlayerPositions>
          {/* Add dealer position */}
          <PlayerSeat
            key="dealer"
            player={{
              id: 'dealer',
              name: 'Dealer',
              chips: 0,
              currentBet: 0,
              position: -1, // Special position for dealer
              cards: [], // Empty cards array for dealer
              isActive: true,
              isCurrent: false,
              isDealer: true,
              isButton: false,
              isSB: false,
              isBB: false,
              status: "ACTIVE"
            }}
            position={getPlayerPosition({
              id: 'dealer',
              name: 'Dealer',
              chips: 0,
              currentBet: 0,
              position: -1,
              cards: [],
              isActive: true,
              isCurrent: false,
              isDealer: true,
              status: "ACTIVE"
            })}
            isHuman={false}
            showdownActive={showdownActive}
            isCurrentTurn={false}
            showTurnHighlight={false}
            isFolding={false}
            updatePlayerSeatPosition={updatePlayerSeatPosition}
            registerChipPosition={registerChipPosition}
            tableContainerRef={tableContainerRef}
          />
          
          {/* Player positions */}
          {filteredPlayers.map((player, index) => {
            try {
              // Ensure player has an ID
              const playerId = player.id || `player_${index}`;
              
              // Create sanitized player object with fallback values
              const sanitizedPlayer: Player = {
                ...player,
                // Use the currentBet from the transformed player data
                currentBet: typeof player.currentBet === 'number' ? player.currentBet : 0,
                id: playerId,
                name: player.name || `Player ${index}`,
                chips: typeof player.chips === 'number' ? player.chips : 1000,
                position: typeof player.position === 'number' ? player.position : index,
                cards: Array.isArray(player.cards) ? player.cards : [null, null],
                // Consider both ACTIVE and ALL_IN as active states
                isActive: player.status === 'ACTIVE' || player.status === 'ALL_IN',
                isCurrent: !!player.isCurrent,
                isDealer: !!player.isDealer,
                isButton: !!player.isButton,
                isSB: !!player.isSB,
                isBB: !!player.isBB
              };
              // If showdown, override cards with revealed hole cards from server
              if (showdownActive && showdownHands) {
                const sh = showdownHands.find(h => h.player_id === playerId);
                if (sh && Array.isArray(sh.cards)) {
                  sanitizedPlayer.cards = sh.cards;
                }
              }
              
              // Get position - use player's actual position from the game state
              const position = getPlayerPosition(sanitizedPlayer);
              
              // Check if this player is the current turn player
              const isPlayerCurrentTurn = playerId === currentTurnPlayerId;
              
              // Check if this player should have the fold highlight
              const isFolding = playerId === foldedPlayerId;
              
              return (
                <PlayerSeat
                  key={playerId}
                  player={sanitizedPlayer}
                  position={position}
                  // Human player sees their hole cards face-up
                  isHuman={humanPlayerId === playerId}
                  showdownActive={showdownActive}
                  isCurrentTurn={isPlayerCurrentTurn}
                  showTurnHighlight={showTurnHighlight && isPlayerCurrentTurn}
                  isFolding={isFolding}
                  updatePlayerSeatPosition={updatePlayerSeatPosition}
                  registerChipPosition={registerChipPosition}
                  tableContainerRef={tableContainerRef}
                  // Suppress static bet display when animating chips to pot
                  suppressBetStack={betsToAnimate.some(b => b.playerId === playerId)}
                  // highlight winning player's cards
                  isWinner={highlightWinnerActive && handWinners.includes(playerId)}
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