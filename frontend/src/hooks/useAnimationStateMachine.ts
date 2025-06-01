/**
 * Animation State Machine for Poker Game UI
 * 
 * This implements a proper finite state machine to handle complex
 * animation sequences and eliminate race conditions.
 * 
 * Principles applied:
 * - State Machine Pattern: Predictable state transitions
 * - Single Responsibility: Only manages animation state
 * - Event-Driven: Reacts to game events and animation completions
 * - Immutability: State transitions are pure functions
 */

import { useCallback, useReducer, useRef, useEffect } from 'react';

// Animation states
export enum AnimationState {
  IDLE = 'idle',
  BETTING_ROUND_FINALIZING = 'betting_round_finalizing',
  CHIP_ANIMATION = 'chip_animation',
  POT_FLASHING = 'pot_flashing',
  STREET_DEALING = 'street_dealing',
  CARD_REVEALING = 'card_revealing',
  SHOWDOWN_HANDS_REVEALING = 'showdown_hands_revealing',
  SHOWDOWN_TRANSITION = 'showdown_transition',
  POT_DISTRIBUTION = 'pot_distribution',
  WINNER_HIGHLIGHT = 'winner_highlight'
}

// Animation events
export enum AnimationEvent {
  START_BETTING_ROUND_FINALIZATION = 'start_betting_round_finalization',
  START_CHIP_ANIMATION = 'start_chip_animation',
  CHIP_ANIMATION_COMPLETE = 'chip_animation_complete',
  START_POT_FLASH = 'start_pot_flash',
  POT_FLASH_COMPLETE = 'pot_flash_complete',
  START_STREET_DEALING = 'start_street_dealing',
  STREET_DEALING_COMPLETE = 'street_dealing_complete',
  START_SHOWDOWN_TRANSITION = 'start_showdown_transition',
  SHOWDOWN_TRANSITION_COMPLETE = 'showdown_transition_complete',
  START_SHOWDOWN_HANDS = 'start_showdown_hands',
  SHOWDOWN_HANDS_COMPLETE = 'showdown_hands_complete',
  START_POT_DISTRIBUTION = 'start_pot_distribution',
  POT_DISTRIBUTION_COMPLETE = 'pot_distribution_complete',
  START_WINNER_HIGHLIGHT = 'start_winner_highlight',
  WINNER_HIGHLIGHT_COMPLETE = 'winner_highlight_complete',
  RESET_TO_IDLE = 'reset_to_idle'
}

// Animation context
export interface AnimationContext {
  playerBets?: Array<{ playerId: string; amount: number; fromPosition?: { x: string; y: string } }>;
  totalPot?: number;
  streetName?: string;
  streetCards?: any[];
  showdownHands?: Array<{ player_id: string; cards: string[] }>;
  potWinners?: any[];
  winnerIds?: string[];
}

// State machine state
interface AnimationMachineState {
  currentState: AnimationState;
  context: AnimationContext;
  queuedEvents: Array<{ event: AnimationEvent; context?: AnimationContext }>;
  isProcessing: boolean;
}

// State machine actions
type AnimationAction = 
  | { type: 'TRANSITION'; event: AnimationEvent; context?: AnimationContext }
  | { type: 'QUEUE_EVENT'; event: AnimationEvent; context?: AnimationContext }
  | { type: 'PROCESS_QUEUE' }
  | { type: 'SET_PROCESSING'; isProcessing: boolean };

// State transition function
const animationReducer = (state: AnimationMachineState, action: AnimationAction): AnimationMachineState => {
  switch (action.type) {
    case 'TRANSITION':
      return transitionState(state, action.event, action.context);
    
    case 'QUEUE_EVENT':
      return {
        ...state,
        queuedEvents: [...state.queuedEvents, { event: action.event, context: action.context }]
      };
    
    case 'PROCESS_QUEUE':
      if (state.queuedEvents.length === 0 || state.isProcessing) {
        return state;
      }
      
      const nextEvent = state.queuedEvents[0];
      const newState = transitionState(state, nextEvent.event, nextEvent.context);
      return {
        ...newState,
        queuedEvents: state.queuedEvents.slice(1),
        isProcessing: true
      };
    
    case 'SET_PROCESSING':
      return { ...state, isProcessing: action.isProcessing };
    
    default:
      return state;
  }
};

