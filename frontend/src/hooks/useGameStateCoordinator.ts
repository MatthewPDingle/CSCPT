/**
 * Game State Coordinator
 * 
 * Coordinates game state updates with animation sequences to prevent
 * race conditions and ensure smooth UI transitions.
 * 
 * Principles applied:
 * - Single Responsibility: Only manages game state coordination
 * - Observer Pattern: Reacts to animation state changes
 * - Command Pattern: Queues state updates as commands
 * - Strategy Pattern: Different handling based on animation state
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { 
  AnimationState, 
  AnimationEvent, 
  useAnimationStateMachine 
} from './useAnimationStateMachine';

// Game state interface
export interface GameState {
  game_id: string;
  players: Array<{
    player_id: string;
    name: string;
    chips: number;
    position: number;
    status: string;
    current_bet: number;
    total_bet: number;
    cards?: any[] | null;
  }>;
  community_cards: any[];
  pots: Array<{
    name: string;
    amount: number;
    eligible_player_ids: string[];
  }>;
  total_pot: number;
  current_round: string;
  button_position: number;
  current_player_idx: number;
  current_bet: number;
  small_blind: number;
  big_blind: number;
}

// Pending update interface
interface PendingUpdate {
  type: 'game_state' | 'round_bets_finalized' | 'street_dealt' | 'showdown_hands' | 'pot_winners';
  data: any;
  timestamp: number;
}

// Hook interface
export interface UseGameStateCoordinatorReturn {
  gameState: GameState | null;
  currentStreetPot: number;
  accumulatedPot: number;
  betsToAnimate: Array<{ playerId: string; amount: number; fromPosition?: { x: string; y: string } }>;
  flashMainPot: boolean;
  flashCurrentStreetPot: boolean;
  showdownHands: Array<{ player_id: string; cards: string[] }> | null;
  handEvaluations: Array<{ player_id: string; description: string }> | null;
  potWinners: any[] | null;
  
  // Actions
  handleMessage: (message: any) => void;
  notifyAnimationComplete: (animationType: string) => void;
  
  // State queries
  isAnimating: boolean;
  currentAnimationState: AnimationState;
}

/**
 * Game State Coordinator Hook
 * 
 * Manages the coordination between game state updates and animations,
 * ensuring that state updates don't interfere with ongoing animations.
 */