// State transition logic
const transitionState = (
  state: AnimationMachineState, 
  event: AnimationEvent, 
  context?: AnimationContext
): AnimationMachineState => {
  const transitions: Record<AnimationState, Partial<Record<AnimationEvent, AnimationState>>> = {
    [AnimationState.IDLE]: {
      [AnimationEvent.START_BETTING_ROUND_FINALIZATION]: AnimationState.BETTING_ROUND_FINALIZING,
      [AnimationEvent.START_SHOWDOWN_TRANSITION]: AnimationState.SHOWDOWN_TRANSITION,
      [AnimationEvent.START_STREET_DEALING]: AnimationState.STREET_DEALING,
    },
    [AnimationState.BETTING_ROUND_FINALIZING]: {
      [AnimationEvent.START_CHIP_ANIMATION]: AnimationState.CHIP_ANIMATION,
    },
    [AnimationState.CHIP_ANIMATION]: {
      [AnimationEvent.CHIP_ANIMATION_COMPLETE]: AnimationState.POT_FLASHING,
    },
    [AnimationState.POT_FLASHING]: {
      [AnimationEvent.POT_FLASH_COMPLETE]: AnimationState.IDLE,
      [AnimationEvent.START_STREET_DEALING]: AnimationState.STREET_DEALING,
      [AnimationEvent.START_SHOWDOWN_HANDS]: AnimationState.SHOWDOWN_HANDS_REVEALING,
    },
    [AnimationState.STREET_DEALING]: {
      [AnimationEvent.STREET_DEALING_COMPLETE]: AnimationState.CARD_REVEALING,
    },
    [AnimationState.CARD_REVEALING]: {
      [AnimationEvent.RESET_TO_IDLE]: AnimationState.IDLE,
    },
    [AnimationState.SHOWDOWN_HANDS_REVEALING]: {
      [AnimationEvent.SHOWDOWN_HANDS_COMPLETE]: AnimationState.POT_DISTRIBUTION,
    },
    [AnimationState.SHOWDOWN_TRANSITION]: {
      [AnimationEvent.SHOWDOWN_TRANSITION_COMPLETE]: AnimationState.IDLE,
      [AnimationEvent.START_SHOWDOWN_HANDS]: AnimationState.SHOWDOWN_HANDS_REVEALING,
    },
    [AnimationState.POT_DISTRIBUTION]: {
      [AnimationEvent.POT_DISTRIBUTION_COMPLETE]: AnimationState.WINNER_HIGHLIGHT,
    },
    [AnimationState.WINNER_HIGHLIGHT]: {
      [AnimationEvent.WINNER_HIGHLIGHT_COMPLETE]: AnimationState.IDLE,
    },
  };

  const nextState = transitions[state.currentState]?.[event];
  
  if (nextState) {
    return {
      ...state,
      currentState: nextState,
      context: { ...state.context, ...context }
    };
  }

  // Invalid transition - log warning and stay in current state
  console.warn(`[ANIMATION-SM] Invalid transition: ${state.currentState} -> ${event}`);
  return state;
};

// Hook interface
export interface UseAnimationStateMachineReturn {
  currentState: AnimationState;
  context: AnimationContext;
  isAnimating: boolean;
  isInState: (state: AnimationState) => boolean;
  canAcceptGameState: boolean;
  dispatchEvent: (event: AnimationEvent, context?: AnimationContext) => void;
  queueEvent: (event: AnimationEvent, context?: AnimationContext) => void;
}

/**
 * Animation State Machine Hook
 * 
 * Provides a clean interface for managing complex animation sequences
 * and preventing race conditions between animations and game state updates.
 */
export const useAnimationStateMachine = (): UseAnimationStateMachineReturn => {
  const [state, dispatch] = useReducer(animationReducer, {
    currentState: AnimationState.IDLE,
    context: {},
    queuedEvents: [],
    isProcessing: false
  });

  const processingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Process queued events when not processing
  useEffect(() => {
    if (!state.isProcessing && state.queuedEvents.length > 0) {
      dispatch({ type: 'PROCESS_QUEUE' });
    }
  }, [state.isProcessing, state.queuedEvents.length]);

  // Auto-complete processing state after transitions
  useEffect(() => {
    if (state.isProcessing) {
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
      
      // Set a short timeout to mark processing as complete
      processingTimeoutRef.current = setTimeout(() => {
        dispatch({ type: 'SET_PROCESSING', isProcessing: false });
      }, 50);
    }

    return () => {
      if (processingTimeoutRef.current) {
        clearTimeout(processingTimeoutRef.current);
      }
    };
  }, [state.isProcessing]);

  const dispatchEvent = useCallback((event: AnimationEvent, context?: AnimationContext) => {
    console.log(`[ANIMATION-SM] Dispatching event: ${event} in state: ${state.currentState}`);
    dispatch({ type: 'TRANSITION', event, context });
  }, [state.currentState]);

  const queueEvent = useCallback((event: AnimationEvent, context?: AnimationContext) => {
    console.log(`[ANIMATION-SM] Queueing event: ${event}`);
    dispatch({ type: 'QUEUE_EVENT', event, context });
  }, []);

  const isInState = useCallback((checkState: AnimationState) => {
    return state.currentState === checkState;
  }, [state.currentState]);

  // Determine if we should accept game state updates
  const canAcceptGameState = state.currentState === AnimationState.IDLE;

  // Check if any animation is running
  const isAnimating = state.currentState !== AnimationState.IDLE;

  return {
    currentState: state.currentState,
    context: state.context,
    isAnimating,
    isInState,
    canAcceptGameState,
    dispatchEvent,
    queueEvent
  };
};