export const useGameStateCoordinator = (): UseGameStateCoordinatorReturn => {
  // Core state
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [currentStreetPot, setCurrentStreetPot] = useState<number>(0);
  const [accumulatedPot, setAccumulatedPot] = useState<number>(0);
  
  // Animation state
  const [betsToAnimate, setBetsToAnimate] = useState<Array<{ playerId: string; amount: number; fromPosition?: { x: string; y: string } }>>([]);
  const [flashMainPot, setFlashMainPot] = useState<boolean>(false);
  const [flashCurrentStreetPot, setFlashCurrentStreetPot] = useState<boolean>(false);
  
  // Showdown state
  const [showdownHands, setShowdownHands] = useState<Array<{ player_id: string; cards: string[] }> | null>(null);
  const [handEvaluations, setHandEvaluations] = useState<Array<{ player_id: string; description: string }> | null>(null);
  const [potWinners, setPotWinners] = useState<any[] | null>(null);
  
  // Animation state machine
  const animationSM = useAnimationStateMachine();
  
  // Pending updates queue
  const [pendingUpdates, setPendingUpdates] = useState<PendingUpdate[]>([]);
  const gameStateRef = useRef<GameState | null>(null);
  
  // Update refs when state changes
  useEffect(() => {
    gameStateRef.current = gameState;
  }, [gameState]);

  // Process pending updates when animation becomes idle
  useEffect(() => {
    if (animationSM.currentState === AnimationState.IDLE && pendingUpdates.length > 0) {
      console.log(`[COORDINATOR] Processing ${pendingUpdates.length} pending updates`);
      
      // Process all pending updates
      const updates = [...pendingUpdates];
      setPendingUpdates([]);
      
      updates.forEach(update => {
        _processUpdateNow(update);
      });
    }
  }, [animationSM.currentState, pendingUpdates]);

  // Handle incoming messages
  const handleMessage = useCallback((message: any) => {
    console.log(`[COORDINATOR] Handling message: ${message.type}, animation state: ${animationSM.currentState}`);
    
    switch (message.type) {
      case 'game_state':
        _handleGameStateUpdate(message.data);
        break;
        
      case 'round_bets_finalized':
        _handleRoundBetsFinalized(message.data);
        break;
        
      case 'street_dealt':
        _handleStreetDealt(message.data);
        break;
        
      case 'showdown_hands_revealed':
        _handleShowdownHands(message.data);
        break;
        
      case 'showdown_transition':
        _handleShowdownTransition();
        break;
        
      case 'pot_winners_determined':
        _handlePotWinners(message.data);
        break;
        
      default:
        console.log(`[COORDINATOR] Unhandled message type: ${message.type}`);
    }
  }, [animationSM.currentState]);

  // Process update immediately
  const _processUpdateNow = useCallback((update: PendingUpdate) => {
    console.log(`[COORDINATOR] Processing update: ${update.type}`);
    
    switch (update.type) {
      case 'game_state':
        setGameState(update.data);
        _updateCurrentStreetPot(update.data);
        break;
        
      case 'round_bets_finalized':
        // This is handled by animation system
        break;
        
      case 'street_dealt':
        // Street dealing is handled by animation system
        break;
        
      case 'showdown_hands':
        setShowdownHands(update.data);
        break;
        
      case 'pot_winners':
        setPotWinners(update.data);
        break;
    }
  }, []);

  // Queue update for later processing
  const _queueUpdate = useCallback((type: PendingUpdate['type'], data: any) => {
    console.log(`[COORDINATOR] Queueing update: ${type}`);
    const update: PendingUpdate = {
      type,
      data,
      timestamp: Date.now()
    };
    setPendingUpdates(prev => [...prev, update]);
  }, []);

  // Handle game state updates
  const _handleGameStateUpdate = useCallback((data: GameState) => {
    if (animationSM.canAcceptGameState) {
      setGameState(data);
      _updateCurrentStreetPot(data);
    } else {
      _queueUpdate('game_state', data);
    }
  }, [animationSM.canAcceptGameState, _queueUpdate]);

  // Handle round bets finalized
  const _handleRoundBetsFinalized = useCallback((data: any) => {
    console.log('[COORDINATOR] Starting betting round finalization');
    
    // Clear current street pot immediately
    setCurrentStreetPot(0);
    
    // Prepare animation data
    const playerBets = data.player_bets?.map((bet: any) => ({
      playerId: bet.player_id,
      amount: bet.amount
    })) || [];
    
    // Start animation sequence
    animationSM.dispatchEvent(AnimationEvent.START_BETTING_ROUND_FINALIZATION);
    animationSM.queueEvent(AnimationEvent.START_CHIP_ANIMATION, { 
      playerBets, 
      totalPot: data.pot 
    });
    
    setBetsToAnimate(playerBets);
    
    // Schedule chip animation completion
    setTimeout(() => {
      setBetsToAnimate([]);
      setAccumulatedPot(data.pot);
      setFlashMainPot(true);
      animationSM.dispatchEvent(AnimationEvent.CHIP_ANIMATION_COMPLETE);
      animationSM.queueEvent(AnimationEvent.START_POT_FLASH);
      
      // Schedule pot flash completion
      setTimeout(() => {
        setFlashMainPot(false);
        animationSM.dispatchEvent(AnimationEvent.POT_FLASH_COMPLETE);
      }, 500); // POT_FLASH_DURATION_MS
      
    }, 500); // CHIP_ANIMATION_DURATION_MS
  }, [animationSM]);

  // Handle street dealt
  const _handleStreetDealt = useCallback((data: any) => {
    console.log(`[COORDINATOR] Street dealt: ${data.street}`);
    
    animationSM.dispatchEvent(AnimationEvent.START_STREET_DEALING, {
      streetName: data.street,
      streetCards: data.cards
    });
    
    // Schedule completion
    setTimeout(() => {
      animationSM.dispatchEvent(AnimationEvent.STREET_DEALING_COMPLETE);
    }, 1000); // Adjust based on actual street dealing time
  }, [animationSM]);

  // Handle showdown transition
  const _handleShowdownTransition = useCallback(() => {
    console.log('[COORDINATOR] Showdown transition');
    
    animationSM.dispatchEvent(AnimationEvent.START_SHOWDOWN_TRANSITION);
    
    // Clear turn-related state immediately
    // This will be handled by the consuming component
    
    setTimeout(() => {
      animationSM.dispatchEvent(AnimationEvent.SHOWDOWN_TRANSITION_COMPLETE);
    }, 100); // Quick transition
  }, [animationSM]);

  // Handle showdown hands
  const _handleShowdownHands = useCallback((data: any) => {
    console.log('[COORDINATOR] Showdown hands revealed');
    
    if (animationSM.canAcceptGameState) {
      setShowdownHands(data.player_hands);
      animationSM.dispatchEvent(AnimationEvent.START_SHOWDOWN_HANDS, {
        showdownHands: data.player_hands
      });
      
      setTimeout(() => {
        animationSM.dispatchEvent(AnimationEvent.SHOWDOWN_HANDS_COMPLETE);
      }, 1500);
    } else {
      _queueUpdate('showdown_hands', data.player_hands);
    }
  }, [animationSM, _queueUpdate]);

  // Handle pot winners
  const _handlePotWinners = useCallback((data: any) => {
    console.log('[COORDINATOR] Pot winners determined');
    
    if (animationSM.canAcceptGameState) {
      setPotWinners(data.pots);
      animationSM.dispatchEvent(AnimationEvent.START_POT_DISTRIBUTION, {
        potWinners: data.pots
      });
      
      setTimeout(() => {
        animationSM.dispatchEvent(AnimationEvent.POT_DISTRIBUTION_COMPLETE);
        animationSM.queueEvent(AnimationEvent.START_WINNER_HIGHLIGHT);
        
        setTimeout(() => {
          animationSM.dispatchEvent(AnimationEvent.WINNER_HIGHLIGHT_COMPLETE);
        }, 500);
      }, 1000);
    } else {
      _queueUpdate('pot_winners', data.pots);
    }
  }, [animationSM, _queueUpdate]);

  // Update current street pot based on game state
  const _updateCurrentStreetPot = useCallback((gameData: GameState) => {
    if (!animationSM.isAnimating) {
      const streetSum = gameData.players.reduce(
        (sum, p) => sum + (p.current_bet || 0),
        0
      );
      setCurrentStreetPot(streetSum);
    }
  }, [animationSM.isAnimating]);

  // Handle animation completion notifications
  const notifyAnimationComplete = useCallback((animationType: string) => {
    console.log(`[COORDINATOR] Animation complete: ${animationType}`);
    
    // Map animation types to events
    const eventMap: Record<string, AnimationEvent> = {
      'round_bets_finalized': AnimationEvent.POT_FLASH_COMPLETE,
      'street_dealt': AnimationEvent.STREET_DEALING_COMPLETE,
      'showdown_hands_revealed': AnimationEvent.SHOWDOWN_HANDS_COMPLETE,
      'pot_winners_determined': AnimationEvent.POT_DISTRIBUTION_COMPLETE,
      'chips_distributed': AnimationEvent.WINNER_HIGHLIGHT_COMPLETE,
      'hand_visually_concluded': AnimationEvent.WINNER_HIGHLIGHT_COMPLETE
    };
    
    const event = eventMap[animationType];
    if (event) {
      animationSM.dispatchEvent(event);
    }
  }, [animationSM]);

  return {
    gameState,
    currentStreetPot,
    accumulatedPot,
    betsToAnimate,
    flashMainPot,
    flashCurrentStreetPot,
    showdownHands,
    handEvaluations,
    potWinners,
    
    handleMessage,
    notifyAnimationComplete,
    
    isAnimating: animationSM.isAnimating,
    currentAnimationState: animationSM.currentState
  };
};